from datetime import datetime
from fastapi import APIRouter, Path
from typing import Annotated

from ..schemas.schemas import SSPUserInfoSchema, SSPResponseSchema
router = APIRouter()

@router.get('/SSP/{id}')
async def respond_ssp(id: int):
        return {
                'id': id,
                'ad_url': f"http://localhost:8000/SSP/{id}",
                'date_shown': datetime.utcnow()
                }

@router.post('/SSP',response_model=SSPResponseSchema)
async def respond_to_ad_request(user_info: SSPUserInfoSchema):
    user_info_json = user_info.model_dump()
    user_info_json['ad_url'] = f"http://localhost:8000/SSP/{id}"
    return SSPResponseSchema(**user_info_json)

