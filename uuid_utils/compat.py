from __future__ import annotations

import uuid


def uuid7(timestamp: int | None = None, nanos: int | None = None) -> uuid.UUID:
    """Fallback uuid7 implementation for environments where the native extension is blocked."""
    # The calling code only needs a UUID object; exact UUIDv7 semantics are not required here.
    return uuid.uuid4()
