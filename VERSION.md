# VERSION.md — Model, Agent & Versioning Strategy

**Project:** SIH 2026 PS 26099 — National Unified Material Master Framework
**Companion file:** `ARCHITECT.md` (source of truth for architecture; this file is source of truth for models/versions)
**Written:** 2 Oct 2026. Model landscape moves fast. Every row below has a **Verification** tag:

- `VERIFIED-2026` = confirmed from a public source during the research pass for this document.
- `VERIFY-BEFORE-PIN` = believed correct but must be checked on the official model card / vendor console before pinning in `models.lock.yaml`.

> Rule: **newest ≠ best.** Material descriptions are short, code-heavy strings ("BOLT HEX M10X50 SS304 GR 8.8"). Embeddings only supply *recall*. Structured attributes and rules supply *precision*. A bigger embedding model will not fix a missing conflict rule, so P0 picks small, fast, offline-capable models.

---

## 1. Development Agent Strategy (Google Antigravity)

The coding agent is a **build-time tool only**. It is never part of the running application. The runtime AI stack (section 2) must work with the coding agent switched off.

| Topic | Decision |
|---|---|
| Agent role | Autonomous implementer of `ARCHITECT.md`. Writes code, tests, Docker files, seed scripts. Does not make architecture decisions. |
| Model choice inside Antigravity | Select the strongest reasoning/coding model offered in Antigravity's model picker on the day. Do not hard-code a name here. Antigravity's available model list changes, so check it in-app. `VERIFY-BEFORE-PIN` |
| Working mode | Use **planning-first** mode for the initial task list and implementation plan (review them against `ARCHITECT.md` §44 before approving). Use faster modes for mechanical work (CRUD routes, UI tables, fixtures). |
| Parallelism | Use separate agents/threads only where module boundaries are clean: (A) backend core + DB, (B) matching engine + category packs, (C) frontend, (D) synthetic data + eval harness. Merge points are the API contract and the DB schema. Do **not** parallelise before M1 (schema + contracts) is merged. |
| Source of truth | `ARCHITECT.md` wins over any agent suggestion. If the agent proposes a deviation, it must be written to `docs/DEVIATIONS.md` with a reason. |
| Guardrails to give the agent | (1) No hard-coded demo results. (2) No semantic-only equivalence path. (3) Never UPDATE/DELETE `material.source_code` or raw description. (4) Never let an LLM produce an identifier. (5) All dashboard numbers from SQL. (6) Run `make test` after each milestone and paste results into `docs/PROGRESS.md`. |
| Verification loop | Agent must run the **trap suite** (`tests/matching/test_traps.py`) at M4 and at every later milestone. A red trap suite blocks the milestone. |
| Secrets | Agent never sees real API keys. `.env.example` only. Real keys stay in your local `.env` (git-ignored). |

---

## 2. Runtime AI Strategy

### 2.1 Summary table

| Role | P0 default | P1 upgrade | Fallback (always available) | Where it runs |
|---|---|---|---|---|
| Deterministic parsing | regex + unit registry + abbreviation dictionaries (in repo) | add `standard_equivalence.yaml` growth | n/a (this *is* the fallback) | in-process, CPU |
| Lexical similarity | RapidFuzz (token-set / WRatio) + char n-gram TF-IDF (scikit-learn) | PostgreSQL `pg_trgm` as pre-filter | n/a | in-process / Postgres |
| Embedding | `sentence-transformers/all-MiniLM-L6-v2` | `BAAI/bge-m3` | TF-IDF char-ngram vectors (scikit-learn) if no model weights are available | local CPU (GPU optional) |
| Reranker | **off in P0** | `BAAI/bge-reranker-v2-m3` cross-encoder | skip stage, keep first-stage order | local CPU/GPU |
| LLM | **off in P0** (`LLM_PROVIDER=none`); templated explanations | local open model via Ollama, or cloud API (Anthropic) | `none` (rule-based extraction + templated explanation) | local first; cloud optional |
| Classifier (category) | keyword/regex rules + TF-IDF + LogisticRegression (scikit-learn) | embedding-kNN on reviewer-confirmed data | rules only | in-process |
| Confidence calibration | fixed prior weights (config) | logistic regression fitted on reviewer labels | priors | in-process |

