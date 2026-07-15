"""Add coach-athlete conversation tables.

Revision ID: 010
Revises: 009
Create Date: 2026-07-03
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010"
down_revision: str | Sequence[str] | None = "009"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

conversation_message_kind = postgresql.ENUM(
    "text",
    "question",
    name="conversation_message_kind",
    create_type=False,
)


def upgrade() -> None:
    bind = op.get_bind()
    conversation_message_kind.create(bind, checkfirst=True)

    op.create_table(
        "conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "coach_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "athlete_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("coach_id", "athlete_id", name="uq_conversations_coach_athlete"),
    )
    op.create_index("ix_conversations_coach_id", "conversations", ["coach_id"])
    op.create_index("ix_conversations_athlete_id", "conversations", ["athlete_id"])

    op.create_table(
        "conversation_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column(
            "conversation_id",
            sa.Uuid(),
            sa.ForeignKey("conversations.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "sender_id",
            sa.Uuid(),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("kind", conversation_message_kind, nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("sort_order", sa.Integer(), nullable=False),
        sa.Column("read_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_conversation_messages_conversation_id",
        "conversation_messages",
        ["conversation_id"],
    )
    op.create_index(
        "ix_conversation_messages_sender_id",
        "conversation_messages",
        ["sender_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_conversation_messages_sender_id", table_name="conversation_messages")
    op.drop_index(
        "ix_conversation_messages_conversation_id",
        table_name="conversation_messages",
    )
    op.drop_table("conversation_messages")
    op.drop_index("ix_conversations_athlete_id", table_name="conversations")
    op.drop_index("ix_conversations_coach_id", table_name="conversations")
    op.drop_table("conversations")

    bind = op.get_bind()
    conversation_message_kind.drop(bind, checkfirst=True)
