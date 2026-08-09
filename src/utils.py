"""Utility helpers for the MahaRERA project."""

# TODO: implement shared utilities


def ensure_dir(path):
    """Ensure a directory exists."""
    import os
    os.makedirs(path, exist_ok=True)
