from app.infrastructure.adapters.password_hasher import Pbkdf2PasswordHasher

ITERATIONS = 1000
PASSWORD = "secreto123"


def _hasher() -> Pbkdf2PasswordHasher:
    return Pbkdf2PasswordHasher(ITERATIONS)


def test_hash_does_not_contain_plaintext() -> None:
    encoded = _hasher().hash(PASSWORD)
    assert PASSWORD not in encoded


def test_hash_is_self_descriptive() -> None:
    encoded = _hasher().hash(PASSWORD)
    parts = encoded.split("$")
    assert parts[0] == "pbkdf2_sha256"
    assert parts[1] == str(ITERATIONS)
    assert len(parts) == 4


def test_verify_accepts_correct_password() -> None:
    hasher = _hasher()
    encoded = hasher.hash(PASSWORD)
    assert hasher.verify(PASSWORD, encoded)


def test_verify_rejects_wrong_password() -> None:
    hasher = _hasher()
    encoded = hasher.hash(PASSWORD)
    assert not hasher.verify("otra-clave", encoded)


def test_verify_rejects_malformed_encoded() -> None:
    hasher = _hasher()
    assert not hasher.verify(PASSWORD, "not-a-valid-hash")
    assert not hasher.verify(PASSWORD, "pbkdf2_sha256$abc$s$h")


def test_salt_makes_hashes_different() -> None:
    hasher = _hasher()
    assert hasher.hash(PASSWORD) != hasher.hash(PASSWORD)
