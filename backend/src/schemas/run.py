from pydantic import BaseModel, Field, model_validator
from src.constants.enums import FEATURES
class RunInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    dataset_id: int
    features: list[str] = Field(min_length=2, max_length=4)
    k_min: int = Field(default=2, ge=2, le=6)
    k_max: int = Field(default=6, ge=2, le=6)
    @model_validator(mode="after")
    def validate_config(self):
        if self.k_min > self.k_max or len(set(self.features)) != len(self.features) or any(x not in FEATURES for x in self.features):
            raise ValueError("特征必须为不重复的已知特征，且 K 下限不能超过上限")
        return self
