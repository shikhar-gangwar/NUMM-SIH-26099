'use client';

import React, { useEffect, useState } from 'react';
import { useParams, useRouter } from 'next/navigation';
import Link from 'next/link';
import { useAuth } from '../../context/AuthContext';
import AppShell from '../../components/AppShell';
import { tokens } from '../../components/design-system/tokens';
import {
  ArrowLeft,
  Lock,
  ShieldCheck,
  Tag,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  XCircle,
  ExternalLink,
  RefreshCw,
  Layers,
  Database,
  ShieldAlert,
  History,
  FileText,
  Building2,
  ChevronDown,
  ChevronUp
} from 'lucide-react';

interface AttributeValueDTO {
  key: string;
  raw_text?: string;
  value?: any;
  unit?: string;
  canonical_value?: any;
  source: string;
  confidence: number;
  rule_id?: string;
  assumed?: boolean;
  internal_conflict?: boolean;
}

interface RecentMatchDTO {
  match_id: string;
  relationship: string;
  equivalence_confidence: number;
  review_status: string;
  veto_applied: boolean;
  veto_gate?: string;
  partner_material_id: string;
  partner_cpse_code: string;
  partner_source_code: string;
  partner_raw_description: string;
  created_at?: string;
}

interface AuditEventDTO {
  seq: number;
  action: string;
  actor_role: string;
  timestamp?: string;
  hash: string;
  reason?: string;
}

interface MaterialDetailDTO {
  id: string;
  cpse_code: string;
  source_code: string;
  raw_description: string;
  raw_uom: string;
  normalized_text?: string;
  uom_canonical?: string;
  uom_dimension?: string;
  category_code: string;
  category_confidence: number;
  attributes: AttributeValueDTO[];
  mapping_nmc?: string;
  mapping_status?: string;
  manufacturer?: string;
  part_number?: string;
  created_at?: string;
  status?: string;
  matches_count: number;
  recent_matches: RecentMatchDTO[];
  audit_events: AuditEventDTO[];
}

