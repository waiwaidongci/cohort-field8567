from fastapi import APIRouter, Depends, Query
from src.config.database import get_db
from src.utils.auth import current_user
from src.controllers.customer_controller import list_customers
router=APIRouter(prefix="/customers")
@router.get("")
def index(dataset_id:int,search:str=Query(default="",max_length=80),offset:int=Query(default=0,ge=0),limit:int=Query(default=30,ge=1,le=200),db=Depends(get_db),user=Depends(current_user)):
    return list_customers(db,dataset_id,search,offset,limit)
