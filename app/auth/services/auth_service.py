from app.shared.utils.otp_generator import generate_otp, hash_otp
from app.shared.utils.loggers import logger
from app.shared.core.exceptions import OTPExpiredException, OTPInvalidException
from app.auth.jwt.jwt import create_access_token, create_refresh_token
from app.auth.interfaces import OTPStorage, MessagePublisher

class AuthService:
    def __init__(self, otp_storage: OTPStorage, publisher: MessagePublisher):
        self.otp_storage = otp_storage
        self.publisher = publisher

    async def send_otp(self, mobile: str):
        otp = generate_otp()
        logger.info(f"Generated OTP for {mobile}")


        await self.otp_storage.store_otp(mobile, otp)
        logger.info(f"Stored OTP hash in cache for {mobile}")

        await self.publisher.publish_sms_job(mobile, otp)
        logger.info(f"Published OTP job for {mobile}")

        return {
            "message": "OTP sent successfully"
        }

    async def verify_otp(self, mobile: str, otp: str):
        try:
            stored_hash = await self.otp_storage.get_otp(mobile)

            if not stored_hash:
                logger.info(f"No OTP found for {mobile}")
                raise OTPExpiredException("OTP has expired or does not exist")

            input_hash = hash_otp(otp)

            if stored_hash != input_hash:
                logger.info(f"OTP mismatch for {mobile}")
                raise OTPInvalidException("Invalid OTP entered")

            logger.info(f"OTP verified for {mobile}")
            
            access_token = create_access_token(mobile)
            refresh_token = create_refresh_token(mobile)
            
            return {
                "Message": "OTP verified successfully",
                "access_token": access_token,
                "refresh_token": refresh_token
            }
        except (OTPExpiredException, OTPInvalidException):
            raise
        except Exception as e:
            logger.error(f"verify_otp crashed | mobile={mobile} | error={e}", exc_info=True)
            raise