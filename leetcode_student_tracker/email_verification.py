import hashlib
import hmac
import secrets
import requests


VERIFICATION_RECIPIENT = 'sktopo26@gmail.com'
DEFAULT_FROM_ADDRESS = 'LeetCode Student Tracker <onboarding@resend.dev>'
CODE_ITERATIONS = 100_000


class EmailProviderAuthError(Exception):
    pass


class EmailProviderResponseError(Exception):
    def __init__(self, status_code):
        self.status_code = status_code


def create_verification_code():
    return f'{secrets.randbelow(1_000_000):06d}'


def hash_verification_code(code):
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', code.encode('ascii'), salt, CODE_ITERATIONS)
    return salt.hex(), digest.hex()


def verify_verification_code(code, salt_hex, digest_hex):
    if len(code) != 6 or not code.isascii() or not code.isdigit():
        return False
    try:
        salt = bytes.fromhex(salt_hex)
        expected_digest = bytes.fromhex(digest_hex)
    except ValueError:
        return False
    actual_digest = hashlib.pbkdf2_hmac('sha256', code.encode('ascii'), salt, CODE_ITERATIONS)
    return hmac.compare_digest(actual_digest, expected_digest)


def send_verification_email(code, api_key, sender):
    response = requests.post(
        'https://api.resend.com/emails',
        headers={'Authorization': f'Bearer {api_key}', 'Content-Type': 'application/json'},
        json={
            'from': sender,
            'to': [VERIFICATION_RECIPIENT],
            'subject': 'LeetCode Student Tracker signup verification',
            'text': (
                f'Your administrator signup verification code is {code}. '
                'It expires in 10 minutes. If you did not request this code, ignore this email.'
            ),
        },
        timeout=20,
    )
    if response.status_code in (401, 403):
        raise EmailProviderAuthError()
    if not response.ok:
        raise EmailProviderResponseError(response.status_code)