"""
Comprehensive tests for encryption and key management modules

Test coverage:
- SymmetricEncryption (AES-256-GCM)
- KeyDerivation (PBKDF2, Argon2)
- FieldEncryption
- FileEncryption
- KeyStore
- KeyRotationManager
- MasterKeyManager
"""

import pytest
import os
import tempfile
import json
from datetime import datetime, timedelta
from pathlib import Path

from app.core.security.encryption import (
    EncryptionAlgorithm,
    KeyDerivationFunction,
    EncryptionConfig,
    EncryptedData,
    DerivedKey,
    SymmetricEncryption,
    KeyDerivation,
    FieldEncryption,
    FileEncryption,
    generate_encryption_key,
    encode_key,
    decode_key,
    ARGON2_AVAILABLE
)

from app.core.security.key_management import (
    KeyStatus,
    KeyType,
    KeyMetadata,
    ManagedKey,
    KeyRotationPolicy,
    KeyStore,
    KeyRotationManager,
    MasterKeyManager,
    initialize_key_management
)


class TestSymmetricEncryption:
    """Test AES-256-GCM encryption"""

    def test_encrypt_decrypt_bytes(self):
        """Test basic encryption and decryption of bytes"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        plaintext = b"Secret message"
        encrypted = encryption.encrypt(plaintext)

        assert encrypted.ciphertext != plaintext
        assert len(encrypted.nonce) == 12
        assert encrypted.algorithm == "aes-256-gcm"

        decrypted = encryption.decrypt(encrypted)
        assert decrypted == plaintext

    def test_encrypt_decrypt_string(self):
        """Test encryption and decryption of strings"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        plaintext = "Hello, 世界!"
        encrypted = encryption.encrypt_string(plaintext)

        decrypted = encryption.decrypt_string(encrypted)
        assert decrypted == plaintext

    def test_different_nonces(self):
        """Test that each encryption uses a different nonce"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        plaintext = b"Same message"
        encrypted1 = encryption.encrypt(plaintext)
        encrypted2 = encryption.encrypt(plaintext)

        assert encrypted1.nonce != encrypted2.nonce
        assert encrypted1.ciphertext != encrypted2.ciphertext

    def test_authenticated_encryption_with_aad(self):
        """Test encryption with additional authenticated data"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        plaintext = b"Secret data"
        aad = b"user_id:12345"

        encrypted = encryption.encrypt(plaintext, associated_data=aad)
        decrypted = encryption.decrypt(encrypted, associated_data=aad)

        assert decrypted == plaintext

    def test_wrong_aad_fails(self):
        """Test that wrong AAD causes decryption to fail"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        plaintext = b"Secret data"
        aad = b"user_id:12345"
        wrong_aad = b"user_id:99999"

        encrypted = encryption.encrypt(plaintext, associated_data=aad)

        with pytest.raises(ValueError, match="Decryption failed"):
            encryption.decrypt(encrypted, associated_data=wrong_aad)

    def test_wrong_key_fails(self):
        """Test that wrong key causes decryption to fail"""
        key1 = generate_encryption_key()
        key2 = generate_encryption_key()

        encryption1 = SymmetricEncryption(key1)
        encryption2 = SymmetricEncryption(key2)

        plaintext = b"Secret message"
        encrypted = encryption1.encrypt(plaintext)

        with pytest.raises(ValueError, match="Decryption failed"):
            encryption2.decrypt(encrypted)

    def test_invalid_key_size(self):
        """Test that invalid key size raises error"""
        with pytest.raises(ValueError, match="Key must be 32 bytes"):
            SymmetricEncryption(b"short_key")

    def test_metadata_preservation(self):
        """Test that metadata is preserved"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        metadata = {"user_id": "123", "field": "email"}
        plaintext = b"test@example.com"

        encrypted = encryption.encrypt(plaintext, metadata=metadata)

        assert encrypted.metadata == metadata
        assert encrypted.key_version == 1

    def test_serialization(self):
        """Test EncryptedData serialization and deserialization"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)

        plaintext = b"Test data"
        encrypted = encryption.encrypt(plaintext)

        # To JSON
        json_str = encrypted.to_json()
        assert isinstance(json_str, str)

        # From JSON
        restored = EncryptedData.from_json(json_str)
        assert restored.ciphertext == encrypted.ciphertext
        assert restored.nonce == encrypted.nonce
        assert restored.algorithm == encrypted.algorithm

        # Verify decryption works
        decrypted = encryption.decrypt(restored)
        assert decrypted == plaintext


class TestKeyDerivation:
    """Test key derivation functions"""

    def test_pbkdf2_sha256(self):
        """Test PBKDF2 with SHA-256"""
        kd = KeyDerivation()
        password = "strong_password_123"

        derived = kd.derive_key_pbkdf2(password, hash_algorithm="sha256")

        assert len(derived.key) == 32
        assert len(derived.salt) == 16
        assert derived.kdf == "pbkdf2-sha256"
        assert derived.iterations >= 100000

    def test_pbkdf2_sha512(self):
        """Test PBKDF2 with SHA-512"""
        kd = KeyDerivation()
        password = "strong_password_123"

        derived = kd.derive_key_pbkdf2(password, hash_algorithm="sha512")

        assert len(derived.key) == 32
        assert derived.kdf == "pbkdf2-sha512"

    def test_pbkdf2_deterministic(self):
        """Test that same password and salt produce same key"""
        kd = KeyDerivation()
        password = "test_password"
        salt = os.urandom(16)

        derived1 = kd.derive_key_pbkdf2(password, salt=salt)
        derived2 = kd.derive_key_pbkdf2(password, salt=salt)

        assert derived1.key == derived2.key

    def test_pbkdf2_different_salts(self):
        """Test that different salts produce different keys"""
        kd = KeyDerivation()
        password = "test_password"

        derived1 = kd.derive_key_pbkdf2(password)
        derived2 = kd.derive_key_pbkdf2(password)

        assert derived1.salt != derived2.salt
        assert derived1.key != derived2.key

    @pytest.mark.skipif(not ARGON2_AVAILABLE, reason="argon2-cffi not installed")
    def test_argon2id(self):
        """Test Argon2id key derivation"""
        kd = KeyDerivation()
        password = "strong_password_123"

        derived = kd.derive_key_argon2(password)

        assert len(derived.key) == 32
        assert len(derived.salt) == 16
        assert derived.kdf == "argon2id"
        assert "time_cost" in derived.params
        assert "memory_cost" in derived.params

    @pytest.mark.skipif(not ARGON2_AVAILABLE, reason="argon2-cffi not installed")
    def test_argon2_deterministic(self):
        """Test Argon2 determinism"""
        kd = KeyDerivation()
        password = "test_password"
        salt = os.urandom(16)

        derived1 = kd.derive_key_argon2(password, salt=salt)
        derived2 = kd.derive_key_argon2(password, salt=salt)

        assert derived1.key == derived2.key

    def test_derive_key_wrapper(self):
        """Test derive_key wrapper function"""
        kd = KeyDerivation()
        password = "test_password"

        # Test PBKDF2-SHA256
        derived = kd.derive_key(password, kdf=KeyDerivationFunction.PBKDF2_SHA256)
        assert derived.kdf == "pbkdf2-sha256"

        # Test PBKDF2-SHA512
        derived = kd.derive_key(password, kdf=KeyDerivationFunction.PBKDF2_SHA512)
        assert derived.kdf == "pbkdf2-sha512"


class TestFieldEncryption:
    """Test field-level encryption"""

    def test_encrypt_decrypt_simple_value(self):
        """Test encrypting simple field values"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)
        field_enc = FieldEncryption(encryption)

        value = "john.doe@example.com"
        encrypted = field_enc.encrypt_field(value, "email")
        decrypted = field_enc.decrypt_field(encrypted)

        assert decrypted == value

    def test_encrypt_decrypt_complex_value(self):
        """Test encrypting complex field values"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)
        field_enc = FieldEncryption(encryption)

        value = {"name": "John", "age": 30, "roles": ["admin", "user"]}
        encrypted = field_enc.encrypt_field(value, "profile")
        decrypted = field_enc.decrypt_field(encrypted)

        assert decrypted == value

    def test_encrypt_fields_in_record(self):
        """Test encrypting multiple fields in a record"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)
        field_enc = FieldEncryption(encryption)

        record = {
            "id": "123",
            "username": "john_doe",
            "email": "john@example.com",
            "ssn": "123-45-6789",
            "created_at": "2024-01-01"
        }

        # Encrypt sensitive fields
        encrypted_record = field_enc.encrypt_fields(record, ["email", "ssn"])

        # Check that specified fields are encrypted
        assert encrypted_record["email"] != record["email"]
        assert encrypted_record["ssn"] != record["ssn"]
        # Check that other fields are unchanged
        assert encrypted_record["username"] == record["username"]

        # Decrypt
        decrypted_record = field_enc.decrypt_fields(encrypted_record, ["email", "ssn"])
        assert decrypted_record["email"] == record["email"]
        assert decrypted_record["ssn"] == record["ssn"]


