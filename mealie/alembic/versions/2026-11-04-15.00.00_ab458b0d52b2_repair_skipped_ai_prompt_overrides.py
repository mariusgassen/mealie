"""repair ai prompt overrides on databases that skipped a91720b8a7e7

Revision ID: ab458b0d52b2
Revises: 071e03b4f851
Create Date: 2026-11-04 15:00:00.000000

The upstream sync placed upstream's a91720b8a7e7 (settings-scoped ai_prompt_overrides) between
1e69ea7cd45e and 7b1d4e9a2c58. Databases that were already at 7b1d4e9a2c58 or later never ran it,
so they still have this fork's group-scoped table from 5e62206b4547 (no settings_id column).
This revision runs the skipped upgrade on those databases and carries the group-scoped overrides over.
"""

import importlib.util
from pathlib import Path

import sqlalchemy as sa
from alembic import op

from mealie.core.root_logger import get_logger

# revision identifiers, used by Alembic.
revision = "ab458b0d52b2"
down_revision: str | None = "071e03b4f851"
branch_labels: str | tuple[str, ...] | None = None
depends_on: str | tuple[str, ...] | None = None

logger = get_logger()


def load_skipped_revision():
    path = next(Path(__file__).parent.glob("*_a91720b8a7e7_*.py"))
    spec = importlib.util.spec_from_file_location("a91720b8a7e7_add_ai_prompt_overrides", path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Unable to import {path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = (
        {c["name"] for c in inspector.get_columns("ai_prompt_overrides")}
        if inspector.has_table("ai_prompt_overrides")
        else set()
    )
    if "settings_id" in columns:
        return

    legacy_overrides = []
    if "group_id" in columns:
        legacy_overrides = conn.execute(
            sa.text(
                "SELECT s.id AS settings_id, o.name, o.prompt, o.created_at, o.update_at "
                "FROM ai_prompt_overrides o JOIN ai_provider_settings s ON s.group_id = o.group_id"
            )
        ).all()

    skipped = load_skipped_revision()
    logger.info("Running skipped revision a91720b8a7e7 for ai_prompt_overrides")
    skipped.upgrade()

    for row in legacy_overrides:
        # Same renames as the custom prompt files; prompts that are no longer customizable are dropped
        category, prompt = row.name.split(".", 1)
        name = skipped.LEGACY_PROMPT_FILES.get(f"{category}/{prompt}.txt", row.name)
        base_prompt_hash = skipped.hash_built_in_prompt(name)
        if base_prompt_hash is None:
            logger.info(f"Dropping override for prompt that is no longer used: {row.name}")
            continue

        # The group's own override is newer than anything imported from OPENAI_CUSTOM_PROMPT_DIR
        conn.execute(
            sa.text("DELETE FROM ai_prompt_overrides WHERE settings_id = :settings_id AND name = :name"),
            {"settings_id": row.settings_id, "name": name},
        )
        conn.execute(
            sa.text(
                "INSERT INTO ai_prompt_overrides "
                "(id, settings_id, name, mode, content, base_prompt_hash, created_at, update_at) "
                "VALUES (:id, :settings_id, :name, :mode, :content, :base_prompt_hash, :created_at, :update_at)"
            ),
            {
                "id": skipped.generate_id(),
                "settings_id": row.settings_id,
                "name": name,
                "mode": "override",
                "content": row.prompt,
                "base_prompt_hash": base_prompt_hash,
                "created_at": row.created_at,
                "update_at": row.update_at,
            },
        )


def downgrade():
    pass
