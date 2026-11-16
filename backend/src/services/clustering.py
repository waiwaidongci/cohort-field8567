import hashlib
import numpy as np
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score
from sklearn.preprocessing import StandardScaler
from src.constants.enums import FEATURES
def cluster_customers(customers, features, k_min=2, k_max=6):
    if len(customers) < max(10, k_max+1):
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
    candidates = []
    fitted = {}
    for k in range(k_min, k_max+1):
        model = KMeans(n_clusters=k, random_state=42, n_init=10).fit(x)
        score = float(silhouette_score(x, model.labels_))
        candidates.append({"k": k, "silhouette": round(score,6), "inertia": round(float(model.inertia_),4)})
        fitted[k] = model
    best = max(candidates, key=lambda c: (c["silhouette"], -c["k"]))
    model = fitted[best["k"]]
    segments = []
    for label in range(best["k"]):
        members = [c for c,l in zip(customers,model.labels_) if int(l)==label]
        center = {f: round(float(np.mean([getattr(c,f) for c in members])),2) for f in FEATURES}
        if center["recency"] >= 55 and center["spend"] >= 700:
            name, recommendation = "沉默高价值", "先提供学习进度回顾，再邀请回归；避免直接用折扣替代价值沟通。"
        elif center["recency"] <= 25 and center["frequency"] >= 8:
            name, recommendation = "活跃深度学习", "邀请主题共创与进阶课程试学，关注复购而非频繁促销。"
        elif center["spend"] < 400:
            name, recommendation = "轻量探索", "优先交付入门内容与课程路径，引导一次小目标完成。"
        else:
            name, recommendation = "稳定潜力", "按近期学习主题推荐课程，观察 14 天内再次学习情况。"
        segments.append({"label":label,"name":name,"size":len(members),"center":center,"customer_ids":[c.id for c in members],"recommendation":recommendation})
    # Preserve every cluster in the preview even if input rows are periodic or sorted.
    rng = np.random.default_rng(42)
    per_cluster = max(1, 180 // best["k"])
    sampled_indices = []
    for label in range(best["k"]):
        indices = np.flatnonzero(model.labels_ == label)
        sampled_indices.extend(rng.choice(indices, size=min(per_cluster, len(indices)), replace=False).tolist())
    sample = [{"code":customers[i].code,"recency":customers[i].recency,"spend":customers[i].spend,"label":int(model.labels_[i])} for i in sorted(sampled_indices)]
    assert {point["label"] for point in sample} == set(int(label) for label in model.labels_), "散点样本必须覆盖所有群组"
    checksum=hashlib.sha256(values.tobytes()).hexdigest()
    return {"best_k":best["k"],"silhouette":best["silhouette"],"candidates":candidates,"sample":sample,"sample_strategy":"stratified_random_seed42","sample_count":len(customers),"features":features,"seed":42,"checksum":checksum}, segments
