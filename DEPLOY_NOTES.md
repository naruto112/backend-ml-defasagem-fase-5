# Deploy Notes - Atualização Backend PEDE (Setembro 2026)

## Resumo das Alterações

Este documento descreve todas as alterações feitas no backend para alinhar com o modelo PEDE 2022-2024 e resolver as 8 divergências identificadas no documento `Divergencias_API_vs_Modelo.md`.

## Arquivos Modificados

### 1. `app/schemas/defasagem_risk_record_schema.py`
- **Campo `defasagem`**: mudou de `StrictNumber` para `StrictInteger`, range de -10/20 para -4/+2
- **Campo `fase_ordem`**: range de 1-9 para 0-8
- **Campo `idade`**: range de 6-18 para 7-26
- **Campo `ano_ingresso`**: range de 2010/2100 para 2016/2023
- **ReadSchema**: `defasagem` mudou para `StrictInteger`

### 2. `app/domain_catalog.py`
- **Campo `instituicao`**: adicionadas 4 categorias (total de 6):
  - Pública
  - Privada
  - Privada - Programa de Apadrinhamento
  - Privada *Parcerias com Bolsa 100%
  - Privada - Pagamento por *Empresa Parceira
  - Concluiu o 3º EM

### 3. `app/models/defasagem_risk_record.py`
- **Check constraints atualizados**:
  - `defasagem`: -4 a +2 (era >= -10)
  - `fase_ordem`: 0-8 (era 1-9)
  - `idade`: 7-26 (era 6-18)
  - `ano_ingresso`: 2016-2023 (era >= 2010)
  - `instituicao`: 6 categorias (era 2)
- **Tipo de coluna `defasagem`**: mudou de `Float` para `SmallInteger`
- **Tamanho de `instituicao`**: mudou de `String(16)` para `String(64)`

### 4. `app/ml/feature_transformer.py`
- **Campo `defasagem`**: conversão para `int` (era `float`)

### 5. `seeds/domain_options.py`
- **Rótulos atualizados**:
  - `defasagem`: "Defasagem escolar (fases, negativa = atrasado)"
  - `fase_ordem`: "Fase de escolaridade PEDE (ordem)" com opções 0-8
  - `ieg`: "Indicador de Engajamento (IEG)"
  - `iaa`: "Indicador de Autoavaliação (IAA)"
  - `ips`: "Indicador Psicossocial (IPS)"
  - `ipv`: "Indicador de Ponto de Virada (IPV)"
  - `inde`: "Índice de Desenvolvimento Educacional (INDE)"
- **Campo `instituicao`**: adicionadas 4 categorias
- **Campo `defasagem`**: tipo mudou para `integer`

### 6. `artifacts/modelo_risco_defasagem.manifest.json`
- **SHA-256**: calculado e atualizado (era "pending")
- **Features**: 12 campos (sem `pedra`)

### 7. `tests/unit/test_defasagem_risk_record_schema.py`
- **Payload atualizado**: valores válidos para novos ranges
- **Testes de range**: atualizados para idade 7-26, defasagem -4/+2
- **Novos testes**: adicionados para validação de `defasagem`

### 8. `README.md`
- **Tabela de campos**: atualizada com ranges e rótulos corretos
- **Exemplo de request**: atualizado com valores válidos

### 9. `compose.yaml`
- **Adicionado build context** para serviço `api` para garantir código atualizado

## Migrations

### Migration 20260909_0005_remove_pedra_column.py
- Remove coluna `pedra` da tabela `defasagem_risk_record`
- Remove constraint `ck_defasagem_risk_pedra`

### Migration 20260909_0006_fix_pede_ranges_and_labels.py
- Altera tipo de coluna `defasagem` de `numeric` para `smallint`
- Aumenta tamanho de `instituicao` de `varchar(16)` para `varchar(64)`
- Atualiza check constraints:
  - `defasagem`: -4 a +2
  - `fase_ordem`: 0-8
  - `idade`: 7-26
  - `ano_ingresso`: 2016-2023
  - `instituicao`: 6 categorias

### Migration 20260909_0007_remove_old_constraints.py
- Remove constraints antigos conflitantes da migration original:
  - `ck_defasagem_record_defasagem`
  - `ck_defasagem_record_fase_ordem`
  - `ck_defasagem_record_idade`
  - `ck_defasagem_record_ano_ingresso`
  - `ck_defasagem_record_instituicao`

### Migration 20260909_0008_clean_domains.py
- Marca campo `pedra` como inactive (soft delete) no domain catalog
- Remove opção `fase_ordem = 9` do domain catalog (era duplicado de Fase 4)

## Instruções para Deploy na Cloud

### 1. Build e Push da Imagem Docker
```bash
docker compose build
docker tag defasagem-risk-api:latest <registry>/defasagem-risk-api:latest
docker push <registry>/defasagem-risk-api:latest
```

### 2. Executar Migrations
```bash
# No ambiente de produção
alembic upgrade head
```

