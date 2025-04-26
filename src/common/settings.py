from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    bot_token: str
    yandex_gpt_url: str
    yandex_oauth_token: str
    yandex_iam_url: str
    yandex_iam_token: str   = ""
    yandex_folder_id: str

    start_retry: int        = 23  # Retry seconds
    admin_user: str

    db_conn_str: str        = "postgresql://postgres:postgres@pg:5432/tgbot"
    alembic_table_name: str = "tgbot"

    q1: str                 = "Дерево пандо"
    q2: str                 = "James Webb Space Telescope"
    q3: str                 = "Могут ли частицы микропластика преодолевать гематоэнцефалический барьер?"

    # Ability to read variables from .env
    model_config = SettingsConfigDict(
        env_file=Path(__file__).parent.parent.parent / '.env',
        env_file_encoding='utf-8',
    )


settings = Settings()
