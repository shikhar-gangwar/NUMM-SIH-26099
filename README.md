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

## Documentation

- [ARCHITECT.md](ARCHITECT.md) - Architectural Source of Truth
- [VERSION.md](VERSION.md) - Model Landscape, Provider Interfaces & Living Version Roadmap
- [docs/PROGRESS.md](docs/PROGRESS.md) - Milestone Completion Tracker
- [docs/DEVIATIONS.md](docs/DEVIATIONS.md) - Recorded Architecture Deviations
