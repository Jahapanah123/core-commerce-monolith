from jose import jwt, JWTError

from app.shared.core.config import settings


def decode_token(token: str) -> dict | None:
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
        return payload

    except JWTError:
        return None