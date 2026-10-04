'use client';

import React, { useEffect, useState } from 'react';
import Link from 'next/link';
import { useAuth } from '../context/AuthContext';
import AppShell from '../components/AppShell';
import { tokens } from '../components/design-system/tokens';
import { Box, Search, Filter, RefreshCw, ArrowRight, ShieldCheck, CheckCircle2, Layers, Upload, Lock } from 'lucide-react';
import { PipeValveIllustration } from '../components/illustrations/IndustrialIcons';

interface AttributeValueDTO {
  key: string;
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
  uom_canonical?: string;
  category_code: string;
  category_confidence: number;
  attributes: AttributeValueDTO[];
  mapping_nmc?: string;
  provenance?: string;
}

export default function MaterialsPage() {
  const { token, user } = useAuth();
  const [materials, setMaterials] = useState<MaterialDTO[]>([]);
  const [search, setSearch] = useState('');
  const [cpseFilter, setCpseFilter] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [provenanceFilter, setProvenanceFilter] = useState('');
  const [loading, setLoading] = useState(true);

  const fetchMaterials = async () => {
    if (!token) return;
    setLoading(true);
    const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    try {
      const params = new URLSearchParams();
      if (search) params.append('search', search);
      if (cpseFilter) params.append('cpse_code', cpseFilter);
      if (categoryFilter) params.append('category_code', categoryFilter);
      if (provenanceFilter) params.append('provenance', provenanceFilter);
      params.append('page_size', '50');

      const res = await fetch(`${apiHost}/api/v1/materials?${params.toString()}`, {
        headers: { Authorization: `Bearer ${token}` }
      });
      if (res.ok) {
        const data = await res.json();
        setMaterials(data);
      }
    } catch (e) {
      console.error('Error fetching materials', e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchMaterials();
  }, [token, cpseFilter, categoryFilter, provenanceFilter]);

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    fetchMaterials();
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
            <PipeValveIllustration style={{ width: '38px', height: '38px' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <h2 style={{ fontSize: '1.5rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
                CPSE MATERIAL MASTER EXPLORER
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
                {materials.length} RECORDS LOADED
              </span>
            </div>
            <p style={{ margin: '0.25rem 0 0 0', color: tokens.colors.textSecondary, fontSize: '0.875rem' }}>
              Search & inspect normalized material records and derived technical attributes across Oil India, NTPC, IOCL and demo CPSEs
            </p>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {user && (user.role === 'REVIEWER' || user.role === 'VIEWER') ? (
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.45rem',
              padding: '0.5rem 0.85rem',
              background: tokens.colors.surfaceSubtle,
              border: `1px solid ${tokens.colors.border}`,
              borderRadius: '0.5rem',
              color: tokens.colors.textMuted,
              fontSize: '0.75rem',
              fontWeight: 800
            }}>
              <Lock style={{ width: '13px', height: '13px' }} />
              IMPORT ACCESS RESTRICTED
            </div>
          ) : (
            <button
              onClick={() => alert('Import Materials: Dataset ingestion active via backend CLI / pipeline. Super Admin ingestion authorized.')}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.45rem',
                padding: '0.5rem 1rem',
                background: tokens.colors.primary,
                color: '#ffffff',
                border: 'none',
                borderRadius: '0.5rem',
                fontWeight: 700,
                fontSize: '0.85rem',
                cursor: 'pointer',
                boxShadow: tokens.shadows.sm
              }}
            >
              <Upload style={{ width: '15px', height: '15px' }} />
              Import Materials
            </button>
          )}

          <button
            onClick={fetchMaterials}
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
            Refresh Records
          </button>
        </div>
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
        <form onSubmit={handleSearchSubmit} style={{ flex: 1, minWidth: '260px', display: 'flex', gap: '0.5rem' }}>
          <div style={{ position: 'relative', flex: 1 }}>
            <Search style={{ position: 'absolute', left: '0.75rem', top: '50%', transform: 'translateY(-50%)', width: '16px', height: '16px', color: tokens.colors.textSecondary }} />
            <input
              type="text"
              placeholder="Search code or description..."
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
          value={provenanceFilter}
          onChange={(e) => setProvenanceFilter(e.target.value)}
          style={{
            padding: '0.5rem 0.75rem',
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.375rem',
            color: tokens.colors.textPrimary,
            fontSize: '0.875rem',
            fontWeight: 600
          }}
        >
          <option value="">All Provenance</option>
          <option value="REAL_PUBLIC">Real Public (Hugging Face)</option>
          <option value="CONTROLLED_GOLDEN_DEMO">Controlled Demo (Golden)</option>
          <option value="SYNTHETIC_DEMO">Synthetic Demo</option>
        </select>

        <select
          value={cpseFilter}
          onChange={(e) => setCpseFilter(e.target.value)}
          style={{
            padding: '0.5rem 0.75rem',
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.375rem',
            color: tokens.colors.textPrimary,
            fontSize: '0.875rem'
          }}
        >
          <option value="">All CPSEs</option>
          <option value="OIL">Oil India Limited (OIL)</option>
          <option value="NTPC">NTPC Limited</option>
          <option value="IOCL">Indian Oil Corporation (IOCL)</option>
          <option value="CPSE-A">CPSE-A (Thermal Power Demo)</option>
          <option value="CPSE-B">CPSE-B (Refinery Demo)</option>
          <option value="CPSE-C">CPSE-C (Exploration Demo)</option>
          <option value="CPSE-D">CPSE-D (Heavy Eng. Demo)</option>
        </select>

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
          <option value="UNCLASSIFIED">UNCLASSIFIED</option>
        </select>
      </div>

      {/* Materials Table */}
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
          <p style={{ fontWeight: 600 }}>Loading CPSE material records...</p>
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
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>CPSE</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>PROVENANCE</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>SOURCE CODE</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>RAW DESCRIPTION</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>NORMALIZED TEXT</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>CATEGORY</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>ATTRIBUTES</th>
                <th style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, fontWeight: 700 }}>MAPPED NMC</th>
                <th style={{ padding: '0.75rem 1rem', textAlign: 'right', color: tokens.colors.textSecondary, fontWeight: 700 }}>ACTION</th>
              </tr>
            </thead>
            <tbody>
              {materials.map((m) => (
                <tr key={m.id} style={{ borderBottom: `1px solid ${tokens.colors.border}` }}>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 800, padding: '0.2rem 0.5rem', background: '#DCFCE7', color: tokens.colors.primary, borderRadius: '0.25rem', border: '1px solid #BBF7D0' }}>
                      {m.cpse_code}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {m.provenance === 'REAL_PUBLIC' ? (
                      <span style={{
                        fontSize: '0.65rem',
                        fontWeight: 800,
                        padding: '0.15rem 0.5rem',
                        background: 'rgba(37, 99, 235, 0.1)',
                        color: '#2563eb',
                        border: '1px solid rgba(37, 99, 235, 0.25)',
                        borderRadius: '0.25rem',
                        letterSpacing: '0.03em',
                        whiteSpace: 'nowrap'
                      }}>
                        REAL PUBLIC
                      </span>
                    ) : m.provenance === 'CONTROLLED_GOLDEN_DEMO' ? (
                      <span style={{
                        fontSize: '0.65rem',
                        fontWeight: 800,
                        padding: '0.15rem 0.5rem',
                        background: 'rgba(234, 179, 8, 0.15)',
                        color: '#ca8a04',
                        border: '1px solid rgba(234, 179, 8, 0.3)',
                        borderRadius: '0.25rem',
                        letterSpacing: '0.03em',
                        whiteSpace: 'nowrap'
                      }}>
                        GOLDEN DEMO
                      </span>
                    ) : (
                      <span style={{
                        fontSize: '0.65rem',
                        fontWeight: 700,
                        padding: '0.15rem 0.45rem',
                        background: tokens.colors.surfaceSubtle,
                        color: tokens.colors.textSecondary,
                        borderRadius: '0.25rem',
                        whiteSpace: 'nowrap'
                      }}>
                        SYNTHETIC
                      </span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', fontFamily: 'monospace' }}>
                    <Link
                      href={`/materials/${m.id}`}
                      style={{ color: tokens.colors.primary, fontWeight: 700, textDecoration: 'none' }}
                    >
                      {m.source_code}
                    </Link>
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: tokens.colors.textPrimary, fontWeight: 600, maxWidth: '240px', lineHeight: 1.3 }}>
                    {m.raw_description}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: tokens.colors.textSecondary, maxWidth: '200px', fontSize: '0.8rem' }}>
                    {m.normalized_text || '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    <span style={{ fontSize: '0.7rem', fontWeight: 700, padding: '0.15rem 0.45rem', background: '#0F766E', color: '#fff', borderRadius: '0.25rem' }}>
                      {m.category_code}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem 1rem', color: tokens.colors.textPrimary }}>
                    {m.attributes.length > 0 ? (
                      <span style={{ fontSize: '0.75rem', background: tokens.colors.surfaceSubtle, padding: '0.2rem 0.5rem', borderRadius: '0.25rem', border: `1px solid ${tokens.colors.border}`, fontWeight: 600 }}>
                        {m.attributes.length} extracted
                      </span>
                    ) : '—'}
                  </td>
                  <td style={{ padding: '0.75rem 1rem' }}>
                    {m.mapping_nmc ? (
                      <span style={{ fontSize: '0.7rem', fontFamily: 'monospace', fontWeight: 800, background: '#DCFCE7', color: tokens.colors.success, padding: '0.2rem 0.5rem', borderRadius: '0.25rem', border: '1px solid #BBF7D0' }}>
                        {m.mapping_nmc}
                      </span>
                    ) : (
                      <span style={{ fontSize: '0.7rem', color: tokens.colors.textSecondary, fontStyle: 'italic' }}>Unmapped</span>
                    )}
                  </td>
                  <td style={{ padding: '0.75rem 1rem', textAlign: 'right' }}>
                    <Link
                      href={`/materials/${m.id}`}
                      style={{
                        padding: '0.35rem 0.75rem',
                        background: tokens.colors.surfaceSubtle,
                        color: tokens.colors.primary,
                        border: `1px solid ${tokens.colors.border}`,
                        borderRadius: '0.375rem',
                        fontSize: '0.75rem',
                        fontWeight: 700,
                        textDecoration: 'none',
                        display: 'inline-flex',
                        alignItems: 'center',
                        gap: '0.25rem'
                      }}
                    >
                      Detail <ArrowRight style={{ width: '12px', height: '12px' }} />
                    </Link>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </AppShell>
  );
}
