'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import AppShell from '../components/AppShell';
import { tokens } from '../components/design-system/tokens';
import {
  Layers,
  RefreshCw,
  Send,
  CheckCircle2,
  AlertTriangle,
  ExternalLink,
  Code,
  X,
  ShieldAlert,
  Cpu,
  Database,
  Server,
  Lock
} from 'lucide-react';

interface SapMaterialDTO {
  id: string;
  sap_product_id: string;
  product_description: string;
  nmc: string;
  status: string;
  payload: any;
  created_at?: string;
}

interface SapStatusDTO {
  adapter: string;
  is_mock: boolean;
  status: string;
  system_id: string;
  client: string;
  description_limit: number;
  total_synced_materials: number;
  last_sync?: {
    sync_id?: string;
    status?: string;
    timestamp?: string;
    records_exported?: number;
    records_accepted?: number;
    records_rejected?: number;
  };
}

export default function IntegrationPage() {
  const { token, user } = useAuth();
  const [statusData, setStatusData] = useState<SapStatusDTO | null>(null);
  const [materials, setMaterials] = useState<SapMaterialDTO[]>([]);
  const [loading, setLoading] = useState(true);
  const [syncing, setSyncing] = useState(false);
  const [syncSuccessMsg, setSyncSuccessMsg] = useState<string | null>(null);
  const [selectedPayload, setSelectedPayload] = useState<any | null>(null);

  const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

  const fetchData = async () => {
    if (!token) return;
    setLoading(true);
    try {
      const [resStatus, resMats] = await Promise.all([
        fetch(`${apiHost}/api/v1/integration/sap/status`, {
          headers: { Authorization: `Bearer ${token}` }
        }),
        fetch(`${apiHost}/api/v1/integration/sap/materials?page_size=50`, {
          headers: { Authorization: `Bearer ${token}` }
        })
      ]);

      if (resStatus.ok) {
        const s = await resStatus.json();
        setStatusData(s);
      }
      if (resMats.ok) {
        const m = await resMats.json();
        setMaterials(m);
      }
    } catch (e) {
      console.error('Error fetching SAP integration data', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, [token]);

  const handleTriggerSync = async () => {
    if (!token) return;
    setSyncing(true);
    setSyncSuccessMsg(null);
    try {
      const res = await fetch(`${apiHost}/api/v1/integration/sap/sync`, {
        method: 'POST',
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const result = await res.json();
        setSyncSuccessMsg(`Successfully synchronized ${result.records_exported} National Materials to Mock SAP ERP!`);
        await fetchData();
      } else {
        alert('Failed to execute SAP synchronization');
      }
    } catch (e) {
      console.error('Error triggering SAP sync', e);
      alert('Error triggering SAP synchronization');
    } finally {
      setSyncing(false);
    }
  };

  return (
    <AppShell>
      {/* Simulation Notice Banner */}
      <div style={{
        background: '#FEF3C7',
        border: '1px solid #FDE68A',
        borderRadius: '0.75rem',
        padding: '0.85rem 1.25rem',
        marginBottom: '1.25rem',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.75rem',
        boxShadow: tokens.shadows.sm
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <AlertTriangle style={{ width: '20px', height: '20px', color: tokens.colors.warning, flexShrink: 0 }} />
          <div>
            <span style={{ fontSize: '0.85rem', fontWeight: 800, color: '#92400E', letterSpacing: '0.02em' }}>
              MOCK SAP S/4HANA ENTERPRISE INTEGRATION
            </span>
            <p style={{ margin: 0, fontSize: '0.775rem', color: '#B45309' }}>
              Simulated SAP S/4HANA Master Data (BAPI_MATERIAL_SAVEDATA) Outbound Adapter. Strictly enforces 40-character short description constraints.
            </p>
          </div>
        </div>
        <span style={{ fontSize: '0.7rem', fontWeight: 800, background: '#FFFFFF', color: '#92400E', padding: '0.2rem 0.6rem', borderRadius: '0.25rem', border: '1px solid #FDE68A' }}>
          RFC BAPI SIMULATION
        </span>
      </div>

      {/* Header Banner */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', flexWrap: 'wrap', gap: '1rem' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary, letterSpacing: '-0.02em' }}>
              ENTERPRISE ERP INTEGRATION HUB
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
              OUTBOUND ADAPTER READY
            </span>
          </div>
          <p style={{ margin: '0.25rem 0 0 0', color: tokens.colors.textSecondary, fontSize: '0.875rem' }}>
            Outbound synchronization of standardized National Material Master records to Mock SAP S/4HANA
          </p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {user && (user.role === 'REVIEWER' || user.role === 'VIEWER') ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.6rem 1.1rem',
              background: tokens.colors.surfaceSubtle,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.5rem',
              color: tokens.colors.textMuted,
              fontSize: '0.8rem',
              fontWeight: 800
            }}>
              <Lock style={{ width: '14px', height: '14px' }} />
              SAP SYNC RESTRICTED (VIEW-ONLY)
            </div>
          ) : (
            <button
              onClick={handleTriggerSync}
              disabled={syncing}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.5rem',
                padding: '0.6rem 1.25rem',
                background: tokens.colors.primary,
                color: '#fff',
                border: 'none',
                borderRadius: '0.5rem',
                fontWeight: 700,
                fontSize: '0.875rem',
                cursor: syncing ? 'not-allowed' : 'pointer',
                boxShadow: tokens.shadows.sm
              }}
            >
              {syncing ? (
                <>
                  <RefreshCw style={{ width: '16px', height: '16px', animation: 'spin 1s linear infinite' }} />
                  Syncing Outbound to SAP...
                </>
              ) : (
                <>
                  <Send style={{ width: '16px', height: '16px' }} />
                  Trigger Outbound Sync to SAP
                </>
              )}
            </button>
          )}

          <button
            onClick={fetchData}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.6rem 1rem',
              background: tokens.colors.surface,
              color: tokens.colors.primary,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.5rem',
              fontWeight: 700,
              fontSize: '0.875rem',
              cursor: 'pointer',
              boxShadow: tokens.shadows.sm
            }}
          >
            <RefreshCw style={{ width: '15px', height: '15px', animation: loading ? 'spin 1s linear infinite' : 'none' }} />
            Refresh
          </button>
        </div>
      </div>

      {syncSuccessMsg && (
        <div 
          className="animate-fade-in"
          style={{
            marginBottom: '1.5rem',
            padding: '0.85rem 1.25rem',
            background: '#DCFCE7',
            border: '1px solid #BBF7D0',
            borderRadius: '0.5rem',
            color: tokens.colors.primary,
            fontSize: '0.875rem',
            fontWeight: 700,
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem'
          }}
        >
          <CheckCircle2 style={{ width: '18px', height: '18px', flexShrink: 0 }} />
          <span>{syncSuccessMsg}</span>
        </div>
      )}

      {/* System Status Architecture Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '1.25rem',
        marginBottom: '1.5rem'
      }}>
        <div className="interactive-card animate-fade-in" style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.25rem', boxShadow: tokens.shadows.sm, transition: 'all 0.22s cubic-bezier(0.16, 1, 0.3, 1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tokens.colors.textSecondary }}>ADAPTER STATUS</span>
            <Server style={{ width: '18px', height: '18px', color: tokens.colors.success }} />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 900, color: tokens.colors.primary }}>
            ACTIVE (MOCK)
          </div>
          <span style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
            Target: <code style={{ color: tokens.colors.primary, fontWeight: 700 }}>{statusData?.system_id || 'S4H_PRD_MOCK'}</code> (Client {statusData?.client || '100'})
          </span>
        </div>

        <div className="interactive-card animate-fade-in" style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.25rem', boxShadow: tokens.shadows.sm, transition: 'all 0.22s cubic-bezier(0.16, 1, 0.3, 1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tokens.colors.textSecondary }}>TOTAL MATERIALS IN SAP</span>
            <Database style={{ width: '18px', height: '18px', color: tokens.colors.teal }} />
          </div>
          <div style={{ fontSize: '1.75rem', fontWeight: 900, color: tokens.colors.textPrimary }}>
            {statusData?.total_synced_materials ?? materials.length}
          </div>
          <span style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary }}>Synchronized Master Records</span>
        </div>

        <div className="interactive-card animate-fade-in" style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.25rem', boxShadow: tokens.shadows.sm, transition: 'all 0.22s cubic-bezier(0.16, 1, 0.3, 1)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tokens.colors.textSecondary }}>DESCRIPTION CONSTRAINT</span>
            <Cpu style={{ width: '18px', height: '18px', color: tokens.colors.warning }} />
          </div>
          <div style={{ fontSize: '1.25rem', fontWeight: 900, color: tokens.colors.textPrimary }}>
            &le; {statusData?.description_limit || 40} Chars
          </div>
          <span style={{ fontSize: '0.75rem', color: tokens.colors.success, fontWeight: 700 }}>
            100% MAKTX Compliant
          </span>
        </div>

        <div style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', padding: '1.25rem', boxShadow: tokens.shadows.sm }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 700, color: tokens.colors.textSecondary }}>LAST SYNC RUN</span>
            <CheckCircle2 style={{ width: '18px', height: '18px', color: tokens.colors.primary }} />
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
            {statusData?.last_sync?.timestamp ? new Date(statusData.last_sync.timestamp).toLocaleString('en-IN') : 'Ready for Sync'}
          </div>
          <span style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
            Accepted: <strong style={{ color: tokens.colors.success }}>{statusData?.last_sync?.records_accepted ?? materials.length}</strong> &bull; Rejected: <strong style={{ color: tokens.colors.danger }}>{statusData?.last_sync?.records_rejected ?? 0}</strong>
          </span>
        </div>
      </div>

      {/* Synchronized Materials Table */}
      <div style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.75rem', overflow: 'hidden', boxShadow: tokens.shadows.sm }}>
        <div style={{ padding: '1.25rem', borderBottom: `1px solid ${tokens.colors.border}`, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <h3 style={{ margin: 0, fontSize: '1.05rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
              Simulated SAP S/4HANA Material Master Records
            </h3>
            <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
              RFC BAPI structures derived deterministically from approved National Material Codes
            </p>
          </div>
          <span style={{ fontSize: '0.75rem', background: '#DCFCE7', color: tokens.colors.primary, padding: '0.2rem 0.6rem', borderRadius: '0.25rem', border: '1px solid #BBF7D0', fontWeight: 800 }}>
            {materials.length} Materials Active
          </span>
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
            <p style={{ fontWeight: 600 }}>Loading SAP Master records...</p>
          </div>
        ) : materials.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: tokens.colors.textSecondary }}>
            <Database style={{ width: '40px', height: '40px', margin: '0 auto 1rem auto', color: tokens.colors.border }} />
            <p style={{ fontWeight: 700, color: tokens.colors.textPrimary, marginBottom: '0.5rem' }}>No SAP Material Master records synchronized yet</p>
            <p style={{ fontSize: '0.8rem', maxWidth: '420px', margin: '0 auto 1.5rem auto', color: tokens.colors.textSecondary }}>
              Approved National Materials from the Review Queue can be exported directly into the simulated SAP S/4HANA ERP master data ledger.
            </p>
            <button
              onClick={handleTriggerSync}
              disabled={syncing}
              style={{
                padding: '0.6rem 1.25rem',
                background: tokens.colors.primary,
                color: '#fff',
                border: 'none',
                borderRadius: '0.375rem',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer'
              }}
            >
              Trigger Initial Outbound Sync
            </button>
          </div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.85rem' }}>
              <thead>
                <tr style={{ background: tokens.colors.surfaceSubtle, textAlign: 'left', borderBottom: `2px solid ${tokens.colors.border}` }}>
                  <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>SAP MATERIAL NO. (MATNR)</th>
                  <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>SHORT TEXT (MAKTX &le; 40)</th>
                  <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>TYPE / UOM</th>
                  <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>NATIONAL CODE (NMC)</th>
                  <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>MAPPED CPSES</th>
                  <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>STATUS</th>
                  <th style={{ padding: '0.75rem 1rem', textAlign: 'right', color: tokens.colors.textSecondary, fontWeight: 700 }}>RFC PAYLOAD</th>
                </tr>
              </thead>
              <tbody>
                {materials.map((m) => {
                  const hdr = m.payload?.HEADER;
                  const crosswalk = m.payload?.NUMM_CROSSWALK;
                  return (
                    <tr key={m.id} style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', fontWeight: 800, color: tokens.colors.primary }}>
                        {m.sap_product_id}
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontWeight: 600, color: tokens.colors.textPrimary, maxWidth: '300px' }}>
                        {m.product_description}
                        <span style={{ display: 'block', fontSize: '0.7rem', color: tokens.colors.textSecondary }}>
                          Len: {m.product_description.length}/40 chars
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontSize: '0.75rem' }}>
                        <span style={{ background: tokens.colors.surfaceSubtle, padding: '0.15rem 0.4rem', borderRadius: '0.2rem', marginRight: '0.3rem', border: `1px solid ${tokens.colors.border}`, fontWeight: 700 }}>
                          {hdr?.MTART || 'ROH'}
                        </span>
                        <span style={{ background: tokens.colors.surfaceSubtle, padding: '0.15rem 0.4rem', borderRadius: '0.2rem', border: `1px solid ${tokens.colors.border}`, fontWeight: 700 }}>
                          {hdr?.MEINS || 'EA'}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace', color: tokens.colors.primary, fontWeight: 800, fontSize: '0.8rem' }}>
                        {m.nmc}
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{ fontSize: '0.75rem', color: tokens.colors.textPrimary, fontWeight: 600 }}>
                          {crosswalk?.MAPPED_CPSE_COUNT ?? 1} CPSE(s)
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem' }}>
                        <span style={{
                          fontSize: '0.7rem',
                          fontWeight: 800,
                          padding: '0.2rem 0.5rem',
                          borderRadius: '0.25rem',
                          background: '#DCFCE7',
                          color: tokens.colors.primary,
                          border: '1px solid #BBF7D0'
                        }}>
                          {m.status}
                        </span>
                      </td>
                      <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                        <button
                          onClick={() => setSelectedPayload(m.payload)}
                          style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: '0.3rem',
                            padding: '0.3rem 0.65rem',
                            background: tokens.colors.surfaceSubtle,
                            color: tokens.colors.primary,
                            border: `1px solid ${tokens.colors.border}`,
                            borderRadius: '0.25rem',
                            fontSize: '0.75rem',
                            fontWeight: 700,
                            cursor: 'pointer'
                          }}
                        >
                          <Code style={{ width: '12px', height: '12px' }} />
                          Payload
                        </button>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* Raw SAP BAPI JSON Modal */}
      {selectedPayload && (
        <div style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(15, 23, 42, 0.6)',
          backdropFilter: 'blur(2px)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          zIndex: 100,
          padding: '1.5rem'
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
            <div style={{
              padding: '1rem 1.25rem',
              borderBottom: `1px solid ${tokens.colors.border}`,
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Code style={{ width: '18px', height: '18px', color: tokens.colors.primary }} />
                <h4 style={{ margin: 0, fontSize: '1rem', fontWeight: 800, color: tokens.colors.textPrimary }}>
                  SAP S/4HANA BAPI_MATERIAL_SAVEDATA Payload
                </h4>
              </div>
              <button
                onClick={() => setSelectedPayload(null)}
                style={{ background: 'transparent', border: 'none', color: tokens.colors.textSecondary, cursor: 'pointer' }}
              >
                <X style={{ width: '18px', height: '18px' }} />
              </button>
            </div>
            <div style={{ padding: '1.25rem', maxHeight: '60vh', overflowY: 'auto' }}>
              <pre style={{
                background: tokens.colors.surfaceSubtle,
                border: `1px solid ${tokens.colors.border}`,
                borderRadius: '0.5rem',
                padding: '1rem',
                color: tokens.colors.textPrimary,
                fontSize: '0.775rem',
                fontFamily: 'monospace',
                overflowX: 'auto',
                margin: 0
              }}>
                {JSON.stringify(selectedPayload, null, 2)}
              </pre>
            </div>
            <div style={{ padding: '0.75rem 1.25rem', background: tokens.colors.surfaceSubtle, borderTop: `1px solid ${tokens.colors.border}`, textAlign: 'right' }}>
              <button
                onClick={() => setSelectedPayload(null)}
                style={{
                  padding: '0.4rem 1rem',
                  background: tokens.colors.primary,
                  color: '#ffffff',
                  border: 'none',
                  borderRadius: '0.375rem',
                  fontWeight: 700,
                  fontSize: '0.8rem',
                  cursor: 'pointer'
                }}
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </AppShell>
  );
}
