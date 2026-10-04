'use client';

import React, { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import AppShell from '../components/AppShell';
import { tokens } from '../components/design-system/tokens';
import {
  GitPullRequest,
  Search,
  Filter,
  AlertTriangle,
  CheckCircle,
  XCircle,
  ArrowRight,
  ShieldCheck,
  RefreshCw,
  HelpCircle,
  CheckCircle2,
  AlertCircle,
  Tag
} from 'lucide-react';
import { BoltFastenerIllustration } from '../components/illustrations/IndustrialIcons';

interface MaterialDTO {
  id: string;
  cpse_code: string;
  source_code: string;
  raw_description: string;
  normalized_text: string;
  category_code: string;
}

interface PairResultDTO {
  id: string;
  run_id: string;
  material_a: MaterialDTO;
  material_b: MaterialDTO;
  relationship: string;
  equivalence_confidence: number;
  raw_score: number;
  review_status: string;
  signals?: {
    semantic?: number;
    lexical?: number;
    attribute?: number;
    attribute_compatibility?: number;
    raw_score?: number;
  } | null;
  veto?: { applied: boolean; gate_id?: string; reason?: string } | null;
  explanation?: string | null;
}

export default function ReviewsPage() {
  const { token } = useAuth();
  const router = useRouter();

  const [reviews, setReviews] = useState<PairResultDTO[]>([]);
  const [summaryCounts, setSummaryCounts] = useState<{
    total: number;
    conflict: number;
    unknown: number;
    safe_equiv: number;
    low_conf: number;
  } | null>(null);
  const [statusTab, setStatusTab] = useState<string>('PROPOSED');
  const [categoryFilter, setCategoryFilter] = useState<string>('');
  const [cpseFilter, setCpseFilter] = useState<string>('');
  const [searchQuery, setSearchQuery] = useState<string>('');
  const [hasVetoFilter, setHasVetoFilter] = useState<boolean | null>(null);
  const [selectedQuickFilter, setSelectedQuickFilter] = useState<string>('ALL');
  const [loading, setLoading] = useState(true);

  const fetchReviews = async () => {
    if (!token) return;
    setLoading(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const params = new URLSearchParams();
      if (statusTab !== 'ALL') params.append('review_status', statusTab);
      if (categoryFilter) params.append('category', categoryFilter);
      if (cpseFilter) params.append('cpse_code', cpseFilter);
      if (searchQuery) params.append('search', searchQuery);
      if (hasVetoFilter !== null) params.append('has_veto', String(hasVetoFilter));
      params.append('page_size', '80');

      const [resReviews, resCounts] = await Promise.all([
        fetch(`${apiHost}/api/v1/reviews?${params.toString()}`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${apiHost}/api/v1/reviews/summary/counts`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (resReviews.ok) {
        const data = await resReviews.json();
        setReviews(data);
      }
      if (resCounts.ok) {
        const countsData = await resCounts.json();
        setSummaryCounts(countsData);
      }
    } catch (e) {
      console.error('Error fetching review queue', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchReviews();
  }, [token, statusTab, categoryFilter, cpseFilter, hasVetoFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchReviews();
  };

  // Filter based on quick chip selection
  const filteredReviews = reviews.filter((item) => {
    const isConflict = item.relationship === 'NOT_EQUIVALENT' || item.veto?.gate_id === 'G1' || item.veto?.gate_id === 'G2' || item.veto?.gate_id === 'G3';
    const isUnknown = item.relationship === 'REVIEW_REQUIRED' || item.veto?.gate_id === 'G4' || item.veto?.gate_id === 'G5' || item.veto?.gate_id === 'G6';
    const isSafe = item.relationship === 'EQUIVALENT' || item.relationship === 'FUNCTIONALLY_EQUIVALENT' || item.relationship === 'EXACT_DUPLICATE' || item.relationship === 'NEAR_DUPLICATE';

    if (selectedQuickFilter === 'CONFLICT') {
      return isConflict;
    }
    if (selectedQuickFilter === 'UNKNOWN') {
      return isUnknown;
    }
    if (selectedQuickFilter === 'LOW_CONF') {
      return item.equivalence_confidence > 0 && item.equivalence_confidence < 0.70 && !isConflict && !isUnknown;
    }
    if (selectedQuickFilter === 'EQUIVALENT') {
      return isSafe;
    }
    return true;
  });

  const getRelationshipBadge = (rel: string, gateId?: string) => {
    if (rel === 'NOT_EQUIVALENT' || gateId === 'G1' || gateId === 'G2' || gateId === 'G3') {
      return {
        label: 'CRITICAL CONFLICT',
        icon: <XCircle style={{ width: '13px', height: '13px' }} />,
        bg: '#FEE2E2',
        color: tokens.colors.danger,
        border: '#FECACA'
      };
    }
    if (rel === 'REVIEW_REQUIRED' || gateId === 'G4' || gateId === 'G5' || gateId === 'G6') {
      return {
        label: 'UNKNOWN ATTRIBUTE / REVIEW',
        icon: <AlertTriangle style={{ width: '13px', height: '13px' }} />,
        bg: '#FEF3C7',
        color: tokens.colors.warning,
        border: '#FDE68A'
      };
    }
    if (rel === 'FUNCTIONALLY_EQUIVALENT' || rel === 'EQUIVALENT' || rel === 'EXACT_DUPLICATE' || rel === 'NEAR_DUPLICATE') {
      return {
        label: 'SAFE EQUIVALENT',
        icon: <CheckCircle2 style={{ width: '13px', height: '13px' }} />,
        bg: '#DCFCE7',
        color: tokens.colors.success,
        border: '#BBF7D0'
      };
    }
    return {
      label: 'LOW CONFIDENCE / RELATED',
      icon: <HelpCircle style={{ width: '13px', height: '13px' }} />,
      bg: '#FEF9C3',
      color: '#A16207',
      border: '#FDE047'
    };
  };

  return (
    <AppShell>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{
            width: '48px',
            height: '48px',
            borderRadius: '0.625rem',
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0
          }}>
            <BoltFastenerIllustration style={{ width: '38px', height: '38px' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
                REVIEW QUEUE
              </h2>
              <span style={{
                fontSize: '0.8rem',
                fontWeight: 800,
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                background: '#DCFCE7',
                color: tokens.colors.primary,
                border: `1px solid #BBF7D0`
              }}>
                {reviews.length} ITEMS DETECTED
              </span>
            </div>
            <p style={{ margin: '0.25rem 0 0 0', color: tokens.colors.textSecondary, fontSize: '0.875rem' }}>
              Multi-CPSE candidate pairs awaiting human stewardship & National Material Code issuance
            </p>
          </div>
        </div>

        <button
          onClick={fetchReviews}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            padding: '0.5rem 1rem',
            background: tokens.colors.surface,
            color: tokens.colors.primary,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.5rem',
            fontWeight: 700,
            fontSize: '0.85rem',
            cursor: 'pointer',
            boxShadow: tokens.shadows.sm
          }}
        >
          <RefreshCw style={{ width: '15px', height: '15px', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
          Refresh Queue
        </button>
      </div>

      {/* Accessible Category Chips (Text + Icon) */}
      <div style={{
        display: 'flex',
        gap: '0.6rem',
        flexWrap: 'wrap',
        marginBottom: '1.25rem',
        padding: '0.75rem',
        background: tokens.colors.surface,
        borderRadius: '0.75rem',
        border: `1px solid ${tokens.colors.border}`
      }}>
        {[
          { id: 'ALL', label: 'ALL CANDIDATES', icon: '⚡', count: summaryCounts?.total ?? reviews.length },
          {
            id: 'CONFLICT',
            label: '🔴 CRITICAL CONFLICT',
            icon: '✕',
            count: summaryCounts?.conflict ?? reviews.filter((r) => r.relationship === 'NOT_EQUIVALENT' || r.veto?.gate_id === 'G1' || r.veto?.gate_id === 'G2' || r.veto?.gate_id === 'G3').length
          },
          {
            id: 'UNKNOWN',
            label: '🟠 UNKNOWN ATTRIBUTE',
            icon: '⚠',
            count: summaryCounts?.unknown ?? reviews.filter((r) => r.relationship === 'REVIEW_REQUIRED' || r.veto?.gate_id === 'G4' || r.veto?.gate_id === 'G5' || r.veto?.gate_id === 'G6').length
          },
          {
            id: 'LOW_CONF',
            label: '🟡 LOW CONFIDENCE',
            icon: '⚡',
            count: summaryCounts?.low_conf ?? reviews.filter((r) => r.equivalence_confidence > 0 && r.equivalence_confidence < 0.70 && r.relationship !== 'NOT_EQUIVALENT' && r.relationship !== 'REVIEW_REQUIRED').length
          },
          {
            id: 'EQUIVALENT',
            label: '🟢 SAFE EQUIVALENT',
            icon: '✓',
            count: summaryCounts?.safe_equiv ?? reviews.filter((r) => r.relationship === 'EQUIVALENT' || r.relationship === 'FUNCTIONALLY_EQUIVALENT' || r.relationship === 'EXACT_DUPLICATE' || r.relationship === 'NEAR_DUPLICATE').length
          }
        ].map((chip) => {
          const isActive = selectedQuickFilter === chip.id;
          return (
            <button
              key={chip.id}
              onClick={() => setSelectedQuickFilter(chip.id)}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.4rem 0.85rem',
                borderRadius: '0.5rem',
                fontSize: '0.8rem',
                fontWeight: 700,
                border: `1px solid ${isActive ? tokens.colors.primary : tokens.colors.border}`,
                background: isActive ? '#DCFCE7' : tokens.colors.surfaceSubtle,
                color: isActive ? tokens.colors.primary : tokens.colors.textSecondary,
                cursor: 'pointer',
                transition: 'all 0.15s ease'
              }}
            >
              <span>{chip.label}</span>
              <span style={{
                background: isActive ? tokens.colors.primary : tokens.colors.border,
                color: isActive ? '#fff' : tokens.colors.textSecondary,
                borderRadius: '9999px',
                padding: '0.1rem 0.4rem',
                fontSize: '0.7rem',
                fontWeight: 800
              }}>
                {chip.count}
              </span>
            </button>
          );
        })}
      </div>

      {/* Status Tabs */}
      <div style={{ display: 'flex', gap: '0.5rem', borderBottom: `2px solid ${tokens.colors.border}`, paddingBottom: '0.75rem', marginBottom: '1.25rem' }}>
        {[
          { id: 'PROPOSED', label: 'Pending Review' },
          { id: 'APPROVED', label: 'Approved (NMC Issued)' },
          { id: 'REJECTED', label: 'Rejected' },
          { id: 'REMAP_REQUIRED', label: 'Remap Required' },
          { id: 'ALL', label: 'All Pairs' }
        ].map((tab) => (
          <button
            key={tab.id}
            onClick={() => setStatusTab(tab.id)}
            style={{
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              border: 'none',
              background: statusTab === tab.id ? tokens.colors.primary : 'transparent',
              color: statusTab === tab.id ? '#ffffff' : tokens.colors.textSecondary,
              fontWeight: statusTab === tab.id ? 700 : 500,
              fontSize: '0.875rem',
              cursor: 'pointer',
              transition: 'all 0.15s'
            }}
          >
            {tab.label}
          </button>
        ))}
      </div>

      {/* Filter Bar */}
      <div style={{
        background: tokens.colors.surface,
        border: `1px solid ${tokens.colors.border}`,
        borderRadius: '0.75rem',
        padding: '1rem',
        marginBottom: '1.5rem',
        display: 'flex',
        flexWrap: 'wrap',
        gap: '1rem',
        alignItems: 'center',
        boxShadow: tokens.shadows.sm
      }}>
        <form onSubmit={handleSearchSubmit} style={{ flex: 1, minWidth: '240px', display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', width: '16px', height: '16px', color: tokens.colors.textSecondary }} />
            <input
              type="text"
              placeholder="Search source codes or description..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              style={{
                width: '100%',
                padding: '0.5rem 0.75rem 0.5rem 2.25rem',
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                borderRadius: '0.375rem',
                color: tokens.colors.textPrimary,
                fontSize: '0.875rem',
                boxSizing: 'border-box'
              }}
            />
          </div>
          <button
            type="submit"
            style={{
              padding: '0.5rem 1rem',
              background: tokens.colors.primary,
              color: '#fff',
              border: 'none',
              borderRadius: '0.375rem',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            Filter
          </button>
        </form>

        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
          style={{
            padding: '0.5rem 0.75rem',
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.375rem',
            color: tokens.colors.textPrimary,
            fontSize: '0.875rem'
          }}
        >
          <option value="">All Categories</option>
          <option value="BOLT">BOLT</option>
          <option value="PIPE">PIPE</option>
          <option value="BEARING">BEARING</option>
          <option value="VALVE">VALVE</option>
          <option value="GASKET">GASKET</option>
          <option value="CABLE">CABLE</option>
        </select>

        <select
          value={hasVetoFilter === null ? '' : String(hasVetoFilter)}
          onChange={(e) => {
            const val = e.target.value;
            setHasVetoFilter(val === '' ? null : val === 'true');
          }}
          style={{
            padding: '0.5rem 0.75rem',
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.375rem',
            color: tokens.colors.textPrimary,
            fontSize: '0.875rem'
          }}
        >
          <option value="">All Gate States</option>
          <option value="true">Safety Gate Vetoed Only</option>
          <option value="false">All Gates Passed</option>
        </select>
      </div>

      {/* Review Cards List */}
      {loading ? (
        <div style={{ textAlign: 'center', padding: '3rem', color: tokens.colors.textSecondary }}>
          <div style={{
            width: '36px',
            height: '36px',
            border: `3px solid ${tokens.colors.border}`,
            borderTop: `3px solid ${tokens.colors.primary}`,
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem auto'
          }} />
          <p style={{ fontWeight: 600 }}>Loading candidate pair matches...</p>
        </div>
      ) : filteredReviews.length === 0 ? (
        <div style={{
          background: tokens.colors.surface,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '0.75rem',
          padding: '3rem',
          textAlign: 'center',
          color: tokens.colors.textSecondary,
          boxShadow: tokens.shadows.sm
        }}>
          <GitPullRequest style={{ width: '40px', height: '40px', margin: '0 auto 1rem auto', color: tokens.colors.border }} />
          <h3 style={{ color: tokens.colors.textPrimary, margin: '0 0 0.5rem 0', fontWeight: 700 }}>No Review Pairs Found</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>No matches fit the selected filter criteria or review status tab.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {filteredReviews.map((match) => {
            const isConflict = match.relationship === 'NOT_EQUIVALENT' || match.veto?.gate_id === 'G1' || match.veto?.gate_id === 'G2' || match.veto?.gate_id === 'G3';
            const isUnknown = match.relationship === 'REVIEW_REQUIRED' || match.veto?.gate_id === 'G4' || match.veto?.gate_id === 'G5' || match.veto?.gate_id === 'G6';
            const isSafe = match.relationship === 'FUNCTIONALLY_EQUIVALENT' || match.relationship === 'EQUIVALENT' || match.relationship === 'EXACT_DUPLICATE' || match.relationship === 'NEAR_DUPLICATE';
            const badge = getRelationshipBadge(match.relationship, match.veto?.gate_id);
            const simPct = Math.round(match.raw_score * 100);

            // Primary reason detection
            let reasonText = 'All mechanical properties match identically';
            if (isConflict) {
              reasonText = match.veto?.reason || `Gate ${match.veto?.gate_id || 'G2'} Property Class / Grade Conflict`;
            } else if (isUnknown) {
              reasonText = match.veto?.reason ? `${match.veto.reason} — Human steward review required` : 'Critical attribute missing in source text — human review required';
            } else if (match.equivalence_confidence < 0.70) {
              reasonText = 'Low matching confidence across specification attributes';
            }

            const cardBorder = isConflict ? '#FECACA' : isUnknown ? '#FDE68A' : isSafe ? '#BBF7D0' : tokens.colors.border;

            return (
              <div
                key={match.id}
                style={{
                  background: tokens.colors.surface,
                  border: `1px solid ${cardBorder}`,
                  borderRadius: '0.75rem',
                  padding: '1.25rem',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  gap: '1.5rem',
                  boxShadow: tokens.shadows.sm,
                  transition: 'border-color 0.2s, box-shadow 0.2s'
                }}
              >
                {/* Left Side: Side-by-Side Materials */}
                <div style={{ flex: 1, display: 'grid', gridTemplateColumns: '1fr auto 1fr', gap: '1rem', alignItems: 'center' }}>
                  {/* Material A */}
                  <div style={{
                    background: tokens.colors.surfaceSubtle,
                    borderRadius: '0.5rem',
                    padding: '0.875rem',
                    border: `1px solid ${tokens.colors.border}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 800, padding: '0.15rem 0.45rem', background: 'var(--surface-3)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '0.25rem' }}>
                        {match.material_a.cpse_code}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)', fontWeight: 700 }}>
                        {match.material_a.source_code}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: tokens.colors.textPrimary, fontWeight: 600, lineHeight: '1.4' }}>
                      {match.material_a.raw_description}
                    </p>
                    <div style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary, marginTop: '0.35rem' }}>
                      Category: <strong>{match.material_a.category_code}</strong>
                    </div>
                  </div>

                  <div style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: '0.2rem'
                  }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, color: tokens.colors.textSecondary }}>VS</span>
                    <ArrowRight style={{ width: '16px', height: '16px', color: tokens.colors.textSecondary }} />
                  </div>

                  {/* Material B */}
                  <div style={{
                    background: tokens.colors.surfaceSubtle,
                    borderRadius: '0.5rem',
                    padding: '0.875rem',
                    border: `1px solid ${tokens.colors.border}`
                  }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.35rem' }}>
                      <span style={{ fontSize: '0.7rem', fontWeight: 800, padding: '0.15rem 0.45rem', background: 'var(--surface-3)', color: 'var(--text-primary)', border: '1px solid var(--border)', borderRadius: '0.25rem' }}>
                        {match.material_b.cpse_code}
                      </span>
                      <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: 'var(--text-secondary)', fontWeight: 700 }}>
                        {match.material_b.source_code}
                      </span>
                    </div>
                    <p style={{ margin: 0, fontSize: '0.875rem', color: tokens.colors.textPrimary, fontWeight: 600, lineHeight: '1.4' }}>
                      {match.material_b.raw_description}
                    </p>
                    <div style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary, marginTop: '0.35rem' }}>
                      Category: <strong>{match.material_b.category_code}</strong>
                    </div>
                  </div>
                </div>

                {/* Right Side: Verdict, Reason & Action */}
                <div style={{ minWidth: '240px', display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                    <span style={{
                      fontSize: '0.725rem',
                      padding: '0.25rem 0.6rem',
                      borderRadius: '0.375rem',
                      background: badge.bg,
                      color: badge.color,
                      border: `1px solid ${badge.border}`,
                      fontWeight: 800,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.35rem'
                    }}>
                      {badge.icon}
                      {badge.label}
                    </span>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end', gap: '0.2rem' }}>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.85rem', fontWeight: 800 }}>
                        <span style={{ fontSize: '0.7rem', color: tokens.colors.textMuted }}>Equiv:</span>
                        <span style={{ color: isConflict ? tokens.colors.danger : isSafe ? tokens.colors.success : tokens.colors.textPrimary }}>
                          {Math.round(match.equivalence_confidence * 100)}%
                        </span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.675rem', color: tokens.colors.textSecondary }}>
                        <span>Sem: <strong>{match.signals?.semantic ? Math.round(match.signals.semantic * 100) : 0}%</strong></span>
                        <span>&bull;</span>
                        <span>Lex: <strong>{match.signals?.lexical ? Math.round(match.signals.lexical * 100) : 0}%</strong></span>
                        <span>&bull;</span>
                        <span>Attr: <strong>{match.signals?.attribute_compatibility ? Math.round(match.signals.attribute_compatibility * 100) : 0}%</strong></span>
                      </div>
                    </div>
                  </div>

                  {/* Primary reason callout */}
                  <div style={{
                    fontSize: '0.75rem',
                    color: isConflict ? tokens.colors.danger : isUnknown ? tokens.colors.warning : isSafe ? tokens.colors.success : tokens.colors.textSecondary,
                    textAlign: 'right',
                    maxWidth: '240px',
                    lineHeight: 1.3,
                    fontWeight: (isConflict || isUnknown || isSafe) ? 600 : 400
                  }}>
                    {isConflict ? `⛔ ${reasonText}` : isUnknown ? `⚠ ${reasonText}` : isSafe ? `✓ ${reasonText}` : reasonText}
                  </div>

                  <button
                    onClick={() => router.push(`/reviews/${match.id}`)}
                    style={{
                      marginTop: '0.35rem',
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.4rem',
                      padding: '0.55rem 1rem',
                      background: tokens.colors.primary,
                      color: '#ffffff',
                      border: 'none',
                      borderRadius: '0.375rem',
                      fontSize: '0.825rem',
                      fontWeight: 700,
                      cursor: 'pointer',
                      boxShadow: tokens.shadows.sm,
                      transition: 'background 0.15s'
                    }}
                  >
                    <span>INSPECT EVIDENCE</span>
                    <ArrowRight style={{ width: '14px', height: '14px' }} />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
