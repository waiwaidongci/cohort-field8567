import hashlib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from src.constants.enums import FEATURES
from src.services.constraints import ConstraintError, SolverBudgetExceeded, diagnose, has_constraints, prepare_problem, solve_assignment


def _segment_profile(center):
    if center["recency"] >= 55 and center["spend"] >= 700:
        return "沉默高价值", "先提供学习进度回顾，再邀请回归；避免直接用折扣替代价值沟通。"
    if center["recency"] <= 25 and center["frequency"] >= 8:
        return "活跃深度学习", "邀请主题共创与进阶课程试学，关注复购而非频繁促销。"
    if center["spend"] < 400:
        return "轻量探索", "优先交付入门内容与课程路径，引导一次小目标完成。"
    return "稳定潜力", "按近期学习主题推荐课程，观察 14 天内再次学习情况。"


def _build_segments(customers, labels, k):
    segments = []
    for label in range(k):
        members = [c for c, l in zip(customers, labels) if int(l) == label]
        center = {f: round(float(np.mean([getattr(c, f) for c in members])), 2) for f in FEATURES}
        name, recommendation = _segment_profile(center)
        segments.append({"label": label, "name": name, "size": len(members), "center": center, "customer_ids": [c.id for c in members], "recommendation": recommendation})
    return segments


def _stratified_sample(customers, labels, k):
    # Preserve every cluster in the preview even if input rows are periodic or sorted.
    rng = np.random.default_rng(42)
    per_cluster = max(1, 180 // k)
    sampled_indices = []
    for label in range(k):
        indices = np.flatnonzero(labels == label)
        sampled_indices.extend(rng.choice(indices, size=min(per_cluster, len(indices)), replace=False).tolist())
    sample = [{"code": customers[i].code, "recency": customers[i].recency, "spend": customers[i].spend, "label": int(labels[i])} for i in sorted(sampled_indices)]
    assert {point["label"] for point in sample} == set(int(label) for label in labels), "散点样本必须覆盖所有群组"
    return sample


def _fit_constrained(x, problem, k):
    """为候选 K 寻找满足全部约束的分群：回溯求合法指派，再做约束版 Lloyd 迭代。

    每轮指派都由完备搜索完成，因此迭代中任何一轮都不会破坏约束。
    """
    units, sizes, cannot_adj = problem.units, problem.sizes, problem.cannot_adj
    unit_vec = np.array([x[members].mean(axis=0) for members in units])
    # 以无约束 KMeans 的中心作为首次指派的距离引导，保持 seed=42 的初始化传统
    centers = KMeans(n_clusters=k, random_state=42, n_init=10).fit(x).cluster_centers_
    assignment = None
    for _ in range(25):
        dist = np.square(unit_vec[:, None, :] - centers[None, :, :]).sum(axis=2)
        new_assignment = solve_assignment(sizes, cannot_adj, k, problem.size_min, problem.size_max, dist=dist)
        if new_assignment is None:
            return assignment  # 首轮即 None 表示该 K 不可行；之后不会发生（搜索完备）
        if new_assignment == assignment:
            break
        assignment = new_assignment
        centers = np.array([x[[i for u in range(len(units)) if assignment[u] == c for i in units[u]]].mean(axis=0) for c in range(k)])
    return assignment


def _relation_checks(customers, labels, problem):
    label_of = {c.code: int(l) for c, l in zip(customers, labels)}

    def group(no):
        return f"群组 {no + 1:02d}"

    checks = []
    for a, b in problem.must:
        la, lb = label_of[a], label_of[b]
        checks.append({"type": "must_link", "codes": [a, b], "satisfied": la == lb, "detail": f"同在{group(la)}" if la == lb else f"被拆分到{group(la)}与{group(lb)}"})
    for a, b in problem.cannot:
        la, lb = label_of[a], label_of[b]
        checks.append({"type": "cannot_link", "codes": [a, b], "satisfied": la != lb, "detail": f"分别在{group(la)}、{group(lb)}" if la != lb else f"同在{group(la)}"})
    return checks


def cluster_customers(customers, features, k_min=2, k_max=6, constraints=None):
    if len(customers) < max(10, k_max + 1):
        raise ValueError("样本不足：需要至少 10 行且多于最大 K")
    values = np.array([[getattr(c, f) for f in features] for c in customers], dtype=float)
    if not np.isfinite(values).all():
        raise ValueError("数据含空值或非有限数")
    if (values.std(axis=0) < 1e-10).any():
        raise ValueError("所选特征含常量列，请移除此特征后重试")
    scaler = StandardScaler()
    x = scaler.fit_transform(values)
    if np.unique(x, axis=0).shape[0] <= k_max:
        raise ValueError("不同观测行过少，无法可靠比较候选 K")
    problem = prepare_problem(customers, constraints) if has_constraints(constraints) else None
    candidates = []
    fitted = {}
    for k in range(k_min, k_max + 1):
        if problem is None:
            model = KMeans(n_clusters=k, random_state=42, n_init=10).fit(x)
            labels = model.labels_
            inertia = float(model.inertia_)
        else:
            try:
                assignment = _fit_constrained(x, problem, k)
                if assignment is None:
                    candidates.append({"k": k, "feasible": False, "note": diagnose(problem, k)})
                    continue
            except SolverBudgetExceeded:
                raise ValueError("约束组合求解超出计算预算，请减少同群或异群约定后重试")
            labels = np.empty(len(customers), dtype=int)
            for u, members in enumerate(problem.units):
                labels[members] = assignment[u]
            centers = np.array([x[labels == c].mean(axis=0) for c in range(k)])
            inertia = float(np.square(x - centers[labels]).sum())
            score = float(silhouette_score(x, labels))
            candidates.append({"k": k, "silhouette": round(score, 6), "inertia": round(inertia, 4), "feasible": True})
            fitted[k] = labels
            continue
        score = float(silhouette_score(x, labels))
        candidates.append({"k": k, "silhouette": round(score, 6), "inertia": round(inertia, 4)})
        fitted[k] = labels
    feasible = [c for c in candidates if c.get("feasible", True)]
    if not feasible:
        notes = list(dict.fromkeys(c["note"] for c in candidates))
        if len(notes) == 1:
            raise ConstraintError("infeasible", notes[0])
        raise ConstraintError("infeasible", "；".join(f"K={c['k']}：{c['note']}" for c in candidates))
    best = max(feasible, key=lambda c: (c["silhouette"], -c["k"]))
    labels = fitted[best["k"]]
    segments = _build_segments(customers, labels, best["k"])
    sample = _stratified_sample(customers, labels, best["k"])
    checksum = hashlib.sha256(values.tobytes()).hexdigest()
    result = {"best_k": best["k"], "silhouette": best["silhouette"], "candidates": candidates, "sample": sample, "sample_strategy": "stratified_random_seed42", "sample_count": len(customers), "features": features, "seed": 42, "checksum": checksum}
    if problem is not None:
        result["constraints"] = {"must_link": [list(p) for p in problem.must], "cannot_link": [list(p) for p in problem.cannot], "size_min": problem.size_min if problem.size_min_given else None, "size_max": problem.size_max if problem.size_max_given else None}
        result["constraint_checks"] = _relation_checks(customers, labels, problem)
        if problem.size_min_given or problem.size_max_given:
            result["size_checks"] = [{"label": s["label"], "size": s["size"], "min": problem.size_min, "max": problem.size_max, "satisfied": problem.size_min <= s["size"] <= problem.size_max} for s in segments]
    return result, segments
