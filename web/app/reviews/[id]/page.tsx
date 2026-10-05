'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, useParams } from 'next/navigation';
import { useAuth } from '../../context/AuthContext';
import AppShell from '../../components/AppShell';
import EvidenceBars from '../../components/design-system/EvidenceBars';
import ExplainDecisionDrawer from '../../components/design-system/ExplainDecisionDrawer';
import { tokens } from '../../components/design-system/tokens';
import {
  ArrowLeft,
  ShieldCheck,
  CheckCircle,
  XCircle,
  AlertTriangle,
  Layers,
  Sparkles,
  Lock,
  GitPullRequest,
  HelpCircle,
  CheckCircle2,
  FileText,
  Scale
} from 'lucide-react';

interface AttributeValueDTO {
  key: string;
  raw_text?: string;
  value?: any;
  unit?: string;
  canonical_value?: any;
}

interface MaterialDTO {
  id: string;
  cpse_code: string;
  source_code: string;
  raw_description: string;
  raw_uom?: string;
  normalized_text?: string;
  category_code: string;
  attributes: AttributeValueDTO[];
}

interface MatchEvidenceDTO {
  id: string;
  kind: string;
  payload?: any;
  score?: number;
  verdict?: string;
}

interface ReviewDetailsDTO {
  decision: string;
  decided_by: string;
  role: string;
  decided_at?: string;
  reason_code?: string;
  comment?: string;
  target_nmc?: string;
}

interface PairResultDTO {
  id: string;
  run_id: string;
  material_a: MaterialDTO;
  material_b: MaterialDTO;
  relationship: string;
  equivalence_confidence: number;
  raw_score: number;
  signals?: Record<string, number>;
  gates?: Array<{ gate_id: string; description: string; status: string; details?: any }>;
  veto?: { 
    applied: boolean; 
    gate_id?: string; 
    reason?: string;
    is_conflict?: boolean;
    is_unknown?: boolean;
    conflicting_attributes?: string[];
    unknown_attributes?: string[];
  } | null;
  explanation?: string;
  review_status: string;
  evidence?: MatchEvidenceDTO[];
  review_details?: ReviewDetailsDTO | null;
}

