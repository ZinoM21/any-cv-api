from datetime import datetime, timedelta, timezone

from jwt import ExpiredSignatureError, PyJWTError, decode, encode

from ..exceptions import (
    HTTPExceptionType,
    UnauthorizedHTTPException,
)


def encode_with_expiry(
    data: dict, expires_in_minutes: int, secret: str, algorithm: str
) -> str:
    data.update(
        {
            "exp": datetime.now(timezone.utc) + timedelta(minutes=expires_in_minutes),
            "iat": datetime.now(timezone.utc),
        }
    )

    return encode(data, secret, algorithm=algorithm)


def decode_jwt(token: str, secret: str, algorithm: str) -> dict:
    try:
        payload = decode(
            token,
            secret,
            algorithms=[algorithm],
        )
        return payload
    except ExpiredSignatureError:
        raise UnauthorizedHTTPException(detail=HTTPExceptionType.TokenExpired.value)
    except PyJWTError:
        raise UnauthorizedHTTPException(detail=HTTPExceptionType.InvalidToken.value)
