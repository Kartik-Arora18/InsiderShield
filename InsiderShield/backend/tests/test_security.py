
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
import pytest

from app.core.config import settings
from app.core.security import (
    create_access_token,
    decode_access_token,
    hash_password,
    verify_password,
)


def _encode_test_token(payload: dict) -> str:
    return jwt.encode(
        payload,
        settings.jwt_secret_key.get_secret_value(),
        algorithm=settings.jwt_algorithm,
    )


def test_argon2_password_hash_verifies_and_is_not_plaintext():
    raw = "A-long-test-password-123!"
    hashed = hash_password(raw)

    assert hashed != raw
    assert verify_password(raw, hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_contains_expected_identity_claims():
    user_id, organization_id = uuid4(), uuid4()

    token = create_access_token(
        user_id=user_id,
        organization_id=organization_id,
        role="admin",
    )

    claims = decode_access_token(token)

    assert claims["sub"] == str(user_id)
    assert claims["org"] == str(organization_id)
    assert claims["role"] == "admin"
    assert claims["type"] == "access"


def test_invalid_token_is_rejected():
    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token("not-a-valid-token")


def test_expired_access_token_is_rejected():
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(uuid4()),
        "org": str(uuid4()),
        "role": "admin",
        "type": "access",
        "iat": now - timedelta(minutes=10),
        "exp": now - timedelta(minutes=5),
    }

    token = _encode_test_token(payload)

    with pytest.raises(jwt.ExpiredSignatureError):
        decode_access_token(token)


def test_tampered_access_token_is_rejected():
    token = create_access_token(
        user_id=uuid4(),
        organization_id=uuid4(),
        role="admin",
    )

    parts = token.split(".")
    parts[1] = ("A" if parts[1][0] != "A" else "B") + parts[1][1:]
    tampered_token = ".".join(parts)

    with pytest.raises(jwt.InvalidTokenError):
        decode_access_token(tampered_token)


def test_wrong_token_type_is_rejected():
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(uuid4()),
        "org": str(uuid4()),
        "role": "admin",
        "type": "refresh",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }

    token = _encode_test_token(payload)

    with pytest.raises(jwt.InvalidTokenError, match="Invalid token type"):
        decode_access_token(token)


def test_missing_required_claim_is_rejected():
    now = datetime.now(timezone.utc)

    payload = {
        "sub": str(uuid4()),
        "org": str(uuid4()),
        "role": "admin",
        "type": "access",
        "iat": now,
        # Deliberately omit exp.
    }

    token = _encode_test_token(payload)

    with pytest.raises(jwt.MissingRequiredClaimError):
        decode_access_token(token)


def test_malformed_uuid_claim_is_rejected():
    now = datetime.now(timezone.utc)

    payload = {
        "sub": "not-a-valid-uuid",
        "org": str(uuid4()),
        "role": "admin",
        "type": "access",
        "iat": now,
        "exp": now + timedelta(minutes=10),
    }

    token = _encode_test_token(payload)

    with pytest.raises(ValueError):
        decode_access_token(token)
