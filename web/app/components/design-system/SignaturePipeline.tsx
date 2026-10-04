'use client';

import React from 'react';
import { Sparkles, FileText, Cpu, ShieldAlert, UserCheck, ArrowRight } from 'lucide-react';
import { tokens } from './tokens';
import { useTheme } from '../../context/ThemeContext';

export default function SignaturePipeline() {
  const { theme } = useTheme();
  const isDark = theme === 'dark';

  const steps = [
    {
      title: 'AI Candidate Retrieval',
      subtitle: 'pgvector HNSW + SVD Top-K',
      icon: Sparkles,
      color: isDark ? '#FACC15' : '#CA8A04',
      bg: isDark ? 'var(--surface-2)' : '#FEFCE8',
      badge: '95.5% Search Pruning'
    },
    {
      title: 'Semantic & Lexical Signals',
      subtitle: 'all-MiniLM-L6-v2 + RapidFuzz',
      icon: FileText,
      color: isDark ? '#38BDF8' : '#0284C7',
      bg: isDark ? 'var(--surface-2)' : '#F0F9FF',
      badge: 'Dual-Channel Match'
    },
    {
      title: 'Technical Attribute Engine',
      subtitle: 'Dimensional & UOM Canonicalization',
      icon: Cpu,
      color: isDark ? '#60A5FA' : '#2563EB',
      bg: isDark ? 'var(--surface-2)' : '#EFF6FF',
      badge: 'Typed Comparators'
    },
    {
      title: 'Veto Lattice Safety Gates',
      subtitle: 'Hard Property Checks (G0–G6)',
      icon: ShieldAlert,
      color: isDark ? '#EF4444' : '#DC2626',
      bg: isDark ? 'var(--surface-2)' : '#FEF2F2',
      badge: 'Mandatory Veto'
    },
    {
      title: 'Human Steward Governance',
      subtitle: 'Atomic NMC Issuance & Mapping',
      icon: UserCheck,
      color: isDark ? '#22C55E' : '#15803D',
      bg: isDark ? 'var(--surface-2)' : '#F0FDF4',
      badge: 'Final Authority'
    }
  ];

  return (
    <div style={{
      background: 'var(--surface-1)',
      border: '1px solid var(--border)',
      borderRadius: '0.75rem',
      padding: '1.25rem 1.5rem',
      boxShadow: isDark ? 'none' : tokens.shadows.card,
      marginBottom: '1.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: isDark ? '#FACC15' : '#166534' }} />
          <h3 style={{ fontSize: '0.95rem', fontWeight: 800, margin: 0, color: 'var(--text-primary)', letterSpacing: '-0.01em' }}>
            ARCHITECTURE DECISION FLOW
          </h3>
          <span style={{ fontSize: '0.75rem', color: 'var(--text-muted)', fontWeight: 500 }}>·</span>
          <span style={{ fontSize: '0.8rem', color: isDark ? '#FACC15' : '#166534', fontWeight: 700 }}>
            "AI assists. Rules protect. Humans govern."
          </span>
        </div>
        <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', background: 'var(--surface-2)', padding: '0.2rem 0.5rem', borderRadius: '0.25rem', fontWeight: 600, border: '1px solid var(--border)' }}>
          Deterministic Engine Invariant #1
        </div>
      </div>

      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(180px, 1fr))',
        gap: '0.75rem',
        alignItems: 'stretch'
      }}>
        {steps.map((step, idx) => {
          const Icon = step.icon;
          return (
            <div key={idx} style={{
              background: step.bg,
              border: isDark ? '1px solid var(--border)' : `1px solid var(--border)`,
              borderTop: isDark ? `3px solid ${step.color}` : '1px solid var(--border)',
              borderRadius: '0.5rem',
              padding: '0.85rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between',
              position: 'relative'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
                  <div style={{
                    width: '28px',
                    height: '28px',
                    borderRadius: '0.375rem',
                    background: isDark ? 'var(--surface-3)' : '#ffffff',
                    border: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    color: step.color
                  }}>
                    <Icon style={{ width: '15px', height: '15px' }} />
                  </div>
                  <span style={{
                    fontSize: '0.65rem',
                    fontWeight: 700,
                    color: step.color,
                    background: isDark ? 'var(--surface-3)' : '#ffffff',
                    padding: '0.15rem 0.35rem',
                    borderRadius: '0.25rem',
                    border: '1px solid var(--border)'
                  }}>
                    {step.badge}
                  </span>
                </div>
                <div style={{ fontSize: '0.825rem', fontWeight: 700, color: 'var(--text-primary)', marginBottom: '0.25rem' }}>
                  {step.title}
                </div>
                <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)', lineHeight: '1.3' }}>
                  {step.subtitle}
                </div>
              </div>

              {idx < steps.length - 1 && (
                <div style={{ display: 'none' }}>
                  <ArrowRight style={{ width: '14px', height: '14px', color: 'var(--text-muted)' }} />
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
}
