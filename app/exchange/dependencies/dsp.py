from fastapi import Request
from typing import Any

async def get_dsp_keys(request: Request) -> dict[str, dict[str, Any]]:
    """Dependency that provides DSP configurations."""
    return request.app.state.api_keys
