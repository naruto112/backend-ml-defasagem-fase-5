"""Fix PEDE field ranges, labels and add missing instituicao categories."""

# ruff: noqa: E501

import sqlalchemy as sa
from alembic import op

revision = "20260909_0006"
down_revision = "20260909_0005"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop old check constraints
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_defasagem")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_fase_ordem")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_idade")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ano")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_instituicao")
    
    # Change defasagem from numeric to smallint
    op.execute("ALTER TABLE defasagem_risk_record ALTER COLUMN defasagem TYPE SMALLINT USING defasagem::SMALLINT")
    
    # Increase instituicao column size to accommodate longer values
    op.execute("ALTER TABLE defasagem_risk_record ALTER COLUMN instituicao TYPE VARCHAR(64)")
    
    # Add new check constraints with correct ranges
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_defasagem CHECK (defasagem >= -4 AND defasagem <= 2)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_fase_ordem CHECK (fase_ordem BETWEEN 0 AND 8)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_idade CHECK (idade BETWEEN 7 AND 26)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ano CHECK (ano_ingresso >= 2016 AND ano_ingresso <= 2023)")
    op.execute(
        "ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_instituicao "
        "CHECK (instituicao IN ('Pública', 'Privada', 'Privada - Programa de Apadrinhamento', "
        "'Privada *Parcerias com Bolsa 100%', 'Privada - Pagamento por *Empresa Parceira', 'Concluiu o 3º EM'))"
    )


def downgrade() -> None:
    # Drop new check constraints
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_defasagem")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_fase_ordem")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_idade")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ano")
    op.execute("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_instituicao")
    
    # Revert defasagem to numeric
    op.execute("ALTER TABLE defasagem_risk_record ALTER COLUMN defasagem TYPE NUMERIC(5, 2) USING defasagem::NUMERIC(5, 2)")
    
    # Revert instituicao column size
    op.execute("ALTER TABLE defasagem_risk_record ALTER COLUMN instituicao TYPE VARCHAR(16)")
    
    # Restore old check constraints
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_defasagem CHECK (defasagem >= -10)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_fase_ordem CHECK (fase_ordem BETWEEN 1 AND 9)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_idade CHECK (idade BETWEEN 6 AND 18)")
    op.execute("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ano CHECK (ano_ingresso >= 2010)")
    op.execute(
        "ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_instituicao "
        "CHECK (instituicao IN ('Pública', 'Privada'))"
    )
