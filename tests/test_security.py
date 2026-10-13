import pytest

from app.core.security import create_access_token, decode_access_token, hash_password, verify_password


def test_password_hash_roundtrip():
    hashed = hash_password("s3cret-pass")
    assert hashed != "s3cret-pass"
    assert verify_password("s3cret-pass", hashed)
    assert not verify_password("otra", hashed)


def test_verify_password_with_garbage_hash_is_false():
    assert verify_password("x", "not-a-hash") is False


def test_token_roundtrip():
    token = create_access_token(user_id="u1", organization_id="o1", role="SYNER_ADMIN")
    payload = decode_access_token(token)
    assert payload["sub"] == "u1"
    assert payload["org"] == "o1"
    assert payload["role"] == "SYNER_ADMIN"


def test_expired_token_raises():
    token = create_access_token(user_id="u1", organization_id="o1", role="SYNER_ADMIN", expires_hours=-1)
    with pytest.raises(ValueError):
        decode_access_token(token)
