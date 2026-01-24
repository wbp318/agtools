"""
Secure Token Storage
AgTools v6.13.3

Provides encrypted storage for sensitive data like authentication tokens.
Uses Fernet symmetric encryption with a machine-derived key.
"""

import base64
import getpass
import platform

try:
    from cryptography.fernet import Fernet, InvalidToken
    from cryptography.hazmat.primitives import hashes
    from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
    CRYPTO_AVAILABLE = True
except ImportError:
    CRYPTO_AVAILABLE = False
    Fernet = None
    InvalidToken = Exception


# Key derivation parameters
_SALT = b"AgTools_Secure_Storage_v1"  # Fixed salt for key derivation
_ITERATIONS = 100000  # PBKDF2 iterations


def _get_machine_identifier() -> str:
    """
    Generate a machine-specific identifier for key derivation.

    Uses a combination of:
    - Username
    - Machine hostname
    - Platform info

    This ensures tokens encrypted on one machine cannot be decrypted on another.
    """
    components = [
        getpass.getuser(),
        platform.node(),
        platform.system(),
        platform.machine(),
    ]
    return "|".join(components)


def _derive_key(machine_id: str) -> bytes:
    """
    Derive a Fernet-compatible key from the machine identifier.

    Uses PBKDF2 with SHA256 to derive a 32-byte key, then base64 encode
    for Fernet compatibility.
    """
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library not available")

    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=_SALT,
        iterations=_ITERATIONS,
    )
    key = kdf.derive(machine_id.encode())
    return base64.urlsafe_b64encode(key)


def _get_fernet() -> "Fernet":
    """Get a Fernet instance with the machine-derived key."""
    if not CRYPTO_AVAILABLE:
        raise RuntimeError("cryptography library not available")

    machine_id = _get_machine_identifier()
    key = _derive_key(machine_id)
    return Fernet(key)


def encrypt_token(token: str) -> str:
    """
    Encrypt a token for secure storage.

    Args:
        token: The plaintext token to encrypt

    Returns:
        Base64-encoded encrypted token string

    Raises:
        RuntimeError: If cryptography library is not available
    """
    if not token:
        return ""

    if not CRYPTO_AVAILABLE:
        # Fallback: return plaintext with warning marker
        return f"UNENCRYPTED:{token}"

    try:
        fernet = _get_fernet()
        encrypted = fernet.encrypt(token.encode())
        return encrypted.decode()
    except Exception as e:
        # On encryption failure, return plaintext with marker
        print(f"Warning: Token encryption failed: {e}")
        return f"UNENCRYPTED:{token}"


def decrypt_token(encrypted_token: str) -> str:
    """
    Decrypt a stored token.

    Args:
        encrypted_token: The encrypted token string

    Returns:
        Decrypted plaintext token, or empty string on failure
    """
    if not encrypted_token:
        return ""

    # Handle unencrypted fallback tokens
    if encrypted_token.startswith("UNENCRYPTED:"):
        return encrypted_token[12:]  # Remove prefix

    if not CRYPTO_AVAILABLE:
        # Can't decrypt without cryptography library
        print("Warning: Cannot decrypt token - cryptography library not available")
        return ""

    try:
        fernet = _get_fernet()
        decrypted = fernet.decrypt(encrypted_token.encode())
        return decrypted.decode()
    except InvalidToken:
        # Token was encrypted on a different machine or is corrupted
        print("Warning: Token decryption failed - token may be from another machine")
        return ""
    except Exception as e:
        print(f"Warning: Token decryption failed: {e}")
        return ""


def is_encryption_available() -> bool:
    """Check if encryption is available."""
    return CRYPTO_AVAILABLE


def migrate_plaintext_token(plaintext_token: str) -> str:
    """
    Migrate a plaintext token to encrypted format.

    This is used during the first load after upgrading to handle
    existing plaintext tokens in settings.json.

    Args:
        plaintext_token: The plaintext token to migrate

    Returns:
        Encrypted token string
    """
    if not plaintext_token:
        return ""

    # Check if already encrypted (starts with gAAAAA for Fernet or UNENCRYPTED:)
    if plaintext_token.startswith("gAAAAA") or plaintext_token.startswith("UNENCRYPTED:"):
        return plaintext_token

    # Encrypt the plaintext token
    return encrypt_token(plaintext_token)
