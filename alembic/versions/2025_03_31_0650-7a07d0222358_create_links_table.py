"""create links table

Revision ID: 7a07d0222358
Revises: a8e4749976c2
Create Date: 2025-03-31 06:50:41.486114

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "7a07d0222358"
down_revision: Union[str, None] = "a8e4749976c2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "links",
        sa.Column("chat_id", sa.Integer(), nullable=False),
        sa.Column("url", sa.Text(), nullable=False),
        sa.Column("tags", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("filters", sa.ARRAY(sa.String()), nullable=True),
        sa.Column("last_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["chat_id"], ["chats.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_links_url"), "links", ["url"], unique=False)


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_links_url"), table_name="links")
    op.drop_table("links")