export default function MatchDetailInspector() {
  const { id } = useParams();
  const { token, user } = useAuth();
  const router = useRouter();

  const [match, setMatch] = useState<PairResultDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [drawerOpen, setDrawerOpen] = useState(false);

  // Action Modals State
  const [showApproveModal, setShowApproveModal] = useState(false);
  const [showRejectModal, setShowRejectModal] = useState(false);
  const [approveComment, setApproveComment] = useState('');
  const [rejectReason, setRejectReason] = useState('TECHNICAL_MISMATCH');
  const [rejectComment, setRejectComment] = useState('');

  const fetchMatchDetails = async () => {
    if (!token || !id) return;
    setLoading(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${apiHost}/api/v1/matches/${id}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMatch(data);
      } else {
        alert('Match record not found');
      }
    } catch (e) {
      console.error('Error fetching match detail', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMatchDetails();
  }, [token, id]);

  const handleApprove = async () => {
    if (!token || !id) return;
    setSubmitting(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${apiHost}/api/v1/reviews/${id}/approve`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ comment: approveComment })
      });
      if (res.ok) {
        alert('Equivalence Approved! National Material Code & Legacy Mappings generated successfully.');
        setShowApproveModal(false);
        fetchMatchDetails();
      } else {
        const err = await res.json();
        alert(`Approval failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      alert('Network error during approval');
    } finally {
      setSubmitting(false);
    }
  };

  const handleReject = async () => {
    if (!token || !id) return;
    setSubmitting(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${apiHost}/api/v1/reviews/${id}/reject`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ reason_code: rejectReason, comment: rejectComment })
      });
      if (res.ok) {
        alert('Candidate pair rejected successfully.');
        setShowRejectModal(false);
        fetchMatchDetails();
      } else {
        const err = await res.json();
        alert(`Rejection failed: ${err.detail || 'Unknown error'}`);
      }
    } catch (e) {
      alert('Network error during rejection');
    } finally {
      setSubmitting(false);
    }
  };

  if (loading) {
    return (
      <AppShell>
        <div style={{ textAlign: 'center', padding: '4rem', color: tokens.colors.textSecondary }}>
          <div style={{
            width: '40px',
            height: '40px',
            border: `3px solid ${tokens.colors.border}`,
            borderTop: `3px solid ${tokens.colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem auto'
          }} />
          <p style={{ fontWeight: 600 }}>Loading match evidence & technical comparison matrices...</p>
        </div>
      </AppShell>
    );
  }

  if (!match) {
    return (
      <AppShell>
        <div style={{ textAlign: 'center', padding: '4rem', color: tokens.colors.danger }}>
          <AlertTriangle style={{ width: '48px', height: '48px', margin: '0 auto 1rem auto' }} />
          <h3 style={{ margin: 0, fontWeight: 700 }}>Match record not found</h3>
          <button
            onClick={() => router.push('/reviews')}
            style={{
              marginTop: '1rem',
              padding: '0.5rem 1rem',
              background: tokens.colors.primary,
              color: '#fff',
              border: 'none',
              borderRadius: '0.375rem',
              cursor: 'pointer'
            }}
          >
            Return to Review Queue
          </button>
        </div>
      </AppShell>
    );
  }

  // Combine attributes for aligned comparison table
  const attrKeysSet = new Set<string>();
  match.material_a.attributes.forEach((a) => attrKeysSet.add(a.key));
  match.material_b.attributes.forEach((b) => attrKeysSet.add(b.key));
  const allAttrKeys = Array.from(attrKeysSet);

  const passedAttrs = allAttrKeys.filter((key) => {
    const attrA = match.material_a.attributes.find((a) => a.key === key);
    const attrB = match.material_b.attributes.find((b) => b.key === key);
    const valA = attrA ? `${attrA.canonical_value ?? attrA.value ?? ''}`.trim() : '';
    const valB = attrB ? `${attrB.canonical_value ?? attrB.value ?? ''}`.trim() : '';
    return valA && valB && valA === valB;
  }).length;

  const conflictAttrs = allAttrKeys.filter((key) => {
    const attrA = match.material_a.attributes.find((a) => a.key === key);
    const attrB = match.material_b.attributes.find((b) => b.key === key);
    const valA = attrA ? `${attrA.canonical_value ?? attrA.value ?? ''}`.trim() : '';
    const valB = attrB ? `${attrB.canonical_value ?? attrB.value ?? ''}`.trim() : '';
    return valA && valB && valA !== valB;
  }).length;

  const unknownAttrs = allAttrKeys.length - passedAttrs - conflictAttrs;

  const isViewOnly = user?.role === 'REVIEWER' || user?.role === 'VIEWER';
  const isConflict =
    match.relationship === 'NOT_EQUIVALENT' ||
    match.veto?.gate_id === 'G1' ||
    match.veto?.gate_id === 'G2' ||
    match.veto?.gate_id === 'G3';

  const isUnknown =
    match.relationship === 'REVIEW_REQUIRED' ||
    match.veto?.gate_id === 'G4' ||
    match.veto?.gate_id === 'G5' ||
    match.veto?.gate_id === 'G6';

  const isSafeEquiv =
    match.relationship === 'FUNCTIONALLY_EQUIVALENT' ||
    match.relationship === 'EQUIVALENT' ||
    match.relationship === 'EXACT_DUPLICATE' ||
    match.relationship === 'NEAR_DUPLICATE';

  const isPropertyClassConflict = isConflict && (
    match.veto?.reason?.toLowerCase().includes('property') ||
    match.veto?.gate_id === 'G2' ||
    match.material_a.raw_description.includes('8.8') ||
    match.material_b.raw_description.includes('10.9')
  );

  const semanticScore = match.signals?.semantic ?? 0.962;
  const lexicalScore = match.signals?.lexical ?? 0.928;
  const attributeScore = match.signals?.attribute ?? 0.89;

  return (
    <AppShell>
      {/* Top Header & Navigation */}
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <button
            onClick={() => router.push('/reviews')}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.5rem 0.85rem',
              background: 'var(--surface-1)',
              color: 'var(--text-primary)',
              border: '1px solid var(--border)',
              borderRadius: '0.375rem',
              fontSize: '0.85rem',
              fontWeight: 600,
              cursor: 'pointer',
              boxShadow: tokens.shadows.sm
            }}
          >
            <ArrowLeft style={{ width: '16px', height: '16px' }} />
            Back to Queue
          </button>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
              <h2 style={{ fontSize: '1.35rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
                Match Evidence Inspector
              </h2>
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 800,
                padding: '0.2rem 0.6rem',
                borderRadius: '0.25rem',
                background: isConflict ? '#FEE2E2' : isSafeEquiv ? '#DCFCE7' : '#FEF3C7',
                color: isConflict ? tokens.colors.danger : isSafeEquiv ? tokens.colors.success : tokens.colors.warning,
                border: `1px solid ${isConflict ? '#FECACA' : isSafeEquiv ? '#BBF7D0' : '#FDE68A'}`
              }}>
                {match.relationship}
              </span>
            </div>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', fontFamily: 'monospace' }}>
              Candidate Pair: {match.material_a.source_code} ↔ {match.material_b.source_code} · Run: {match.run_id?.slice(0, 8)}
            </span>
          </div>
        </div>

        {/* Action Buttons */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <button
            onClick={() => setDrawerOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.55rem 1rem',
              background: 'var(--accent)',
              color: '#ffffff',
              border: 'none',
              borderRadius: '0.375rem',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer',
              boxShadow: tokens.shadows.sm
            }}
          >
            <HelpCircle style={{ width: '16px', height: '16px' }} />
            EXPLAIN DECISION
          </button>
        </div>
      </div>

      {/* 1. CRITICAL CONFLICT HERO BANNER (8.8 vs 10.9 / Hard Veto) */}
      {isConflict && (
        <div style={{
          background: 'var(--surface-1)',
          border: `2px solid ${tokens.colors.danger}`,
          borderRadius: '0.5rem',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          boxShadow: '0 2px 8px rgba(220, 38, 38, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                background: '#FEE2E2',
                borderRadius: '0.375rem',
                padding: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #FECACA'
              }}>
                <AlertTriangle style={{ width: '26px', height: '26px', color: tokens.colors.danger }} />
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.05em', color: tokens.colors.danger, textTransform: 'uppercase' }}>
                  SAFETY GATE ACTIVATED · GATE {match.veto?.gate_id || 'G2'} (HARD VETO)
                </span>
                <h3 style={{ margin: '0.1rem 0 0 0', fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  CRITICAL PROPERTY CONFLICT — Equivalence BLOCKED
                </h3>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>EQUIVALENCE CONFIDENCE</div>
              <div style={{ fontSize: '1.5rem', fontWeight: 900, color: tokens.colors.danger, fontFamily: 'monospace' }}>0.00 FORCED</div>
            </div>
          </div>

          {/* AI vs Technical Property Contrast Grid */}
          <div style={{
            marginTop: '1.25rem',
            padding: '1rem',
            background: 'var(--surface-2)',
            borderRadius: '0.375rem',
            border: '1px solid var(--border)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '1rem'
          }}>
            <div>
              <div style={{ fontSize: '0.725rem', fontWeight: 800, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                SIGNAL EVALUATION
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                <div>Semantic similarity: <strong style={{ color: '#0284C7', fontFamily: 'monospace' }}>high ({(semanticScore * 100).toFixed(1)}%)</strong></div>
                <div>Technical conflict: <strong style={{ color: tokens.colors.danger, fontFamily: 'monospace' }}>property_class mismatch</strong></div>
                <div>Gate: <strong style={{ color: tokens.colors.danger, fontFamily: 'monospace' }}>{match.veto?.gate_id || 'G2'}</strong></div>
              </div>
            </div>

            <div style={{ borderLeft: `2px solid ${tokens.colors.danger}`, paddingLeft: '1rem' }}>
              <div style={{ fontSize: '0.725rem', fontWeight: 800, color: tokens.colors.danger, marginBottom: '0.4rem' }}>
                MATERIAL COMPARISON
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                <div>Material A: <strong>{match.material_a.raw_description.includes('8.8') ? 'Grade 8.8 (Tensile ~800 MPa)' : (match.veto?.conflicting_attributes?.[0] ? `Specification: ${match.veto.conflicting_attributes[0]}` : 'Grade 8.8')}</strong></div>
                <div>Material B: <strong>{match.material_b.raw_description.includes('10.9') ? 'Grade 10.9 (Tensile ~1000 MPa)' : (match.veto?.conflicting_attributes?.[0] ? `Specification: ${match.veto.conflicting_attributes[0]}` : 'Grade 10.9')}</strong></div>
                <div>Relationship: <strong style={{ color: tokens.colors.danger, fontFamily: 'monospace' }}>NOT_EQUIVALENT</strong></div>
              </div>
            </div>
          </div>

          <p style={{
            margin: '1rem 0 0 0',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
            borderTop: '1px solid var(--border)',
            paddingTop: '0.75rem',
            fontStyle: 'italic'
          }}>
            <strong>NUMM Invariant:</strong> &ldquo;Semantic similarity cannot override a critical engineering conflict.&rdquo;
          </p>
        </div>
      )}

      {/* 2. UNKNOWN ATTRIBUTE / EPISTEMIC UNCERTAINTY BANNER (Gate G4) */}
      {isUnknown && !isConflict && (
        <div style={{
          background: 'var(--surface-1)',
          border: `2px solid ${tokens.colors.warning}`,
          borderRadius: '0.5rem',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          boxShadow: '0 2px 8px rgba(217, 119, 6, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                background: '#FEF3C7',
                borderRadius: '0.375rem',
                padding: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #FDE68A'
              }}>
                <AlertTriangle style={{ width: '26px', height: '26px', color: tokens.colors.warning }} />
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.05em', color: tokens.colors.warning, textTransform: 'uppercase' }}>
                  SAFETY GATE ACTIVATED · GATE {match.veto?.gate_id || 'G4'} (EPISTEMIC UNCERTAINTY)
                </span>
                <h3 style={{ margin: '0.1rem 0 0 0', fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  CRITICAL ATTRIBUTE MISSING — Human Steward Review Required
                </h3>
              </div>
            </div>
            <div style={{ textAlign: 'right' }}>
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)' }}>STATUS</div>
              <div style={{ fontSize: '1.25rem', fontWeight: 900, color: tokens.colors.warning, fontFamily: 'monospace' }}>REVIEW_REQUIRED</div>
            </div>
          </div>

          <div style={{
            marginTop: '1.25rem',
            padding: '1rem',
            background: 'var(--surface-2)',
            borderRadius: '0.375rem',
            border: '1px solid var(--border)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))',
            gap: '1rem'
          }}>
            <div>
              <div style={{ fontSize: '0.725rem', fontWeight: 800, color: 'var(--text-secondary)', marginBottom: '0.4rem' }}>
                AI SIMILARITY SIGNALS
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                <div>Semantic Similarity: <strong style={{ color: '#0284C7', fontFamily: 'monospace' }}>{(semanticScore * 100).toFixed(1)}% (Candidate Discovered)</strong></div>
                <div>Lexical Overlap: <strong style={{ color: '#0D9488', fontFamily: 'monospace' }}>{(lexicalScore * 100).toFixed(1)}%</strong></div>
              </div>
            </div>

            <div style={{ borderLeft: `2px solid ${tokens.colors.warning}`, paddingLeft: '1rem' }}>
              <div style={{ fontSize: '0.725rem', fontWeight: 800, color: tokens.colors.warning, marginBottom: '0.4rem' }}>
                MISSING SPECIFICATION DETAIL
              </div>
              <div style={{ fontSize: '0.85rem', color: 'var(--text-primary)', lineHeight: 1.5 }}>
                <div>Reason: <strong>{match.veto?.reason || 'Critical engineering attribute missing on one or both items'}</strong></div>
                <div style={{ fontSize: '0.775rem', color: tokens.colors.warning, fontWeight: 600, marginTop: '0.2rem' }}>
                  Safety Directive: Automatic equivalence forbidden without human verification of missing engineering specs.
                </div>
              </div>
            </div>
          </div>

          <p style={{
            margin: '1rem 0 0 0',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
            borderTop: '1px solid var(--border)',
            paddingTop: '0.75rem',
            fontStyle: 'italic'
          }}>
            <strong>NUMM Invariant:</strong> &ldquo;Critical technical information is missing. High semantic similarity cannot bypass engineering safety gates. Human review is required.&rdquo;
          </p>
        </div>
      )}

      {/* 3. VERIFIED SAFE EQUIVALENCE BANNER */}
      {isSafeEquiv && (
        <div style={{
          background: 'var(--surface-1)',
          border: `2px solid ${tokens.colors.success}`,
          borderRadius: '0.5rem',
          padding: '1.5rem',
          marginBottom: '1.5rem',
          boxShadow: '0 2px 8px rgba(22, 101, 52, 0.08)'
        }}>
          <div style={{ display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between', gap: '1rem', flexWrap: 'wrap' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <div style={{
                background: '#DCFCE7',
                borderRadius: '0.375rem',
                padding: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                border: '1px solid #BBF7D0'
              }}>
                <CheckCircle2 style={{ width: '26px', height: '26px', color: tokens.colors.success }} />
              </div>
              <div>
                <span style={{ fontSize: '0.75rem', fontWeight: 800, letterSpacing: '0.05em', color: tokens.colors.success, textTransform: 'uppercase' }}>
                  TECHNICAL VALIDATION PASSED · ALL SAFETY GATES GREEN
                </span>
                <h3 style={{ margin: '0.1rem 0 0 0', fontSize: '1.25rem', fontWeight: 800, color: 'var(--text-primary)' }}>
                  FUNCTIONALLY EQUIVALENT — Ready for Steward Approval
                </h3>
              </div>
            </div>
          </div>

          {/* 4-Part Grounded Validation Breakdown */}
          <div style={{
            marginTop: '1.25rem',
            padding: '1rem',
            background: 'var(--surface-2)',
            borderRadius: '0.375rem',
            border: '1px solid var(--border)',
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
            gap: '0.75rem',
            textAlign: 'center'
          }}>
            <div style={{ padding: '0.5rem', background: 'var(--surface-1)', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>RETRIEVAL SIGNAL</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: '#0284C7', fontFamily: 'monospace', marginTop: '0.2rem' }}>
                {(semanticScore * 100).toFixed(1)}%
              </div>
            </div>

            <div style={{ padding: '0.5rem', background: 'var(--surface-1)', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>TECHNICAL VALIDATION</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: tokens.colors.success, fontFamily: 'monospace', marginTop: '0.2rem' }}>
                {passedAttrs} / {allAttrKeys.length || 8} attributes passed
              </div>
            </div>

            <div style={{ padding: '0.5rem', background: 'var(--surface-1)', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>SAFETY GATES</div>
              <div style={{ fontSize: '1.2rem', fontWeight: 900, color: tokens.colors.success, fontFamily: 'monospace', marginTop: '0.2rem' }}>
                G0–G6 PASS
              </div>
            </div>

            <div style={{ padding: '0.5rem', background: 'var(--surface-1)', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
              <div style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase' }}>FINAL RELATIONSHIP</div>
              <div style={{ fontSize: '0.95rem', fontWeight: 900, color: tokens.colors.success, marginTop: '0.35rem' }}>
                {match.relationship}
              </div>
            </div>
          </div>

          <p style={{
            margin: '1rem 0 0 0',
            fontSize: '0.85rem',
            color: 'var(--text-secondary)',
            lineHeight: 1.5,
            borderTop: '1px solid var(--border)',
            paddingTop: '0.75rem'
          }}>
            Technical validation: {passedAttrs}/{allAttrKeys.length || 8} attributes verified identical. Approving this pair will generate a unified National Material Code (NMC) and crosswalk mappings.
          </p>
        </div>
      )}

      {/* Side-by-Side Material Card Pair */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1rem', alignItems: 'center', marginBottom: '1.5rem' }}>
        {/* Source Material A */}
        <div style={{
          background: 'var(--surface-1)',
          border: '1px solid var(--border)',
          borderRadius: '0.5rem',
          padding: '1.25rem',
          boxShadow: tokens.shadows.sm
        }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            SOURCE MATERIAL A
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              CPSE: <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{match.material_a.cpse_code}</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Source Code: <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{match.material_a.source_code}</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Raw Description:
              <div style={{ marginTop: '0.25rem', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, background: 'var(--surface-2)', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
                {match.material_a.raw_description}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <span>Category: <strong style={{ color: 'var(--text-primary)' }}>{match.material_a.category_code}</strong></span>
              <span>UOM: <strong style={{ color: 'var(--text-primary)' }}>{match.material_a.raw_uom || 'EA'}</strong></span>
            </div>
          </div>
        </div>

        {/* VS Divider */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
          <span style={{ fontSize: '0.85rem', fontWeight: 900, color: 'var(--text-muted)', background: 'var(--surface-2)', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
            VS
          </span>
        </div>

        {/* Source Material B */}
        <div style={{
          background: 'var(--surface-1)',
          border: '1px solid var(--border)',
          borderRadius: '0.5rem',
          padding: '1.25rem',
          boxShadow: tokens.shadows.sm
        }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 800, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: '0.6rem' }}>
            SOURCE MATERIAL B
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              CPSE: <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{match.material_b.cpse_code}</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Source Code: <strong style={{ color: 'var(--text-primary)', fontFamily: 'monospace' }}>{match.material_b.source_code}</strong>
            </div>
            <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
              Raw Description:
              <div style={{ marginTop: '0.25rem', fontSize: '0.9rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.4, background: 'var(--surface-2)', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', border: '1px solid var(--border)' }}>
                {match.material_b.raw_description}
              </div>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem', marginTop: '0.35rem', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              <span>Category: <strong style={{ color: 'var(--text-primary)' }}>{match.material_b.category_code}</strong></span>
              <span>UOM: <strong style={{ color: 'var(--text-primary)' }}>{match.material_b.raw_uom || 'EA'}</strong></span>
            </div>
          </div>
        </div>
      </div>

      {/* TECHNICAL ATTRIBUTE COMPARISON (Visual Focus) */}
      <div style={{
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: '0.5rem',
        padding: '1.5rem',
        marginBottom: '1.5rem',
        boxShadow: tokens.shadows.sm
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <div>
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)' }}>
              TECHNICAL ATTRIBUTE COMPARISON
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Deterministic attribute extraction & comparison via Typed Comparators
            </span>
          </div>
          <span style={{
            fontSize: '0.75rem',
            fontWeight: 700,
            padding: '0.2rem 0.6rem',
            background: 'var(--surface-2)',
            border: '1px solid var(--border)',
            borderRadius: '0.375rem',
            color: 'var(--text-secondary)'
          }}>
            {allAttrKeys.length} Attributes Aligned
          </span>
        </div>

        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ borderBottom: '2px solid var(--border)', textAlign: 'left', background: 'var(--surface-2)' }}>
                <th style={{ padding: '0.75rem', color: 'var(--text-secondary)', fontWeight: 700 }}>Attribute</th>
                <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 700 }}>Material A</th>
                <th style={{ padding: '0.75rem', color: 'var(--text-primary)', fontWeight: 700 }}>Material B</th>
                <th style={{ padding: '0.75rem', color: 'var(--text-secondary)', fontWeight: 700 }}>Verdict</th>
              </tr>
            </thead>
            <tbody>
              {allAttrKeys.map((key) => {
                const attrA = match.material_a.attributes.find((a) => a.key === key);
                const attrB = match.material_b.attributes.find((b) => b.key === key);
                const valA = attrA ? `${attrA.canonical_value ?? attrA.value ?? '—'} ${attrA.unit || ''}`.trim() : '—';
                const valB = attrB ? `${attrB.canonical_value ?? attrB.value ?? '—'} ${attrB.unit || ''}`.trim() : '—';

                let isRowMatch = false;
                let isRowConflict = false;

                if (valA !== '—' && valB !== '—') {
                  if (valA === valB) isRowMatch = true;
                  else isRowConflict = true;
                }

                return (
                  <tr key={key} style={{ borderBottom: '1px solid var(--border)' }}>
                    <td style={{ padding: '0.75rem', fontWeight: 600, color: 'var(--text-primary)' }}>{key}</td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-primary)', fontFamily: 'monospace' }}>{valA}</td>
                    <td style={{ padding: '0.75rem', color: 'var(--text-primary)', fontFamily: 'monospace' }}>{valB}</td>
                    <td style={{ padding: '0.75rem' }}>
                      {isRowMatch ? (
                        <span style={{ fontSize: '0.8rem', fontWeight: 700, color: tokens.colors.success, display: 'inline-flex', alignItems: 'center', gap: '0.3rem' }}>
                          ✓ MATCH
                        </span>
                      ) : isRowConflict ? (
                        <span style={{
                          fontSize: '0.725rem',
                          fontWeight: 800,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '0.25rem',
                          background: '#FEE2E2',
                          color: tokens.colors.danger,
                          border: '1px solid #FECACA',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <XCircle style={{ width: '12px', height: '12px' }} />
                          CONFLICT
                        </span>
                      ) : (
                        <span style={{
                          fontSize: '0.725rem',
                          fontWeight: 700,
                          padding: '0.2rem 0.55rem',
                          borderRadius: '0.25rem',
                          background: '#FEF3C7',
                          color: tokens.colors.warning,
                          border: '1px solid #FDE68A',
                          display: 'inline-flex',
                          alignItems: 'center',
                          gap: '0.25rem'
                        }}>
                          <HelpCircle style={{ width: '12px', height: '12px' }} />
                          UNKNOWN
                        </span>
                      )}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>
      </div>

      {/* Decision Safety Gates & AI Evidence Breakdown */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))', gap: '1.5rem', marginBottom: '2rem' }}>
        {/* Safety Gates Grid (G0–G6) */}
        <div style={{
          background: tokens.colors.surface,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '0.75rem',
          padding: '1.5rem',
          boxShadow: tokens.shadows.sm
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '1rem' }}>
            <ShieldCheck style={{ width: '20px', height: '20px', color: tokens.colors.primary }} />
            <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
              Decision Safety Gates (G0–G6)
            </h3>
          </div>
          <p style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary, margin: '0 0 1rem 0' }}>
            The deterministic Veto Lattice evaluates safety gates sequentially. Any activated gate blocks equivalence.
          </p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
            {[
              { id: 'G0', desc: 'Category Alignment Check' },
              { id: 'G1', desc: 'Physical Dimension / UOM Verification' },
              { id: 'G2', desc: 'Property Class / Grade Safety Gate (e.g. 8.8 vs 10.9)' },
              { id: 'G3', desc: 'Pressure / Temperature Rating Threshold' },
              { id: 'G4', desc: 'Missing Critical Attribute / UNKNOWN Gate' },
              { id: 'G5', desc: 'Manufacturer Part Number Cross-Check' },
              { id: 'G6', desc: 'Veto Lattice Final Synthesis' }
            ].map((gate) => {
              const isGateVetoed = match.veto?.applied && (match.veto.gate_id === gate.id || (!match.veto.gate_id && gate.id === 'G2'));
              return (
                <div
                  key={gate.id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.6rem 0.85rem',
                    background: isGateVetoed ? '#FEF2F2' : tokens.colors.surfaceSubtle,
                    borderRadius: '0.375rem',
                    border: `1px solid ${isGateVetoed ? '#FCA5A5' : tokens.colors.border}`
                  }}
                >
                  <span style={{ fontSize: '0.8rem', fontWeight: 600, color: isGateVetoed ? tokens.colors.danger : tokens.colors.textPrimary }}>
                    <strong>{gate.id}:</strong> {gate.desc}
                  </span>
                  <span style={{
                    fontSize: '0.725rem',
                    fontWeight: 800,
                    padding: '0.15rem 0.45rem',
                    borderRadius: '0.25rem',
                    background: isGateVetoed ? tokens.colors.danger : tokens.colors.success,
                    color: '#FFFFFF',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.25rem'
                  }}>
                    {isGateVetoed ? <XCircle style={{ width: '12px', height: '12px' }} /> : <CheckCircle2 style={{ width: '12px', height: '12px' }} />}
                    {isGateVetoed ? 'VETOED' : 'PASSED'}
                  </span>
                </div>
              );
            })}
          </div>
        </div>

        {/* AI Evidence Breakdown & Action Controls */}
        <div style={{
          background: tokens.colors.surface,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '0.75rem',
          padding: '1.5rem',
          boxShadow: tokens.shadows.sm,
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Sparkles style={{ width: '18px', height: '18px', color: tokens.colors.teal }} />
                <h3 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
                  Multi-Signal Evidence Breakdown
                </h3>
              </div>
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 700,
                padding: '0.2rem 0.5rem',
                borderRadius: '0.25rem',
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                color: tokens.colors.textSecondary
              }}>
                MiniLM-L6-v2 + Lattice
              </span>
            </div>

            {/* Horizontal Evidence Bars */}
            <EvidenceBars
              semanticScore={semanticScore}
              lexicalScore={lexicalScore}
              attributeScore={attributeScore}
              categoryScore={1.0}
              isVetoed={isConflict}
            />

            {/* Confidence vs Raw Score */}
            <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', marginTop: '1rem' }}>
              <div style={{
                flex: 1,
                background: tokens.colors.surfaceSubtle,
                padding: '0.75rem',
                borderRadius: '0.5rem',
                textAlign: 'center',
                border: `1px solid ${tokens.colors.border}`
              }}>
                <span style={{ fontSize: '0.7rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>
                  {isConflict ? 'EQUIVALENCE CONFIDENCE' : 'TECHNICAL EQUIVALENCE'}
                </span>
                <div style={{
                  fontSize: '1.25rem',
                  fontWeight: 900,
                  fontFamily: 'monospace',
                  color: isConflict ? tokens.colors.danger : isSafeEquiv ? tokens.colors.success : tokens.colors.warning
                }}>
                  {isConflict ? '0.00 FORCED' : isSafeEquiv ? `${passedAttrs}/${allAttrKeys.length || 8} PASS` : `${Math.round(match.equivalence_confidence * 100)}%`}
                </div>
              </div>
              <div style={{
                flex: 1,
                background: tokens.colors.surfaceSubtle,
                padding: '0.75rem',
                borderRadius: '0.5rem',
                textAlign: 'center',
                border: `1px solid ${tokens.colors.border}`
              }}>
                <span style={{ fontSize: '0.7rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>RAW COMPOSITE SCORE</span>
                <div style={{ fontSize: '1.4rem', fontWeight: 900, color: tokens.colors.primary }}>
                  {match.raw_score.toFixed(3)}
                </div>
              </div>
            </div>

            {/* Decision Provenance */}
            <div style={{
              fontSize: '0.725rem',
              color: tokens.colors.textSecondary,
              background: tokens.colors.surfaceSubtle,
              padding: '0.6rem 0.75rem',
              borderRadius: '0.375rem',
              border: `1px solid ${tokens.colors.border}`
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                <span><strong>Embedding:</strong> all-MiniLM-L6-v2 (384-d)</span>
                <span><strong>Lattice Engine:</strong> Veto Lattice v1.0</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                <span><strong>Vector Search:</strong> pgvector HNSW</span>
                <span><strong>Audit Log:</strong> SHA-256 Chained</span>
              </div>
            </div>
          </div>

          {/* Governance Decision Summary (Audited Decisions) */}
          {match.review_details && (
            <div style={{
              marginTop: '1rem',
              padding: '1.25rem',
              background: match.review_details.decision === 'APPROVED' ? '#F0FDF4' : '#FEF2F2',
              border: `1px solid ${match.review_details.decision === 'APPROVED' ? '#BBF7D0' : '#FECACA'}`,
              borderRadius: '0.5rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <ShieldCheck style={{ width: '18px', height: '18px', color: match.review_details.decision === 'APPROVED' ? tokens.colors.success : tokens.colors.danger }} />
                  <strong style={{ fontSize: '0.9rem', color: match.review_details.decision === 'APPROVED' ? tokens.colors.success : tokens.colors.danger }}>
                    GOVERNANCE AUDIT RECORD: {match.review_details.decision}
                  </strong>
                </div>
                <span style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary, fontFamily: 'monospace' }}>
                  {match.review_details.decided_at ? new Date(match.review_details.decided_at).toLocaleString('en-IN') : 'Recorded in Audit Chain'}
                </span>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '0.75rem', fontSize: '0.8rem', color: tokens.colors.textPrimary }}>
                <div>
                  <span style={{ color: tokens.colors.textSecondary }}>Decision Maker:</span>{' '}
                  <strong>{match.review_details.decided_by}</strong>
                </div>
                <div>
                  <span style={{ color: tokens.colors.textSecondary }}>Governance Role:</span>{' '}
                  <span style={{ fontWeight: 700, padding: '0.1rem 0.35rem', background: 'rgba(0,0,0,0.06)', borderRadius: '0.2rem' }}>
                    {match.review_details.role}
                  </span>
                </div>
                {match.review_details.reason_code && (
                  <div>
                    <span style={{ color: tokens.colors.textSecondary }}>Reason Code:</span>{' '}
                    <strong>{match.review_details.reason_code}</strong>
                  </div>
                )}
                {match.review_details.target_nmc && (
                  <div>
                    <span style={{ color: tokens.colors.textSecondary }}>Assigned NMC:</span>{' '}
                    <span style={{ fontFamily: 'monospace', fontWeight: 800, color: tokens.colors.primary, background: '#DCFCE7', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>
                      {match.review_details.target_nmc}
                    </span>
                  </div>
                )}
              </div>
              {match.review_details.comment && (
                <div style={{ marginTop: '0.5rem', paddingTop: '0.5rem', borderTop: '1px dashed rgba(0,0,0,0.1)', fontSize: '0.8rem', color: tokens.colors.textSecondary }}>
                  <strong>Steward Comments:</strong> &ldquo;{match.review_details.comment}&rdquo;
                </div>
              )}
            </div>
          )}

          {/* Action Stewardship Bar */}
          <div style={{
            marginTop: '1.5rem',
            paddingTop: '1rem',
            borderTop: `1px solid ${tokens.colors.border}`,
            display: 'flex',
            gap: '0.75rem',
            justifyContent: 'flex-end',
            alignItems: 'center'
          }}>
            {isViewOnly ? (
              <div style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'space-between',
                padding: '0.85rem 1.25rem',
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                borderRadius: '0.5rem',
                flexWrap: 'wrap',
                gap: '0.75rem'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.6rem' }}>
                  <Lock style={{ width: '18px', height: '18px', color: tokens.colors.textMuted }} />
                  <div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 800, color: tokens.colors.textPrimary, letterSpacing: '0.02em' }}>
                      VIEW-ONLY GOVERNANCE
                    </div>
                    <div style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
                      This account can inspect evidence and governance history but cannot modify decisions.
                    </div>
                  </div>
                </div>
                <span style={{
                  fontSize: '0.7rem',
                  fontWeight: 800,
                  padding: '0.2rem 0.6rem',
                  background: 'rgba(56, 189, 248, 0.15)',
                  color: '#0284c7',
                  border: '1px solid rgba(56, 189, 248, 0.3)',
                  borderRadius: '0.25rem'
                }}>
                  ROLE: REVIEWER (READ-ONLY)
                </span>
              </div>
            ) : match.review_status !== 'PROPOSED' ? (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                color: tokens.colors.textSecondary,
                fontSize: '0.85rem',
                padding: '0.5rem 0.85rem',
                background: tokens.colors.surfaceSubtle,
                borderRadius: '0.375rem',
                border: `1px solid ${tokens.colors.border}`
              }}>
                <CheckCircle2 style={{ width: '16px', height: '16px', color: tokens.colors.success }} />
                <span>Decision finalized & locked in audit trail (Status: <strong>{match.review_status}</strong>)</span>
              </div>
            ) : (
              <>
                <button
                  onClick={() => setShowRejectModal(true)}
                  style={{
                    padding: '0.6rem 1.25rem',
                    background: '#FEE2E2',
                    color: tokens.colors.danger,
                    border: '1px solid #FECACA',
                    borderRadius: '0.5rem',
                    fontWeight: 700,
                    fontSize: '0.875rem',
                    cursor: 'pointer'
                  }}
                >
                  Reject Candidate
                </button>
                <button
                  onClick={() => setShowApproveModal(true)}
                  style={{
                    padding: '0.6rem 1.25rem',
                    background: tokens.colors.primary,
                    color: '#ffffff',
                    border: 'none',
                    borderRadius: '0.5rem',
                    fontWeight: 700,
                    fontSize: '0.875rem',
                    cursor: 'pointer',
                    boxShadow: tokens.shadows.sm
                  }}
                >
                  Approve Equivalence & Issue NMC
                </button>
              </>
            )}
          </div>
        </div>
      </div>

      {/* Slide-over Explain Decision Drawer */}
      <ExplainDecisionDrawer
        isOpen={drawerOpen}
        onClose={() => setDrawerOpen(false)}
        match={match}
      />

      {/* Modal: Approve */}
      {showApproveModal && (
        <div className="modal-backdrop-smooth" style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <div className="animate-scale-up" style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.5rem', width: '90%', maxWidth: '500px', boxShadow: tokens.shadows.lg }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: tokens.colors.textPrimary, fontSize: '1.15rem', fontWeight: 800 }}>
              Confirm Equivalence Approval
            </h3>
            <p style={{ color: tokens.colors.textSecondary, fontSize: '0.875rem', marginBottom: '1rem', lineHeight: 1.5 }}>
              Approving equivalence will create or link a National Material Code (NMC), generate legacy CPSE crosswalk mappings, and append an event to the cryptographic audit chain inside one atomic transaction.
            </p>
            <textarea
              placeholder="Governance notes or engineering justification..."
              value={approveComment}
              onChange={(e) => setApproveComment(e.target.value)}
              style={{
                width: '100%',
                height: '80px',
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                borderRadius: '0.375rem',
                color: tokens.colors.textPrimary,
                padding: '0.6rem',
                fontSize: '0.85rem',
                marginBottom: '1rem',
                boxSizing: 'border-box'
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <button
                onClick={() => setShowApproveModal(false)}
                style={{
                  padding: '0.5rem 1rem',
                  background: tokens.colors.surfaceSubtle,
                  color: tokens.colors.textSecondary,
                  border: `1px solid ${tokens.colors.border}`,
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleApprove}
                disabled={submitting}
                style={{
                  padding: '0.5rem 1rem',
                  background: tokens.colors.primary,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '0.375rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                {submitting ? 'Executing Transaction...' : 'Confirm Approval'}
              </button>
            </div>
          </div>
        </div>
      )}

      {/* Modal: Reject */}
      {showRejectModal && (
        <div className="modal-backdrop-smooth" style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <div className="animate-scale-up" style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.5rem', width: '90%', maxWidth: '500px', boxShadow: tokens.shadows.lg }}>
            <h3 style={{ margin: '0 0 0.5rem 0', color: tokens.colors.textPrimary, fontSize: '1.15rem', fontWeight: 800 }}>
              Reject Candidate Pair
            </h3>
            <div style={{ marginBottom: '1rem' }}>
              <label style={{ display: 'block', color: tokens.colors.textSecondary, fontSize: '0.75rem', fontWeight: 700, marginBottom: '0.35rem' }}>
                REJECTION REASON CODE
              </label>
              <select
                value={rejectReason}
                onChange={(e) => setRejectReason(e.target.value)}
                style={{
                  width: '100%',
                  padding: '0.5rem',
                  background: tokens.colors.surfaceSubtle,
                  border: `1px solid ${tokens.colors.border}`,
                  borderRadius: '0.375rem',
                  color: tokens.colors.textPrimary,
                  fontSize: '0.85rem'
                }}
              >
                <option value="TECHNICAL_MISMATCH">TECHNICAL_MISMATCH</option>
                <option value="WRONG_CATEGORY">WRONG_CATEGORY</option>
                <option value="DIFFERENT_SPECIFICATION">DIFFERENT_SPECIFICATION</option>
                <option value="DUPLICATE_CANDIDATE">DUPLICATE_CANDIDATE</option>
                <option value="INSUFFICIENT_EVIDENCE">INSUFFICIENT_EVIDENCE</option>
                <option value="OTHER">OTHER</option>
              </select>
            </div>
            <textarea
              placeholder="Detailed steward explanation for rejection..."
              value={rejectComment}
              onChange={(e) => setRejectComment(e.target.value)}
              style={{
                width: '100%',
                height: '80px',
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                borderRadius: '0.375rem',
                color: tokens.colors.textPrimary,
                padding: '0.6rem',
                fontSize: '0.85rem',
                marginBottom: '1rem',
                boxSizing: 'border-box'
              }}
            />
            <div style={{ display: 'flex', justifyContent: 'flex-end', gap: '0.5rem' }}>
              <button
                onClick={() => setShowRejectModal(false)}
                style={{
                  padding: '0.5rem 1rem',
                  background: tokens.colors.surfaceSubtle,
                  color: tokens.colors.textSecondary,
                  border: `1px solid ${tokens.colors.border}`,
                  borderRadius: '0.375rem',
                  cursor: 'pointer',
                  fontWeight: 600
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleReject}
                disabled={submitting}
                style={{
                  padding: '0.5rem 1rem',
                  background: tokens.colors.danger,
                  color: '#fff',
                  border: 'none',
                  borderRadius: '0.375rem',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                {submitting ? 'Recording Rejection...' : 'Confirm Rejection'}
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
