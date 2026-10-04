'use client';

import React, { useEffect, useState } from 'react';
import { useAuth } from '../context/AuthContext';
import AppShell from '../components/AppShell';
import { tokens } from '../components/design-system/tokens';
import {
  Layers,
  Search,
  CheckCircle2,
  Link,
  RefreshCw,
  ChevronDown,
  ChevronUp,
  ShieldCheck,
  Building2,
  FileText,
  Hash
} from 'lucide-react';
import { NmcDatabaseIllustration } from '../components/illustrations/IndustrialIcons';

interface LegacyMappingDTO {
  id: string;
  material_id: string;
  national_material_uid: string;
  cpse_code: string;
  cpse_name?: string;
  source_code?: string;
  raw_description?: string;
  provenance?: string;
  provenance_label?: string;
  status: string;
  valid_from: string;
}

interface NationalMaterialDTO {
  uid: string;
  nmc: string;
  category_code: string;
  status: string;
  canonical_description: string;
  sap_short_description: string;
  spec_fingerprint: string;
  current_version_no: number;
  created_at: string;
  cpse_count: number;
  legacy_mappings_count: number;
  legacy_mappings: LegacyMappingDTO[];
}

export default function NationalMaterialsPage() {
  const { token } = useAuth();
  const [items, setItems] = useState<NationalMaterialDTO[]>([]);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [expandedUid, setExpandedUid] = useState<string | null>(null);

  const fetchNationalMaterials = async () => {
    if (!token) return;
    setLoading(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (categoryFilter) params.append('category_code', categoryFilter);

      const res = await fetch(`${apiHost}/api/v1/national-materials?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setItems(data);
        if (data.length > 0 && !expandedUid) {
          setExpandedUid(data[0].uid);
        }
      }
    } catch (e) {
      console.error('Error fetching national materials', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchNationalMaterials();
  }, [token, categoryFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchNationalMaterials();
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
            <NmcDatabaseIllustration style={{ width: '38px', height: '38px' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
                NATIONAL MATERIAL MASTER
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
                {items.length} CANONICAL RECORDS
              </span>
            </div>
            <p style={{ margin: '0.25rem 0 0 0', color: tokens.colors.textSecondary, fontSize: '0.875rem' }}>
              Authoritative master catalog with ISO 7064 MOD 97-10 check digits & active CPSE crosswalks
            </p>
          </div>
        </div>

        <button
          onClick={fetchNationalMaterials}
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
          Refresh Registry
        </button>
      </div>

      {/* Filter Bar */}
      <div style={{
        background: tokens.colors.surface,
        border: `1px solid ${tokens.colors.border}`,
        borderRadius: '0.75rem',
        padding: '1rem',
        marginBottom: '1.5rem',
        display: 'flex',
        gap: '1rem',
        alignItems: 'center',
        boxShadow: tokens.shadows.sm
      }}>
        <form onSubmit={handleSearchSubmit} style={{ flex: 1, display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', width: '16px', height: '16px', color: tokens.colors.textSecondary }} />
            <input
              type="text"
              placeholder="Search NMC string or canonical description..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
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
              cursor: 'pointer'
            }}
          >
            Search
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
      </div>

      {/* Registry Grid / List */}
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
          <p style={{ fontWeight: 600 }}>Loading National Material Master records...</p>
        </div>
      ) : items.length === 0 ? (
        <div style={{
          background: tokens.colors.surface,
          border: `1px solid ${tokens.colors.border}`,
          borderRadius: '0.75rem',
          padding: '3rem',
          textAlign: 'center',
          color: tokens.colors.textSecondary,
          boxShadow: tokens.shadows.sm
        }}>
          <Layers style={{ width: '40px', height: '40px', margin: '0 auto 1rem auto', color: tokens.colors.border }} />
          <h3 style={{ color: tokens.colors.textPrimary, margin: '0 0 0.5rem 0', fontWeight: 700 }}>No National Materials Found</h3>
          <p style={{ margin: 0, fontSize: '0.875rem' }}>Approve candidate pairs in the Review Queue to generate unified NMCs.</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          {items.map((nat) => {
            const isExpanded = expandedUid === nat.uid;
            const uniqueCpses = Array.from(new Set(nat.legacy_mappings.map((m) => m.cpse_code)));
            const updatedDate = new Date(nat.created_at).toLocaleDateString('en-IN', {
              year: 'numeric',
              month: 'short',
              day: 'numeric'
            });

            return (
              <div
                key={nat.uid}
                style={{
                  background: tokens.colors.surface,
                  border: `1px solid ${tokens.colors.border}`,
                  borderRadius: '0.75rem',
                  padding: '1.25rem',
                  boxShadow: tokens.shadows.sm,
                  transition: 'box-shadow 0.2s'
                }}
              >
                {/* Header Row */}
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.75rem', flexWrap: 'wrap', gap: '0.5rem' }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                    <span style={{
                      fontSize: '1.1rem',
                      fontFamily: 'monospace',
                      fontWeight: 800,
                      color: tokens.colors.primary,
                      background: '#DCFCE7',
                      padding: '0.35rem 0.75rem',
                      borderRadius: '0.375rem',
                      border: '1px solid #BBF7D0'
                    }}>
                      {nat.nmc}
                    </span>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      padding: '0.2rem 0.55rem',
                      background: '#0F766E',
                      color: '#fff',
                      borderRadius: '0.25rem'
                    }}>
                      {nat.category_code}
                    </span>
                    <span style={{
                      fontSize: '0.75rem',
                      fontWeight: 700,
                      color: tokens.colors.success,
                      display: 'flex',
                      alignItems: 'center',
                      gap: '0.25rem',
                      background: '#F0FDF4',
                      padding: '0.15rem 0.5rem',
                      borderRadius: '0.25rem',
                      border: '1px solid #BBF7D0'
                    }}>
                      <CheckCircle2 style={{ width: '13px', height: '13px' }} />
                      ACTIVE (v{nat.current_version_no})
                    </span>
                  </div>

                  <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                    <span style={{ fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
                      CPSEs: <strong style={{ color: tokens.colors.primary }}>{uniqueCpses.length}</strong> | Mappings: <strong style={{ color: tokens.colors.textPrimary }}>{nat.legacy_mappings_count}</strong> | Updated: <strong>{updatedDate}</strong>
                    </span>
                    <button
                      onClick={() => setExpandedUid(isExpanded ? null : nat.uid)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.25rem',
                        padding: '0.35rem 0.65rem',
                        background: tokens.colors.surfaceSubtle,
                        border: `1px solid ${tokens.colors.border}`,
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        color: tokens.colors.textPrimary,
                        cursor: 'pointer'
                      }}
                    >
                      {isExpanded ? (
                        <>Collapse <ChevronUp style={{ width: '14px', height: '14px' }} /></>
                      ) : (
                        <>Details <ChevronDown style={{ width: '14px', height: '14px' }} /></>
                      )}
                    </button>
                  </div>
                </div>

                {/* Canonical Description */}
                <h4 style={{ margin: '0 0 0.5rem 0', color: tokens.colors.textPrimary, fontSize: '1.05rem', fontWeight: 700, lineHeight: 1.4 }}>
                  {nat.canonical_description}
                </h4>

                {/* Progressive Disclosure: Details */}
                {isExpanded && (
                  <div style={{ marginTop: '1rem', paddingTop: '1rem', borderTop: `1px solid ${tokens.colors.border}` }}>
                    {/* 1. Harmonized CPSE Source Materials & Legacy Crosswalk */}
                    <div style={{ marginBottom: '1.25rem' }}>
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.6rem' }}>
                        <span style={{ fontSize: '0.75rem', fontWeight: 800, color: tokens.colors.textSecondary, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                          Harmonized CPSE Source Materials ({nat.legacy_mappings.length} Crosswalk Links across {uniqueCpses.length} CPSEs)
                        </span>
                        <span style={{ fontSize: '0.7rem', color: tokens.colors.primary, fontWeight: 700 }}>
                          Cross-CPSE Harmonized
                        </span>
                      </div>
                      {nat.legacy_mappings.length === 0 ? (
                        <p style={{ margin: 0, fontSize: '0.8rem', color: tokens.colors.textSecondary, fontStyle: 'italic' }}>
                          No legacy mappings attached to this canonical record yet.
                        </p>
                      ) : (
                        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '0.75rem' }}>
                          {nat.legacy_mappings.map((m) => {
                            const isPublic = m.provenance === 'REAL_PUBLIC';
                            return (
                              <div
                                key={m.id}
                                style={{
                                  background: tokens.colors.surfaceSubtle,
                                  padding: '0.85rem 1rem',
                                  borderRadius: '0.5rem',
                                  border: `1px solid ${tokens.colors.border}`,
                                  display: 'flex',
                                  flexDirection: 'column',
                                  gap: '0.4rem'
                                }}
                              >
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                                    <span style={{
                                      fontWeight: 800,
                                      color: tokens.colors.primary,
                                      background: '#DCFCE7',
                                      padding: '0.2rem 0.5rem',
                                      borderRadius: '0.25rem',
                                      fontSize: '0.75rem',
                                      border: '1px solid #BBF7D0'
                                    }}>
                                      {m.cpse_code}
                                    </span>
                                    <span style={{ fontFamily: 'monospace', fontWeight: 800, color: tokens.colors.textPrimary, fontSize: '0.85rem' }}>
                                      {m.source_code || m.material_id?.slice(0, 8)}
                                    </span>
                                  </div>
                                  <span style={{
                                    fontSize: '0.675rem',
                                    fontWeight: 700,
                                    padding: '0.15rem 0.5rem',
                                    borderRadius: '9999px',
                                    background: isPublic ? '#CCFBF1' : '#F1F5F9',
                                    color: isPublic ? '#0F766E' : '#475569',
                                    border: `1px solid ${isPublic ? '#99F6E4' : '#CBD5E1'}`
                                  }}>
                                    {m.provenance_label || (isPublic ? 'Public-source record' : 'Synthetic demonstration record')}
                                  </span>
                                </div>
                                {m.raw_description && (
                                  <p style={{ margin: 0, fontSize: '0.8rem', color: tokens.colors.textSecondary, lineHeight: 1.35 }}>
                                    {m.raw_description}
                                  </p>
                                )}
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.2rem', paddingTop: '0.35rem', borderTop: `1px dashed ${tokens.colors.border}`, fontSize: '0.7rem' }}>
                                  <span style={{ color: tokens.colors.textSecondary }}>{m.cpse_name || m.cpse_code}</span>
                                  <span style={{ color: tokens.colors.success, fontWeight: 700, display: 'flex', alignItems: 'center', gap: '0.25rem' }}>
                                    <CheckCircle2 style={{ width: '11px', height: '11px' }} />
                                    ACTIVE MAPPING
                                  </span>
                                </div>
                              </div>
                            );
                          })}
                        </div>
                      )}
                    </div>

                    {/* 2. Specification Fingerprint & SAP Description */}
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '1rem' }}>
                      <div style={{ background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.5rem', border: `1px solid ${tokens.colors.border}` }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: tokens.colors.textSecondary, marginBottom: '0.25rem' }}>
                          SPECIFICATION FINGERPRINT (SHA-256 IMMUTABLE GUARD)
                        </div>
                        <span style={{ fontFamily: 'monospace', color: tokens.colors.textSecondary, fontSize: '0.75rem', wordBreak: 'break-all' }}>
                          {nat.spec_fingerprint}
                        </span>
                      </div>

                      <div style={{ background: tokens.colors.surfaceSubtle, padding: '0.75rem', borderRadius: '0.5rem', border: `1px solid ${tokens.colors.border}` }}>
                        <div style={{ fontSize: '0.7rem', fontWeight: 700, color: tokens.colors.textSecondary, marginBottom: '0.25rem' }}>
                          SAP 40-CHAR SHORT DESCRIPTION (RFC / BAPI CONSTRAINED)
                        </div>
                        <span style={{ fontFamily: 'monospace', color: tokens.colors.primary, fontWeight: 700, fontSize: '0.875rem' }}>
                          {nat.sap_short_description}
                        </span>
                      </div>
                    </div>
                  </div>
                )}
              </div>
            );
          })}
        </div>
      )}
    </AppShell>
  );
}
