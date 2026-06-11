class AppException(Exception):
    def __init__(self, message: str = None, status_code: int = 500):
        self.message = message
        self.status_code = status_code
        super().__init__(self.message or "An unexpected error occurred")

class UserNotFoundException(AppException):
    status_code = 404
    detail = "User not found"

class InvalidCredentialsException(AppException):
    status_code = 401
    detail = "Invalid credentials"

class UserAlreadyExistsException(AppException):
    status_code = 409
    detail = "User already exists"

class OTPExpiredException(AppException):
    status_code = 400
    detail = "OTP has expired"

class OTPInvalidException(AppException):
    status_code = 400
    detail = "Invalid OTP entered"

class OTPAlreadySentException(AppException):
    status_code = 429
    detail = "OTP already sent, please wait before requesting again"

class OTPMaxAttemptsException(AppException):
    status_code = 429
    detail = "Too many wrong attempts, please request a new OTP"

class SMSSendFailedException(AppException):
    status_code = 500
    detail = "Failed to send OTP, please try again"
    
class OTPVerificationFailedException(AppException):
    status_code = 400
    detail = "OTP verification failed, please try again"

async def app_exception_handler(request, exc: AppException):
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.message or getattr(exc, 'detail', "An error occurred")}
    )