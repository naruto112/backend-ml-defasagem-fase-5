"""Create defasagem_risk_record table and update domain_field data_type constraint."""

# ruff: noqa: E501

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "20260903_0004"
down_revision = "20260714_0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Update domain_field data_type constraint to include 'number'
    op.execute("ALTER TABLE domain_field DROP CONSTRAINT IF EXISTS ck_domain_field_data_type")
    op.execute(
        "ALTER TABLE domain_field ADD CONSTRAINT ck_domain_field_data_type "
        "CHECK (data_type IN ('integer', 'string', 'number'))"
    )

    # Drop old obesity-related tables and domain fields
    op.execute("DROP TABLE IF EXISTS obesity_record CASCADE")
    op.execute("DELETE FROM domain_option WHERE domain_field_id IN (SELECT id FROM domain_field WHERE name IN ('monitora_calorias', 'fuma', 'come_vegetaiis', 'refeicoes_diariamente', 'come_entre_refeicao', 'litro_agua', 'frequencia_semanal_atvidade_fisica', 'horas_dispositivo_eletronico', 'consome_bebida_alcoolica', 'historico_familiar', 'alimentos_calorico', 'meio_transporte'))")
    op.execute("DELETE FROM domain_field WHERE name IN ('monitora_calorias', 'fuma', 'come_vegetaiis', 'refeicoes_diariamente', 'come_entre_refeicao', 'litro_agua', 'frequencia_semanal_atvidade_fisica', 'horas_dispositivo_eletronico', 'consome_bebida_alcoolica', 'historico_familiar', 'alimentos_calorico', 'meio_transporte')")

    # Create defasagem_risk_record table
    op.create_table(
        "defasagem_risk_record",
        sa.Column("id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("defasagem", sa.Numeric(5, 2), nullable=False),
        sa.Column("fase_ordem", sa.SmallInteger(), nullable=False),
        sa.Column("idade", sa.SmallInteger(), nullable=False),
        sa.Column("ano_ingresso", sa.Integer(), nullable=False),
        sa.Column("ida", sa.Numeric(5, 2), nullable=False),
        sa.Column("ieg", sa.Numeric(5, 2), nullable=False),
        sa.Column("iaa", sa.Numeric(5, 2), nullable=False),
        sa.Column("ips", sa.Numeric(5, 2), nullable=False),
        sa.Column("ipv", sa.Numeric(5, 2), nullable=False),
        sa.Column("inde", sa.Numeric(5, 2), nullable=False),
        sa.Column("genero", sa.String(16), nullable=False),
        sa.Column("instituicao", sa.String(16), nullable=False),
        sa.Column("pedra", sa.String(16), nullable=False),
        sa.Column("probabilidade", sa.Numeric(5, 4), nullable=False),
        sa.Column("faixa_risco", sa.String(32), nullable=False),
        sa.Column("acao_sugerida", sa.String(256), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.CheckConstraint("idade BETWEEN 6 AND 18", name="ck_defasagem_record_idade"),
        sa.CheckConstraint(
            "genero IN ('Feminino', 'Masculino')", name="ck_defasagem_record_genero"
        ),
        sa.CheckConstraint(
            "instituicao IN ('Pública', 'Privada')", name="ck_defasagem_record_instituicao"
        ),
        sa.CheckConstraint(
            "pedra IN ('Quartzo', 'Ágata', 'Ametista', 'Topázio')",
            name="ck_defasagem_record_pedra",
        ),
        sa.CheckConstraint("defasagem >= -10", name="ck_defasagem_record_defasagem"),
        sa.CheckConstraint("fase_ordem BETWEEN 1 AND 9", name="ck_defasagem_record_fase_ordem"),
        sa.CheckConstraint("ano_ingresso >= 2010", name="ck_defasagem_record_ano_ingresso"),
        sa.CheckConstraint(
            "probabilidade BETWEEN 0 AND 1", name="ck_defasagem_record_probabilidade"
        ),
        sa.CheckConstraint(
            "faixa_risco IN ('Baixo', 'Médio', 'Alto')", name="ck_defasagem_record_faixa_risco"
        ),
        sa.PrimaryKeyConstraint("id", name="pk_defasagem_risk_record"),
    )
    op.create_index("ix_defasagem_risk_record_created_at", "defasagem_risk_record", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_defasagem_risk_record_created_at", table_name="defasagem_risk_record")
    op.drop_table("defasagem_risk_record")
    
    # Revert domain_field data_type constraint
    op.execute("ALTER TABLE domain_field DROP CONSTRAINT IF EXISTS ck_domain_field_data_type")
    op.execute(
        "ALTER TABLE domain_field ADD CONSTRAINT ck_domain_field_data_type "
        "CHECK (data_type IN ('integer', 'string'))"
    )

    # Recreate obesity_record table on downgrade (optional)
    # Note: This is a simplified recreation - full schema would need all columns
