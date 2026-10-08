from django.core import signing

SALT = "upl.verify-email"
MAX_AGE = 60 * 60 * 24 * 3  # 3 days


def make_token(user):
    return signing.dumps({"uid": user.pk, "email": user.email}, salt=SALT)


def read_token(token):
    """Returns payload or None. Signed + expiring; tampering or expiry -> None."""
    try:
        return signing.loads(token, salt=SALT, max_age=MAX_AGE)
    except signing.BadSignature:
        return None
