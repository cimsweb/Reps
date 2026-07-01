import base64
import hashlib
import secrets

_SCRYPT_N = 2**14
_SCRYPT_R = 8
_SCRYPT_P = 1
_SCRYPT_DKLEN = 32


class ScryptPasswordHasher:
    """Scrypt-based password hasher using the Python standard library."""

    def hash(self, password: str) -> str:
        salt = secrets.token_bytes(16)
        derived = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_SCRYPT_DKLEN,
        )
        salt_encoded = base64.b64encode(salt).decode()
        derived_encoded = base64.b64encode(derived).decode()
        return f"scrypt${salt_encoded}${derived_encoded}"

    def verify(self, password: str, password_hash: str) -> bool:
        try:
            algorithm, salt_encoded, derived_encoded = password_hash.split("$", maxsplit=2)
        except ValueError:
            return False

        if algorithm != "scrypt":
            return False

        salt = base64.b64decode(salt_encoded.encode())
        expected = base64.b64decode(derived_encoded.encode())
        actual = hashlib.scrypt(
            password.encode(),
            salt=salt,
            n=_SCRYPT_N,
            r=_SCRYPT_R,
            p=_SCRYPT_P,
            dklen=_SCRYPT_DKLEN,
        )
        return secrets.compare_digest(actual, expected)
