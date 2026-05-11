from datetime import datetime
from fastapi import APIRouter

from ..schemas.schemas import SSPUserInfoSchema, SSPResponseSchema


router = APIRouter()

@router.get('/SSP/{id}')
async def respond_ssp(id: int):
        return {
                'id': id,
                'ads_url': f"http://localhost:8000/SSP/{id}",
                'date_shown': datetime.utcnow()
                }

@router.post('/SSP/{id}', response_model=SSPAnswerSchema)
async def respond_to_ad_request(
        id: int,
        user_info: SSPUserInfoSchema
):
    user_info.ad_url = f"http://localhost:8000/SSP/{id}"
    return user_info

