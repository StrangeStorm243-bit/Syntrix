"""Tests for credential encryption utilities."""

from __future__ import annotations

from unittest.mock import patch

from signalops.utils.credentials import decrypt_credential, encrypt_credential


class TestCredentialEncryption:
    def test_encrypt_decrypt_roundtrip(self, tmp_path):  # type: ignore[no-untyped-def]
        """Encrypted credential can be decrypted back."""
        key_file = tmp_path / "fernet.key"
        with (
            patch("signalops.utils.credentials._KEY_FILE", key_file),
            patch("signalops.utils.credentials._KEY_DIR", tmp_path),
        ):
            encrypted = encrypt_credential("my_secret_password")
            assert encrypted != "my_secret_password"
            decrypted = decrypt_credential(encrypted)
            assert decrypted == "my_secret_password"

    def test_decrypt_plaintext_returns_as_is(self, tmp_path):  # type: ignore[no-untyped-def]
        """Decrypting a non-encrypted string returns it as-is."""
        key_file = tmp_path / "fernet.key"
        with (
            patch("signalops.utils.credentials._KEY_FILE", key_file),
            patch("signalops.utils.credentials._KEY_DIR", tmp_path),
        ):
            # Force key creation first
            encrypt_credential("dummy")
            # Now try decrypting plaintext
            result = decrypt_credential("plain_text_password")
            assert result == "plain_text_password"

    def test_different_encryptions_produce_different_ciphertext(self, tmp_path):  # type: ignore[no-untyped-def]
        """Same plaintext produces different ciphertext (Fernet uses random IV)."""
        key_file = tmp_path / "fernet.key"
        with (
            patch("signalops.utils.credentials._KEY_FILE", key_file),
            patch("signalops.utils.credentials._KEY_DIR", tmp_path),
        ):
            enc1 = encrypt_credential("same_password")
            enc2 = encrypt_credential("same_password")
            assert enc1 != enc2  # Fernet adds random IV
            assert decrypt_credential(enc1) == "same_password"
            assert decrypt_credential(enc2) == "same_password"
