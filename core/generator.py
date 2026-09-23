"""
core/generator.py
---------------------
Secure password generation (using `secrets`, not `random`) plus an
entropy-based strength estimator that drives the strength meter and the
crack-time estimate shown on the Create Password screen.
"""

import string
import secrets
import math

SYMBOLS = "!@#$%^&*()-_=+[]{};:,.<>?"

MIN_LENGTH = 4
MAX_LENGTH = 128
DEFAULT_LENGTH = 16

# Assumed attacker speed for the crack-time estimate: ~10 billion guesses/sec
# is a commonly cited figure for a fast offline attack against a weakly
# hashed password. This is an estimate for illustration, not a guarantee.
ASSUMED_GUESSES_PER_SECOND = 1e10


def clamp_length(value, fallback=DEFAULT_LENGTH):
    """Safely coerce arbitrary input (string, float, None, garbage) into a
    valid password length in [MIN_LENGTH, MAX_LENGTH]. Never raises."""
    try:
        n = int(round(float(value)))
    except (TypeError, ValueError):
        return fallback
    return max(MIN_LENGTH, min(MAX_LENGTH, n))


def generate_password(length=DEFAULT_LENGTH, use_upper=True, use_lower=True,
                       use_digits=True, use_symbols=True) -> str:
    """Generate a cryptographically secure random password (4-128 chars),
    guaranteeing at least one character from each selected character set."""
    length = clamp_length(length)

    pools = []
    if use_upper:
        pools.append(string.ascii_uppercase)
    if use_lower:
        pools.append(string.ascii_lowercase)
    if use_digits:
        pools.append(string.digits)
    if use_symbols:
        pools.append(SYMBOLS)

    if not pools:
        pools = [string.ascii_lowercase]  # never return an empty password

    all_chars = "".join(pools)

    # Guarantee at least one char from each selected pool, but only as many
    # "guaranteed" picks as fit within the requested length (matters for
    # very short lengths, e.g. length=4 with all 4 options on).
    password_chars = [secrets.choice(pool) for pool in pools[:length]]
    remaining = max(length - len(password_chars), 0)
    password_chars += [secrets.choice(all_chars) for _ in range(remaining)]

    # Fisher-Yates shuffle using a CSPRNG so pool order doesn't leak position
    for i in range(len(password_chars) - 1, 0, -1):
        j = secrets.randbelow(i + 1)
        password_chars[i], password_chars[j] = password_chars[j], password_chars[i]

    return "".join(password_chars[:length])


def _pool_size(use_upper, use_lower, use_digits, use_symbols):
    size = 0
    if use_upper:
        size += 26
    if use_lower:
        size += 26
    if use_digits:
        size += 10
    if use_symbols:
        size += len(SYMBOLS)
    return size or 26  # matches the lowercase-only fallback in generate_password


def calculate_entropy(length, use_upper=True, use_lower=True,
                       use_digits=True, use_symbols=True) -> float:
    """Shannon entropy in bits for a random password of this length drawn
    uniformly from the selected character pools: length * log2(pool_size)."""
    pool_size = _pool_size(use_upper, use_lower, use_digits, use_symbols)
    if pool_size <= 1 or length <= 0:
        return 0.0
    return length * math.log2(pool_size)


def _format_duration(seconds: float) -> str:
    if seconds < 1:
        return "instantly"
    units = [
        ("second", 1),
        ("minute", 60),
        ("hour", 3600),
        ("day", 86400),
        ("year", 31_536_000),
    ]
    if seconds < 31_536_000 * 1000:
        for name, size in reversed(units):
            if seconds >= size:
                value = seconds / size
                plural = "" if abs(value - 1) < 0.05 else "s"
                return f"~{value:,.0f} {name}{plural}"
        return f"~{seconds:.0f} seconds"
    years = seconds / 31_536_000
    return f"~{years:.2e} years"


def estimate_crack_time(entropy_bits: float) -> str:
    """Rough estimated time to brute-force a password of this entropy at
    ASSUMED_GUESSES_PER_SECOND. Illustrative, not a precise guarantee."""
    if entropy_bits <= 0:
        return "instantly"
    seconds = (2 ** entropy_bits) / ASSUMED_GUESSES_PER_SECOND
    return _format_duration(seconds)


# Ordered weakest -> strongest. Bar fill (1-4 segments) is derived from the
# tier index; the label/color always reflect the true entropy-based tier,
# even once the bar is visually maxed out at 4 segments.
_STRENGTH_TIERS = [
    (0, "Weak", "#F85149"),
    (30, "Fair", "#D29922"),
    (46, "Good", "#58A6FF"),
    (66, "Strong", "#3FB950"),
    (90, "Very Strong", "#238636"),
]


def password_strength(password_or_length, use_upper=True, use_lower=True,
                       use_digits=True, use_symbols=True):
    """Entropy-based strength rating.

    Accepts either:
    - a password string (evaluates its actual length/content), or
    - an integer length (evaluates the options that *would* be used) -
      this lets the UI update the meter live as the user drags the length
      slider or toggles options, before generating.

    Returns (bar_score 0-4, label, color_hex, entropy_bits, crack_time_str).
    """
    if isinstance(password_or_length, str):
        password = password_or_length
        if not password:
            return 0, "Empty", "#8B949E", 0.0, "instantly"
        length = len(password)
        use_upper = any(c.isupper() for c in password)
        use_lower = any(c.islower() for c in password)
        use_digits = any(c.isdigit() for c in password)
        use_symbols = any(c in SYMBOLS for c in password)
    else:
        length = clamp_length(password_or_length)
        if length <= 0:
            return 0, "Empty", "#8B949E", 0.0, "instantly"

    entropy = calculate_entropy(length, use_upper, use_lower, use_digits, use_symbols)

    tier_index = 0
    for i, (min_bits, _, _) in enumerate(_STRENGTH_TIERS):
        if entropy >= min_bits:
            tier_index = i
    _, label, color = _STRENGTH_TIERS[tier_index]

    bar_score = min(tier_index + 1, 4)
    crack_time = estimate_crack_time(entropy)
    return bar_score, label, color, entropy, crack_time
