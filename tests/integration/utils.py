from uuid import UUID


def extract_uuid(path: str) -> str:
    """Return the first URL path segment that is a valid UUID."""
    for part in path.split("/"):
        try:
            UUID(part)
        except ValueError:
            continue
        return part
    raise ValueError(f"No UUID found in path: {path}")
