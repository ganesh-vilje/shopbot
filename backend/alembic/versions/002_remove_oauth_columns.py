"""remove oauth columns from customers

Revision ID: 002
Revises: 001
Create Date: 2026-04-07
"""

from alembic import op
import sqlalchemy as sa


revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("customers")}

    if "oauth_provider" in columns:
        op.drop_column("customers", "oauth_provider")
    if "oauth_id" in columns:
        op.drop_column("customers", "oauth_id")


def downgrade() -> None:
    bind = op.get_bind()
    inspector = sa.inspect(bind)
    columns = {column["name"] for column in inspector.get_columns("customers")}

    if "oauth_provider" not in columns:
        op.add_column("customers", sa.Column("oauth_provider", sa.String(50), nullable=True))
    if "oauth_id" not in columns:
        op.add_column("customers", sa.Column("oauth_id", sa.String(255), nullable=True))
