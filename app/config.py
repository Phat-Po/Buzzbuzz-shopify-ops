from pathlib import Path
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///data/launch_os.db"
    anthropic_api_key: str = ""
    shopify_store: str = ""
    shopify_admin_token: str = ""
    shopify_api_version: str = "2025-04"
    default_brand: str = ""
    default_currency: str = "USD"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
MEDIA_DIR = DATA_DIR / "media"

settings = Settings()
