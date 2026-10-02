import hashlib
import hmac
import secrets


ALGORITHM = 'pbkdf2_sha256'
ITERATIONS = 600_000
SALT_BYTES = 16


def hash_password(password):
    salt = secrets.token_bytes(SALT_BYTES)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, ITERATIONS)
    return f'{ALGORITHM}${ITERATIONS}${salt.hex()}${digest.hex()}'


def verify_password(password, encoded_hash):
    try:
        algorithm, iteration_text, salt_text, digest_text = encoded_hash.split('$')
        iterations = int(iteration_text)
        salt = bytes.fromhex(salt_text)
        expected_digest = bytes.fromhex(digest_text)
    except (AttributeError, TypeError, ValueError):
        return False

    if algorithm != ALGORITHM or iterations < 100_000 or len(salt) < SALT_BYTES or len(expected_digest) != 32:
        return False

    actual_digest = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, iterations)
    return hmac.compare_digest(actual_digest, expected_digest)
