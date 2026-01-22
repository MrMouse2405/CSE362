import secrets


def generateSecureRandomString():
    """
    # Generating IDs and secrets

    We can generate IDs and secrets by generating
    a random byte array and encoding it into a string.

    For a general purpose ID and secret, we want at least 120 bits of entropy.
    With 120 bits of entropy, you can generate 1,000,000 IDs/second without
    worrying about collisions and not ever think about brute force attacks.

    Since these strings will be used as secrets as well, it's crucial to
    use a cryptographically-secure random source.

    **Math.random() should NOT be used for generating secrets.**
    """
    return secrets.token_urlsafe(120)
