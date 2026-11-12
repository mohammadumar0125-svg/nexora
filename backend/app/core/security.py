import base64
import hashlib
import hmac
import re
import secrets
import string
import struct
import time
import urllib.parse
from typing import Optional

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

ph = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
    hash_len=32,
    salt_len=16,
)

DUMMY_HASH = ph.hash("TimingMitigationDummyPassword#2026!")

PROMPT_INJECTION_PATTERNS = [
    r"ignore\s+(?:all\s+)?(?:previous|prior|above)\s+instructions",
    r"system\s+override",
    r"reveal\s+(?:the\s+)?system\s+prompt",
    r"drop\s+table",
    r"other\s+tenant",
    r"bypass\s+rls",
]


def hash_password(password: str) -> str:
    return ph.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    if not hashed_password:
        return False
    try:
        return ph.verify(hashed_password, plain_password)
    except VerifyMismatchError:
        return False


def validate_password_strength(password: str) -> Optional[str]:
    if len(password) < 10:
        return "Password must be at least 10 characters long."
    if not any(c.isupper() for c in password):
        return "Password must include at least one uppercase letter."
    if not any(c.islower() for c in password):
        return "Password must include at least one lowercase letter."
    if not any(c.isdigit() for c in password):
        return "Password must include at least one numeric digit."
    if not any(c in "!@#$%^&*()-_=+[]{};:,.<>?/|~" for c in password):
        return "Password must include at least one special character."
    return None


def generate_random_token(num_bytes: int = 48) -> str:
    return secrets.token_urlsafe(num_bytes)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def generate_csrf_token() -> str:
    return secrets.token_urlsafe(32)


def verify_csrf_token(header_token: Optional[str], session_csrf_token: Optional[str]) -> bool:
    if not header_token or not session_csrf_token:
        return False
    return secrets.compare_digest(header_token, session_csrf_token)


def generate_temp_password(length: int = 14) -> str:
    alphabet = string.ascii_letters + string.digits + "!@#$%&*"
    pwd = [
        secrets.choice(string.ascii_uppercase),
        secrets.choice(string.ascii_lowercase),
        secrets.choice(string.digits),
        secrets.choice("!@#$%&*"),
    ]
    pwd += [secrets.choice(alphabet) for _ in range(max(length - 4, 6))]
    secrets.SystemRandom().shuffle(pwd)
    return "".join(pwd)


def slugify_tenant(name: str) -> str:
    clean = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or "workspace"
    suffix = secrets.token_hex(3)
    return f"{clean[:48]}-{suffix}"


# --- Pure-Python RFC 6238 TOTP MFA ---
def generate_mfa_secret() -> str:
    raw = secrets.token_bytes(20)
    return base64.b32encode(raw).decode("ascii").rstrip("=")


def get_totp_uri(secret: str, email: str, issuer: str = "NEXORA") -> str:
    label = urllib.parse.quote(f"{issuer}:{email}")
    return f"otpauth://totp/{label}?secret={secret}&issuer={urllib.parse.quote(issuer)}&algorithm=SHA1&digits=6&period=30"


def compute_totp_code(secret: str, counter_offset: int = 0) -> str:
    padded = secret.upper() + "=" * ((8 - len(secret) % 8) % 8)
    key = base64.b32decode(padded)
    counter = int(time.time() // 30) + counter_offset
    msg = struct.pack(">Q", counter)
    digest = hmac.new(key, msg, hashlib.sha1).digest()
    offset = digest[-1] & 0x0F
    code_int = (struct.unpack(">I", digest[offset : offset + 4])[0] & 0x7FFFFFFF) % 1_000_000
    return f"{code_int:06d}"


def verify_totp_code(secret: Optional[str], code: Optional[str]) -> bool:
    if not secret or not code or not code.isdigit() or len(code) != 6:
        return False
    for offset in (-1, 0, 1):
        if hmac.compare_digest(compute_totp_code(secret, offset), code):
            return True
    return False


# --- AI Prompt Safety ---
def detect_prompt_injection(text_input: str) -> bool:
    lowered = text_input.lower()
    return any(re.search(pat, lowered) for pat in PROMPT_INJECTION_PATTERNS)


def sanitize_prompt_input(text_input: str) -> str:
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]", " ", text_input).strip()
    return cleaned[:2000]
