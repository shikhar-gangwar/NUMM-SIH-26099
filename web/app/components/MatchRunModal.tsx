'use client';

import React, { useState, useEffect } from 'react';
import { useAuth } from '../context/AuthContext';
import { tokens } from './design-system/tokens';
import { 
  Play, RefreshCw, CheckCircle2, AlertTriangle, ShieldAlert, 
  Layers, X, Activity, Cpu, ArrowRight, Sparkles 
} from 'lucide-react';

interface MatchRunStats {
  total_materials?: number;
  materials_processed?: number;
  candidates_retrieved?: number;
  comparisons_performed?: number;
  relationship_counts?: Record<string, number>;
  veto_count?: number;
  duration_ms?: number;
  progress_pct?: number;
  error?: string;
}

interface MatchRunDTO {
  id: string;
  scope?: any;
  mode: string;
  stats?: MatchRunStats;
  status: string;
  started_at?: string;
  finished_at?: string;
}

interface MatchRunModalProps {
  isOpen: boolean;
  onClose: () => void;
  onComplete?: () => void;
}

export default function MatchRunModal({ isOpen, onClose, onComplete }: MatchRunModalProps) {
  const { token, user } = useAuth();
  const [scopeType, setScopeType] = useState<'all' | 'cpse' | 'category' | 'demo'>('demo');
  const [cpseCode, setCpseCode] = useState('OIL');
  const [category, setCategory] = useState('BOLT');
  const [mode, setMode] = useState('LIVE');
  const [running, setRunning] = useState(false);
  const [currentRun, setCurrentRun] = useState<MatchRunDTO | null>(null);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isResetting, setIsResetting] = useState(false);

  const isReviewer = user && user.role !== 'SUPER_ADMIN' && user.role !== 'DATA_STEWARD';

  const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  // Check for currently running job when opening modal
  useEffect(() => {
    if (!isOpen || !token) return;
    checkActiveStatus();
  }, [isOpen, token]);

  const checkActiveStatus = async () => {
    try {
      const res = await fetch(`${apiHost}/api/v1/matching/status/active`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        if (data.is_active && data.current_run) {
          setCurrentRun(data.current_run);
          setRunning(true);
        } else if (data.last_completed_run && !currentRun) {
          setCurrentRun(data.last_completed_run);
        }
      }
    } catch (e) {
      console.error('Error fetching active match run status', e);
    }
  };

  // Polling loop while running - stable interval keyed on run ID
  useEffect(() => {
    if (!running || !currentRun?.id || !token) return;

    let isMounted = true;
    const interval = setInterval(async () => {
      try {
        const res = await fetch(`${apiHost}/api/v1/matching/runs/${currentRun.id}`, {
          headers: { Authorization: `Bearer ${token}` }
        });
        if (res.ok && isMounted) {
          const runData: MatchRunDTO = await res.json();
          setCurrentRun(runData);

          if (runData.status === 'COMPLETED' || runData.status === 'FAILED' || runData.status === 'CANCELLED') {
            setRunning(false);
            if (onComplete && runData.status === 'COMPLETED') {
              onComplete();
            }
          }
        }
      } catch (e) {
        console.error('Error polling run progress', e);
      }
    }, 1000);

    return () => {
      isMounted = false;
      clearInterval(interval);
    };
  }, [running, currentRun?.id, token]);

  const handleCancelRun = async () => {
    if (!token || !currentRun?.id) return;
    try {
      const res = await fetch(`${apiHost}/api/v1/matching/runs/${currentRun.id}/cancel`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setCurrentRun(data);
        setRunning(false);
        setErrorMsg(null);
      }
    } catch (e) {
      console.error('Failed to cancel run', e);
    }
  };

  const handleResetActive = async () => {
    if (!token) return;
    setIsResetting(true);
    try {
      await fetch(`${apiHost}/api/v1/matching/runs/reset-active`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      setRunning(false);
      setErrorMsg(null);
      await checkActiveStatus();
    } catch (e) {
      console.error('Failed to reset active runs', e);
    } finally {
      setIsResetting(false);
    }
  };

  const handleLaunchRun = async (force: boolean = false) => {
    if (!token) return;
    if (isReviewer) {
      setErrorMsg('Permission Denied: Only SUPER_ADMIN or DATA_STEWARD can trigger match runs.');
      return;
    }
    setErrorMsg(null);
    setRunning(true);

    let scopePayload: any = {};
    let runMode = mode;
    if (scopeType === 'demo') {
      scopePayload = { is_demo: true, demo: true };
      runMode = 'SIH_DEMO';
    } else if (scopeType === 'all') {
      scopePayload = { all: true };
    } else if (scopeType === 'cpse') {
      scopePayload = { cpse_code: cpseCode };
    } else if (scopeType === 'category') {
      scopePayload = { category: category };
    }

    try {
      const res = await fetch(`${apiHost}/api/v1/matching/runs?async_mode=true`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          Authorization: `Bearer ${token}`
        },
        body: JSON.stringify({
          scope: scopePayload,
          mode: runMode,
          force: force
        })
      });

      if (res.status === 202) {
        const runData = await res.json();
        setCurrentRun(runData);
      } else if (res.status === 409) {
        const errData = await res.json();
        const activeId = errData.detail?.active_run_id;
        setErrorMsg('A match run is already in progress. You can attach to it or reset active lock.');
        if (activeId) {
          const activeRes = await fetch(`${apiHost}/api/v1/matching/runs/${activeId}`, {
            headers: { Authorization: `Bearer ${token}` }
          });
          if (activeRes.ok) {
            const activeData = await activeRes.json();
            setCurrentRun(activeData);
          }
        }
      } else {
        const err = await res.json();
        setErrorMsg(err.detail?.message || err.detail || 'Failed to trigger match run');
        setRunning(false);
      }
    } catch (e: any) {
      setErrorMsg(e.message || 'Error triggering match run');
      setRunning(false);
    }
  };

  if (!isOpen) return null;

  const stats = currentRun?.stats;
  const progressPct = stats?.progress_pct ?? (currentRun?.status === 'COMPLETED' ? 100 : 0);

  return (
    <div style={{
      position: 'fixed',
      inset: 0,
      background: 'rgba(2, 6, 23, 0.7)',
      backdropFilter: 'blur(5px)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 50,
      padding: '1rem'
    }}>
      <div style={{
        background: tokens.colors.surface,
        border: `1px solid ${tokens.colors.border}`,
        borderRadius: '0.75rem',
        width: '100%',
        maxWidth: '680px',
        boxShadow: tokens.shadows.lg,
        overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{
          padding: '1.25rem 1.5rem',
          borderBottom: `1px solid ${tokens.colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          background: tokens.colors.surface
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <div style={{
              width: '36px',
              height: '36px',
              borderRadius: '0.5rem',
              background: tokens.colors.primaryLight,
              border: `1px solid ${tokens.colors.primaryBorder}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: tokens.colors.primary
            }}>
              <Cpu style={{ width: '20px', height: '20px' }} />
            </div>
            <div>
              <h3 style={{ margin: 0, fontSize: '1.1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                AI Matching Engine Console
              </h3>
              <p style={{ margin: 0, fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
                Hybrid pgvector HNSW retrieval + typed attribute comparators + veto lattice
              </p>
            </div>
          </div>
          <button
            onClick={onClose}
            style={{
              background: 'transparent',
              border: 'none',
              color: tokens.colors.textSecondary,
              cursor: 'pointer',
              padding: '0.25rem'
            }}
            title="Close Console"
          >
            <X style={{ width: '20px', height: '20px' }} />
          </button>
        </div>

        {/* Body */}
        <div style={{ padding: '1.5rem', maxHeight: '75vh', overflowY: 'auto' }}>
          {isReviewer && (
            <div style={{
              marginBottom: '1rem',
              padding: '0.65rem 0.85rem',
              background: tokens.colors.warningBg,
              border: `1px solid ${tokens.colors.warningBorder}`,
              borderRadius: '0.375rem',
              color: tokens.colors.warning,
              fontSize: '0.78rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}>
              <ShieldAlert style={{ width: '16px', height: '16px', flexShrink: 0 }} />
              <span>
                <strong>View-Only Inspection:</strong> You are logged in as <strong>{user?.role || 'REVIEWER'}</strong>. Initiating match runs requires SUPER_ADMIN or DATA_STEWARD credentials.
              </span>
            </div>
          )}

          {errorMsg && (
            <div style={{
              marginBottom: '1rem',
              padding: '0.75rem 1rem',
              background: tokens.colors.dangerBg,
              border: `1px solid ${tokens.colors.dangerBorder}`,
              borderRadius: '0.5rem',
              color: tokens.colors.danger,
              fontSize: '0.8rem',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.75rem',
              flexWrap: 'wrap'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <AlertTriangle style={{ width: '16px', height: '16px', flexShrink: 0 }} />
                <span>{errorMsg}</span>
              </div>
              {!isReviewer && (
                <button
                  type="button"
                  onClick={handleResetActive}
                  disabled={isResetting}
                  style={{
                    padding: '0.3rem 0.65rem',
                    background: '#ffffff',
                    color: tokens.colors.danger,
                    border: `1px solid ${tokens.colors.dangerBorder}`,
                    borderRadius: '0.25rem',
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    cursor: isResetting ? 'wait' : 'pointer'
                  }}
                >
                  {isResetting ? 'Clearing Lock...' : 'Reset Engine Lock'}
                </button>
              )}
            </div>
          )}

          {/* Scope Selection (Disabled while running) */}
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', fontSize: '0.8rem', fontWeight: 700, color: tokens.colors.textPrimary, marginBottom: '0.5rem' }}>
              Execution Scope
            </label>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', marginBottom: '0.75rem' }}>
              <button
                type="button"
                disabled={running}
                onClick={() => setScopeType('demo')}
                style={{
                  padding: '0.6rem 0.4rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.78rem',
                  fontWeight: 700,
                  cursor: running ? 'not-allowed' : 'pointer',
                  border: scopeType === 'demo' ? `1px solid ${tokens.colors.success}` : `1px solid ${tokens.colors.border}`,
                  background: scopeType === 'demo' ? tokens.colors.successBg : tokens.colors.surfaceSubtle,
                  color: scopeType === 'demo' ? tokens.colors.success : tokens.colors.textSecondary
                }}
              >
                ⚡ SIH Demo (~2s)
              </button>
              <button
                type="button"
                disabled={running}
                onClick={() => setScopeType('all')}
                style={{
                  padding: '0.6rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: running ? 'not-allowed' : 'pointer',
                  border: scopeType === 'all' ? `1px solid ${tokens.colors.primary}` : `1px solid ${tokens.colors.border}`,
                  background: scopeType === 'all' ? tokens.colors.primaryLight : tokens.colors.surfaceSubtle,
                  color: scopeType === 'all' ? tokens.colors.primary : tokens.colors.textSecondary
                }}
              >
                All Materials
              </button>
              <button
                type="button"
                disabled={running}
                onClick={() => setScopeType('cpse')}
                style={{
                  padding: '0.6rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: running ? 'not-allowed' : 'pointer',
                  border: scopeType === 'cpse' ? `1px solid ${tokens.colors.primary}` : `1px solid ${tokens.colors.border}`,
                  background: scopeType === 'cpse' ? tokens.colors.primaryLight : tokens.colors.surfaceSubtle,
                  color: scopeType === 'cpse' ? tokens.colors.primary : tokens.colors.textSecondary
                }}
              >
                By CPSE
              </button>
              <button
                type="button"
                disabled={running}
                onClick={() => setScopeType('category')}
                style={{
                  padding: '0.6rem',
                  borderRadius: '0.375rem',
                  fontSize: '0.78rem',
                  fontWeight: 600,
                  cursor: running ? 'not-allowed' : 'pointer',
                  border: scopeType === 'category' ? `1px solid ${tokens.colors.primary}` : `1px solid ${tokens.colors.border}`,
                  background: scopeType === 'category' ? tokens.colors.primaryLight : tokens.colors.surfaceSubtle,
                  color: scopeType === 'category' ? tokens.colors.primary : tokens.colors.textSecondary
                }}
              >
                By Category
              </button>
            </div>

            {scopeType === 'demo' && (
              <div style={{
                marginBottom: '0.75rem',
                padding: '0.65rem 0.85rem',
                background: tokens.colors.successBg,
                border: `1px solid ${tokens.colors.successBorder}`,
                borderRadius: '0.375rem',
                fontSize: '0.75rem',
                color: tokens.colors.success,
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem'
              }}>
                <Sparkles style={{ width: '14px', height: '14px', flexShrink: 0 }} />
                <span>
                  <strong>Deterministic SIH Speedrun:</strong> Evaluates 45 real cross-CPSE items across all 6 P0 categories through full pgvector + veto lattice in ~2 seconds.
                </span>
              </div>
            )}

            {scopeType === 'cpse' && (
              <div style={{ marginBottom: '0.75rem' }}>
                <select
                  disabled={running}
                  value={cpseCode}
                  onChange={(e) => setCpseCode(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    background: tokens.colors.surfaceSubtle,
                    border: `1px solid ${tokens.colors.border}`,
                    borderRadius: '0.375rem',
                    color: tokens.colors.textPrimary,
                    fontSize: '0.85rem'
                  }}
                >
                  <option value="OIL">OIL — Oil India Limited</option>
                  <option value="NTPC">NTPC — NTPC Limited</option>
                  <option value="IOCL">IOCL — Indian Oil Corporation Limited</option>
                  <option value="CPSE-A">CPSE-A — Thermal Power Demo</option>
                  <option value="CPSE-B">CPSE-B — Refinery & Petrochem Demo</option>
                  <option value="CPSE-C">CPSE-C — Exploration & Mining Demo</option>
                  <option value="CPSE-D">CPSE-D — Heavy Engineering Demo</option>
                </select>
              </div>
            )}

            {scopeType === 'category' && (
              <div style={{ marginBottom: '0.75rem' }}>
                <select
                  disabled={running}
                  value={category}
                  onChange={(e) => setCategory(e.target.value)}
                  style={{
                    width: '100%',
                    padding: '0.5rem 0.75rem',
                    background: tokens.colors.surfaceSubtle,
                    border: `1px solid ${tokens.colors.border}`,
                    borderRadius: '0.375rem',
                    color: tokens.colors.textPrimary,
                    fontSize: '0.85rem'
                  }}
                >
                  <option value="BOLT">BOLT — Fasteners, Studs, Hex Bolts</option>
                  <option value="PIPE">PIPE — Seamless & Welded Piping</option>
                  <option value="BEARING">BEARING — Deep Groove Ball & Roller Bearings</option>
                  <option value="VALVE">VALVE — Gate, Globe, Ball & Check Valves</option>
                  <option value="GASKET">GASKET — Spiral Wound & Flat Ring Gaskets</option>
                  <option value="CABLE">CABLE — Armoured Power & Control Cables</option>
                </select>
              </div>
            )}
          </div>

          {/* Engine Parameters Card */}
          <div style={{
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.5rem',
            padding: '0.75rem 1rem',
            marginBottom: '1.25rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            fontSize: '0.75rem',
            flexWrap: 'wrap',
            gap: '0.5rem'
          }}>
            <div>
              <span style={{ color: tokens.colors.textMuted }}>EMBEDDING MODEL: </span>
              <span style={{ color: tokens.colors.info, fontWeight: 700, fontFamily: 'monospace' }}>all-MiniLM-L6-v2 (384-d)</span>
            </div>
            <div>
              <span style={{ color: tokens.colors.textMuted }}>VECTOR RETRIEVAL: </span>
              <span style={{ color: tokens.colors.success, fontWeight: 700, fontFamily: 'monospace' }}>pgvector HNSW</span>
            </div>
            <div>
              <span style={{ color: tokens.colors.textMuted }}>SAFETY VETO: </span>
              <span style={{ color: tokens.colors.warning, fontWeight: 700, fontFamily: 'monospace' }}>G0–G6 Active</span>
            </div>
          </div>

          {/* Live Progress Card (If Run Exists) */}
          {currentRun && (
            <div style={{
              background: tokens.colors.surfaceSubtle,
              border: `1px solid ${currentRun.status === 'COMPLETED' ? tokens.colors.successBorder : currentRun.status === 'FAILED' ? tokens.colors.dangerBorder : currentRun.status === 'CANCELLED' ? tokens.colors.warningBorder : tokens.colors.infoBorder}`,
              borderRadius: '0.5rem',
              padding: '1rem',
              marginBottom: '1.25rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <Activity style={{
                    width: '16px',
                    height: '16px',
                    color: currentRun.status === 'COMPLETED' ? tokens.colors.success : currentRun.status === 'FAILED' ? tokens.colors.danger : currentRun.status === 'CANCELLED' ? tokens.colors.warning : tokens.colors.info,
                    animation: running ? 'pulse 1.5s infinite' : 'none'
                  }} />
                  <span style={{ fontWeight: 700, color: tokens.colors.textPrimary, fontSize: '0.85rem' }}>
                    Status: {currentRun.status}
                  </span>
                  {running && !isReviewer && (
                    <button
                      type="button"
                      onClick={handleCancelRun}
                      style={{
                        padding: '0.15rem 0.5rem',
                        fontSize: '0.7rem',
                        fontWeight: 700,
                        background: 'transparent',
                        border: `1px solid ${tokens.colors.dangerBorder}`,
                        color: tokens.colors.danger,
                        borderRadius: '0.25rem',
                        cursor: 'pointer'
                      }}
                      title="Halt active matching execution"
                    >
                      Stop Run
                    </button>
                  )}
                </div>
                <span style={{ fontSize: '0.75rem', fontFamily: 'monospace', color: tokens.colors.textMuted }}>
                  ID: {currentRun.id.substring(0, 13)}...
                </span>
              </div>

              {/* Progress Bar */}
              <div style={{ width: '100%', height: '8px', background: tokens.colors.border, borderRadius: '4px', overflow: 'hidden', marginBottom: '0.75rem' }}>
                <div style={{
                  width: running && progressPct === 0 ? '25%' : `${progressPct}%`,
                  height: '100%',
                  background: currentRun.status === 'COMPLETED' ? tokens.colors.success : currentRun.status === 'FAILED' ? tokens.colors.danger : currentRun.status === 'CANCELLED' ? tokens.colors.warning : tokens.colors.primary,
                  transition: 'width 0.4s ease',
                  animation: running && progressPct === 0 ? 'pulse 1.5s infinite' : 'none'
                }} />
              </div>

              {/* Stats Counters */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem', textAlign: 'center' }}>
                <div style={{ background: tokens.colors.surface, padding: '0.5rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                  <div style={{ fontSize: '0.65rem', color: tokens.colors.textMuted, fontWeight: 700 }}>PROCESSED</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: tokens.colors.primary }}>
                    {stats?.materials_processed ?? (currentRun.status === 'COMPLETED' ? (stats?.total_materials ?? 45) : 0)} / {stats?.total_materials ?? (scopeType === 'demo' ? 45 : 0)}
                  </div>
                </div>

                <div style={{ background: tokens.colors.surface, padding: '0.5rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                  <div style={{ fontSize: '0.65rem', color: tokens.colors.textMuted, fontWeight: 700 }}>COMPARISONS</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                    {stats?.comparisons_performed ?? 0}
                  </div>
                </div>

                <div style={{ background: tokens.colors.surface, padding: '0.5rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                  <div style={{ fontSize: '0.65rem', color: tokens.colors.textMuted, fontWeight: 700 }}>VETOES</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: tokens.colors.danger }}>
                    {stats?.veto_count ?? 0}
                  </div>
                </div>

                <div style={{ background: tokens.colors.surface, padding: '0.5rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}` }}>
                  <div style={{ fontSize: '0.65rem', color: tokens.colors.textMuted, fontWeight: 700 }}>DURATION</div>
                  <div style={{ fontSize: '1rem', fontWeight: 800, color: tokens.colors.success }}>
                    {stats?.duration_ms ? `${(stats.duration_ms / 1000).toFixed(1)}s` : '0s'}
                  </div>
                </div>
              </div>

              {/* Relationship Breakdown */}
              {stats?.relationship_counts && (
                <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem', fontSize: '0.7rem', flexWrap: 'wrap' }}>
                  <span style={{ background: tokens.colors.successBg, color: tokens.colors.success, border: `1px solid ${tokens.colors.successBorder}`, padding: '0.15rem 0.5rem', borderRadius: '0.2rem', fontWeight: 700 }}>
                    Equivalents: {stats.relationship_counts['FUNCTIONALLY_EQUIVALENT'] || 0}
                  </span>
                  <span style={{ background: tokens.colors.warningBg, color: tokens.colors.warning, border: `1px solid ${tokens.colors.warningBorder}`, padding: '0.15rem 0.5rem', borderRadius: '0.2rem', fontWeight: 700 }}>
                    Review Required: {stats.relationship_counts['REVIEW_REQUIRED'] || 0}
                  </span>
                  <span style={{ background: tokens.colors.dangerBg, color: tokens.colors.danger, border: `1px solid ${tokens.colors.dangerBorder}`, padding: '0.15rem 0.5rem', borderRadius: '0.2rem', fontWeight: 700 }}>
                    Not Equivalent: {stats.relationship_counts['NOT_EQUIVALENT'] || 0}
                  </span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div style={{
          padding: '1rem 1.5rem',
          background: tokens.colors.surfaceSubtle,
          borderTop: `1px solid ${tokens.colors.border}`,
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center'
        }}>
          <button
            onClick={onClose}
            style={{
              padding: '0.5rem 1rem',
              background: tokens.colors.surface,
              color: tokens.colors.textSecondary,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.375rem',
              fontWeight: 600,
              fontSize: '0.85rem',
              cursor: 'pointer'
            }}
          >
            Close
          </button>

          <button
            onClick={() => handleLaunchRun(false)}
            disabled={running || isReviewer}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.55rem 1.25rem',
              background: running || isReviewer ? tokens.colors.borderDark : tokens.colors.primary,
              color: '#fff',
              border: 'none',
              borderRadius: '0.375rem',
              fontWeight: 700,
              fontSize: '0.85rem',
              cursor: running || isReviewer ? 'not-allowed' : 'pointer',
              boxShadow: tokens.shadows.sm,
              opacity: running || isReviewer ? 0.75 : 1
            }}
          >
            {running ? (
              <>
                <RefreshCw style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
                Matching In Progress...
              </>
            ) : isReviewer ? (
              <>
                <ShieldAlert style={{ width: '16px', height: '16px' }} />
                Restricted (Reviewer Role)
              </>
            ) : (
              <>
                <Play style={{ width: '16px', height: '16px' }} />
                Trigger Match Run
              </>
            )}
          </button>
        </div>
      </div>
    </div>
  );
}
