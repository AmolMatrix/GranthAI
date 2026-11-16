"""Small shared helpers."""
from datetime import datetime, timezone


def utcnow():
    """Timezone-aware replacement for the deprecated datetime.utcnow()."""
    return datetime.now(timezone.utc)
