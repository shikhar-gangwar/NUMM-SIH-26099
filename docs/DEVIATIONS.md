# DEVIATIONS.md — Architecture & Version Deviation Log

This file records any departure from `ARCHITECT.md` or `VERSION.md` along with its rationale and impact.

| ID | Date | Component | Proposed Deviation | Rationale | Impact | Approved By |
|---|---|---|---|---|---|---|
| — | 2026-10-02 | — | None | Initial architecture strictly followed. | None | System |
| ENV-01 | 2026-10-03 | Infrastructure / Docker | Remap host PostgreSQL port `5432` to `5433` | Host port 5432 was occupied by pre-existing unrelated container (`ecosphere-postgres`). Remapped host port to `5433:5432` to avoid deleting or stopping existing services. | Zero architectural impact. Internal Compose network container port remains `db:5432`. | User |

