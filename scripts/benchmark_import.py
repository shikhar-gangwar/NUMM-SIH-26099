import sys
import time
import pandas as pd
sys.path.insert(0, 'backend')
from app.normalization.text import normalize_text
from app.normalization.uom import normalize_uom
from app.extraction.extractor import detect_category, extract_attributes

df = pd.read_csv('data/real/material_description_corpus.csv', nrows=500)
t0 = time.time()
for _, r in df.iterrows():
    uom, dim, _ = normalize_uom(str(r['unit']) if pd.notna(r['unit']) else 'EA')
    norm = normalize_text(str(r['description']))
    hint = str(r['item_type_hint']) if pd.notna(r['item_type_hint']) else None
    cat = detect_category(norm.text, hint=hint)
    attrs = extract_attributes(norm.text, cat)
dur = time.time() - t0
print(f"500 rows processed in {dur:.2f}s ({500/dur:.1f} rows/s)")