### 2.2 Embedding model

| Candidate | Facts | Role | Verification |
|---|---|---|---|
| **all-MiniLM-L6-v2** (P0 default) | ~22M params, 384-d, English-centric, very fast on CPU, small download. | Recall engine for blocked candidates. Good enough because attribute rules do the precision work. | `VERIFIED-2026` (widely cited as the fastest CPU-friendly option in 2026 roundups) |
| **BAAI/bge-m3** (P1 default) | ~568M params, 1024-d, 8,192-token input, MIT license, 100+ languages, produces dense + sparse + ColBERT-style outputs. | Better multilingual/Hinglish robustness. Can supply a sparse signal for hybrid search later. | `VERIFIED-2026` |
| **Qwen3-Embedding-0.6B / 4B / 8B** | Apache 2.0, up to 32K context, flexible output dims, **requires an instruction prefix on the query side**. Published MMTEB average for 0.6B (64.33) is above BGE-M3 (59.56) on the model card comparison (values as of May 2025 card). | Alternate if bge-m3 underperforms on your eval. 8B needs a real GPU. | `VERIFIED-2026` (numbers are vendor-card values, not our benchmark) |
| **EmbeddingGemma-300m** | 300M params, 768-d (Matryoshka down to 128), 2,048-token context, task prefixes required, Gemma license terms. | Alternate small multilingual model. Check license fit for government deployment. | `VERIFIED-2026` |
| Hosted APIs (OpenAI/Gemini/Voyage) | Strong quality but send CPSE data outside the boundary. | **Not used** in P0. P2 only if data-sovereignty rules allow. | n/a |

**Why not just use the biggest one?** (1) Offline demo reliability matters more than a few benchmark points. (2) General MTEB scores say little about "M10 vs M12 bolt". (3) Download size and CPU latency hurt a one-day sprint. (4) Switching later is cheap because of section 3 and section 6.

**Decision rule for upgrading P0 → P1 embedding:** run the eval harness (`ARCHITECT.md` §36) on the adjudicated pair set with each model. Switch only if recall@K of true equivalents (K = candidate cap) improves **and** false-positive rate after the full pipeline does not worsen.

**Operational notes**
- Pre-download weights into a Docker volume (`HF_HOME=/models`) *before* the demo. Do not rely on venue Wi-Fi. A previous public SIH 26099 repo explicitly documented a TF-IDF fallback for this exact reason; we keep that idea and make it a first-class `EmbeddingProvider`.
- Normalise vectors (`normalize_embeddings=True`) and use cosine distance.
- Store embeddings with `model_version_id` (section 4). Never mix vectors from different models in one index.

### 2.3 Vector storage (pgvector)

- Require pgvector **≥ 0.8.2**. A buffer-overflow fix for parallel HNSW builds (CVE-2026-3172) shipped in 0.8.2 per a secondary source. Pin the exact patch version in `docker-compose.yml` after checking the official releases page; secondary sources disagreed on the latest 0.8.x number (0.8.3 vs 0.8.6). `VERIFY-BEFORE-PIN`
- `vector` HNSW index limit is 2,000 dims; `halfvec` allows up to 4,000. 384-d and 1024-d fit plain `vector`. Use `halfvec` only if you move to a larger model.
- Iterative index scans (`hnsw.iterative_scan`, available since 0.8) matter because we filter by category/status. Enable `relaxed_order` for filtered queries. `VERIFIED-2026`
- P0 data volume (a few thousand rows) does not need an ANN index at all. Create the HNSW index anyway so the production path is exercised, but always compare against exact search in tests.

### 2.4 Reranker

