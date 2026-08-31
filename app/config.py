from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    cosmos_connection_string: str = ""
    cosmos_database_name: str = "ragapi"
    cosmos_container_name: str = "documents"

    chroma_dir: str = "data/chroma"
    collection_name: str = "health_insurance"

    azure_storage_connection_string: str = ""
    azure_storage_container: str = "documents"

    embedding_model: str = "text-embedding-3-small"
    llm_model: str = "gpt-4o-mini"

    rrf_k: int = 60  # standard RRF constant
    confidence_threshold: float = 0.0  # min vector similarity to attempt an answer
    score_threshold: float = 0.15  # min vector similarity for a chunk to count

    allowed_download_domains: set[str] = {"medicare.gov", "cms.gov", "healthcare.gov"}


settings = Settings()
