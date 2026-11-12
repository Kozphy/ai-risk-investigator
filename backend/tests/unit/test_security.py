from app.core.security import Role, create_access_token, decode_token, hash_password, verify_password


def test_password_hash_roundtrip() -> None:
    hashed = hash_password("ChangeMe123!")
    assert verify_password("ChangeMe123!", hashed)
    assert not verify_password("wrong", hashed)


def test_jwt_roundtrip() -> None:
    token = create_access_token("00000000-0000-0000-0000-000000000001", Role.AUDITOR)
    payload = decode_token(token)
    assert payload["sub"] == "00000000-0000-0000-0000-000000000001"
    assert payload["role"] == "auditor"
    assert payload["type"] == "access"