- **P1:** `BAAI/bge-reranker-v2-m3` (cross-encoder, multilingual). `VERIFY-BEFORE-PIN`
- Alternate: a small English MS-MARCO cross-encoder (e.g. `cross-encoder/ms-marco-MiniLM-L-6-v2`) for CPU-only boxes. `VERIFY-BEFORE-PIN`
- **Hard rule:** reranker output is *one feature* in the confidence engine. It can reorder candidates. It can never override a critical-attribute veto. Generic rerankers are trained for query-passage relevance, not engineering equivalence, so they will rate "Gr 8.8" and "Gr 10.9" as extremely relevant to each other.
- Cost: reranking K=20 pairs per material at ~tens of ms/pair on CPU is acceptable offline but slow interactively. Run only for pairs that survive gates (veto-failed pairs are skipped).

### 2.5 LLM

The LLM is an **assistant**, never the equivalence judge.

| Allowed use | Output validated by | Default |
|---|---|---|
| Difficult attribute extraction (free-text with no regex hit) | Pydantic schema + category pack allowed-values + unit parser. Extracted values are tagged `source=LLM` and treated as lower-trust (cannot establish MATCH on a critical attribute without reviewer confirmation). | off |
| Canonical description drafting | Must be re-derivable from structured attributes. Final canonical description is built **deterministically** from attributes; LLM text is only an optional alternate suggestion. | off |
| Category classification assist | Must output a category id from the registry. Unknown → `UNCLASSIFIED`. | off |
| Reviewer assistance / explanation | Reads the evidence ledger only. Must not introduce facts not in evidence. | templated text; LLM paraphrase optional |

Forbidden: LLM-issued National Material Codes, LLM deciding relationship type, LLM overriding a veto, LLM-only matching.

