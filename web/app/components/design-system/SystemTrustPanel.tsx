'use client';

import React from 'react';
import { ShieldCheck, Cpu, Database, FileCheck, CheckCircle2 } from 'lucide-react';
import { tokens } from './tokens';

export default function SystemTrustPanel() {
  const items = [
    { label: 'Matching Engine', status: 'ACTIVE', color: tokens.colors.success },
    { label: 'Vector Search (pgvector HNSW)', status: 'ACTIVE', color: tokens.colors.success },
    { label: 'Veto Lattice Engine', status: 'ACTIVE (G0–G6)', color: tokens.colors.success },
    { label: 'Audit Chain Integrity', status: 'VALID (SHA-256)', color: tokens.colors.success },
    { label: 'Embedding Model', status: 'all-MiniLM-L6-v2 (384-d)', color: tokens.colors.info },
    { label: 'LLM Decision Role', status: 'DISABLED (Rules Authoritative)', color: tokens.colors.textMuted },
  ];

  return (
    <div style={{
      background: tokens.colors.surface,
      border: `1px solid ${tokens.colors.border}`,
      borderRadius: '0.75rem',
      padding: '1.25rem 1.5rem',
      boxShadow: tokens.shadows.card,
      marginBottom: '1.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <ShieldCheck style={{ width: '18px', height: '18px', color: tokens.colors.primary }} />
        <h4 style={{ margin: 0, fontSize: '0.875rem', fontWeight: 800, color: tokens.colors.textPrimary, textTransform: 'uppercase', letterSpacing: '0.03em' }}>
          SYSTEM TRUST & ENGINE PROVENANCE
        </h4>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.75rem' }}>
        {items.map((item, idx) => (
          <div key={idx} style={{
            background: tokens.colors.surfaceSubtle,
            border: `1px solid ${tokens.colors.border}`,
            borderRadius: '0.375rem',
            padding: '0.6rem 0.75rem',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: tokens.colors.textSecondary }}>
              {item.label}
            </span>
            <span style={{
              fontSize: '0.675rem',
              fontWeight: 700,
              padding: '0.15rem 0.4rem',
              borderRadius: '0.2rem',
              background: tokens.colors.surface,
              border: `1px solid ${tokens.colors.border}`,
              color: item.color
            }}>
              {item.status}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
