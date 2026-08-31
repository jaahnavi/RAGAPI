from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


@dataclass
class Documents:
    """A document item as stored in the Cosmos DB 'documents' container.

    `id` is the Cosmos item id and partition key (a uuid4 string) — it
    replaces the old auto-increment integer primary key.
    """

    id: str
    filename: str
    filepath: str | None = None
    source_url: str | None = None
    content_hash: str | None = None
    source_type: str = "upload"  # "seed" or "upload"
    status: str = "processing"  # processing / ready / failed
    error: str | None = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)

    def to_item(self) -> dict:
        return asdict(self)

    @classmethod
    def from_item(cls, item: dict) -> "Documents":
        return cls(**{f: item.get(f) for f in cls.__dataclass_fields__})
