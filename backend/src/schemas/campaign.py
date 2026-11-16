from pydantic import BaseModel, Field
class CampaignInput(BaseModel):
    name: str = Field(min_length=2, max_length=160)
    segment_id: int
    note: str = Field(default="", max_length=1000)
