'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import AppShell from '../components/AppShell';
import { tokens } from '../components/design-system/tokens';
import {
  FileCheck,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  Lock,
  RefreshCw,
  Eye,
  Hash,
  Database,
  X
} from 'lucide-react';

import { AuditChainIllustration } from '../components/illustrations/IndustrialIcons';

interface AuditEventDTO {
  seq: number;
  ts: string;
  actor_id: string;
  actor_role: string;
  action: string;
  entity_type: string;
  entity_id: string;
  before?: any;
  after?: any;
  reason?: string;
  model_refs?: any;
  request_id?: string;
  prev_hash: string;
  hash: string;
}

interface AuditVerifyResultDTO {
  valid: boolean;
  total_events: number;
  broken_seq?: number;
  verified_at: string;
}

export default function AuditPage() {
  const { token } = useAuth();
  const [events, setEvents] = useState<AuditEventDTO[]>([]);
  const [verifyResult, setVerifyResult] = useState<AuditVerifyResultDTO | null>(null);
  const [loading, setLoading] = useState(true);
  const [verifying, setVerifying] = useState(false);
  const [selectedEvent, setSelectedEvent] = useState<AuditEventDTO | null>(null);

  const fetchAuditEvents = async () => {
    if (!token) return;
    setLoading(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${apiHost}/api/v1/audit?page=1&page_size=50`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setEvents(data);
      }
    } catch (e) {
      console.error('Error fetching audit events', e);
    } finally {
      setLoading(false);
    }
  };

  const handleVerifyChain = async () => {
    if (!token) return;
    setVerifying(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const res = await fetch(`${apiHost}/api/v1/audit/verify`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const result = await res.json();
        setVerifyResult(result);
      }
    } catch (e) {
      console.error('Error verifying audit chain', e);
    } finally {
      setVerifying(false);
    }
  };

  useEffect(() => {
    fetchAuditEvents();
    handleVerifyChain();
  }, [token]);

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
            <AuditChainIllustration style={{ width: '38px', height: '38px' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
                CRYPTOGRAPHIC AUDIT CHAIN EXPLORER
              </h2>
              <span style={{
                fontSize: '0.8rem',
                fontWeight: 800,
                padding: '0.25rem 0.75rem',
                borderRadius: '9999px',
                background: '#DCFCE7',
                color: tokens.colors.primary,
                border: '1px solid #BBF7D0'
              }}>
                SHA-256 APPEND-ONLY CHAIN
              </span>
            </div>
            <p style={{ margin: '0.25rem 0 0 0', color: tokens.colors.textSecondary, fontSize: '0.875rem' }}>
              Cryptographically sealed provenance chain guaranteeing immutable governance history and tamper-detection
            </p>
          </div>
        </div>

        <button
          onClick={handleVerifyChain}
          disabled={verifying}
          style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
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
          <ShieldCheck style={{ width: '18px', height: '18px', animation: verifying ? 'spin 1s linear infinite' : 'none' }} />
          {verifying ? 'Verifying Hash Chain...' : 'VERIFY AUDIT CHAIN'}
        </button>
      </div>

      {/* Verification Result Banner */}
      {verifyResult && (
        <div style={{
          background: verifyResult.valid ? '#F0FDF4' : '#FEF2F2',
          border: `1px solid ${verifyResult.valid ? '#BBF7D0' : '#FECACA'}`,
          borderRadius: '0.75rem',
          padding: '1rem 1.25rem',
          marginBottom: '1.5rem',
          display: 'flex',
          alignItems: 'center',
          gap: '0.75rem',
          boxShadow: tokens.shadows.sm
        }}>
          {verifyResult.valid ? (
            <CheckCircle2 style={{ width: '24px', height: '24px', color: tokens.colors.success }} />
          ) : (
            <AlertTriangle style={{ width: '24px', height: '24px', color: tokens.colors.danger }} />
          )}
          <div>
            <h4 style={{ margin: 0, color: verifyResult.valid ? tokens.colors.primary : tokens.colors.danger, fontWeight: 800, fontSize: '1rem' }}>
              {verifyResult.valid ? 'Cryptographic Audit Chain Intact & Valid' : 'Audit Chain Verification Failed!'}
            </h4>
            <p style={{ margin: '0.2rem 0 0 0', color: tokens.colors.textSecondary, fontSize: '0.85rem' }}>
              {verifyResult.valid
                ? `All ${verifyResult.total_events} sequential governance events verified against SHA-256 prev_hash links without deviation.`
                : `Hash link broken at sequence #${verifyResult.broken_seq}. Potential integrity compromise detected.`}
            </p>
          </div>
        </div>
      )}

      {/* Audit Events Table */}
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
          <p style={{ fontWeight: 600 }}>Loading cryptographic audit trail...</p>
        </div>
      ) : (
        <div style={{
          background: tokens.colors.surface,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '0.75rem',
          overflow: 'hidden',
          boxShadow: tokens.shadows.sm
        }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
            <thead>
              <tr style={{ background: tokens.colors.surfaceSubtle, textAlign: 'left', borderBottom: `2px solid ${tokens.colors.border}` }}>
                <th style={{ padding: '0.75rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>SEQ #</th>
                <th style={{ padding: '0.75rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>TIMESTAMP</th>
                <th style={{ padding: '0.75rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>ACTION</th>
                <th style={{ padding: '0.75rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>ENTITY</th>
                <th style={{ padding: '0.75rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>SHA-256 HASH</th>
                <th style={{ padding: '0.75rem', textAlign: 'right', color: tokens.colors.textSecondary, fontWeight: 700 }}>INSPECT</th>
              </tr>
            </thead>
            <tbody>
              {events.map((ev) => (
                <tr key={ev.seq} style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
                  <td style={{ padding: '0.75rem', fontWeight: 800, color: tokens.colors.primary, fontFamily: 'monospace' }}>
                    #{ev.seq}
                  </td>
                  <td style={{ padding: '0.75rem', color: tokens.colors.textSecondary, fontSize: '0.8rem' }}>
                    {new Date(ev.ts).toLocaleString('en-IN')}
                  </td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, padding: '0.2rem 0.5rem', background: '#DCFCE7', color: tokens.colors.primary, borderRadius: '0.25rem', border: '1px solid #BBF7D0' }}>
                      {ev.action}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem', color: tokens.colors.textPrimary, fontWeight: 600 }}>
                    {ev.entity_type} ({ev.entity_id?.slice(0, 8)}...)
                  </td>
                  <td style={{ padding: '0.75rem', fontFamily: 'monospace', color: tokens.colors.textSecondary, fontSize: '0.75rem' }}>
                    {ev.hash?.slice(0, 18)}...
                  </td>
                  <td style={{ padding: '0.75rem', textAlign: 'right' }}>
                    <button
                      onClick={() => setSelectedEvent(ev)}
                      style={{
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.35rem 0.65rem',
                        background: tokens.colors.surfaceSubtle,
                        color: tokens.colors.primary,
                        border: `1px solid ${tokens.colors.border}`,
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        cursor: 'pointer'
                      }}
                    >
                      <Eye style={{ width: '13px', height: '13px' }} /> Inspect
                    </button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* JSON Inspector Modal */}
      {selectedEvent && (
        <div className="modal-backdrop-smooth" style={{ position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.6)', backdropFilter: 'blur(4px)', display: 'flex', justifyContent: 'center', alignItems: 'center', zIndex: 100 }}>
          <div className="animate-scale-up" style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.5rem', width: '90%', maxWidth: '650px', maxHeight: '80vh', overflowY: 'auto', boxShadow: tokens.shadows.lg }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem' }}>
              <h3 style={{ margin: 0, color: tokens.colors.textPrimary, fontSize: '1.15rem', fontWeight: 800 }}>
                Audit Event Inspector — Sequence #{selectedEvent.seq}
              </h3>
              <button onClick={() => setSelectedEvent(null)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: tokens.colors.textSecondary }}>
                <X style={{ width: '18px', height: '18px' }} />
              </button>
            </div>
            <div style={{ fontSize: '0.8rem', color: tokens.colors.textSecondary, marginBottom: '1rem' }}>
              Action: <strong style={{ color: tokens.colors.primary }}>{selectedEvent.action}</strong> · Entity: {selectedEvent.entity_type} · Actor: <strong>{selectedEvent.actor_role}</strong>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <strong style={{ color: tokens.colors.textPrimary, fontSize: '0.8rem' }}>SHA-256 Prev Hash:</strong>
              <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: tokens.colors.textSecondary, background: tokens.colors.surfaceSubtle, padding: '0.5rem 0.75rem', borderRadius: '0.375rem', marginTop: '0.25rem', border: `1px solid ${tokens.colors.border}`, wordBreak: 'break-all' }}>
                {selectedEvent.prev_hash}
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <strong style={{ color: tokens.colors.textPrimary, fontSize: '0.8rem' }}>SHA-256 Current Event Hash:</strong>
              <div style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: tokens.colors.primary, background: '#DCFCE7', padding: '0.5rem 0.75rem', borderRadius: '0.375rem', marginTop: '0.25rem', border: '1px solid #BBF7D0', wordBreak: 'break-all', fontWeight: 700 }}>
                {selectedEvent.hash}
              </div>
            </div>

            <div style={{ marginBottom: '1rem' }}>
              <strong style={{ color: tokens.colors.textPrimary, fontSize: '0.8rem' }}>Event Diff & Model Provenance:</strong>
              <pre style={{ fontFamily: 'monospace', fontSize: '0.75rem', color: tokens.colors.textPrimary, background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.375rem', border: `1px solid ${tokens.colors.border}`, overflowX: 'auto', maxHeight: '200px' }}>
                {JSON.stringify({ before: selectedEvent.before, after: selectedEvent.after, reason: selectedEvent.reason, model_refs: selectedEvent.model_refs }, null, 2)}
              </pre>
            </div>

            <div style={{ display: 'flex', justifyContent: 'flex-end' }}>
              <button
                onClick={() => setSelectedEvent(null)}
                style={{ padding: '0.5rem 1rem', background: tokens.colors.primary, color: '#fff', border: 'none', borderRadius: '0.375rem', fontWeight: 700, cursor: 'pointer' }}
              >
                Close Inspector
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
