import random
import hashlib

def generate_otp(length=6) -> str:
    otp = "".join([str(random.randint(0, 9)) for _ in range(length)])
    return otp

def hash_otp(otp: str) -> str:
    return hashlib.sha256(otp.encode()).hexdigest()

def verify_otp_hash(input_otp: str, hashed_otp: str) -> bool:
    return hash_otp(input_otp) == hashed_otp