### 3. Atualizar Seeds
```bash
python -m seeds.domain_options
```

### 4. Reiniciar Serviço
```bash
# Reiniciar o serviço da API para carregar novo código e modelo
```

### 5. Verificar Health Check
```bash
curl https://backend-ml-defasagem-fase-5.onrender.com/health/live
```

### 6. Testar API
```bash
curl -X POST https://backend-ml-defasagem-fase-5.onrender.com/api/v1/defasagem-risk-records \
  -H "Content-Type: application/json" \
  -d '{
    "defasagem": -1,
    "fase_ordem": 2,
    "idade": 12,
    "ano_ingresso": 2022,
    "ida": 7.8,
    "ieg": 8.2,
    "iaa": 6.5,
    "ips": 9.1,
    "ipv": 7.3,
    "inde": 8.0,
    "genero": "Feminino",
    "instituicao": "Privada - Programa de Apadrinhamento"
  }'
```

## Verificação Pós-Deploy

1. **Verificar domains endpoint**:
   ```bash
   curl https://backend-ml-defasagem-fase-5.onrender.com/api/v1/domains
   ```
   - Confirmar 12 campos
   - Confirmar rótulos corretos
   - Confirmar 6 categorias de `instituicao`

2. **Testar todas as categorias de `instituicao`**:
   - Pública
   - Privada
   - Privada - Programa de Apadrinhamento
   - Privada *Parcerias com Bolsa 100%
   - Privada - Pagamento por *Empresa Parceira
   - Concluiu o 3º EM

3. **Testar ranges de validação**:
   - `defasagem`: -4 a +2
   - `fase_ordem`: 0-8
   - `idade`: 7-26
   - `ano_ingresso`: 2016-2023

## Rollback (se necessário)

### Reverter Migrations
```bash
alembic downgrade 20260909_0004
```

### Reverter Código
```bash
git checkout <commit-anterior>
docker compose build
docker compose up -d
```

## Problemas Pendentes na Cloud (Identificados em 10/09/2026)

### Status Local vs Cloud
Todos os 4 problemas listados no documento `Divergencias_API_vs_Modelo (1).md` foram testados localmente e **funcionam corretamente**:

| Problema | Status Local | Status Cloud | Causa Provável |
|---|---|---|---|
| 1. `fase_ordem = 0` retorna 500 | ✅ 201 | ❌ 500 | Migration 0007 não aplicada |
| 2. 4 instituições retornam 500 | ✅ 201 (todas) | ❌ 500 | Migration 0007 não aplicada |
| 3. `pedra` no /domains | ✅ Ausente | ❌ Presente | Migration 0008 não aplicada |
| 4. `fase_ordem = 9` no /domains | ✅ Ausente | ❌ Presente | Migration 0008 não aplicada |

### Instruções Específicas para Cloud

#### 1. Aplicar Todas as Migrations (Crítico)
Execute todas as migrations pendentes (0007 e 0008):

```bash
# No ambiente de produção
alembic upgrade head
```

Verificar se as migrations foram aplicadas:
```bash
alembic current
# Deve mostrar: 20260909_0008
```

**Migration 0007** remove constraints antigos que causam IntegrityError para:
- `fase_ordem = 0`
- As 4 novas categorias de `instituicao`

**Migration 0008** limpa o domain catalog:
- Marca `pedra` como inactive (soft delete)
- Remove `fase_ordem = 9` (era duplicado de Fase 4)

#### 2. Verificar Constraints no Banco
Após aplicar a migration 0007, verificar se os constraints antigos foram removidos:

```sql
SELECT conname FROM pg_constraint 
WHERE conrelid = 'defasagem_risk_record'::regclass 
AND contype = 'c' 
ORDER BY conname;
```

NÃO deve aparecer:
- `ck_defasagem_record_defasagem`
- `ck_defasagem_record_fase_ordem`
- `ck_defasagem_record_idade`
- `ck_defasagem_record_ano_ingresso`
- `ck_defasagem_record_instituicao`

#### 3. Verificar Domains Endpoint
```bash
curl https://backend-ml-defasagem-fase-5.onrender.com/api/v1/domains
```

Deve mostrar:
- 12 campos (sem `pedra`)
- `fase_ordem` com opções 0-8 (sem 9)
- `instituicao` com 6 categorias

## Notas Importantes

- O modelo ML (`modelo_risco_defasagem.joblib`) foi treinado com 12 features (sem `pedra`)
- As categorias de `instituicao` no modelo incluem as 6 novas categorias
- O OneHotEncoder do modelo está configurado com `handle_unknown='ignore'`, então categorias desconhecidas não causam erro
- A migration 0007 é crítica para remover constraints conflitantes que causam IntegrityError
- A migration 0008 limpa o domain catalog (remove `pedra` e `fase_ordem=9`)
- **Todos os problemas na cloud são causados por migrations não aplicadas, não por código incorreto**
