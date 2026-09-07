# Defasagem Risk API

API Flask/PostgreSQL para consultar 13 dominios PEDE e cadastrar registros de
risco de defasagem escolar com **predicao automatica via Machine Learning**.

O cliente envia os 13 campos PEDE e a API prediz probabilidade, faixa de risco e
acao sugerida server-side antes de persistir o registro (16 campos no banco).

## Arquitetura ML

```
POST /api/v1/defasagem-risk-records (13 campos)
  │
  ├─ Validacao (schema 13 inputs PEDE)
  ├─ FeatureTransformer (13 inputs → 13 features)
  ├─ DefasagemRiskPredictor (model.predict_proba → probabilidade)
  └─ Persistencia (13 inputs + probabilidade, faixa_risco, acao_sugerida)
```

### Pipeline de inferencia (`app/ml/`)

| Modulo | Responsabilidade |
|--------|-----------------|
| `feature_transformer.py` | Transforma os 13 campos PEDE em DataFrame com 13 features |
| `model_loader.py` | Verifica integridade do artefato (SHA-256 + tamanho) e carrega o modelo |
| `predictor.py` | Orquestra transformacao + predicao + classificacao em faixas de risco |

### Artefato do modelo

- Arquivo: `artifacts/modelo_risco_defasagem.joblib`
- Manifesto: `artifacts/modelo_risco_defasagem.manifest.json` (SHA-256, features, faixas de risco)
- Verificacao: `python scripts/verify_model_artifact.py artifacts/modelo_risco_defasagem.manifest.json`
- Gerar/atualizar manifesto: `python scripts/generate_model_manifest.py artifacts/modelo_risco_defasagem.joblib`
  (extrai SHA-256, tamanho, algoritmo, features e versao do sklearn do modelo;
  reaproveita `version`, `class_map` e `provenance` do manifesto existente. Use
  `-` como destino para imprimir sem gravar. Sempre revise os campos marcados
  com `TODO` antes de commitar.)

> Trocou o `.joblib`? O `modelo_risco_defasagem.manifest.json` fixa o hash/tamanho do artefato,
> entao a API falha com `SHA-256 mismatch` ate o manifesto ser regenerado.
> Rode o gerador acima e confira se as `features` do novo modelo batem com as
> produzidas por `feature_transformer.py`.

### Faixas de risco

| Faixa | Probabilidade | Acao sugerida |
|-------|--------------|--------------|
| Baixo | 0.00 - 0.25 | Sem sinal de alerta |
| Medio | 0.25 - 0.50 | Monitorar no proximo ciclo |
| Alto | 0.50 - 1.00 | Prioridade de acompanhamento |

### Campos PEDE (13 indicadores)

| Campo | Tipo | Descricao |
|-------|------|----------|
| defasagem | numerico | Defasagem escolar (anos) |
| fase_ordem | inteiro | Fase de escolaridade (1-9) |
| idade | inteiro | Idade do aluno (6-18 anos) |
| ano_ingresso | inteiro | Ano de ingresso na escola |
| ida | numerico | Indicador de Desempenho Academico (0-10) |
| ieg | numerico | Indicador de Eficiencia Escolar (0-10) |
| iaa | numerico | Indicador de Aproveitamento Anual (0-10) |
| ips | numerico | Indicador de Progresso Escolar (0-10) |
| ipv | numerico | Indicador de Proficiencia em Portugues (0-10) |
| inde | numerico | Indicador de Desempenho Escolar (0-10) |
| genero | texto | Gênero (masculino/feminino) |
| instituicao | texto | Tipo de instituicao (publica/privada) |
| pedra | texto | Pedra (quartil_1/quartil_2/quartil_3/quartil_4) |

## Executar com Docker

Crie `.env` a partir de `.env.example`, substitua `change-me` por uma senha local
e mantenha a mesma credencial em `DATABASE_URL`. Depois execute:

```powershell
docker compose up --build
```

A API fica em `http://localhost:8000`, o Swagger em `/api/docs` e o documento
OpenAPI em `/api/openapi.json`. O PostgreSQL nao publica porta no host.

### Variaveis de ambiente ML

| Variavel | Default | Descricao |
|----------|---------|-----------|
| `ML_MODEL_PATH` | `artifacts/modelo_risco_defasagem.joblib` | Caminho do modelo serializado |
| `ML_MANIFEST_PATH` | `artifacts/modelo_risco_defasagem.manifest.json` | Caminho do manifesto de verificacao |

## Desenvolvimento

Requer Python >=3.12 e PostgreSQL. Com `APP_ENV` e `DATABASE_URL` configurados:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
.\.venv\Scripts\alembic.exe upgrade head
.\.venv\Scripts\python.exe -m seeds.domain_options
.\.venv\Scripts\python.exe -m pytest --cov=app
```

Qualidade:

```powershell
.\.venv\Scripts\python.exe -m ruff check app seeds migrations tests scripts
.\.venv\Scripts\python.exe -m ruff format --check app seeds migrations tests scripts
.\.venv\Scripts\python.exe -m mypy app seeds scripts
```

### Falha ao rodar o migrate localmente

Se o projeto nao rodar localmente e o `alembic upgrade head` (migrate) falhar,
suba manualmente o schema executando o script SQL em
`migrations/versions/script.sql` direto no banco de dados. Exemplo com `psql`:

```powershell
psql "$env:DATABASE_URL" -f migrations/versions/script.sql
```

## Rotas

- `GET /health/live` e `GET /health/ready`
- `GET /api/v1/domains` e `GET /api/v1/domains/{field_name}`
- `POST /api/v1/defasagem-risk-records` — aceita 13 campos PEDE, retorna 16 (com probabilidade, faixa_risco, acao_sugerida)
- `GET /api/v1/defasagem-risk-records` — lista todos os registros
- `GET /api/v1/defasagem-risk-records/{id}`

### Contrato POST /api/v1/defasagem-risk-records

**Request (13 campos PEDE):**

```json
{
  "defasagem": 1.5,
  "fase_ordem": 3,
  "idade": 10,
  "ano_ingresso": 2020,
  "ida": 7.8,
  "ieg": 8.2,
  "iaa": 6.5,
  "ips": 9.1,
  "ipv": 7.3,
  "inde": 8.0,
  "genero": "masculino",
  "instituicao": "publica",
  "pedra": "quartil_1"
}
```

**Response (16 campos — probabilidade, faixa_risco, acao_sugerida calculados pelo modelo):**

```json
{
  "id": "uuid",
  "created_at": "2026-09-04T18:00:00Z",
  "defasagem": 1.5,
  "fase_ordem": 3,
  "idade": 10,
  "ano_ingresso": 2020,
  "ida": 7.8,
  "ieg": 8.2,
  "iaa": 6.5,
  "ips": 9.1,
  "ipv": 7.3,
  "inde": 8.0,
  "genero": "masculino",
  "instituicao": "publica",
  "pedra": "quartil_1",
  "probabilidade": 0.35,
  "faixa_risco": "Medio",
  "acao_sugerida": "Monitorar no proximo ciclo"
}
```

> Se o campo `probabilidade`, `faixa_risco` ou `acao_sugerida` for enviado no payload, a API retorna `422 unknown_field`.

Erros usam `application/problem+json`. Toda resposta inclui `X-Request-ID`.
Payloads e campos de saude nao sao registrados nos logs.

## Limites de uso

Esta versao e local/academica. Exposicao publica esta bloqueada ate definir
autenticacao, autorizacao, consentimento, retencao, descarte, TLS, CORS, backup
e politica de acesso a respostas por UUID.
