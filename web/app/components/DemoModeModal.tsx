'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { tokens } from './design-system/tokens';
import { 
  Sparkles, X, ArrowRight, Layers, BarChart3, RefreshCw, FileCheck, Play
} from 'lucide-react';

interface DemoModeModalProps {
  isOpen: boolean;
  onClose: () => void;
  onOpenMatchModal?: () => void;
}

export default function DemoModeModal({ isOpen, onClose, onOpenMatchModal }: DemoModeModalProps) {
  const router = useRouter();
  const { token } = useAuth();
  const { theme } = useTheme();
  const isDark = theme === 'dark';
  const [scenarios, setScenarios] = useState<any | null>(null);
  const [loading, setLoading] = useState(false);

  const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  useEffect(() => {
    if (!isOpen) return;
    const fetchScenarios = async () => {
      setLoading(true);
      try {
        const res = await fetch(`${apiHost}/api/v1/meta/demo-scenarios`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {}
        });
        if (res.ok) {
          const data = await res.json();
          setScenarios(data.scenarios);
        }
      } catch (e) {
        console.error('Error loading demo scenarios', e);
      } finally {
        setLoading(false);
      }
    };
    fetchScenarios();
  }, [isOpen, token, apiHost]);

  if (!isOpen) return null;

  const navigateTo = (path: string) => {
    onClose();
    router.push(path);
  };

  const trap88 = scenarios?.trap_88_109;
  const trapUnknown = scenarios?.trap_unknown;
  const safeEquiv = scenarios?.safe_equivalent;

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: isDark ? 'rgba(0, 0, 0, 0.70)' : 'rgba(15, 23, 42, 0.65)',
      backdropFilter: 'blur(6px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 70,
      padding: '1.5rem'
    }}>
      <div style={{
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: '0.75rem',
        width: '100%',
        maxWidth: '860px',
        maxHeight: '90vh',
        boxShadow: isDark ? '0 25px 50px -12px rgba(0, 0, 0, 0.8)' : '0 25px 50px -12px rgba(15, 23, 42, 0.25)',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: '1px solid var(--border)',
          background: isDark ? 'linear-gradient(135deg, #171717 0%, #1e1e1e 100%)' : 'linear-gradient(135deg, #166534 0%, #15803d 100%)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '0.5rem',
              background: isDark ? '#111111' : '#FFFFFF',
              border: isDark ? '1px solid var(--border)' : 'none',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: isDark ? '#FACC15' : '#166534'
            }}>
              <Sparkles style={{ width: '20px', height: '20px' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <h3 style={{ margin: 0, fontSize: '1.15rem', fontWeight: 800, color: isDark ? '#F5F5F5' : '#FFFFFF' }}>
                  SIH 2026 Golden Path Demo Walkthrough
                </h3>
                <span style={{ fontSize: '0.65rem', background: '#DC2626', color: '#FFFFFF', padding: '0.1rem 0.45rem', borderRadius: '0.2rem', fontWeight: 800, letterSpacing: '0.05em' }}>
                  LIVE DEMO
                </span>
              </div>
              <p style={{ margin: 0, fontSize: '0.775rem', color: isDark ? '#A3A3A3' : '#DCFCE7' }}>
                Curated competition walkthrough of AI matching, safety gates, NMC generation, ERP sync, and audit trails.
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            aria-label="Close Demo Tour"
            style={{ background: isDark ? 'rgba(255, 255, 255, 0.08)' : 'rgba(255, 255, 255, 0.2)', border: 'none', color: '#FFFFFF', cursor: 'pointer', padding: '0.35rem', borderRadius: '0.375rem', display: 'flex', alignItems: 'center', justifyContent: 'center' }}
          >
            <X style={{ width: '20px', height: '20px' }} />
          </button>
        </div>

        {/* Modal Body - Scenarios Cards */}
        <div style={{ padding: '1.5rem', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '0.875rem', background: 'var(--background)' }}>
          
          {/* Step 1: Trigger Matching Engine */}
          <div style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: isDark ? '#FACC15' : '#0284c7', color: isDark ? '#080808' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                1
              </div>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 700 }}>
                  AI Matching & Hybrid pgvector Retrieval
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Execute an end-to-end match run over PostgreSQL materials using MiniLM embeddings and candidate blocking (95.5% reduction).
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                onClose();
                if (onOpenMatchModal) onOpenMatchModal();
                else router.push('/governance');
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: isDark ? '#FACC15' : '#0284c7',
                color: isDark ? '#080808' : '#fff',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              <Play style={{ width: '13px', height: '13px' }} />
              Trigger Engine
            </button>
          </div>

          {/* Step 2: Trap 1 - 8.8 vs 10.9 Property Class Veto */}
          <div style={{
            background: 'var(--danger-bg)',
            border: '1px solid var(--danger-border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(220,38,38,0.06)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#DC2626', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                2
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                  <h4 style={{ margin: 0, color: isDark ? '#FCA5A5' : '#991B1B', fontSize: '0.9rem', fontWeight: 700 }}>
                    Hero Scenario: Grade 8.8 vs 10.9 Conflict (Gate G2)
                  </h4>
                  <span style={{ fontSize: '0.65rem', background: '#DC2626', color: '#FFFFFF', padding: '0.1rem 0.35rem', borderRadius: '0.2rem', fontWeight: 700 }}>
                    HARD VETO
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.75rem', color: isDark ? '#F87171' : '#7F1D1D' }}>
                  Two bolts have 96% semantic similarity, but Gate G2 strictly blocks equivalence due to critical tensile property conflict (confidence forced to 0.00).
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                if (trap88?.match_id) {
                  navigateTo(`/reviews/${trap88.match_id}`);
                } else {
                  navigateTo('/reviews?relationship=NOT_EQUIVALENT');
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: '#DC2626',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              Inspect 8.8 vs 10.9 Evidence
              <ArrowRight style={{ width: '13px', height: '13px' }} />
            </button>
          </div>

          {/* Step 3: Trap 2 - UNKNOWN Missing Grade Gate */}
          <div style={{
            background: 'var(--warning-bg)',
            border: '1px solid var(--warning-border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(217,119,6,0.06)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#D97706', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                3
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                  <h4 style={{ margin: 0, color: isDark ? '#FCD34D' : '#92400E', fontSize: '0.9rem', fontWeight: 700 }}>
                    Missing Attribute Scenario: Unknown Spec (Gate G4)
                  </h4>
                  <span style={{ fontSize: '0.65rem', background: '#D97706', color: '#FFFFFF', padding: '0.1rem 0.35rem', borderRadius: '0.2rem', fontWeight: 700 }}>
                    REVIEW REQUIRED
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.75rem', color: isDark ? '#FBBF24' : '#B45309' }}>
                  When a critical property class cannot be established, Gate G4 strictly forces status to REVIEW_REQUIRED. Unsafe auto-acceptance is blocked.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                if (trapUnknown?.match_id) {
                  navigateTo(`/reviews/${trapUnknown.match_id}`);
                } else {
                  navigateTo('/reviews?relationship=REVIEW_REQUIRED');
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: '#D97706',
                color: '#FFFFFF',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              Inspect UNKNOWN Case
              <ArrowRight style={{ width: '13px', height: '13px' }} />
            </button>
          </div>

          {/* Step 4: True Equivalence & Atomic NMC Generation */}
          <div style={{
            background: 'var(--success-bg)',
            border: '1px solid var(--success-border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(22,101,52,0.06)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: isDark ? '#22C55E' : '#166534', color: isDark ? '#080808' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                4
              </div>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
                  <h4 style={{ margin: 0, color: isDark ? '#86EFAC' : '#166534', fontSize: '0.9rem', fontWeight: 700 }}>
                    True Equivalence & Atomic NMC Issuance
                  </h4>
                  <span style={{ fontSize: '0.65rem', background: isDark ? '#22C55E' : '#166534', color: isDark ? '#080808' : '#DCFCE7', padding: '0.1rem 0.35rem', borderRadius: '0.2rem', fontWeight: 700 }}>
                    ISO 7064 CHECK DIGIT
                  </span>
                </div>
                <p style={{ margin: 0, fontSize: '0.75rem', color: isDark ? '#4ADE80' : '#15803D' }}>
                  Steward approves true technical equivalent. Generates deterministic National Material Code (NMC), creates legacy mappings, and records to audit hash chain in a single atomic transaction.
                </p>
              </div>
            </div>
            <button
              onClick={() => {
                if (safeEquiv?.match_id) {
                  navigateTo(`/reviews/${safeEquiv.match_id}`);
                } else {
                  navigateTo('/reviews?relationship=FUNCTIONALLY_EQUIVALENT');
                }
              }}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: isDark ? '#22C55E' : '#166534',
                color: isDark ? '#080808' : '#fff',
                border: 'none',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              Open Safe Equivalence Pair
              <ArrowRight style={{ width: '13px', height: '13px' }} />
            </button>
          </div>

          {/* Step 5: National Registry & Legacy Crosswalk */}
          <div style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#7C3AED', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                5
              </div>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 700 }}>
                  National Material Master & Crosswalk
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Inspect standardized National Material records, spec-fingerprints, and multi-CPSE legacy code crosswalk mappings.
                </p>
              </div>
            </div>
            <button
              onClick={() => navigateTo('/national-materials')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: 'var(--surface-2)',
                color: isDark ? '#C4B5FD' : '#6D28D9',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              <Layers style={{ width: '13px', height: '13px' }} />
              National Registry
            </button>
          </div>

          {/* Step 6: Procurement Consolidation Analytics */}
          <div style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#0284c7', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                6
              </div>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 700 }}>
                  Procurement Intelligence & Joint Tendering
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Real SQL-derived metrics calculating shared National Material Codes across CPSEs, mapping coverage %, and bulk procurement opportunities.
                </p>
              </div>
            </div>
            <button
              onClick={() => navigateTo('/analytics')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: 'var(--surface-2)',
                color: isDark ? '#7DD3FC' : '#0369A1',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              <BarChart3 style={{ width: '13px', height: '13px' }} />
              Analytics
            </button>
          </div>

          {/* Step 7: Mock SAP S/4HANA ERP Outbound Sync */}
          <div style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: '#D97706', color: '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                7
              </div>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 700 }}>
                  Simulated SAP S/4HANA ERP Outbound Sync
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Simulated outbound synchronization of National Materials to SAP BAPI format with strict 40-character description truncation.
                </p>
              </div>
            </div>
            <button
              onClick={() => navigateTo('/integration')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: 'var(--surface-2)',
                color: isDark ? '#FDE68A' : '#B45309',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              <RefreshCw style={{ width: '13px', height: '13px' }} />
              Mock SAP Hub
            </button>
          </div>

          {/* Step 8: Cryptographic Audit Verification */}
          <div style={{
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            padding: '1rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap: '1rem',
            boxShadow: isDark ? 'none' : '0 1px 3px rgba(0,0,0,0.05)'
          }}>
            <div style={{ display: 'flex', alignItems: 'flex-start', gap: '0.75rem' }}>
              <div style={{ width: '28px', height: '28px', borderRadius: '50%', background: isDark ? '#FACC15' : '#166534', color: isDark ? '#080808' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '0.75rem', fontWeight: 800, flexShrink: 0 }}>
                8
              </div>
              <div>
                <h4 style={{ margin: '0 0 0.25rem 0', color: 'var(--text-primary)', fontSize: '0.9rem', fontWeight: 700 }}>
                  Cryptographic Audit Chain Verification
                </h4>
                <p style={{ margin: 0, fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                  Verify the append-only SHA-256 hash chain of all governance actions with live cryptographic verification.
                </p>
              </div>
            </div>
            <button
              onClick={() => navigateTo('/audit')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.45rem 0.85rem',
                background: 'var(--surface-2)',
                color: isDark ? '#FACC15' : '#166534',
                border: '1px solid var(--border)',
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                fontWeight: 700,
                cursor: 'pointer',
                whiteSpace: 'nowrap'
              }}
            >
              <FileCheck style={{ width: '13px', height: '13px' }} />
              Verify Audit
            </button>
          </div>

        </div>

        {/* Footer */}
        <div style={{
          padding: '1rem 1.5rem',
          borderTop: '1px solid var(--border)',
          background: 'var(--surface-2)',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)' }}>
            National Unified Material Master &bull; SIH 2026 Prototype
          </span>
          <button
            onClick={onClose}
            style={{
              padding: '0.45rem 1.1rem',
              background: isDark ? 'var(--surface-3)' : '#0F172A',
              color: '#FFFFFF',
              border: '1px solid var(--border)',
              borderRadius: '0.375rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            Close Tour
          </button>
        </div>
      </div>
    </div>
  );
}
