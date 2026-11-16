"""同群 / 异群 / 每群人数约束的可行分群求解。

同群约定经并查集传递连成不可拆分的组件；求解器以组件为单位做带回溯的
指派搜索，逐客贪心走出的死路会被回退，因此只要存在合法分群就能找到，
不会把搜索顺序造成的失败误判为无解。
"""
import sys
from types import SimpleNamespace


class ConstraintError(ValueError):
    """约束不可行。kind: conflict=关系冲突, capacity=容量不满足, infeasible=各候选 K 均不可行。"""

    def __init__(self, kind, message):
        super().__init__(message)
        self.kind = kind


class SolverBudgetExceeded(RuntimeError):
    pass


def normalize_constraints(constraints):
    c = constraints or {}
    must = sorted({tuple(sorted((str(a).strip(), str(b).strip()))) for a, b in c.get("must_link") or []})
    cannot = sorted({tuple(sorted((str(a).strip(), str(b).strip()))) for a, b in c.get("cannot_link") or []})
    return must, cannot, c.get("size_min"), c.get("size_max")


def has_constraints(constraints):
    must, cannot, size_min, size_max = normalize_constraints(constraints)
    return bool(must or cannot or size_min is not None or size_max is not None)


def prepare_problem(customers, constraints):
    """把匿名编号约定编译成组件级问题；同群关系经传递生效，直接冲突在此抛出。"""
    must, cannot, size_min, size_max = normalize_constraints(constraints)
    codes = [c.code for c in customers]
    index = {code: i for i, code in enumerate(codes)}
    for pair in (*must, *cannot):
        for code in pair:
            if code not in index:
                raise ValueError(f"匿名编号 {code} 不存在于当前数据集")
    n = len(customers)
    parent = list(range(n))

    def find(x):
        while parent[x] != x:
            parent[x] = parent[parent[x]]
            x = parent[x]
        return x

    for a, b in must:
        ra, rb = find(index[a]), find(index[b])
        if ra != rb:
            parent[ra] = rb

    members_of = {}
    for i in range(n):
        members_of.setdefault(find(i), []).append(i)
    units = sorted(members_of.values(), key=lambda members: members[0])
    unit_of = [0] * n
    for u, members in enumerate(units):
        for i in members:
            unit_of[i] = u

    must_adj = {code: set() for code in codes}
    for a, b in must:
        must_adj[a].add(b)
        must_adj[b].add(a)

    def must_path(a, b):
        prev = {a: None}
        queue = [a]
        for cur in queue:
            if cur == b:
                break
            for nxt in sorted(must_adj[cur]):
                if nxt not in prev:
                    prev[nxt] = cur
                    queue.append(nxt)
        path = [b]
        while prev[path[-1]] is not None:
            path.append(prev[path[-1]])
        return list(reversed(path))

    cannot_adj = [set() for _ in units]
    for a, b in cannot:
        ua, ub = unit_of[index[a]], unit_of[index[b]]
        if ua == ub:
            chain = " → ".join(must_path(a, b))
            raise ConstraintError("conflict", f"关系冲突：{a} 与 {b} 约定异群，但同群约定经 {chain} 传递后要求二者同群")
        cannot_adj[ua].add(ub)
        cannot_adj[ub].add(ua)

    return SimpleNamespace(
        units=units,
        codes=codes,
        sizes=[len(members) for members in units],
        cannot_adj=cannot_adj,
        size_min=size_min if size_min is not None else 1,
        size_max=size_max if size_max is not None else n,
        size_min_given=size_min is not None,
        size_max_given=size_max is not None,
        must=must,
        cannot=cannot,
    )


