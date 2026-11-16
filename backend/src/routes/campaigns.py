from fastapi import APIRouter, Depends, Response
from src.config.database import get_db
from src.utils.auth import current_user, editor, admin
from src.schemas.campaign import CampaignInput
from src.controllers import campaign_controller as controller
router=APIRouter(prefix="/campaigns")
@router.get("")
def index(db=Depends(get_db),user=Depends(current_user)):
    return controller.list_campaigns(db)
@router.post("",status_code=201)
def create(data:CampaignInput,db=Depends(get_db),user=Depends(editor)):
    return controller.create_campaign(db,data)
@router.patch("/{campaign_id}/approve")
def approve(campaign_id:int,db=Depends(get_db),user=Depends(admin)):
    return controller.approve_campaign(db,campaign_id)
@router.get("/{campaign_id}/export")
def export(campaign_id:int,db=Depends(get_db),user=Depends(current_user)):
    return Response(controller.export_campaign(db,campaign_id),media_type="text/csv; charset=utf-8",headers={"Content-Disposition":f'attachment; filename="campaign-{campaign_id}.csv"'})
