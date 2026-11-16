from fastapi import APIRouter, Depends
from src.config.database import get_db
from src.utils.auth import current_user
from src.controllers.segment_controller import list_segments
from src.schemas.segment import SegmentSummary
router=APIRouter(prefix="/segments")
@router.get("", response_model=list[SegmentSummary])
def index(run_id:int|None=None,db=Depends(get_db),user=Depends(current_user)):
    return list_segments(db,run_id)
