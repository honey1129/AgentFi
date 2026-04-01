"""add run controls and execution indexes

Revision ID: 20260401_000001
Revises:
Create Date: 2026-04-01 00:00:01
"""

from __future__ import annotations

from alembic import op
import sqlalchemy as sa


revision = "20260401_000001"
down_revision = None
branch_labels = None
depends_on = None


def _has_index(indexes: list[dict], name: str) -> bool:
    return any(index.get("name") == name for index in indexes)


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "agent_runs" not in inspector.get_table_names():
        return

    columns = {column["name"]: column for column in inspector.get_columns("agent_runs")}

    if "parent_run_id" not in columns:
        op.add_column("agent_runs", sa.Column("parent_run_id", sa.String(length=64), nullable=True))

    if "attempt_count" not in columns:
        op.add_column(
            "agent_runs",
            sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        )

    if "max_attempts" not in columns:
        op.add_column(
            "agent_runs",
            sa.Column("max_attempts", sa.Integer(), nullable=False, server_default="3"),
        )

    if "timeout_seconds" not in columns:
        op.add_column(
            "agent_runs",
            sa.Column("timeout_seconds", sa.Integer(), nullable=False, server_default="90"),
        )

    if "celery_task_id" not in columns:
        op.add_column("agent_runs", sa.Column("celery_task_id", sa.String(length=120), nullable=True))

    if "failure_reason" not in columns:
        op.add_column("agent_runs", sa.Column("failure_reason", sa.Text(), nullable=True))

    if "queued_at" not in columns:
        op.add_column(
            "agent_runs",
            sa.Column(
                "queued_at",
                sa.DateTime(timezone=True),
                nullable=True,
                server_default=sa.text("CURRENT_TIMESTAMP"),
            ),
        )
        if "created_at" in columns:
            op.execute(
                sa.text(
                    "UPDATE agent_runs SET queued_at = COALESCE(created_at, started_at, finished_at, UTC_TIMESTAMP()) "
                    "WHERE queued_at IS NULL"
                )
            )
        else:
            op.execute(
                sa.text(
                    "UPDATE agent_runs SET queued_at = COALESCE(started_at, finished_at, UTC_TIMESTAMP()) "
                    "WHERE queued_at IS NULL"
                )
            )
        op.alter_column("agent_runs", "queued_at", nullable=False, server_default=sa.text("CURRENT_TIMESTAMP"))

    if "next_retry_at" not in columns:
        op.add_column("agent_runs", sa.Column("next_retry_at", sa.DateTime(timezone=True), nullable=True))

    if "cancel_requested_at" not in columns:
        op.add_column("agent_runs", sa.Column("cancel_requested_at", sa.DateTime(timezone=True), nullable=True))

    if "dead_lettered_at" not in columns:
        op.add_column("agent_runs", sa.Column("dead_lettered_at", sa.DateTime(timezone=True), nullable=True))

    if "started_at" in columns and not columns["started_at"].get("nullable", True):
        op.alter_column("agent_runs", "started_at", existing_type=sa.DateTime(timezone=True), nullable=True)

    indexes = inspector.get_indexes("agent_runs")
    if not _has_index(indexes, "ix_agent_runs_status_queued_at"):
        op.create_index("ix_agent_runs_status_queued_at", "agent_runs", ["status", "queued_at"], unique=False)
    if not _has_index(indexes, "ix_agent_runs_agent_id_queued_at"):
        op.create_index("ix_agent_runs_agent_id_queued_at", "agent_runs", ["agent_id", "queued_at"], unique=False)
    if not _has_index(indexes, "ix_agent_runs_dead_lettered_at"):
        op.create_index("ix_agent_runs_dead_lettered_at", "agent_runs", ["dead_lettered_at"], unique=False)


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)

    if "agent_runs" not in inspector.get_table_names():
        return

    indexes = inspector.get_indexes("agent_runs")
    if _has_index(indexes, "ix_agent_runs_dead_lettered_at"):
        op.drop_index("ix_agent_runs_dead_lettered_at", table_name="agent_runs")
    if _has_index(indexes, "ix_agent_runs_agent_id_queued_at"):
        op.drop_index("ix_agent_runs_agent_id_queued_at", table_name="agent_runs")
    if _has_index(indexes, "ix_agent_runs_status_queued_at"):
        op.drop_index("ix_agent_runs_status_queued_at", table_name="agent_runs")

    columns = {column["name"] for column in inspector.get_columns("agent_runs")}
    for column_name in [
        "dead_lettered_at",
        "cancel_requested_at",
        "next_retry_at",
        "queued_at",
        "failure_reason",
        "celery_task_id",
        "timeout_seconds",
        "max_attempts",
        "attempt_count",
        "parent_run_id",
    ]:
        if column_name in columns:
            op.drop_column("agent_runs", column_name)