class TestFileEncryption:
    """Test file-level encryption"""

    def test_encrypt_decrypt_file(self):
        """Test encrypting and decrypting a file"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)
        file_enc = FileEncryption(encryption)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create test file
            plaintext_path = os.path.join(tmpdir, "plaintext.txt")
            encrypted_path = os.path.join(tmpdir, "encrypted.bin")
            decrypted_path = os.path.join(tmpdir, "decrypted.txt")

            plaintext_content = b"This is a secret document with sensitive information."
            with open(plaintext_path, "wb") as f:
                f.write(plaintext_content)

            # Encrypt
            encrypted_data = file_enc.encrypt_file(plaintext_path, encrypted_path)

            # Verify encrypted file is different
            with open(encrypted_path, "rb") as f:
                encrypted_content = f.read()
            assert encrypted_content != plaintext_content

            # Decrypt
            file_enc.decrypt_file(encrypted_path, decrypted_path, encrypted_data)

            # Verify decrypted content matches
            with open(decrypted_path, "rb") as f:
                decrypted_content = f.read()
            assert decrypted_content == plaintext_content

    def test_encrypt_file_with_metadata(self):
        """Test file encryption with metadata"""
        key = generate_encryption_key()
        encryption = SymmetricEncryption(key)
        file_enc = FileEncryption(encryption)

        with tempfile.TemporaryDirectory() as tmpdir:
            plaintext_path = os.path.join(tmpdir, "test.txt")
            encrypted_path = os.path.join(tmpdir, "test.enc")

            with open(plaintext_path, "wb") as f:
                f.write(b"Test content")

            metadata = {"owner": "user123", "purpose": "backup"}
            encrypted_data = file_enc.encrypt_file(plaintext_path, encrypted_path, metadata)

            assert encrypted_data.metadata == metadata


class TestKeyStore:
    """Test key storage and management"""

    def test_store_and_retrieve_key(self):
        """Test storing and retrieving keys"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)

        data_key = generate_encryption_key()
        managed_key = key_store.store_key(
            key=data_key,
            key_id="test-key-001",
            description="Test encryption key"
        )

        assert managed_key.metadata.key_id == "test-key-001"
        assert managed_key.metadata.status == KeyStatus.ACTIVE
        assert managed_key.key == data_key

        # Retrieve
        retrieved = key_store.get_key("test-key-001")
        assert retrieved is not None
        assert retrieved.key == data_key

    def test_get_active_key(self):
        """Test getting active keys only"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)

        data_key = generate_encryption_key()
        key_store.store_key(key=data_key, key_id="active-key")

        # Should return active key
        active = key_store.get_active_key("active-key")
        assert active is not None

        # Retire key
        key_store.retire_key("active-key")

        # Should not return retired key
        active = key_store.get_active_key("active-key")
        assert active is None

    def test_key_expiration(self):
        """Test key expiration"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)

        data_key = generate_encryption_key()
        expires_at = datetime.utcnow() - timedelta(hours=1)  # Already expired

        key_store.store_key(
            key=data_key,
            key_id="expired-key",
            expires_at=expires_at
        )

        # Should not return expired key
        active = key_store.get_active_key("expired-key")
        assert active is None

        # Should be marked as retired
        managed_key = key_store.get_key("expired-key")
        assert managed_key.metadata.status == KeyStatus.RETIRED

    def test_increment_usage(self):
        """Test usage count tracking"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)

        data_key = generate_encryption_key()
        key_store.store_key(key=data_key, key_id="usage-key")

        # Initial usage count
        managed_key = key_store.get_key("usage-key")
        assert managed_key.metadata.usage_count == 0

        # Increment
        key_store.increment_usage("usage-key")
        key_store.increment_usage("usage-key")

        managed_key = key_store.get_key("usage-key")
        assert managed_key.metadata.usage_count == 2

    def test_mark_compromised(self):
        """Test marking key as compromised"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)

        data_key = generate_encryption_key()
        key_store.store_key(key=data_key, key_id="compromised-key")

        result = key_store.mark_compromised("compromised-key")
        assert result is True

        managed_key = key_store.get_key("compromised-key")
        assert managed_key.metadata.status == KeyStatus.COMPROMISED

    def test_list_keys_with_filters(self):
        """Test listing keys with filters"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)

        # Store multiple keys
        key_store.store_key(generate_encryption_key(), "data-key-1", KeyType.DATA)
        key_store.store_key(generate_encryption_key(), "data-key-2", KeyType.DATA)
        key_store.store_key(generate_encryption_key(), "session-key-1", KeyType.SESSION)

        # Retire one key
        key_store.retire_key("data-key-1")

        # List all DATA keys
        data_keys = key_store.list_keys(key_type=KeyType.DATA)
        assert len(data_keys) == 2

        # List active keys
        active_keys = key_store.list_keys(status=KeyStatus.ACTIVE)
        assert len(active_keys) == 2

        # List retired keys
        retired_keys = key_store.list_keys(status=KeyStatus.RETIRED)
        assert len(retired_keys) == 1

    def test_persistent_storage(self):
        """Test key persistence to disk"""
        with tempfile.TemporaryDirectory() as tmpdir:
            master_key = generate_encryption_key()
            storage_path = os.path.join(tmpdir, "keys")

            # Create key store and store a key
            key_store1 = KeyStore(master_key, storage_path)
            data_key = generate_encryption_key()
            key_store1.store_key(key=data_key, key_id="persistent-key")

            # Create new key store instance (should load from disk)
            key_store2 = KeyStore(master_key, storage_path)
            retrieved = key_store2.get_key("persistent-key")

            assert retrieved is not None
            assert retrieved.key == data_key


class TestKeyRotationManager:
    """Test key rotation management"""

    def test_set_rotation_policy(self):
        """Test setting rotation policy"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        data_key = generate_encryption_key()
        key_store.store_key(key=data_key, key_id="rotate-key")

        policy = KeyRotationPolicy(
            rotation_period=timedelta(days=90),
            max_usage=10000
        )
        rotation_mgr.set_rotation_policy("rotate-key", policy)

        assert "rotate-key" in rotation_mgr.rotation_policies

    def test_should_rotate_by_time(self):
        """Test time-based rotation detection"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        # Create key with old activation time
        data_key = generate_encryption_key()
        managed_key = key_store.store_key(key=data_key, key_id="old-key")
        managed_key.metadata.activated_at = datetime.utcnow() - timedelta(days=100)
        managed_key.metadata.rotation_period = timedelta(days=90)

        policy = KeyRotationPolicy(rotation_period=timedelta(days=90))
        rotation_mgr.set_rotation_policy("old-key", policy)

        should_rotate, reason = rotation_mgr.should_rotate("old-key")
        assert should_rotate is True
        assert "period" in reason.lower()

    def test_should_rotate_by_usage(self):
        """Test usage-based rotation detection"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        data_key = generate_encryption_key()
        managed_key = key_store.store_key(key=data_key, key_id="high-usage-key")

        # Simulate high usage
        managed_key.metadata.usage_count = 101
        managed_key.metadata.max_usage = 100

        policy = KeyRotationPolicy(
            rotation_period=timedelta(days=365),  # Long period
            max_usage=100
        )
        rotation_mgr.set_rotation_policy("high-usage-key", policy)

        should_rotate, reason = rotation_mgr.should_rotate("high-usage-key")
        assert should_rotate is True
        assert "usage" in reason.lower()

    def test_should_rotate_compromised(self):
        """Test rotation on compromise"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        data_key = generate_encryption_key()
        key_store.store_key(key=data_key, key_id="compromised-key")
        key_store.mark_compromised("compromised-key")

        policy = KeyRotationPolicy(
            rotation_period=timedelta(days=365),
            rotate_on_compromise=True
        )
        rotation_mgr.set_rotation_policy("compromised-key", policy)

        should_rotate, reason = rotation_mgr.should_rotate("compromised-key")
        assert should_rotate is True
        assert "compromised" in reason.lower()

    def test_rotate_key(self):
        """Test key rotation"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        old_key = generate_encryption_key()
        key_store.store_key(key=old_key, key_id="rotate-me")

        # Rotate
        old_managed, new_managed = rotation_mgr.rotate_key("rotate-me")

        assert old_managed.metadata.status == KeyStatus.ROTATING
        assert new_managed.metadata.status == KeyStatus.ACTIVE
        assert new_managed.metadata.version == old_managed.metadata.version + 1
        assert new_managed.key != old_managed.key

    def test_get_rotation_status(self):
        """Test getting rotation status"""
        master_key = generate_encryption_key()
        key_store = KeyStore(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        data_key = generate_encryption_key()
        key_store.store_key(
            key=data_key,
            key_id="status-key",
            rotation_period=timedelta(days=30)
        )

        policy = KeyRotationPolicy(
            rotation_period=timedelta(days=30),
            max_usage=5000
        )
        rotation_mgr.set_rotation_policy("status-key", policy)

        status = rotation_mgr.get_rotation_status("status-key")

        assert status["key_id"] == "status-key"
        assert "version" in status
        assert "should_rotate" in status
        assert "days_until_rotation" in status
        assert "usage_remaining" in status


class TestMasterKeyManager:
    """Test master key management"""

    def test_generate_master_key(self):
        """Test master key generation"""
        mkm = MasterKeyManager()
        master_key = mkm.generate_master_key()

        assert len(master_key) == 32

    def test_derive_master_key_from_password(self):
        """Test deriving master key from password"""
        mkm = MasterKeyManager()
        password = "super_secret_master_password"

        master_key, salt = mkm.derive_master_key_from_password(password)

        assert len(master_key) == 32
        assert len(salt) > 0

        # Test determinism
        master_key2, _ = mkm.derive_master_key_from_password(password, salt)
        assert master_key == master_key2

    def test_wrap_unwrap_key(self):
        """Test key wrapping and unwrapping"""
        mkm = MasterKeyManager()
        master_key = mkm.generate_master_key()
        data_key = generate_encryption_key()

        # Wrap
        wrapped = mkm.wrap_key(data_key, master_key)
        assert wrapped.ciphertext != data_key

        # Unwrap
        unwrapped = mkm.unwrap_key(wrapped, master_key)
        assert unwrapped == data_key

    def test_export_import_master_key(self):
        """Test master key export and import"""
        mkm = MasterKeyManager()
        master_key = mkm.generate_master_key()
        password = "backup_password_123"

        # Export
        export_data = mkm.export_master_key(master_key, password)

        assert "encrypted_master_key" in export_data
        assert "nonce" in export_data
        assert "salt" in export_data
        assert "exported_at" in export_data

        # Import
        imported_key = mkm.import_master_key(export_data, password)
        assert imported_key == master_key

    def test_import_with_wrong_password_fails(self):
        """Test that import fails with wrong password"""
        mkm = MasterKeyManager()
        master_key = mkm.generate_master_key()
        password = "correct_password"
        wrong_password = "wrong_password"

        export_data = mkm.export_master_key(master_key, password)

        with pytest.raises(ValueError, match="Decryption failed"):
            mkm.import_master_key(export_data, wrong_password)


class TestKeyManagementIntegration:
    """Integration tests for key management"""

    def test_initialize_key_management(self):
        """Test initializing global key management"""
        with tempfile.TemporaryDirectory() as tmpdir:
            master_key = generate_encryption_key()
            storage_path = os.path.join(tmpdir, "keys")

            key_store = initialize_key_management(master_key, storage_path)

            assert key_store is not None
            assert key_store.storage_path == Path(storage_path)

    def test_full_encryption_workflow(self):
        """Test complete encryption workflow with key management"""
        # Initialize key management
        master_key = generate_encryption_key()
        key_store = initialize_key_management(master_key)
        rotation_mgr = KeyRotationManager(key_store)

        # Store data encryption key
        data_key = generate_encryption_key()
        key_store.store_key(key=data_key, key_id="app-data-key")

        # Set rotation policy
        policy = KeyRotationPolicy(
            rotation_period=timedelta(days=90),
            max_usage=10000
        )
        rotation_mgr.set_rotation_policy("app-data-key", policy)

        # Use key for encryption
        encryption = SymmetricEncryption(data_key)
        plaintext = b"Sensitive user data"
        encrypted = encryption.encrypt(plaintext)

        # Track usage
        key_store.increment_usage("app-data-key")

        # Decrypt
        decrypted = encryption.decrypt(encrypted)
        assert decrypted == plaintext

        # Check rotation status
        status = rotation_mgr.get_rotation_status("app-data-key")
        assert status["usage_count"] == 1
        assert status["usage_remaining"] == 9999


class TestUtilityFunctions:
    """Test utility functions"""

    def test_generate_encryption_key(self):
        """Test key generation"""
        key = generate_encryption_key()
        assert len(key) == 32

        # Different sizes
        key16 = generate_encryption_key(16)
        assert len(key16) == 16

    def test_encode_decode_key(self):
        """Test key encoding and decoding"""
        key = generate_encryption_key()

        encoded = encode_key(key)
        assert isinstance(encoded, str)

        decoded = decode_key(encoded)
        assert decoded == key


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
