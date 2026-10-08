"""added field to reasone

Revision ID: 020edc0e589e
Revises: c80abfcceba9
Create Date: 2026-10-08 16:38:13.358167

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa



# revision identifiers, used by Alembic.
revision: str = '020edc0e589e'
down_revision: Union[str, None] = 'c80abfcceba9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Старые причины по умолчанию считаются неуважительными.
    # Пользователь может явно включить флаг в UI.
    op.add_column(
        "absence_reasons",
        sa.Column(
            "is_valid",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


    op.add_column(
        "training_attendance",
        sa.Column(
            "reason_id",
            sa.Integer(),
            nullable=True,
        ),
    )


    op.create_index(
        "ix_training_attendance_reason_id",
        "training_attendance",
        ["reason_id"],
        unique=False,
    )


    op.create_foreign_key(
        "fk_training_attendance_reason_id_absence_reasons",
        "training_attendance",
        "absence_reasons",
        ["reason_id"],
        ["id"],
        ondelete="SET NULL",
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_training_attendance_reason_id_absence_reasons",
        "training_attendance",
        type_="foreignkey",
    )


    op.drop_index(
        "ix_training_attendance_reason_id",
        table_name="training_attendance",
    )


    op.drop_column(
        "training_attendance",
        "reason_id",
    )


    op.drop_column(
        "absence_reasons",
        "is_valid",
    )