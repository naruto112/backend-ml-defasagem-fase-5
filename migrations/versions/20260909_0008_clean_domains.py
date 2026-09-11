"""Clean up domain catalog - remove pedra field and fase_ordem=9 option."""

import sqlalchemy as sa
from alembic import op

revision = "20260909_0008"
down_revision = "20260909_0007"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Mark pedra field as inactive (soft delete)
    op.execute("UPDATE domain_field SET active = FALSE WHERE name = 'pedra'")
    
    # Remove fase_ordem = 9 option (it was a duplicate of Fase 4)
    op.execute("""
        DELETE FROM domain_option 
        WHERE domain_field_id = (SELECT id FROM domain_field WHERE name = 'fase_ordem')
        AND value = '9'
    """)


def downgrade() -> None:
    # Restore pedra field as active
    op.execute("UPDATE domain_field SET active = TRUE WHERE name = 'pedra'")
    
    # Restore fase_ordem = 9 option
    op.execute("""
        INSERT INTO domain_option (domain_field_id, value, label, display_order, active, created_at, updated_at)
        SELECT id, '9', '9º ano', 9, TRUE, NOW(), NOW()
        FROM domain_field WHERE name = 'fase_ordem'
        ON CONFLICT (domain_field_id, value) DO NOTHING
    """)
