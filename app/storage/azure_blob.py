from urllib.parse import urlparse

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient, ContainerClient

from app.config import settings

_container_client: ContainerClient | None = None


def get_container_client() -> ContainerClient:
    global _container_client
    if _container_client is None:
        service_client = BlobServiceClient.from_connection_string(
            settings.azure_storage_connection_string
        )
        container_client = service_client.get_container_client(
            settings.azure_storage_container
        )
        if not container_client.exists():
            container_client.create_container()
        _container_client = container_client
    return _container_client


def get_blob_url(blob_name: str) -> str:
    return get_container_client().get_blob_client(blob_name).url


def _to_blob_name(blob_name_or_url: str) -> str:
    """Accept either a bare blob name (e.g. 'uploads/x.pdf') or a full blob
    URL (e.g. 'https://acct.blob.core.windows.net/container/uploads/x.pdf')
    and return just the blob name."""
    if blob_name_or_url.startswith("http://") or blob_name_or_url.startswith("https://"):
        path = urlparse(blob_name_or_url).path.lstrip("/")
        # path is "<container>/<blob_name>" — drop the container segment
        return path.split("/", 1)[1]
    return blob_name_or_url


def upload_blob(blob_name: str, content: bytes) -> str:
    """Uploads content under blob_name and returns the blob's full absolute URL."""
    get_container_client().upload_blob(name=blob_name, data=content, overwrite=True)
    return get_blob_url(blob_name)


def download_blob(blob_name_or_url: str) -> bytes:
    return get_container_client().download_blob(_to_blob_name(blob_name_or_url)).readall()


def delete_blob(blob_name_or_url: str) -> None:
    try:
        get_container_client().delete_blob(_to_blob_name(blob_name_or_url))
    except ResourceNotFoundError:
        pass
