from pydantic import BaseModel, Field, model_validator
from src.constants.enums import FEATURES
class ConstraintsInput(BaseModel):
    must_link: list[tuple[str, str]] = Field(default_factory=list, max_length=500)
    cannot_link: list[tuple[str, str]] = Field(default_factory=list, max_length=500)
    size_min: int | None = Field(default=None, ge=1, le=5000)
    size_max: int | None = Field(default=None, ge=1, le=5000)
    @model_validator(mode="after")
    def validate_constraints(self):
        def normalize(pairs, label):
            seen = set()
            for a, b in pairs:
                a, b = a.strip(), b.strip()
                if not a or not b or len(a) > 80 or len(b) > 80:
                    raise ValueError(f"{label}约定含空白或超长匿名编号")
                if a == b:
                    raise ValueError(f"{label}约定中编号 {a} 不能与自身配对")
                seen.add(tuple(sorted((a, b))))
            return sorted(seen)
        must = normalize(self.must_link, "同群")
        cannot = normalize(self.cannot_link, "异群")
        both = set(must) & set(cannot)
        if both:
            a, b = sorted(both)[0]
            raise ValueError(f"关系冲突：{a} 与 {b} 既约定同群又约定异群")
        if self.size_min is not None and self.size_max is not None and self.size_min > self.size_max:
            raise ValueError("每群人数下限不能大于上限")
        self.must_link = must
        self.cannot_link = cannot
        return self
class RunInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    dataset_id: int
    features: list[str] = Field(min_length=2, max_length=4)
    k_min: int = Field(default=2, ge=2, le=6)
    k_max: int = Field(default=6, ge=2, le=6)
    constraints: ConstraintsInput | None = None
    @model_validator(mode="after")
    def validate_config(self):
        if self.k_min > self.k_max or len(set(self.features)) != len(self.features) or any(x not in FEATURES for x in self.features):
            raise ValueError("特征必须为不重复的已知特征，且 K 下限不能超过上限")
        if self.constraints and not (self.constraints.must_link or self.constraints.cannot_link or self.constraints.size_min is not None or self.constraints.size_max is not None):
            self.constraints = None
        return self
