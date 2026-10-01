from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    jira_base_url: str
    jira_email: str
    jira_api_token: str
    jira_board_id: int
    download_dir: Path = Path("downloads") # Directorio donde se descargaran los adjuntos de Jira
    output_file: Path = Path("output/merged.docx") # Documento final con texto e imagenes

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


