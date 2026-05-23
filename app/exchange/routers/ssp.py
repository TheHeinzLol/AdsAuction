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

@router.post('/SSP/{id}', response_model=SSPResponseSchema)
async def respond_to_ad_request(
        id: Annotated[int, Path()],
        user_info: SSPUserInfoSchema
):
    REQUESTS.labels(endpoint='/SSP/id', method='post', status='200').inc()
    user_info_json = user_info.model_dump()
    user_info_json['ad_url'] = f"http://localhost:8000/SSP/{id}"
    return SSPResponseSchema(**user_info_json)

#observ start

from prometheus_client import Counter, generate_latest
from fastapi import Response
REQUESTS = Counter(
        "ad_requests_total",
        "Total HTTP ad requests recieved",
        labelnames=['endpoint', 'method', 'status'],
        namespace='AdExchange',
        )
@router.get('/metrics')
def get_metrics():
    return Response(
            media_type="text/plain",
            content=generate_latest(),
            )
#observ end

