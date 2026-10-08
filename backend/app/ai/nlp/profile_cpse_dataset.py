"""
CPSE Material Corpus Dataset Profiler
SIH 26099 Dataset Inspection Utility

Usage:
    python -m app.ai.nlp.profile_cpse_dataset
"""

import sys
from pathlib import Path
import pandas as pd


def locate_dataset_csv() -> Path | None:
    """Locate material_description_corpus.csv in standard project locations."""
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parents[2]  # backend -> project root

    candidate_paths = [
        project_root / "backend" / "data" / "real" / "material_description_corpus.csv",
        project_root / "data" / "real" / "material_description_corpus.csv",
        Path("backend/data/real/material_description_corpus.csv").resolve(),
        Path("data/real/material_description_corpus.csv").resolve(),
    ]

    for path in candidate_paths:
        if path.exists() and path.is_file():
            return path
    return None


def run_profile():
    csv_path = locate_dataset_csv()

    print("==================================================")
    print("SIH 26099 DATASET PROFILE")
    print("==================================================")
    print()

    if csv_path is None:
        print("[ERROR] Local dataset file not found.")
        print("Expected location: backend/data/real/material_description_corpus.csv")
        print("Profiling aborted.")
        return

    print("DATASET")
    print(f"File Path        : {csv_path}")
    print(f"File Size        : {csv_path.stat().st_size / (1024 * 1024):.2f} MB")
    
    # Load dataset with pandas
    df = pd.read_csv(csv_path, low_memory=False)

    total_rows = len(df)
    total_cols = len(df.columns)
    print(f"Total Rows       : {total_rows:,}")
    print(f"Total Columns    : {total_cols}")
    print()

    print("SCHEMA")
    print("Columns:")
    for idx, col in enumerate(df.columns, 1):
        print(f"  {idx:2d}. {col}")
    print()

    print("MISSING VALUES")
    null_counts = df.isnull().sum()
    for col, count in null_counts.items():
        pct = (count / total_rows) * 100
        print(f"  {col:<22}: {count:>6,} missing ({pct:>5.1f}%)")
    print()

    # Description Analysis
    desc_series: pd.Series = pd.Series(df['description'].fillna('').astype(str))
    desc_clean: pd.Series = desc_series.str.strip()
    
    empty_whitespace_count: int = (desc_clean == '').sum()
    valid_mask = (desc_clean != '').values
    valid_df: pd.DataFrame = pd.DataFrame(df.iloc[valid_mask].copy())
    valid_desc: pd.Series = pd.Series(valid_df['description'].fillna('').astype(str))

    unique_desc_count: int = valid_desc.nunique()
    duplicate_desc_count: int = len(valid_desc) - unique_desc_count
    uniqueness_pct: float = (unique_desc_count / len(valid_desc)) * 100 if len(valid_desc) > 0 else 0.0

    print("DUPLICATES")
    print(f"Total Non-Empty Descriptions: {len(valid_desc):,}")
    print(f"Unique Descriptions         : {unique_desc_count:,}")
    print(f"Duplicate Descriptions      : {duplicate_desc_count:,}")
    print(f"Uniqueness Percentage       : {uniqueness_pct:.2f}%")
    print(f"Empty/Whitespace Count      : {empty_whitespace_count:,}")
    print()

    print("ORGANIZATIONS")
    org_counts = df['organization'].fillna('UNSPECIFIED').value_counts()
    for org, cnt in org_counts.items():
        pct = (cnt / total_rows) * 100
        print(f"  {org:<35}: {cnt:>6,} rows ({pct:>5.1f}%)")

    print("\nUnique Descriptions per Organization:")
    org_unique = valid_df.groupby('organization')['description'].nunique()
    for org, cnt in org_unique.items():
        print(f"  {org:<35}: {cnt:>6,} unique descriptions")
    print()

    print("CROSS-ORGANISATION OVERLAP")
    desc_org_group = valid_df.groupby('description')['organization'].nunique()
    cross_org_desc_count: int = (desc_org_group > 1).sum()
    print(f"Descriptions appearing in >1 Organization: {cross_org_desc_count:,}")

    print()

    print("DESCRIPTION STATISTICS")
    desc_lengths: pd.Series = valid_desc.str.len()
    print(f"Min Length       : {desc_lengths.min():.0f} characters")
    print(f"Max Length       : {desc_lengths.max():.0f} characters")
    print(f"Mean Length      : {desc_lengths.mean():.2f} characters")
    print(f"Median Length    : {desc_lengths.median():.0f} characters")
    print(f"25th Percentile  : {desc_lengths.quantile(0.25):.0f} characters")
    print(f"75th Percentile  : {desc_lengths.quantile(0.75):.0f} characters")
    print()

    print("DESCRIPTION KIND DISTRIBUTION")
    kind_counts = df['description_kind'].fillna('UNSPECIFIED').value_counts()
    for kind, cnt in kind_counts.items():
        print(f"  {kind:<30}: {cnt:>6,}")
    print()

    print("SOURCE SYSTEM DISTRIBUTION")
    sys_counts = df['source_system'].fillna('UNSPECIFIED').value_counts()
    for s_sys, cnt in sys_counts.items():
        print(f"  {s_sys:<30}: {cnt:>6,}")
    print()

    print("ITEM TYPES (Top 20)")
    item_counts = df['item_type_hint'].fillna('UNSPECIFIED').value_counts().head(20)
    for item, cnt in item_counts.items():
        print(f"  {item:<30}: {cnt:>6,}")
    print()

    print("PRODUCT CATEGORIES (Top 20)")
    cat_counts = df['product_category'].fillna('UNSPECIFIED').value_counts().head(20)
    for cat, cnt in cat_counts.items():
        print(f"  {cat:<30}: {cnt:>6,}")
    print()

    print("UNITS (Top 20)")
    unit_counts = df['unit'].fillna('UNSPECIFIED').value_counts().head(20)
    for u, cnt in unit_counts.items():
        print(f"  {u:<30}: {cnt:>6,}")
    print()

    print("SOURCE SECTIONS (Top 20)")
    sec_counts = df['source_section'].fillna('UNSPECIFIED').value_counts().head(20)
    for sec, cnt in sec_counts.items():
        print(f"  {sec:<50}: {cnt:>6,}")
    print()

    print("TOP EXACT DUPLICATES (Top 20 Most Frequent)")
    grouped_desc = valid_df.groupby('description')
    dup_counts: pd.DataFrame = pd.DataFrame({
        'total_count': grouped_desc['corpus_id'].count(),
        'orgs': grouped_desc['organization'].apply(lambda x: ", ".join(sorted(set(x.dropna()))))
    }).sort_values(by='total_count', ascending=False)

    top_duplicates = dup_counts[dup_counts['total_count'] > 1].head(20)
    for idx, (desc, row) in enumerate(top_duplicates.iterrows(), 1):
        trunc_desc = str(desc) if len(str(desc)) <= 70 else str(desc)[:67] + "..."
        print(f"{idx:2d}. [{row['total_count']:>3d}x] ({row['orgs']})")
        print(f"    {trunc_desc}")
    print()

    print("CROSS-ORGANISATION EXAMPLES (Top 20 Cross-Org Exact Descriptions)")
    cross_org_df = dup_counts[dup_counts['orgs'].astype(str).str.contains(',')].head(20)
    if len(cross_org_df) == 0:
        print("  None found.")
    else:
        for idx, (desc, row) in enumerate(cross_org_df.iterrows(), 1):
            trunc_desc = str(desc) if len(str(desc)) <= 70 else str(desc)[:67] + "..."
            print(f"{idx:2d}. [{row['total_count']:>3d}x] Orgs: [{row['orgs']}]")
            print(f"    Description: {trunc_desc}")
    print()


if __name__ == "__main__":
    run_profile()

