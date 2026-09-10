"""Remove pedra column from defasagem_risk_record table."""

# ruff: noqa: E501

import sqlalchemy as sa
from alembic import op

revision = "20260909_0005"
down_revision = "20260903_0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the check constraint for pedra
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_record_pedra")
    
    # Drop the pedra column
    op.drop_column("defasagem_risk_record", "pedra")


def downgrade() -> None:
    # Add back the pedra column
    op.add_column(
        "defasagem_risk_record",
        sa.Column("pedra", sa.String(16), nullable=False)
    )
    
    # Add back the check constraint
    op.execute(
        "ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_record_pedra "
        "CHECK (pedra IN ('Quartzo', 'Ágata', 'Ametista', 'Topázio'))"
    )
