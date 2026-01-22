from functools import lru_cache
import json
from typing import List, Union

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")
    jwt_secret_key: str = Field(..., env="JWT_SECRET_KEY")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_exp_minutes: int = Field(120, env="JWT_EXP_MINUTES")

    database_path: str = Field("app/db/mangas.db", env="DATABASE_PATH")

    resources_portadas_dir: str = Field("resources/portadas", env="RESOURCES_PORTADAS_DIR")
    resources_capitulos_dir: str = Field("resources/capitulos", env="RESOURCES_CAPITULOS_DIR")
    resources_logos_dir: str = Field("resources/logos", env="RESOURCES_LOGOS_DIR")
    resources_tmp_dir: str = Field("resources/tmp", env="RESOURCES_TMP_DIR")
    default_portada_filename: str = Field("portada_por_defecto.jpg", env="DEFAULT_PORTADA_FILENAME")
    static_portadas_path: str = Field("/static/portadas", env="STATIC_PORTADAS_PATH")
    static_capitulos_path: str = Field("/static/capitulos", env="STATIC_CAPITULOS_PATH")
    static_logos_path: str = Field("/static/logos", env="STATIC_LOGOS_PATH")

    CORS_ALLOW_ORIGINS: Union[List[str], str] = Field(default="*", env="CORS_ALLOW_ORIGINS")
    min_image_bytes: int = Field(1024, env="MIN_IMAGE_BYTES")
    database_path: str = Field("app/db/mangas.db", env="DATABASE_PATH")

    resources_portadas_dir: str = Field("resources/portadas", env="RESOURCES_PORTADAS_DIR")
    resources_capitulos_dir: str = Field("resources/capitulos", env="RESOURCES_CAPITULOS_DIR")
    resources_logos_dir: str = Field("resources/logos", env="RESOURCES_LOGOS_DIR")
    resources_tmp_dir: str = Field("resources/tmp", env="RESOURCES_TMP_DIR")
    default_portada_filename: str = Field("portada_por_defecto.jpg", env="DEFAULT_PORTADA_FILENAME")
    static_portadas_path: str = Field("/static/portadas", env="STATIC_PORTADAS_PATH")
    static_capitulos_path: str = Field("/static/capitulos", env="STATIC_CAPITULOS_PATH")
    static_logos_path: str = Field("/static/logos", env="STATIC_LOGOS_PATH")

    CORS_ALLOW_ORIGINS: Union[List[str], str] = Field(default="*", env="CORS_ALLOW_ORIGINS")
    min_image_bytes: int = Field(1024, env="MIN_IMAGE_BYTES")

    @field_validator("CORS_ALLOW_ORIGINS", mode="before")
    @classmethod
    def _parse_cors_origins(cls, value):
        if isinstance(value, str):
            value = value.strip()
            if value.startswith("[") and value.endswith("]"):
                try:
                    parsed = json.loads(value)
                    if isinstance(parsed, list):
                        return [item for item in parsed if isinstance(item, str) and item.strip()] or ["*"]
                except json.JSONDecodeError:
                    pass
            items = [item.strip() for item in value.split(",") if item.strip()]
            return items or ["*"]
        if isinstance(value, (list, tuple, set)):
            return [str(item).strip() for item in value if str(item).strip()] or ["*"]
        return ["*"]

    @property
    def cors_allow_origins(self) -> List[str]:
        return self.CORS_ALLOW_ORIGINS


@lru_cache()
def get_settings() -> Settings:
    return Settings()