| Provider option | Model id | Role | Local/Cloud | Notes | Verification |
|---|---|---|---|---|---|
| `none` (P0 default) | — | deterministic everything | local | Demo-safe. | n/a |
| `ollama` | configurable `LLM_MODEL` (an instruction-tuned open model you have already pulled) | extraction + explanation, data stays on box | local | Needs ~8 GB RAM for 7–8B-class quantised models; slower on CPU. Do not make a specific tag mandatory. | `VERIFY-BEFORE-PIN` |
| `anthropic` | `claude-haiku-4-5-20251001` | cheap, fast extraction/classification assist | cloud | Use only with non-sensitive or approved data. | `VERIFIED-2026` (id from Anthropic's published model list) |
| `anthropic` | `claude-sonnet-5-5` | higher-quality explanations / hard extraction | cloud | Costlier; use for reviewer-assist on demand, not bulk. | `VERIFIED-2026` |
| `openai_compatible` | configurable | any OpenAI-compatible endpoint (vLLM, LM Studio, gateway) | either | Makes provider swap a config change. | n/a |

Data-sovereignty note: CPSE procurement data is sensitive. Default posture is **local-first, cloud-optional, cloud-off by default**. The UI shows a visible "LLM: OFF / LOCAL / CLOUD" badge.

### 2.6 Deterministic NLP stack

| Tool | Use |
|---|---|
| Python `re` + curated regex library per attribute | size/grade/standard/thread/rating extraction |
| Abbreviation dictionary (`abbreviations.yaml`) | `SS`→STAINLESS STEEL, `CS`→CARBON STEEL, `GR`→GRADE, `HEX`→HEXAGON, `BRG`→BEARING, `VLV`→VALVE … |
| Unit registry (`units.py`, own small table) | length/pressure/temperature/mass conversions, inch/mm, NB/DN, bar/psi/MPa |
| RapidFuzz | token-set ratio, partial ratio, Jaro-Winkler for typos |
| scikit-learn | TF-IDF, LogisticRegression, metrics (precision/recall/F1), optional calibration |
| Pandas | import, validation, bulk transforms |

---

## 3. Model Abstraction

All AI-ish capabilities sit behind **provider interfaces** defined in `backend/app/ai/providers/base.py`. Application code imports only the interfaces and a factory.

```
EmbeddingProvider
  - name, version, dimension, max_input_tokens
  - embed_documents(texts: list[str]) -> list[list[float]]
  - embed_query(text: str) -> list[float]
  - fingerprint() -> ModelFingerprint

RerankerProvider
  - name, version
  - score_pairs(pairs: list[tuple[str,str]]) -> list[float]
  - fingerprint() -> ModelFingerprint

LLMProvider
  - name, version
  - complete_json(task: str, input: dict, schema: JSONSchema, temperature=0) -> LLMResult
  - fingerprint() -> ModelFingerprint

LLMResult = { output: dict, raw_text: str, prompt_hash: str, tokens_in, tokens_out, latency_ms }

ModelFingerprint = { provider, model_id, model_version, revision_or_digest, dimension?, params_hash }
```

Rules:
1. Factory reads `EMBEDDING_PROVIDER`, `RERANKER_PROVIDER`, `LLM_PROVIDER` from env and returns an implementation. Unknown → startup error (fail fast).
2. Every provider returns a `ModelFingerprint`. On first use it is upserted into `model_version` (table in `ARCHITECT.md` §27) and the row id is stored on everything the provider produces.
3. Providers must be **pure with respect to the DB**. They do not read or write tables.
4. LLM calls use `temperature=0`, JSON-schema-constrained output, and a `prompt_template_id` + `prompt_hash` stored with the result. Prompts live in `backend/app/ai/prompts/*.md` with a version header.
5. Every provider has a `FakeProvider` for tests (deterministic hash-based vectors, canned LLM JSON). Unit tests never download models.
6. A provider failure never fails the pipeline. The stage records `degraded=true` with the reason, uses the fallback, and the evidence ledger shows it.

Implementations to build in P0: `SentenceTransformersEmbedding`, `TfidfEmbedding` (fallback), `FakeEmbedding`, `NoneLLM`, `FakeLLM`.
P1: `BgeM3Embedding`, `CrossEncoderReranker`, `OllamaLLM`, `AnthropicLLM`, `OpenAICompatibleLLM`.

---

## 4. Versioning — what every AI decision records

Every machine-produced artefact stores a pointer to the exact versions that produced it.

### 4.1 `model_version` table (registry)

| Field | Meaning |
|---|---|
| `id` | UUID PK |
| `kind` | `EMBEDDING` \| `RERANKER` \| `LLM` \| `CLASSIFIER` \| `RULESET` \| `CATEGORY_PACK` \| `SCORING_CONFIG` |
| `provider` | e.g. `sentence-transformers`, `ollama`, `anthropic`, `internal` |
| `model_id` | e.g. `sentence-transformers/all-MiniLM-L6-v2` |
| `model_version` | provider's version tag or HF revision/commit hash |
| `dimension` | for embeddings |
| `params_hash` | hash of inference params (temperature, prompt template hash, normalisation flag) |
| `config_hash` | for `RULESET` / `SCORING_CONFIG` / `CATEGORY_PACK`: sha256 of the canonical file content |
| `registered_at` | timestamp |
| `status` | `ACTIVE` \| `DEPRECATED` \| `RETIRED` |

### 4.2 Fields stamped on decisions

Each `MatchEvidence` / `MaterialMatch` / `Classification` / `Attribute extraction` row stores:

```
model              (provider/model_id, human-readable)
model_version      (FK model_version.id for the LLM/classifier if used, else null)
embedding_model    (human-readable)
embedding_version  (FK model_version.id)
reranker_version   (FK, nullable)
ruleset_version    (FK, RULESET: normalisation + comparators code version)
category_pack_version (FK, CATEGORY_PACK config_hash)
scoring_config_version (FK, SCORING_CONFIG config_hash)
prompt_template_id + prompt_hash   (only if LLM used)
input_hash         (sha256 of canonical input payload)
timestamp          (UTC)
degraded           (bool) + degraded_reason
```

This satisfies: *model, model_version, embedding_model, embedding_version, timestamp* plus the extra items needed to reproduce a decision.

### 4.3 Code/software versions

- App version = git tag, exposed at `GET /api/meta/version` with the active `model_version` ids.
- `models.lock.yaml` (committed) lists the pinned provider ids and revisions. CI fails if running fingerprints differ from the lock unless `ALLOW_MODEL_DRIFT=true`.

---

## 5. Environment Variables

Everything that selects a model/provider or its endpoint is an environment variable. Nothing model-specific is hard-coded.

```
# --- Embeddings ---
EMBEDDING_PROVIDER=sentence_transformers   # sentence_transformers | tfidf | fake
EMBEDDING_MODEL=sentence-transformers/all-MiniLM-L6-v2
EMBEDDING_DIM=384
EMBEDDING_BATCH_SIZE=64
EMBEDDING_DEVICE=cpu                       # cpu | cuda
EMBEDDING_QUERY_PREFIX=                    # needed by some models (Qwen3, Gemma)
EMBEDDING_DOC_PREFIX=
HF_HOME=/models                            # model cache volume
HF_HUB_OFFLINE=1                           # set after pre-download

# --- Reranker ---
RERANKER_PROVIDER=none                     # none | cross_encoder
RERANKER_MODEL=BAAI/bge-reranker-v2-m3
RERANKER_TOP_N=20

# --- LLM ---
LLM_PROVIDER=none                          # none | ollama | anthropic | openai_compatible | fake
LLM_MODEL=
LLM_BASE_URL=                              # ollama / openai-compatible endpoint
LLM_API_KEY=                               # never committed; empty for none/ollama
LLM_TIMEOUT_S=30
LLM_MAX_RETRIES=1
LLM_ALLOWED_TASKS=extract,explain          # whitelist; "classify" optional
LLM_SEND_RAW_DATA=false                    # if false, only redacted/normalised text is sent

# --- Matching config ---
MATCH_CONFIG_PATH=/app/config/scoring.yaml
CATEGORY_PACKS_DIR=/app/config/category_packs
ABBREVIATIONS_PATH=/app/config/abbreviations.yaml
STANDARD_EQUIV_PATH=/app/config/standard_equivalence.yaml
CANDIDATE_CAP=20
AUTO_ACCEPT_ENABLED=true

# --- Infra / security ---
DATABASE_URL=postgresql+psycopg://...
JWT_SECRET=                                # required, no default
JWT_ACCESS_TTL_MIN=30
SEED_ADMIN_PASSWORD=                       # required for seed script
CORS_ORIGINS=http://localhost:3000
MAX_UPLOAD_MB=20
SAP_ADAPTER=mock                           # mock | s4_odata (P2)
```

`.env.example` is committed with empty secrets. Startup validates required vars and prints the active provider/model summary (no secrets) to logs.

---

## 6. Upgrade Strategy (changing models without invalidating history)

Principles: **decisions are immutable facts about a moment in time**; model upgrades create *new* facts, they do not rewrite old ones.

### 6.1 Embedding model upgrade (e.g. MiniLM → BGE-M3)

1. Register new `model_version` row (status `ACTIVE_CANDIDATE`).
2. Create new embedding storage for the new dimension (new column or table `material_embedding_<id>` with its own HNSW index). Old vectors stay.
3. Backfill embeddings in batches (resumable job, progress in `job_run`).
4. **Shadow run:** execute a `MatchRun` with `mode=SHADOW` using the new model. Results go to `material_match` with `run_id` marked shadow; they are not shown in the review queue.
5. Compare in the eval harness (§36): recall@K on true equivalents, false-positive count after the full pipeline, disagreement list. Reviewers can spot-check the disagreements.
6. If accepted: set `ACTIVE_EMBEDDING_MODEL_ID` (config row, audited). New runs use it. Old vectors can be dropped later; old `material_match` rows keep their original `embedding_version` and are never edited.
7. Rollback = flip the active id back (old vectors still present until retired).

### 6.2 LLM / reranker upgrade

Same shadow-run pattern. Because the LLM only assists extraction/explanation, a change affects only rows tagged `source=LLM`. Re-extraction creates a **new attribute version** (`material_attribute.version`+1, `supersedes_id`). The previous version remains.

### 6.3 Rules / category pack / scoring config upgrade

- Files are content-hashed into `model_version` (`RULESET`, `CATEGORY_PACK`, `SCORING_CONFIG`).
- Changing a threshold or critical-attribute list = new hash = new version row.
- Re-evaluation of existing pairs is **opt-in**: "Re-run with ruleset vX" creates new `material_match` rows linked to the old via `supersedes_match_id`. The reviewer UI shows both and flags changed verdicts.

### 6.4 What happens to already-approved decisions

- A human approval is a human fact. It is **never** auto-revoked by a model upgrade.
- If a newer ruleset would have vetoed an already-approved link, the system raises a `REVALIDATION_FLAG` (visible in Review Queue and Governance dashboard). A Data Steward decides. The audit trail records both the original approval and the revalidation outcome.

### 6.5 Release checklist for any model/ruleset change

1. Update `models.lock.yaml`.
2. Run unit + trap suite with `Fake*` providers.
3. Run eval harness with real providers on the adjudicated set; attach the metrics JSON to the PR.
4. Shadow run on current data; review disagreements.
5. Flip active version (audited action, requires `DATA_STEWARD` or higher).
6. Keep previous version `DEPRECATED` (not deleted) for at least one review cycle.

---

## 7. Honest limitations of this document

- Model facts were gathered from public pages in a single research session. Vendor-card benchmark numbers (e.g. MMTEB) are not our measurements. Our own measurements come only from the eval harness on the synthetic + adjudicated sets.
- Reranker ids and the Ollama model tag are marked `VERIFY-BEFORE-PIN` and must be checked on the official model card before they go into `models.lock.yaml`.
- Antigravity's current model list and feature set were not inspected; confirm in-app.
- Nothing here is a performance claim for the final system. Report only numbers produced by `make eval`.

---

## 8. Implementation Roadmap & Version History

### 8.1 Summary Roadmap Matrix

| Version | Milestone | Status | Target Capabilities |
|---|---|---|---|
| `v0.1` | M0 Scaffold | Implemented | Repo scaffold, Docker Compose (web/api/db), Makefile, `/health`, Next.js app |
| `v0.2` | M1 Foundation | Implemented | DB schema (19 entities), triggers, config loader, AI providers, JWT auth/RBAC, audit chain, OpenAPI DTOs |
| `v0.3` | M2 Ingestion & Normalization | Planned | Ingestion pipeline, validation, UOM/text normaliser, 6 category packs, attribute persistence |
| `v0.4` | M3 Synthetic Data & Evaluation | Planned | Synthetic data generator, trap pairs, eval metrics framework |
| `v0.5` | M4 Classification & Matching Engine | Planned | Category classifier, blocking, pgvector, lexical, veto lattice, confidence engine, job runner |
| `v0.6` | M5 Review, National Material & Legacy Mapping | Planned | Review state machine, claim/decision API, NMC generator, spec-fingerprint guard, legacy mapping |
| `v0.7` | M6 Analytics, Procurement, Audit & Export | Planned | SQL analytics, procurement aggregation, crosswalk CSV export, audit verification |
| `v0.8` | M7 Frontend | Planned | 10 Next.js screens, review detail with verdict chips/veto banner, analytics dashboard |
| `v0.9` | M8 Mock SAP Integration | Planned | `ERPAdapter`, `MockSapAdapter`, 40-char limit enforcement, mock SAP material store |
| `v1.0` | M9 Hardening & SIH Demo Release | Planned | Seed/demo scripts, offline testing, production documentation, full verification |

---

### 8.2 Version History Details

#### Version v0.1 — M0 Scaffold
- **Status:** Implemented
- **Milestone Completed:** M0 Scaffold
- **Implementation Date:** 2026-10-02
- **Major Capabilities Added:** Project scaffold, Docker Compose setup (`web`, `api`, `db` containers), Makefile, `.env.example`, `models.lock.yaml`, `/health` & `/ready` endpoints, Next.js scaffold.
- **Model/Provider Versions Used:** N/A (Scaffold phase)
- **Configuration/Ruleset Hashes:** N/A
- **Database/Schema Changes:** Docker container database creation (`pgvector/pgvector:pg16`).
- **API Contract Changes:** `GET /health`, `GET /ready`.
- **Test/Evaluation Status:** Health check operational.
- **Known Limitations:** Basic scaffold only.
- **Architectural Deviations:** None.

#### Version v0.2 — M1 Foundation
- **Status:** Implemented
- **Milestone Completed:** M1 Foundation
- **Implementation Date:** 2026-10-02
- **Major Capabilities Added:** 19 SQLAlchemy ORM entities, PostgreSQL immutability & audit triggers DDL (`triggers.sql`), config loader with SHA256 hashing (`config_loader`), AI provider interface layer (`SentenceTransformers`, `TfidfEmbedding`, `FakeEmbedding`, `NoneLLM`), JWT HS256 auth & Argon2 password hashing, RBAC middleware (`require_role`), SHA-256 hash-chained Audit service & verification, frozen Pydantic OpenAPI DTOs.
- **Model/Provider Versions Used:** `SentenceTransformersEmbedding` (`sentence-transformers/all-MiniLM-L6-v2`, 384-d), `TfidfEmbedding` fallback, `NoneLLM` (`LLM_PROVIDER=none`).
- **Configuration/Ruleset Hashes:** `scoring.yaml` (sha256 registered), `category_packs/*.yaml` (6 packs registered).
- **Database/Schema Changes:** 19 core tables (`cpse`, `app_user`, `import_batch`, `material`, `category`, `classification`, `material_attribute`, `material_embedding`, `match_run`, `material_match`, `match_evidence`, `national_material`, `national_material_version`, `nmc_counter`, `legacy_mapping`, `review`, `procurement_record`, `audit_event`, `model_version`), PostgreSQL triggers on `material` and `audit_event`, partial unique indexes.
- **API Contract Changes:** `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `GET /api/v1/meta/version`, `GET /api/v1/audit`, `GET /api/v1/audit/verify`.
- **Test/Evaluation Status:** Unit tests passing (`test_config_loader.py`, `test_providers.py`, `test_hash_chain.py`, `test_health.py`, `test_auth.py`).
- **Known Limitations:** Ingestion and matching engines built in M2–M4.
- **Architectural Deviations:** None.


---

### 8.3 Future Versions (Planned Roadmap)

- **v0.2 — M1 Foundation:** Planned schema (19 entities), immutability triggers, config loader, provider interface layer (`SentenceTransformers`, `TF-IDF`, `Fake`, `NoneLLM`), JWT Auth & RBAC, hash-chained Audit service.
- **v0.3 — M2 Ingestion & Normalization:** Planned file upload validation, normalisation engine, 6 category packs, attribute extraction rules.
- **v0.4 — M3 Synthetic Data & Evaluation:** Planned deterministic synthetic dataset generator, eval metrics suite.
- **v0.5 — M4 Classification & Matching Engine:** Planned blocking, vector retrieval, lexical matching, attribute comparators, veto lattice, confidence engine, background worker.
- **v0.6 — M5 Review, National Material & Legacy Mapping:** Planned review workflow, NMC generator with ISO 7064 check digit, spec-fingerprint guard, legacy mapping history.
- **v0.7 — M6 Analytics, Procurement, Audit & Export:** Planned SQL-based analytics endpoints, procurement aggregation, crosswalk exporter, audit verifier.
- **v0.8 — M7 Frontend:** Planned 10 Next.js screens with rich UI/UX, verdict chips, veto banners, Recharts.
- **v0.9 — M8 Mock SAP Integration:** Planned `MockSapAdapter` with 40-char limit enforcement and SAP product sync.
- **v1.0 — M9 Hardening & SIH Demo Release:** Planned seed scripts, offline capability verification, final test suite green.

