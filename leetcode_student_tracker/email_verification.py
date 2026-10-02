import hashlib
import hmac
import secrets
import smtplib
import ssl
from email.message import EmailMessage


VERIFICATION_RECIPIENT = 'sktopo26@gmail.com'
CODE_ITERATIONS = 100_000


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


def send_verification_email(code, sender, app_password):
    message = EmailMessage()
    message['From'] = sender
    message['To'] = VERIFICATION_RECIPIENT
    message['Subject'] = 'LeetCode Student Tracker signup verification'
    message.set_content(
        f'Your administrator signup verification code is {code}. '
        'It expires in 10 minutes. If you did not request this code, ignore this email.'
    )

    with smtplib.SMTP('smtp.gmail.com', 587, timeout=20) as server:
        server.ehlo()
        server.starttls(context=ssl.create_default_context())
        server.ehlo()
        server.login(sender, app_password)
        server.send_message(message)