from fastapi import APIRouter, Depends
from src.config.database import get_db
from src.utils.auth import current_user, editor
from src.schemas.dataset import DatasetInput
from src.controllers import dataset_controller as controller
router=APIRouter(prefix="/datasets")
@router.get("")
def index(db=Depends(get_db),user=Depends(current_user)):
    return controller.list_datasets(db)
@router.post("",status_code=201)
def create(data:DatasetInput,db=Depends(get_db),user=Depends(editor)):
    return controller.import_dataset(db,data)
