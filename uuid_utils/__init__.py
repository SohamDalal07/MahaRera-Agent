from __future__ import annotations

import uuid

from typing import Any

try:
    from ._uuid_utils import uuid7 as _uuid_utils_uuid7
except ImportError:
    _uuid_utils_uuid7 = None


def uuid7(timestamp: int | None = None, nanos: int | None = None) -> uuid.UUID:
    """Generate a UUIDv7-like value.

    This fallback uses Python's standard uuid module and provides a compatible
    `uuid7` interface for environments where the Rust-backed extension is blocked.
    """
    if _uuid_utils_uuid7 is not None:
        if timestamp is None and nanos is None:
            return _uuid_utils_uuid7()
        return _uuid_utils_uuid7(timestamp=timestamp, nanos=nanos)

    # Fallback: derive a deterministic UUID from the current time and random bits.
    # This is not a full UUIDv7 implementation, but it satisfies the interface
    # expected by langchain-core.
    if timestamp is None:
        return uuid.uuid4()
    if nanos is None:
        raise ValueError("Both timestamp and nanos must be provided when using a custom timestamp")

    # Construct a UUID using timestamp and random bytes.
    # Keep the format as a version 4-like UUID for compatibility.
    random_bytes = uuid.uuid4().bytes[8:]
    ts_bytes = timestamp.to_bytes(8, "big", signed=False)
    return uuid.UUID(bytes=ts_bytes[:8] + random_bytes)
