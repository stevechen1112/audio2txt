from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm

from ..security import login

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/token")
async def issue_token(form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Return a bearer token for API calls
    """
    return login(form_data)
