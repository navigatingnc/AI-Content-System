import os
from cryptography.fernet import Fernet, InvalidToken

# Attempt to load the Fernet key from an environment variable
# For initial setup or if the key is not set, a default key can be generated and used.
# IMPORTANT: In a production environment, FERNET_KEY *MUST* be securely generated and managed.
#            This hardcoded key generation is for development convenience ONLY.
#            A good practice is to generate it once and store it as an env variable.
# Example: key = Fernet.generate_key() then set FERNET_KEY=key.decode()
#
# For this exercise, if FERNET_KEY is not set, we'll use a fixed, insecure key.
# This is NOT FOR PRODUCTION.
_DEFAULT_FERNET_KEY_STR = "your-32-byte-long-fixed-key-for-dev-only" # Replace with a real generated key for dev if desired
FERNET_KEY_STR = os.getenv('FERNET_KEY', _DEFAULT_FERNET_KEY_STR)

if FERNET_KEY_STR == _DEFAULT_FERNET_KEY_STR:
    print("WARNING: Using default, insecure Fernet key for encryption. Set FERNET_KEY environment variable for production.", flush=True)
    # In a real scenario, you might want to raise an error or auto-generate one and print it,
    # but for this exercise, we'll proceed with the default if not set.

try:
    # Ensure the key is bytes
    FERNET_KEY = FERNET_KEY_STR.encode('utf-8')
    # Validate key by creating a Fernet instance (will raise error if key is invalid)
    _ = Fernet(FERNET_KEY)
except ValueError as e:
    print(f"ERROR: Invalid Fernet key: {e}. Ensure FERNET_KEY is a valid base64 encoded string of 32 bytes.", flush=True)
    # Fallback to a known-good (but insecure for sharing) key for the sake of the exercise, to avoid crashing.
    # This is still NOT FOR PRODUCTION.
    FERNET_KEY = Fernet.generate_key() # Generates a new key if the provided one is bad
    print(f"WARNING: Falling back to a newly generated (insecure) Fernet key: {FERNET_KEY.decode()}", flush=True)


_cipher_suite = Fernet(FERNET_KEY)

def encrypt_data(data: str) -> bytes:
    """Encrypts a string using Fernet encryption."""
    if not isinstance(data, str):
        raise TypeError("Data must be a string")
    encrypted_data = _cipher_suite.encrypt(data.encode('utf-8'))
    return encrypted_data

def decrypt_data(encrypted_data: bytes) -> str:
    """Decrypts data using Fernet encryption."""
    if not isinstance(encrypted_data, bytes):
        raise TypeError("Encrypted data must be bytes")
    try:
        decrypted_data = _cipher_suite.decrypt(encrypted_data)
        return decrypted_data.decode('utf-8')
    except InvalidToken:
        # Handle cases where the token is invalid (e.g., tampered or wrong key)
        # Log this error appropriately in a real application
        print("ERROR: Invalid token or key during decryption.", flush=True)
        raise # Or return an error indicator / empty string depending on desired handling
    except Exception as e:
        print(f"ERROR: An unexpected error occurred during decryption: {e}", flush=True)
        raise
