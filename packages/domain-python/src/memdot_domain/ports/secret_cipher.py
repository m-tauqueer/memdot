"""Secret cipher port — encrypt/decrypt without owning product credential storage."""

from typing import Protocol


class SecretCipherPort(Protocol):
    """Generic secret-cipher interface used by self-host and hosted providers."""

    def encrypt(self, plaintext: bytes, *, key_name: str) -> bytes:
        """Encrypt plaintext for the named key. Never log plaintext or ciphertext."""
        ...

    def decrypt(self, ciphertext: bytes, *, key_name: str) -> bytes:
        """Decrypt ciphertext for the named key. Never log plaintext or ciphertext."""
        ...
