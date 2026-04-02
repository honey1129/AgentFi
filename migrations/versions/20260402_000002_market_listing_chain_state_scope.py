"""scope market listing chain state uniqueness by contract

Revision ID: 20260402_000002
Revises: 20260401_000001
Create Date: 2026-04-02 00:00:02
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260402_000002"
down_revision = "20260401_000001"
branch_labels = None
depends_on = None

TABLE_NAME = "market_listing_chain_states"
OLD_INDEX_NAME = "chain_listing_id"
NEW_INDEX_NAME = "uq_market_listing_chain_states_market_contract_chain_listing_id"


def _has_index(bind, table_name: str, index_name: str) -> bool:
    row = bind.execute(
        sa.text(
            """
            SELECT 1
            FROM information_schema.statistics
            WHERE table_schema = DATABASE()
              AND table_name = :table_name
              AND index_name = :index_name
            LIMIT 1
            """
        ),
        {"table_name": table_name, "index_name": index_name},
    ).first()
    return row is not None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if TABLE_NAME not in inspector.get_table_names():
        return

    if _has_index(bind, TABLE_NAME, OLD_INDEX_NAME):
        op.drop_index(OLD_INDEX_NAME, table_name=TABLE_NAME)

    if not _has_index(bind, TABLE_NAME, NEW_INDEX_NAME):
        op.create_index(
            NEW_INDEX_NAME,
            TABLE_NAME,
            ["market_contract_address", "chain_listing_id"],
            unique=True,
        )


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if TABLE_NAME not in inspector.get_table_names():
        return

    if _has_index(bind, TABLE_NAME, NEW_INDEX_NAME):
        op.drop_index(NEW_INDEX_NAME, table_name=TABLE_NAME)

    if not _has_index(bind, TABLE_NAME, OLD_INDEX_NAME):
        op.create_index(OLD_INDEX_NAME, TABLE_NAME, ["chain_listing_id"], unique=True)
