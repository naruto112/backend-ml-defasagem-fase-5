"""update_field_ranges_defasagem_idade_ano_ingresso_scores

Revision ID: 0c2e38a2b548
Revises: 20260909_0008
Create Date: 2026-09-10 23:05:49.639934
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text


revision: str = '0c2e38a2b548'
down_revision: Union[str, None] = '20260909_0008'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Use raw SQL to handle the constraint changes properly
    conn = op.get_bind()
    
    # Drop old constraints individually, ignore if they don't exist
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_defasagem"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_idade"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ano"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ida"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ieg"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_iaa"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ips"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ipv"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_inde"))

    # Create new constraints with updated ranges
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_defasagem CHECK (defasagem >= -100 AND defasagem <= 100)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_idade CHECK (idade BETWEEN 1 AND 99)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ano CHECK (ano_ingresso >= 2016 AND ano_ingresso <= 4000)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ida CHECK (ida BETWEEN 0 AND 100)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ieg CHECK (ieg BETWEEN 0 AND 100)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_iaa CHECK (iaa BETWEEN 0 AND 100)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ips CHECK (ips BETWEEN 0 AND 100)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ipv CHECK (ipv BETWEEN 0 AND 100)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_inde CHECK (inde BETWEEN 0 AND 100)"))


def downgrade() -> None:
    conn = op.get_bind()
    
    # Drop new constraints
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_defasagem"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_idade"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ano"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ida"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ieg"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_iaa"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ips"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_ipv"))
    conn.execute(text("ALTER TABLE defasagem_risk_record DROP CONSTRAINT IF EXISTS ck_defasagem_risk_inde"))

    # Restore old constraints
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_defasagem CHECK (defasagem >= -4 AND defasagem <= 2)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_idade CHECK (idade BETWEEN 7 AND 26)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ano CHECK (ano_ingresso >= 2016 AND ano_ingresso <= 2023)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ida CHECK (ida BETWEEN 0 AND 10)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ieg CHECK (ieg BETWEEN 0 AND 10)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_iaa CHECK (iaa BETWEEN 0 AND 10)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ips CHECK (ips BETWEEN 0 AND 10)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_ipv CHECK (ipv BETWEEN 0 AND 10)"))
    conn.execute(text("ALTER TABLE defasagem_risk_record ADD CONSTRAINT ck_defasagem_risk_inde CHECK (inde BETWEEN 0 AND 10)"))
