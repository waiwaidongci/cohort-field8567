from pydantic import BaseModel
class SegmentSummary(BaseModel):
    id: int
    run_id: int
    label: int
    name: str
    size: int
    center: dict[str, float]
    recommendation: str
    model_config = {"from_attributes": True}
