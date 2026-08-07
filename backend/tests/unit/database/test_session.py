from pydantic import SecretStr

from app.core.config import Settings
from app.database.session import build_database_url


def test_build_database_url_preserves_and_hides_password() -> None:
    password = "p@ss:word/with#symbols"
    settings = Settings(
        database_password=SecretStr(password),
        _env_file=None,
    )

    database_url = build_database_url(settings)

    assert database_url.drivername == "postgresql+psycopg_async"
    assert database_url.username == "pulsewatch_app"
    assert database_url.password == password
    assert database_url.host == "127.0.0.1"
    assert database_url.port == 5432
    assert database_url.database == "pulsewatch"
    assert password not in str(database_url)
