"""
core/crypto.py
------------------
Encryption primitives for SecureVault.

- PBKDF2-HMAC-SHA256 turns the master password into a 256-bit AES key
  (200,000 iterations, to slow down brute-force / offline guessing attacks).
- AES-256-GCM (authenticated encryption) encrypts/decrypts the vault data.
  GCM gives both confidentiality (unreadable without the key) AND integrity
  (a wrong password or tampered file is detected via the auth tag, instead
  of silently returning garbage).

This module has no knowledge of screens/UI - it's pure crypto logic so it
can be tested and reused independently.
"""

from Crypto.Cipher import AES
from Crypto.Protocol.KDF import PBKDF2
from Crypto.Hash import SHA256
from Crypto.Random import get_random_bytes

PBKDF2_ITERATIONS = 200_000
KEY_LENGTH = 32       # 256-bit AES key
SALT_LENGTH = 16
NONCE_LENGTH = 12      # standard for AES-GCM


def generate_salt() -> bytes:
    """A fresh random salt - always generate a NEW one per vault/export,
    never reuse a salt across different secrets."""
    return get_random_bytes(SALT_LENGTH)


def derive_key(password: str, salt: bytes) -> bytes:
    """Derive a 256-bit AES key from a master password + salt via PBKDF2."""
    return PBKDF2(
        password.encode("utf-8"),
        salt,
        dkLen=KEY_LENGTH,
        count=PBKDF2_ITERATIONS,
        hmac_hash_module=SHA256,
    )


def encrypt(key: bytes, plaintext: bytes):
    """Encrypt plaintext bytes under `key`. Returns (nonce, ciphertext, tag)."""
    cipher = AES.new(key, AES.MODE_GCM)
    ciphertext, tag = cipher.encrypt_and_digest(plaintext)
    return cipher.nonce, ciphertext, tag


def decrypt(key: bytes, nonce: bytes, ciphertext: bytes, tag: bytes) -> bytes:
    """Decrypt + verify. Raises ValueError if the key (i.e. the password)
    is wrong or the data has been tampered with - callers should catch
    this and show 'incorrect password' rather than a crash."""
    cipher = AES.new(key, AES.MODE_GCM, nonce=nonce)
    return cipher.decrypt_and_verify(ciphertext, tag)
