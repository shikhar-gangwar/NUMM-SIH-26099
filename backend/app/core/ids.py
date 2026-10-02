import uuid

def generate_uuidv7() -> uuid.UUID:
    """Generate a UUIDv7 (time-ordered UUID). Standard uuid.uuid4 fallback if uuid7 unavailable."""
    if hasattr(uuid, "uuid7"):
        return getattr(uuid, "uuid7")()
    return uuid.uuid4()
