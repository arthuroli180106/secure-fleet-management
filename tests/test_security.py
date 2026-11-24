from app.security import hash_password, verify_password, password_is_strong

def test_password_hash_is_not_plaintext():
    raw = "Very-Strong-Password-123!"
    hashed = hash_password(raw)
    assert hashed != raw
    assert verify_password(hashed, raw)
    assert not verify_password(hashed, "wrong-password")

def test_password_policy():
    assert password_is_strong("Very-Strong-Password-123!")
    assert not password_is_strong("short")