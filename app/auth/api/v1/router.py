from fastapi import APIRouter, Request, HTTPException, status
from app.auth.schemas.auth import SendOTPRequest, VerifyOTPRequest
from app.shared.utils.loggers import logger
from app.shared.core.exceptions import OTPExpiredException, OTPInvalidException

router = APIRouter(prefix="/auth", tags=["OTP Authentication"])

@router.post("/get-otp")
async def get_otp(
    request: Request,
    payload: SendOTPRequest,
):
    service = request.app.state.auth_service
    return await service.get_otp(payload.mobile)

@router.post("/verify-otp")
async def verify_otp(
    request: Request,
    payload: VerifyOTPRequest,
):
    service = request.app.state.auth_service
    try:     
        return await service.verify_otp(payload.mobile, payload.otp)
    except OTPExpiredException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except OTPInvalidException as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error(f"verify_otp endpoint error | mobile={payload.mobile} | error={e}", exc_info=True)  # ← ADD THIS
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Internal Server Error")