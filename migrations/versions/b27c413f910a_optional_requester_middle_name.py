"""Сделать отчество заявителя необязательным."""

from alembic import op
import sqlalchemy as sa

revision = "b27c413f910a"
down_revision = "4fa089b76b58"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column(
        "bookings", "requester_middle_name", existing_type=sa.String(128), nullable=True
    )


def downgrade() -> None:
    # Откат не должен молча подменять отсутствующие отчества выдуманными данными.
    op.alter_column(
        "bookings", "requester_middle_name", existing_type=sa.String(128), nullable=False
    )
