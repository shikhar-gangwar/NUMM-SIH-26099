# PROGRESS.md — Milestone Completion Tracker

## Status Summary

- [x] **M0: Scaffold** (Completed: 2026-10-02)
- [x] **M1: Schema, Config, Providers, Auth, Audit** (Completed: 2026-10-02)
- [ ] **M2: Ingestion, Normalisation, Extraction** (Next)
- [ ] **M3: Synthetic Data & Evaluation**
- [ ] **M3: Synthetic Data & Evaluation**
- [ ] **M4: Classification & Matching Engine**
- [ ] **M5: Review, National Material, Legacy**
- [ ] **M6: Analytics, Procurement, Audit APIs, Exports**
- [ ] **M7: Frontend (10 screens)**
- [ ] **M8: Mock SAP Integration**
- [ ] **M9: Hardening & Demo Release**

---

## Self-Review Checklist

- [ ] Every PS capability (§2) reachable in the UI or API.
- [ ] Trap suite 100%; unsafe auto-accepts 0.
- [ ] Source immutability and audit immutability proven by tests.
- [ ] No hard-coded KPIs or demo outcomes (`T-ANA-01`).
- [ ] App works with `LLM_PROVIDER=none` and offline.
- [ ] MOCK vs PRODUCTION integration clearly separated.
- [ ] No secrets or default passwords committed.
- [ ] `make test eval e2e` all pass on a fresh clone.
