from fastapi import APIRouter, Depends
from src.config.database import get_db
from src.utils.auth import current_user, editor
from src.schemas.run import RunInput
from src.controllers import run_controller as controller
router=APIRouter(prefix="/runs")
@router.get("")
def index(db=Depends(get_db),user=Depends(current_user)):
    return controller.list_runs(db)
@router.post("",status_code=201)
def create(data:RunInput,db=Depends(get_db),user=Depends(editor)):
    return controller.create_run(db,data)
@router.get("/{run_id}")
def detail(run_id:int,db=Depends(get_db),user=Depends(current_user)):
    return controller.run_detail(db,run_id)
