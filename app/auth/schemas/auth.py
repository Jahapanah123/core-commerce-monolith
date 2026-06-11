from pydantic import BaseModel, Field, field_validator
import re

class SendOTPRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=10)

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Invalid mobile number")
        return v
    
class VerifyOTPRequest(BaseModel):
    mobile: str = Field(..., min_length=10, max_length=10)
    otp: str = Field(..., min_length=6, max_length=6)

    @field_validator("mobile")
    @classmethod
    def validate_mobile(cls, v):
        if not re.match(r"^[6-9]\d{9}$", v):
            raise ValueError("Invalid mobile number")
        return v

    @field_validator("otp")
    @classmethod
    def validate_otp(cls, v):
        if not v.isdigit():
            raise ValueError("OTP must be numeric")
        return v