import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from mealie.services.openai import OpenAIService
from tests.utils.alembic_reader import ALEMBIC_MIGRATIONS, import_file

GROUP_ID = "a" * 32
SETTINGS_ID = "b" * 32


def _upgrade(connection: sa.Connection) -> list[sa.Row]:
    path = next(ALEMBIC_MIGRATIONS.glob("*ab458b0d52b2*.py"))
    with Operations.context(MigrationContext.configure(connection)):
        import_file("repair_skipped_ai_prompt_overrides", path).upgrade()

    return list(
        connection.execute(
            sa.text("SELECT settings_id, name, mode, content, base_prompt_hash FROM ai_prompt_overrides ORDER BY name")
        )
    )


def _create_settings(connection: sa.Connection) -> None:
    connection.execute(sa.text("CREATE TABLE ai_provider_settings (id CHAR(32) PRIMARY KEY, group_id CHAR(32))"))
    connection.execute(
        sa.text("INSERT INTO ai_provider_settings (id, group_id) VALUES (:id, :group_id)"),
        {"id": SETTINGS_ID, "group_id": GROUP_ID},
    )


def test_migration_converts_group_scoped_table_that_skipped_a91720b8a7e7(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_CUSTOM_PROMPT_DIR", raising=False)

    engine = sa.create_engine("sqlite://")
    try:
        with engine.connect() as connection:
            _create_settings(connection)
            # The table as revision 5e62206b4547 created it
            connection.execute(
                sa.text(
                    "CREATE TABLE ai_prompt_overrides (id CHAR(32) PRIMARY KEY, group_id CHAR(32) NOT NULL, "
                    "name VARCHAR NOT NULL, prompt TEXT NOT NULL, created_at DATETIME, update_at DATETIME)"
                )
            )
            for i, (name, prompt) in enumerate(
                [
                    ("recipes.build-recipe", "my build"),
                    ("recipes.compile-source", "my compile"),  # moved to system.compile-source
                    ("general.debug", "no longer customizable"),
                ]
            ):
                connection.execute(
                    sa.text("INSERT INTO ai_prompt_overrides (id, group_id, name, prompt) VALUES (:id, :g, :n, :p)"),
                    {"id": str(i) * 32, "g": GROUP_ID, "n": name, "p": prompt},
                )

            rows = _upgrade(connection)
    finally:
        engine.dispose()

    assert [(row.settings_id, row.name, row.mode, row.content) for row in rows] == [
        (SETTINGS_ID, "recipes.build-recipe", "override", "my build"),
        (SETTINGS_ID, "system.compile-source", "override", "my compile"),
    ]
    for row in rows:
        assert row.base_prompt_hash == OpenAIService._hash_prompt(OpenAIService.get_default_prompt(row.name))


def test_migration_leaves_settings_scoped_table_alone(monkeypatch) -> None:
    monkeypatch.delenv("OPENAI_CUSTOM_PROMPT_DIR", raising=False)

    engine = sa.create_engine("sqlite://")
    try:
        with engine.connect() as connection:
            _create_settings(connection)
            connection.execute(
                sa.text(
                    "CREATE TABLE ai_prompt_overrides (id CHAR(32) PRIMARY KEY, settings_id CHAR(32) NOT NULL, "
                    "name VARCHAR NOT NULL, mode VARCHAR NOT NULL, content VARCHAR NOT NULL, base_prompt_hash VARCHAR)"
                )
            )
            connection.execute(
                sa.text(
                    "INSERT INTO ai_prompt_overrides (id, settings_id, name, mode, content) "
                    "VALUES (:id, :s, 'recipes.build-recipe', 'append', 'extra')"
                ),
                {"id": "c" * 32, "s": SETTINGS_ID},
            )

            rows = _upgrade(connection)
    finally:
        engine.dispose()

    assert [(row.name, row.mode, row.content) for row in rows] == [("recipes.build-recipe", "append", "extra")]
