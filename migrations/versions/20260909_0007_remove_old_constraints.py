"""Remove old conflicting check constraints from previous migration."""

# ruff: noqa: E501

import sqlalchemy as sa
from alembic import op

revision = "20260909_0007"
down_revision = "20260909_0006"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old conflicting constraints from the original migration
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_record_defasagem")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_record_fase_ordem")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_record_idade")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_record_ano_ingresso")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_record_instituicao")


def downgrade() -> None:
    # Restore old constraints (not recommended but for completeness)
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_record_defasagem CHECK (defasagem::numeric >= '-10'::integer::numeric)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_record_fase_ordem CHECK (fase_ordem >= 1 AND fase_ordem <= 9)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_record_idade CHECK (idade >= 6 AND idade <= 18)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_record_ano_ingresso CHECK (ano_ingresso >= 2010)")
    op.execute(
        "ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_record_instituicao "
        "CHECK (instituicao::text = ANY (ARRAY['Pública'::character varying::text, 'Privada'::character varying::text]))"
    )
