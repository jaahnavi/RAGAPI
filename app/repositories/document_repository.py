from azure.cosmos.container import ContainerProxy
from azure.cosmos.exceptions import CosmosResourceNotFoundError

from app.models.document import Documents, _now_iso


def get_by_id(container: ContainerProxy, doc_id: str) -> Documents | None:
    try:
        item = container.read_item(item=doc_id, partition_key=doc_id)
    except CosmosResourceNotFoundError:
        return None
    return Documents.from_item(item)


def get_by_source_url(container: ContainerProxy, url: str) -> Documents | None:
    items = list(container.query_items(
        query="SELECT * FROM c WHERE c.source_url = @url",
        parameters=[{"name": "@url", "value": url}],
        enable_cross_partition_query=True,
    ))
    return Documents.from_item(items[0]) if items else None


def get_by_content_hash(container: ContainerProxy, content_hash: str) -> Documents | None:
    items = list(container.query_items(
        query="SELECT * FROM c WHERE c.content_hash = @hash",
        parameters=[{"name": "@hash", "value": content_hash}],
        enable_cross_partition_query=True,
    ))
    return Documents.from_item(items[0]) if items else None


def list_all(container: ContainerProxy) -> list[Documents]:
    items = container.query_items(
        query="SELECT * FROM c ORDER BY c.created_at DESC",
        enable_cross_partition_query=True,
    )
    return [Documents.from_item(item) for item in items]


def create(container: ContainerProxy, doc: Documents) -> Documents:
    item = container.create_item(body=doc.to_item())
    return Documents.from_item(item)


def update_status(container: ContainerProxy, doc: Documents, status: str, error: str | None = None) -> Documents:
    doc.status = status
    doc.error = error
    doc.updated_at = _now_iso()
    item = container.upsert_item(body=doc.to_item())
    return Documents.from_item(item)


def delete(container: ContainerProxy, doc_id: str) -> None:
    try:
        container.delete_item(item=doc_id, partition_key=doc_id)
    except CosmosResourceNotFoundError:
        pass
