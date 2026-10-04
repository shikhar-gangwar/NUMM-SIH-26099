# National Unified Material Master Framework (SIH 2026 · PS 26099)

AI-Driven Standardization and Harmonization of Material Master Data Across CPSEs.

## Quick Start (Docker)

```bash
# 1. Copy environment template
cp .env.example .env

# 2. Build and launch services
make up

# 3. Access web interface
# Open http://localhost:3000 in your browser
```

## Available Commands

- `make up` - Build and start containers (`web`, `api`, `db`)
- `make down` - Stop and remove containers
- `make test` - Run backend unit & integration tests
- `make lint` - Run code quality linters
- `make seed-demo` - Load synthetic CPSE demo data
- `make eval` - Execute evaluation harness & trap suite

## SIH Demo Credentials

These credentials are for local SIH prototype demonstration only and must not be used in production.

### Super Administrator
- **Username:** `steward_admin`
- **Password:** `DevSec_D1I6hALEJYSYhoLsYpWwkPc0`
- **Role:** `SUPER_ADMIN`
- **Capabilities:** Full system control, data stewardship, manual review approval/rejection, ERP synchronization triggers, audit log inspection, batch execution.

### Reviewer
- **Username:** `reviewer_demo`
- **Password:** `NUMM-Demo-Reviewer-2026!`
- **Role:** `REVIEWER`
- **Capabilities:** Review queue inspection, technical evidence exploration, candidate approval/rejection, master data viewing. (Restricted from system admin operations).

## Documentation

- [ARCHITECT.md](ARCHITECT.md) - Architectural Source of Truth
- [VERSION.md](VERSION.md) - Model Landscape, Provider Interfaces & Living Version Roadmap
- [docs/PROGRESS.md](docs/PROGRESS.md) - Milestone Completion Tracker
- [docs/DEVIATIONS.md](docs/DEVIATIONS.md) - Recorded Architecture Deviations
- [docs/PRODUCT_AUDIT.md](docs/PRODUCT_AUDIT.md) - Comprehensive Quality & Verification Audit

## Data Source & Attribution

### SIH 26099 — CPSE Material Code Harmonisation Dataset

- **Hugging Face Repository:** [https://huggingface.co/datasets/Prasenjeet25/sih26099-cpse-material-codes](https://huggingface.co/datasets/Prasenjeet25/sih26099-cpse-material-codes)
- **Dataset Title:** SIH 26099 — Collected Dataset
- **License:** Creative Commons Attribution 4.0 International ([CC BY 4.0](https://creativecommons.org/licenses/by/4.0/))
- **Source Organizations:**
  - Oil India Limited (`OIL_INDIA`)
  - NTPC Limited (`NTPC`)
  - Indian Oil Corporation Limited (`IOCL`)
- **Corpus Size:** 21,513 industrial material descriptions across Pipes, Valves, Bolts/Fasteners, Bearings, Gaskets, Cables, and Equipment.
- **Reference Standards:** Material abbreviations, material grades, pressure classes, unit normalisation, and UNSPSC taxonomy mappings.

### Provenance & Access Disclaimer

- **Public Demonstration Data:** Publicly collected CPSE tender data and open-source industrial records are used exclusively for prototype demonstration, benchmarking, and cross-enterprise deduplication evaluation.
- **Controlled Demo Records:** Curated golden test scenarios (`CONTROLLED_GOLDEN_DEMO`) are included to demonstrate deterministic safety gates (such as G2 tensile property conflicts and G4 unstated metallurgy review triggers).
- **Confidentiality:** This prototype makes no claim of authorized or direct access to proprietary, classified, or confidential internal databases of participating CPSEs. Raw source descriptions and identifiers are maintained immutably with full lineage.

