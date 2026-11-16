from pydantic import BaseModel, Field
class CustomerRow(BaseModel):
    code: str = Field(min_length=1, max_length=80)
    recency: float = Field(ge=0, le=3650, allow_inf_nan=False)
    frequency: float = Field(ge=0, le=100000, allow_inf_nan=False)
    spend: float = Field(ge=0, le=10000000, allow_inf_nan=False)
    learning_days: float = Field(ge=0, le=3650, allow_inf_nan=False)