def solve_assignment(sizes, cannot_adj, k, size_min, size_max, dist=None, budget=200000):
    """把组件指派到 k 个群，满足异群关系与每群人数 [size_min, size_max]。

    带回溯的完备搜索：存在合法指派时返回其一（dist 提供时按到群中心的
    距离优先尝试），不存在时返回 None。dist[u][c] 只影响搜索顺序。
    """
    m = len(sizes)
    total = sum(sizes)
    if k * size_min > total or k * size_max < total or any(s > size_max for s in sizes):
        return None
    if sys.getrecursionlimit() < m + 100:
        sys.setrecursionlimit(m + 1000)
    constrained = [u for u in range(m) if sizes[u] > 1 or cannot_adj[u]]
    free = [u for u in range(m) if sizes[u] == 1 and not cannot_adj[u]]
    order = sorted(constrained, key=lambda u: (-len(cannot_adj[u]), -sizes[u], u))
    if dist is not None:
        free_by_cluster = [sorted(free, key=lambda u: (dist[u][c], u)) for c in range(k)]
    else:
        free_by_cluster = [list(free) for _ in range(k)]
    assign = [-1] * m
    cl_size = [0] * k
    placed = [0]
    nodes = [0]

    def capacity_ok():
        remaining = total - placed[0]
        if sum(size_max - s for s in cl_size) < remaining:
            return False
        if sum(max(0, size_min - s) for s in cl_size) > remaining:
            return False
        return True

    def has_option(u):
        for c in range(k):
            if cl_size[c] + sizes[u] > size_max:
                continue
            if any(assign[v] == c for v in cannot_adj[u]):
                continue
            return True
        return False

    def place_free():
        # 人数为 1 且无异群约定的组件可以互换：先补齐各群下限，再按距离填充，
        # 只要总容量够就不会走死路。
        need = [max(0, size_min - s) for s in cl_size]
        if len(free) < sum(need) or len(free) > sum(size_max - s for s in cl_size):
            return False
        unplaced = set(free)
        for c in range(k):
            if not need[c]:
                continue
            for u in free_by_cluster[c]:
                if not need[c]:
                    break
                if u in unplaced:
                    assign[u] = c
                    cl_size[c] += 1
                    unplaced.discard(u)
                    need[c] -= 1
        for u in sorted(unplaced):
            if dist is not None:
                cands = sorted(range(k), key=lambda c: (dist[u][c], c))
            else:
                cands = sorted(range(k), key=lambda c: (cl_size[c], c))
            for c in cands:
                if cl_size[c] < size_max:
                    assign[u] = c
                    cl_size[c] += 1
                    break
        return True

    def dfs(idx):
        if idx == len(order):
            return place_free()
        u = order[idx]
        if dist is not None:
            candidates = sorted(range(k), key=lambda c: (dist[u][c], c))
        else:
            used = sum(1 for s in cl_size if s > 0)
            candidates = range(min(used + 1, k))  # 空群彼此等价，只尝试第一个空群，消除对称重复
        for c in candidates:
            if cl_size[c] + sizes[u] > size_max:
                continue
            if any(assign[v] == c for v in cannot_adj[u]):
                continue
            assign[u] = c
            cl_size[c] += sizes[u]
            placed[0] += sizes[u]
            nodes[0] += 1
            if nodes[0] > budget:
                raise SolverBudgetExceeded()
            ok = capacity_ok() and all(has_option(v) for v in cannot_adj[u] if assign[v] == -1)
            if ok and dfs(idx + 1):
                return True
            assign[u] = -1
            cl_size[c] -= sizes[u]
            placed[0] -= sizes[u]
        return False

    return assign if dfs(0) else None


def find_clique(cannot_adj, r):
    """在异群关系图中找一个 r 阶团，作为不可着色的人证；找不到返回 None。"""
    nodes = sorted(u for u in range(len(cannot_adj)) if cannot_adj[u])
    clique = []

    def dfs(cands):
        if len(clique) == r:
            return True
        for i, v in enumerate(cands):
            nxt = [w for w in cands[i + 1:] if w in cannot_adj[v]]
            if len(clique) + 1 + len(nxt) < r:
                continue
            clique.append(v)
            if dfs(nxt):
                return True
            clique.pop()
        return False

    return list(clique) if dfs(nodes) else None


def diagnose(problem, k):
    """解释候选 K 为何不可行：关系冲突，或容量不满足并给出人数依据。"""
    sizes = problem.sizes
    total = sum(sizes)
    m = len(sizes)
    if solve_assignment([1] * m, problem.cannot_adj, k, 1, m) is None:
        clique = find_clique(problem.cannot_adj, k + 1)
        if clique:
            names = "、".join(problem.codes[problem.units[u][0]] for u in clique)
            return f"关系冲突：{names} 两两约定异群，至少需要 {k + 1} 个群，候选 K={k} 无法满足"
        involved = sum(1 for adj in problem.cannot_adj if adj)
        return f"关系冲突：异群约定在 K={k} 下无法同时满足（涉及 {involved} 个同群组件），请减少异群约定或提高 K 上限"
    if solve_assignment(sizes, [set() for _ in range(m)], k, problem.size_min, problem.size_max) is None:
        for u, s in enumerate(sizes):
            if s > problem.size_max:
                sample = "、".join(problem.codes[i] for i in problem.units[u][:3])
                return f"容量不满足：同群约定把 {s} 位客户连成不可拆分的一体（{sample} 等），超过每群人数上限 {problem.size_max}"
        if m < k:
            return f"容量不满足：同群约定把 {total} 位客户连成 {m} 个不可拆分的组件，无法填满 K={k} 个群（每群至少 {problem.size_min} 人）"
        if k * problem.size_max < total:
            return f"容量不满足：K={k} 且每群上限 {problem.size_max} 人时最多容纳 {k * problem.size_max} 人，少于客户总数 {total}"
        if k * problem.size_min > total:
            return f"容量不满足：K={k} 且每群至少 {problem.size_min} 人时共需 {k * problem.size_min} 人，超过客户总数 {total}"
        comp = sorted((s for s in sizes if s > 1), reverse=True)
        listing = "、".join(str(s) for s in comp[:6]) + ("…" if len(comp) > 6 else "")
        return f"容量不满足：{len(comp)} 个同群组件（{listing} 人）无法按每群 {problem.size_min}–{problem.size_max} 人装入 {k} 个群"
    return f"关系与容量组合冲突：异群约定与每群 {problem.size_min}–{problem.size_max} 人在 K={k} 下无法同时满足，请放宽人数范围或调整约定"