export default function MaterialDetailPage() {
  const params = useParams();
  const router = useRouter();
  const { token } = useAuth();
  const [material, setMaterial] = useState<MaterialDetailDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  // Progressive disclosure section states
  const [showMatches, setShowMatches] = useState(true);
  const [showAudit, setShowAudit] = useState(true);

  const materialId = Array.isArray(params?.id) ? params.id[0] : params?.id;

  const fetchDetail = async () => {
    if (!token || !materialId) return;
    setLoading(true);
    setError(null);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${apiHost}/api/v1/materials/${materialId}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMaterial(data);
      } else {
        setError(`Failed to load material details (${res.status})`);
      }
    } catch (e: any) {
      setError(e.message || 'Error communicating with API backend');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDetail();
  }, [token, materialId]);

  return (
    <AppShell>
      {/* Top Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.25rem' }}>
        <button
          onClick={() => router.push('/materials')}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.4rem',
            padding: '0.5rem 0.85rem',
            background: tokens.colors.surface,
            color: tokens.colors.textPrimary,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 600,
            boxShadow: tokens.shadows.sm
          }}
        >
          <ArrowLeft style={{ width: '16px', height: '16px' }} />
          Back to Materials
        </button>

        <button
          onClick={fetchDetail}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 0.85rem',
            background: tokens.colors.surface,
            color: tokens.colors.primary,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.5rem',
            cursor: 'pointer',
            fontSize: '0.85rem',
            fontWeight: 700,
            boxShadow: tokens.shadows.sm
          }}
        >
          <RefreshCw style={{ width: '14px', height: '14px', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh Material
        </button>
      </div>

      {loading ? (
        <div style={{ padding: '3rem', textAlign: 'center', color: tokens.colors.textSecondary }}>
          <div style={{
            width: '36px',
            height: '36px',
            border: `3px solid ${tokens.colors.border}`,
            borderTop: `3px solid ${tokens.colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem auto'
          }} />
          <p style={{ fontWeight: 600 }}>Loading material provenance & technical records...</p>
        </div>
      ) : error || !material ? (
        <div style={{ padding: '2rem', background: '#FEE2E2', border: `1px solid ${tokens.colors.danger}`, borderRadius: '0.75rem', color: tokens.colors.danger }}>
          <p style={{ fontWeight: 700, margin: 0 }}>{error || 'Material not found'}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>
          
          {/* Header Banner */}
          <div style={{
            background: tokens.colors.surface,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.75rem',
            padding: '1.5rem',
            display: 'flex',
            flexWrap: 'wrap',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: tokens.shadows.sm
          }}>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.5rem' }}>
                <span style={{
                  background: '#DCFCE7',
                  color: tokens.colors.primary,
                  fontSize: '0.75rem',
                  fontWeight: 800,
                  padding: '0.2rem 0.6rem',
                  borderRadius: '0.375rem',
                  border: '1px solid #BBF7D0'
                }}>
                  {material.cpse_code}
                </span>
                <span style={{
                  background: '#0F766E',
                  color: '#fff',
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.6rem',
                  borderRadius: '0.375rem'
                }}>
                  {material.category_code}
                </span>
                <span style={{
                  background: material.status === 'ACTIVE' ? '#F0FDF4' : tokens.colors.surfaceSubtle,
                  color: material.status === 'ACTIVE' ? tokens.colors.success : tokens.colors.textSecondary,
                  fontSize: '0.75rem',
                  fontWeight: 700,
                  padding: '0.2rem 0.5rem',
                  borderRadius: '0.375rem',
                  border: `1px solid ${material.status === 'ACTIVE' ? '#BBF7D0' : tokens.colors.border}`
                }}>
                  {material.status || 'ACTIVE'}
                </span>
              </div>
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, color: tokens.colors.textPrimary, margin: '0 0 0.25rem 0', fontFamily: 'monospace' }}>
                {material.source_code}
              </h1>
              <p style={{ margin: 0, color: tokens.colors.textSecondary, fontSize: '0.8rem' }}>
                Material UUID: <span style={{ fontFamily: 'monospace', color: tokens.colors.textPrimary }}>{material.id}</span>
              </p>
            </div>

            {/* Linked NMC Status Card */}
            {material.mapping_nmc ? (
              <div style={{
                background: '#DCFCE7',
                border: '1px solid #BBF7D0',
                borderRadius: '0.5rem',
                padding: '0.75rem 1.25rem',
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <ShieldCheck style={{ width: '28px', height: '28px', color: tokens.colors.primary }} />
                <div>
                  <div style={{ fontSize: '0.7rem', fontWeight: 800, color: tokens.colors.primary, textTransform: 'uppercase' }}>
                    STANDARDIZED NATIONAL MATERIAL MASTER
                  </div>
                  <div style={{ fontSize: '1.15rem', fontWeight: 900, color: tokens.colors.textPrimary, fontFamily: 'monospace' }}>
                    {material.mapping_nmc}
                  </div>
                </div>
                <Link
                  href="/national-materials"
                  style={{
                    marginLeft: '0.5rem',
                    padding: '0.4rem 0.75rem',
                    background: tokens.colors.primary,
                    color: '#fff',
                    borderRadius: '0.375rem',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    textDecoration: 'none',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}
                >
                  Registry <ExternalLink style={{ width: '12px', height: '12px' }} />
                </Link>
              </div>
            ) : (
              <div style={{
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                borderRadius: '0.5rem',
                padding: '0.75rem 1rem',
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: tokens.colors.textSecondary,
                fontSize: '0.85rem'
              }}>
                <Tag style={{ width: '16px', height: '16px' }} />
                <span>Pending Cross-CPSE Harmonization (No NMC Linked)</span>
              </div>
            )}
          </div>

          {/* Section 1: IDENTITY & Section 2: NORMALIZED DATA */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(420px, 1fr))', gap: '1.5rem' }}>
            
            {/* 1. IDENTITY */}
            <div style={{
              background: tokens.colors.surface,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.75rem',
              padding: '1.25rem',
              boxShadow: tokens.shadows.sm
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Lock style={{ width: '16px', height: '16px', color: tokens.colors.primary }} />
                  <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                    1. Identity (CPSE Source Record)
                  </h3>
                </div>
                <span style={{ fontSize: '0.65rem', fontWeight: 800, color: tokens.colors.primary, background: '#DCFCE7', padding: '0.15rem 0.5rem', borderRadius: '0.2rem', border: '1px solid #BBF7D0' }}>
                  POSTGRES TRIGGER PROTECTED
                </span>
              </div>

              <div style={{ background: tokens.colors.surfaceSubtle, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.5rem', padding: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.7rem', color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: '0.25rem' }}>RAW DESCRIPTION</div>
                <div style={{ color: tokens.colors.textPrimary, fontWeight: 600, fontSize: '0.9rem', wordBreak: 'break-word', lineHeight: 1.4 }}>
                  {material.raw_description}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.8rem' }}>
                <div>
                  <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>RAW UOM</span>
                  <span style={{ color: tokens.colors.textPrimary, fontWeight: 700 }}>{material.raw_uom || 'EA'}</span>
                </div>
                <div>
                  <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>MANUFACTURER</span>
                  <span style={{ color: tokens.colors.textPrimary, fontWeight: 700 }}>{material.manufacturer || '—'}</span>
                </div>
                <div>
                  <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>PART NUMBER</span>
                  <span style={{ color: tokens.colors.textPrimary, fontWeight: 700, fontFamily: 'monospace' }}>{material.part_number || '—'}</span>
                </div>
              </div>
            </div>

            {/* 2. NORMALIZED DATA */}
            <div style={{
              background: tokens.colors.surface,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.75rem',
              padding: '1.25rem',
              boxShadow: tokens.shadows.sm
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
                <Cpu style={{ width: '16px', height: '16px', color: tokens.colors.teal }} />
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                  2. Normalized Data (NFKC + Token Expansion)
                </h3>
              </div>

              <div style={{ background: tokens.colors.surfaceSubtle, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.5rem', padding: '0.75rem', marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.7rem', color: tokens.colors.textSecondary, fontWeight: 700, marginBottom: '0.25rem' }}>CANONICAL NORMALIZED TEXT</div>
                <div style={{ color: tokens.colors.primary, fontWeight: 700, fontFamily: 'monospace', fontSize: '0.875rem', wordBreak: 'break-word', lineHeight: 1.4 }}>
                  {material.normalized_text || '—'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.8rem' }}>
                <div>
                  <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>CANONICAL UOM</span>
                  <span style={{ color: tokens.colors.primary, fontWeight: 800 }}>{material.uom_canonical || 'EA'}</span>
                </div>
                <div>
                  <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>DIMENSION</span>
                  <span style={{ color: tokens.colors.textPrimary, fontWeight: 700 }}>{material.uom_dimension || 'COUNT'}</span>
                </div>
                <div>
                  <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>CATEGORY CONF</span>
                  <span style={{ color: tokens.colors.success, fontWeight: 800 }}>{Math.round(material.category_confidence * 100)}%</span>
                </div>
              </div>
            </div>

          </div>

          {/* Section 3: EXTRACTED ATTRIBUTES */}
          <div style={{
            background: tokens.colors.surface,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.75rem',
            padding: '1.25rem',
            boxShadow: tokens.shadows.sm
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Layers style={{ width: '16px', height: '16px', color: tokens.colors.primary }} />
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                  3. Extracted Technical Attributes & Rule Provenance
                </h3>
              </div>
              <span style={{ fontSize: '0.75rem', background: tokens.colors.surfaceSubtle, color: tokens.colors.primary, padding: '0.2rem 0.5rem', borderRadius: '0.25rem', border: `1px solid ${tokens.colors.border}`, fontWeight: 700 }}>
                {material.attributes.length} Attributes Extracted
              </span>
            </div>

            {material.attributes.length === 0 ? (
              <div style={{ padding: '2rem', textAlign: 'center', color: tokens.colors.textSecondary, fontSize: '0.85rem' }}>
                No structured technical attributes extracted for this item.
              </div>
            ) : (
              <div style={{ overflowX: 'auto' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                  <thead>
                    <tr style={{ background: tokens.colors.surfaceSubtle, color: tokens.colors.textSecondary, textAlign: 'left', borderBottom: `2px solid ${tokens.colors.border}` }}>
                      <th style={{ padding: '0.6rem 0.75rem' }}>ATTRIBUTE KEY</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>EXTRACTED VALUE</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>CANONICAL NORMALIZED</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>RULE PROVENANCE</th>
                      <th style={{ padding: '0.6rem 0.75rem' }}>CONFIDENCE</th>
                    </tr>
                  </thead>
                  <tbody>
                    {material.attributes.map((attr, idx) => (
                      <tr key={idx} style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
                        <td style={{ padding: '0.6rem 0.75rem', fontWeight: 700, color: tokens.colors.textPrimary }}>
                          {attr.key}
                        </td>
                        <td style={{ padding: '0.6rem 0.75rem', color: '#0369A1', fontFamily: 'monospace', fontWeight: 600 }}>
                          {String(attr.value || attr.raw_text || '—')} {attr.unit || ''}
                        </td>
                        <td style={{ padding: '0.6rem 0.75rem', color: tokens.colors.primary, fontFamily: 'monospace', fontWeight: 700 }}>
                          {String(attr.canonical_value || '—')}
                        </td>
                        <td style={{ padding: '0.6rem 0.75rem' }}>
                          <span style={{ fontSize: '0.7rem', fontFamily: 'monospace', background: tokens.colors.surfaceSubtle, color: tokens.colors.textSecondary, padding: '0.15rem 0.4rem', borderRadius: '0.2rem', border: `1px solid ${tokens.colors.border}` }}>
                            {attr.rule_id || 'RULE_EXTRACTOR'}
                          </span>
                        </td>
                        <td style={{ padding: '0.6rem 0.75rem', color: tokens.colors.success, fontWeight: 700 }}>
                          {Math.round((attr.confidence || 1.0) * 100)}%
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>

          {/* Section 4: AI / MODEL PROVENANCE */}
          <div style={{
            background: tokens.colors.surface,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.75rem',
            padding: '1.25rem',
            boxShadow: tokens.shadows.sm
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <ShieldCheck style={{ width: '16px', height: '16px', color: tokens.colors.primary }} />
              <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                4. AI / Model Provenance
              </h3>
            </div>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem', fontSize: '0.8rem' }}>
              <div style={{ background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>EMBEDDING MODEL</span>
                <span style={{ fontWeight: 700, color: tokens.colors.textPrimary }}>sentence-transformers/all-MiniLM-L6-v2</span>
              </div>
              <div style={{ background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>INDEXING & SEARCH</span>
                <span style={{ fontWeight: 700, color: tokens.colors.textPrimary }}>PostgreSQL pgvector HNSW (cosine)</span>
              </div>
              <div style={{ background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>DECISION AUTHORITY</span>
                <span style={{ fontWeight: 700, color: tokens.colors.primary }}>Deterministic Veto Lattice v1.0 (G0–G6)</span>
              </div>
              <div style={{ background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                <span style={{ color: tokens.colors.textSecondary, display: 'block', fontSize: '0.7rem', fontWeight: 700 }}>LLM INFERENCE</span>
                <span style={{ fontWeight: 700, color: tokens.colors.textSecondary }}>OFF (Zero hallucination risk)</span>
              </div>
            </div>
          </div>

          {/* Section 5: MATCH HISTORY */}
          <div style={{
            background: tokens.colors.surface,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.75rem',
            padding: '1.25rem',
            boxShadow: tokens.shadows.sm
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Database style={{ width: '16px', height: '16px', color: tokens.colors.primary }} />
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                  5. Candidate Matches & Pairwise Decisions ({material.matches_count} Pairs)
                </h3>
              </div>
              <button
                onClick={() => setShowMatches(!showMatches)}
                style={{ background: 'none', border: 'none', color: tokens.colors.textSecondary, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', fontWeight: 700 }}
              >
                {showMatches ? <>Collapse <ChevronUp style={{ width: '14px', height: '14px' }} /></> : <>Expand <ChevronDown style={{ width: '14px', height: '14px' }} /></>}
              </button>
            </div>

            {showMatches && (
              material.recent_matches.length === 0 ? (
                <div style={{ padding: '2rem', textAlign: 'center', color: tokens.colors.textSecondary, fontSize: '0.85rem' }}>
                  No candidate pairwise comparisons generated yet. Trigger a Match Run in AI Matching to evaluate candidates.
                </div>
              ) : (
                <div style={{ overflowX: 'auto' }}>
                  <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
                    <thead>
                      <tr style={{ background: tokens.colors.surfaceSubtle, color: tokens.colors.textSecondary, textAlign: 'left', borderBottom: `2px solid ${tokens.colors.border}` }}>
                        <th style={{ padding: '0.6rem 0.75rem' }}>PARTNER CPSE</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>PARTNER CODE & DESCRIPTION</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>RELATIONSHIP</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>CONFIDENCE</th>
                        <th style={{ padding: '0.6rem 0.75rem' }}>VETO STATUS</th>
                        <th style={{ padding: '0.6rem 0.75rem', textAlign: 'right' }}>ACTION</th>
                      </tr>
                    </thead>
                    <tbody>
                      {material.recent_matches.map((m) => (
                        <tr key={m.match_id} style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            <span style={{ fontSize: '0.7rem', fontWeight: 800, padding: '0.15rem 0.45rem', background: '#DCFCE7', color: tokens.colors.primary, borderRadius: '0.25rem', border: '1px solid #BBF7D0' }}>
                              {m.partner_cpse_code}
                            </span>
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', maxWidth: '320px' }}>
                            <div style={{ fontFamily: 'monospace', color: tokens.colors.primary, fontWeight: 700 }}>{m.partner_source_code}</div>
                            <div style={{ color: tokens.colors.textSecondary, fontSize: '0.75rem', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                              {m.partner_raw_description}
                            </div>
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            <span style={{
                              fontSize: '0.7rem',
                              fontWeight: 700,
                              padding: '0.15rem 0.45rem',
                              borderRadius: '0.25rem',
                              background: m.relationship === 'FUNCTIONALLY_EQUIVALENT' || m.relationship === 'EQUIVALENT' ? '#DCFCE7' : m.relationship === 'REVIEW_REQUIRED' ? '#FEF3C7' : '#FEE2E2',
                              color: m.relationship === 'FUNCTIONALLY_EQUIVALENT' || m.relationship === 'EQUIVALENT' ? tokens.colors.success : m.relationship === 'REVIEW_REQUIRED' ? tokens.colors.warning : tokens.colors.danger
                            }}>
                              {m.relationship}
                            </span>
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', color: tokens.colors.textPrimary, fontWeight: 700 }}>
                            {(m.equivalence_confidence * 100).toFixed(1)}%
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem' }}>
                            {m.veto_applied ? (
                              <span style={{ fontSize: '0.7rem', color: tokens.colors.danger, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <ShieldAlert style={{ width: '13px', height: '13px' }} />
                                {m.veto_gate || 'VETO FIRED'}
                              </span>
                            ) : (
                              <span style={{ fontSize: '0.7rem', color: tokens.colors.success, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                <CheckCircle2 style={{ width: '13px', height: '13px' }} />
                                All Gates Passed
                              </span>
                            )}
                          </td>
                          <td style={{ padding: '0.6rem 0.75rem', textAlign: 'right' }}>
                            <Link
                              href={`/reviews/${m.match_id}`}
                              style={{
                                padding: '0.3rem 0.65rem',
                                background: tokens.colors.surfaceSubtle,
                                color: tokens.colors.primary,
                                border: `1px solid ${tokens.colors.border}`,
                                borderRadius: '0.375rem',
                                fontSize: '0.75rem',
                                fontWeight: 700,
                                textDecoration: 'none'
                              }}
                            >
                              Inspect Evidence
                            </Link>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )
            )}
          </div>

          {/* Section 6 & 7: REVIEW HISTORY & NATIONAL MATERIAL */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: '1.5rem' }}>
            {/* 6. REVIEW HISTORY */}
            <div style={{
              background: tokens.colors.surface,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.75rem',
              padding: '1.25rem',
              boxShadow: tokens.shadows.sm
            }}>
              <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                6. Review History & Stewardship State
              </h3>
              <div style={{ fontSize: '0.85rem', color: tokens.colors.textSecondary, lineHeight: 1.5 }}>
                <div>Mapping Status: <strong style={{ color: material.mapping_status === 'APPROVED' ? tokens.colors.success : tokens.colors.warning }}>{material.mapping_status || 'PROPOSED'}</strong></div>
                <div style={{ marginTop: '0.25rem' }}>Steward Authority: <strong>Designated CPSE Material Officer / Steward</strong></div>
                <div style={{ marginTop: '0.5rem', fontStyle: 'italic', fontSize: '0.775rem' }}>
                  Decisions recorded with immutable role signatures and cryptographic hash chaining.
                </div>
              </div>
            </div>

            {/* 7. NATIONAL MATERIAL */}
            <div style={{
              background: tokens.colors.surface,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.75rem',
              padding: '1.25rem',
              boxShadow: tokens.shadows.sm
            }}>
              <h3 style={{ margin: '0 0 0.75rem 0', fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                7. National Material Master Status
              </h3>
              {material.mapping_nmc ? (
                <div>
                  <div style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary, marginBottom: '0.25rem' }}>ASSIGNED NMC</div>
                  <div style={{ fontSize: '1.2rem', fontFamily: 'monospace', fontWeight: 900, color: tokens.colors.primary }}>
                    {material.mapping_nmc}
                  </div>
                  <p style={{ margin: '0.5rem 0 0 0', fontSize: '0.8rem', color: tokens.colors.textSecondary }}>
                    This source material is actively crosswalked to the National Catalog.
                  </p>
                </div>
              ) : (
                <div style={{ color: tokens.colors.textSecondary, fontSize: '0.85rem' }}>
                  Not yet linked to a National Material Code. Complete equivalence review in the Review Queue to generate an NMC.
                </div>
              )}
            </div>
          </div>

          {/* Section 8: AUDIT HISTORY */}
          <div style={{
            background: tokens.colors.surface,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.75rem',
            padding: '1.25rem',
            boxShadow: tokens.shadows.sm
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <History style={{ width: '16px', height: '16px', color: tokens.colors.primary }} />
                <h3 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                  8. Cryptographic Audit History (SHA-256 Hash Chain)
                </h3>
              </div>
              <button
                onClick={() => setShowAudit(!showAudit)}
                style={{ background: 'none', border: 'none', color: tokens.colors.textSecondary, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '0.25rem', fontSize: '0.75rem', fontWeight: 700 }}
              >
                {showAudit ? <>Collapse <ChevronUp style={{ width: '14px', height: '14px' }} /></> : <>Expand <ChevronDown style={{ width: '14px', height: '14px' }} /></>}
              </button>
            </div>

            {showAudit && (
              material.audit_events.length === 0 ? (
                <div style={{ padding: '1.5rem', textAlign: 'center', color: tokens.colors.textSecondary, fontSize: '0.85rem' }}>
                  No direct governance audit events logged for this item yet.
                </div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                  {material.audit_events.map((ev) => (
                    <div
                      key={ev.seq}
                      style={{
                        background: tokens.colors.surfaceSubtle,
                        border: `1px solid ${tokens.colors.border}`,
                        borderRadius: '0.375rem',
                        padding: '0.6rem 0.8rem',
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        fontSize: '0.8rem'
                      }}
                    >
                      <div>
                        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                          <span style={{ fontSize: '0.7rem', fontWeight: 800, color: tokens.colors.primary }}>#{ev.seq} {ev.action}</span>
                          <span style={{ fontSize: '0.65rem', background: '#DCFCE7', color: tokens.colors.primary, padding: '0.1rem 0.35rem', borderRadius: '0.2rem', fontWeight: 700 }}>{ev.actor_role}</span>
                          <span style={{ fontSize: '0.7rem', color: tokens.colors.textSecondary }}>{ev.timestamp ? new Date(ev.timestamp).toLocaleString() : ''}</span>
                        </div>
                        <div style={{ color: tokens.colors.textPrimary, fontSize: '0.75rem' }}>{ev.reason || 'Governance event'}</div>
                      </div>
                      <div style={{ fontFamily: 'monospace', fontSize: '0.65rem', color: tokens.colors.textSecondary }}>
                        {ev.hash.substring(0, 16)}...
                      </div>
                    </div>
                  ))}
                </div>
              )
            )}
          </div>

        </div>
      )}
    </AppShell>
  );
}
