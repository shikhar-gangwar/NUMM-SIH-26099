from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.db.session import get_db
from app.db.models import Material, Cpse, Classification, MatchRun, MaterialMatch, NationalMaterial, LegacyMapping
from app.api.deps import require_role
from app.api.schemas.governance import AnalyticsSummaryDTO, AnalyticsChartsDTO, ProcurementAnalyticsDTO, ConsolidationOpportunityDTO

router = APIRouter(tags=["Analytics & Governance Intelligence"])

@router.get("/analytics/summary", response_model=AnalyticsSummaryDTO)
@router.get("/governance/summary", response_model=AnalyticsSummaryDTO)
def get_analytics_summary(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns SQL-derived top-level KPI summary metrics for the governance dashboard.
    """
    total_mats = db.query(Material).filter_by(status="ACTIVE").count()
    cpse_cnt = db.query(Cpse).count()
    runs_cnt = db.query(MatchRun).count()
    potential_dups = db.query(MaterialMatch).filter(
        MaterialMatch.relationship.in_(["FUNCTIONALLY_EQUIVALENT", "NEAR_DUPLICATE", "EXACT_DUPLICATE"])
    ).count()
    review_q = db.query(MaterialMatch).filter_by(review_status="PROPOSED").count()
    appr_cnt = db.query(MaterialMatch).filter_by(review_status="APPROVED").count()
    rej_cnt = db.query(MaterialMatch).filter_by(review_status="REJECTED").count()
    nat_mats = db.query(NationalMaterial).filter_by(status="ACTIVE").count()
    leg_maps = db.query(LegacyMapping).filter_by(status="ACTIVE").count()
    
    # Provenance counts from real database
    public_cnt = db.query(Material).filter_by(status="ACTIVE", provenance="REAL_PUBLIC").count()
    golden_cnt = db.query(Material).filter_by(status="ACTIVE", provenance="CONTROLLED_GOLDEN_DEMO").count()
    synth_cnt = db.query(Material).filter(
        Material.status == "ACTIVE",
        Material.provenance.in_(["SYNTHETIC_DEMO", "SYNTHETIC"])
    ).count()

    return AnalyticsSummaryDTO(
        total_materials=total_mats,
        cpse_count=cpse_cnt,
        match_runs_count=runs_cnt,
        potential_duplicates=potential_dups,
        review_queue_count=review_q,
        approved_count=appr_cnt,
        rejected_count=rej_cnt,
        national_materials_count=nat_mats,
        legacy_mappings_count=leg_maps,
        public_records_count=public_cnt,
        controlled_demo_count=golden_cnt,
        synthetic_demo_count=synth_cnt
    )

@router.get("/analytics/charts", response_model=AnalyticsChartsDTO)
def get_analytics_charts(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns SQL-derived distribution charts for the governance dashboard.
    """
    # 1. Materials by CPSE (ordered descending)
    mats_cpse_rows = (
        db.query(Cpse.code, func.count(Material.id))
        .join(Material, Material.cpse_id == Cpse.id)
        .filter(Material.status == "ACTIVE")
        .group_by(Cpse.code)
        .order_by(func.count(Material.id).desc())
        .all()
    )
    mats_by_cpse = {code: cnt for code, cnt in mats_cpse_rows}

    # 2. Materials by Category (ordered descending)
    mats_cat_rows = (
        db.query(Classification.category_code, func.count(Classification.material_id))
        .filter_by(is_current=True)
        .group_by(Classification.category_code)
        .order_by(func.count(Classification.material_id).desc())
        .all()
    )
    mats_by_cat = {cat: cnt for cat, cnt in mats_cat_rows}

    # 3. Relationship distribution
    rel_rows = (
        db.query(MaterialMatch.relationship, func.count(MaterialMatch.id))
        .group_by(MaterialMatch.relationship)
        .order_by(func.count(MaterialMatch.id).desc())
        .all()
    )
    rel_dist = {rel: cnt for rel, cnt in rel_rows}

    # 4. Review status distribution
    rev_rows = (
        db.query(MaterialMatch.review_status, func.count(MaterialMatch.id))
        .group_by(MaterialMatch.review_status)
        .order_by(func.count(MaterialMatch.id).desc())
        .all()
    )
    rev_dist = {st: cnt for st, cnt in rev_rows}

    # 5. Confidence histogram
    matches = db.query(MaterialMatch.equivalence_confidence).all()
    conf_hist = {"0.0 - 0.5": 0, "0.5 - 0.7": 0, "0.7 - 0.9": 0, "0.9 - 1.0": 0}
    for (conf,) in matches:
        if conf < 0.5:
            conf_hist["0.0 - 0.5"] += 1
        elif conf < 0.7:
            conf_hist["0.5 - 0.7"] += 1
        elif conf < 0.9:
            conf_hist["0.7 - 0.9"] += 1
        else:
            conf_hist["0.9 - 1.0"] += 1

    # 6. Veto reasons breakdown
    veto_matches = db.query(MaterialMatch.veto).filter(MaterialMatch.veto != None).all()
    veto_reasons = {}
    for (v,) in veto_matches:
        if isinstance(v, dict) and v.get("applied"):
            gid = v.get("gate_id", "VETO_APPLIED")
            veto_reasons[gid] = veto_reasons.get(gid, 0) + 1

    # 7. Materials by Provenance
    prov_rows = (
        db.query(Material.provenance, func.count(Material.id))
        .filter(Material.status == "ACTIVE")
        .group_by(Material.provenance)
        .order_by(func.count(Material.id).desc())
        .all()
    )
    prov_dist = {p or "SYNTHETIC_DEMO": cnt for p, cnt in prov_rows}

    # 8. Mapping coverage calculation
    total_mats = db.query(Material).filter_by(status="ACTIVE").count()
    mapped_cnt = db.query(LegacyMapping.material_id).filter_by(status="ACTIVE").distinct().count()
    unmapped_cnt = total_mats - mapped_cnt
    coverage_pct = round((mapped_cnt / total_mats * 100.0), 2) if total_mats > 0 else 0.0

    mapping_cov = {
        "total_materials": total_mats,
        "mapped_materials": mapped_cnt,
        "unmapped_materials": unmapped_cnt,
        "coverage_pct": coverage_pct
    }

    return AnalyticsChartsDTO(
        materials_by_cpse=mats_by_cpse,
        materials_by_category=mats_by_cat,
        relationship_distribution=rel_dist,
        review_status_distribution=rev_dist,
        confidence_histogram=conf_hist,
        veto_reasons_breakdown=veto_reasons,
        materials_by_provenance=prov_dist,
        mapping_coverage=mapping_cov
    )

@router.get("/analytics/procurement", response_model=ProcurementAnalyticsDTO)
def get_procurement_analytics(
    db: Session = Depends(get_db),
    current_user = Depends(require_role(["VIEWER", "REVIEWER", "DATA_STEWARD", "SUPER_ADMIN"]))
):
    """
    Returns SQL-derived procurement consolidation intelligence.
    Identifies shared National Materials across CPSEs, mapping coverage, and potential procurement savings.
    """
    # Active materials total
    total_materials = db.query(Material).filter_by(status="ACTIVE").count()

    # Mapped materials count
    mapped_cnt = db.query(LegacyMapping.material_id).filter_by(status="ACTIVE").distinct().count()
    coverage_pct = round((mapped_cnt / total_materials * 100.0), 2) if total_materials > 0 else 0.0

    # Unresolved reviews - Single fast join query
    from sqlalchemy import and_
    unresolved_cat_rows = (
        db.query(Classification.category_code, func.count(MaterialMatch.id))
        .join(Classification, and_(Classification.material_id == MaterialMatch.material_a_id, Classification.is_current == True), isouter=True)
        .filter(MaterialMatch.review_status == "PROPOSED")
        .group_by(Classification.category_code)
        .all()
    )
    unresolved_cat_dist = {(cat or "UNCLASSIFIED"): cnt for cat, cnt in unresolved_cat_rows}
    unresolved_count = sum(unresolved_cat_dist.values())

    # Shared National Materials across CPSEs
    active_national = db.query(NationalMaterial).filter_by(status="ACTIVE").all()
    sharing_nmc_count = 0
    duplicate_materials_count = 0
    consolidation_opportunities = []

    for nat in active_national:
        legs = db.query(LegacyMapping).filter_by(national_material_uid=nat.uid, status="ACTIVE").all()
        mat_ids = [l.material_id for l in legs]
        if not mat_ids:
            continue

        cpses_for_nmc = db.query(Material.cpse_id).filter(Material.id.in_(mat_ids)).distinct().all()
        cpse_count = len(cpses_for_nmc)

        if cpse_count >= 2:
            sharing_nmc_count += 1
            duplicate_materials_count += len(mat_ids)

            # Calculate deterministic demonstration pricing based on spec_fingerprint hash
            hash_val = sum(ord(c) for c in nat.spec_fingerprint)
            base_price = float(50 + (hash_val % 450)) # e.g. $50 to $500
            min_price = round(base_price * 0.85, 2)
            max_price = round(base_price * 1.35, 2)
            avg_price = round((min_price + max_price) / 2.0, 2)
            est_savings = round((max_price - min_price) * len(mat_ids) * 12.0, 2)

            consolidation_opportunities.append(
                ConsolidationOpportunityDTO(
                    nmc=nat.nmc,
                    canonical_description=nat.canonical_description,
                    category_code=nat.category_code,
                    cpse_count=cpse_count,
                    mapped_materials_count=len(mat_ids),
                    min_unit_price=min_price,
                    max_unit_price=max_price,
                    avg_unit_price=avg_price,
                    estimated_annual_savings=est_savings,
                    demonstration_flag="Synthetic demonstration data"
                )
            )

    # Sort opportunities by estimated annual savings descending
    consolidation_opportunities.sort(key=lambda x: x.estimated_annual_savings, reverse=True)

    return ProcurementAnalyticsDTO(
        cpse_sharing_nmc_count=sharing_nmc_count,
        duplicate_materials_count=duplicate_materials_count,
        mapping_coverage_pct=coverage_pct,
        unresolved_review_count=unresolved_count,
        unresolved_review_concentration=unresolved_cat_dist,
        top_consolidation_opportunities=consolidation_opportunities[:10],
        demonstration_notes="All price variance and monetary savings metrics in this prototype are calculated from synthetic demonstration unit prices. Real-world material equivalence and legacy crosswalk mappings are 100% derived from exact SQL and technical attribute matching."
    )

