'use client';

import React from 'react';
import { tokens } from '../design-system/tokens';

interface IndustrialHeroDiagramProps {
  className?: string;
  style?: React.CSSProperties;
}

export default function IndustrialHeroDiagram({ className, style }: IndustrialHeroDiagramProps) {
  return (
    <div
      className={className}
      style={{
        background: 'var(--surface, #ffffff)',
        border: '1px solid var(--border, #e2e8f0)',
        borderRadius: '0.875rem',
        padding: '1.5rem',
        boxShadow: 'var(--shadow-card, 0 4px 6px -1px rgba(0, 0, 0, 0.05))',
        position: 'relative',
        overflow: 'hidden',
        ...style
      }}
    >
      {/* Background subtle engineering grid pattern */}
      <svg
        aria-hidden="true"
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          width: '100%',
          height: '100%',
          opacity: 0.04,
          pointerEvents: 'none'
        }}
      >
        <defs>
          <pattern id="industrial-grid" width="24" height="24" patternUnits="userSpaceOnUse">
            <path d="M 24 0 L 0 0 0 24" fill="none" stroke="currentColor" strokeWidth="0.8" />
          </pattern>
        </defs>
        <rect width="100%" height="100%" fill="url(#industrial-grid)" />
      </svg>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.25rem', position: 'relative' }}>
        <div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.2rem' }}>
            <span style={{
              fontSize: '0.65rem',
              fontWeight: 800,
              letterSpacing: '0.08em',
              textTransform: 'uppercase',
              color: 'var(--primary, #047857)',
              background: 'var(--primary-light, #d1fae5)',
              padding: '0.15rem 0.5rem',
              borderRadius: '0.25rem'
            }}>
              System Architecture Flow
            </span>
            <span style={{ fontSize: '0.75rem', fontWeight: 600, color: 'var(--text-muted, #64748b)' }}>
              Deterministic Engineering Pipeline
            </span>
          </div>
          <h4 style={{ fontSize: '1.05rem', fontWeight: 800, margin: 0, color: 'var(--text-primary, #0f172a)' }}>
            One National Language for Industrial Materials
          </h4>
        </div>
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: '0.4rem',
          fontSize: '0.7rem',
          fontWeight: 700,
          color: '#16a34a',
          background: 'rgba(22, 163, 74, 0.1)',
          padding: '0.25rem 0.6rem',
          borderRadius: '9999px'
        }}>
          <span style={{ width: '6px', height: '6px', borderRadius: '50%', background: '#16a34a' }} />
          <span>REAL PUBLIC DATA VERIFIED</span>
        </div>
      </div>

      {/* Interactive Process Pipeline Diagram */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))',
        gap: '0.75rem',
        position: 'relative'
      }}>
        {/* Step 1: Real Public Data */}
        <div style={{
          background: 'var(--surface-subtle, #f8fafc)',
          border: '1px solid var(--border, #e2e8f0)',
          borderRadius: '0.625rem',
          padding: '0.85rem',
          position: 'relative'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-muted, #64748b)' }}>01 SOURCE</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--primary, #047857)" strokeWidth="1.8">
              <path d="M4 6h16M4 12h16M4 18h16" />
              <rect x="2" y="3" width="20" height="18" rx="2" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-primary, #0f172a)', marginBottom: '0.2rem' }}>
            CPSE Catalogs
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            Oil India &bull; NTPC &bull; IOCL
            <span style={{ display: 'block', fontSize: '0.65rem', color: 'var(--text-muted, #64748b)', marginTop: '0.2rem' }}>
              21,513 Public Rows
            </span>
          </div>
        </div>

        {/* Step 2: Normalization */}
        <div style={{
          background: 'var(--surface-subtle, #f8fafc)',
          border: '1px solid var(--border, #e2e8f0)',
          borderRadius: '0.625rem',
          padding: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-muted, #64748b)' }}>02 CLEAN</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="var(--teal, #0d9488)" strokeWidth="1.8">
              <path d="M12 3v18M3 12h18M7.5 7.5l9 9M16.5 7.5l-9 9" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-primary, #0f172a)', marginBottom: '0.2rem' }}>
            Normalization
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            UoM conversion &amp; regex standard abbreviations
          </div>
        </div>

        {/* Step 3: AI Retrieval */}
        <div style={{
          background: 'var(--surface-subtle, #f8fafc)',
          border: '1px solid var(--border, #e2e8f0)',
          borderRadius: '0.625rem',
          padding: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-muted, #64748b)' }}>03 AI SEARCH</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#2563eb" strokeWidth="1.8">
              <circle cx="11" cy="11" r="8" />
              <line x1="21" y1="21" x2="16.65" y2="16.65" />
              <path d="M11 8v6M8 11h6" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-primary, #0f172a)', marginBottom: '0.2rem' }}>
            pgvector HNSW
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            384-dim semantic candidate blocking
          </div>
        </div>

        {/* Step 4: Technical Attributes */}
        <div style={{
          background: 'var(--surface-subtle, #f8fafc)',
          border: '1px solid var(--border, #e2e8f0)',
          borderRadius: '0.625rem',
          padding: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-muted, #64748b)' }}>04 PARSING</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#7c3aed" strokeWidth="1.8">
              <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
              <polyline points="14 2 14 8 20 8" />
              <line x1="16" y1="13" x2="8" y2="13" />
              <line x1="16" y1="17" x2="8" y2="17" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-primary, #0f172a)', marginBottom: '0.2rem' }}>
            Typed Attributes
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            Grade, DN, PN, schedule, pitch, standards
          </div>
        </div>

        {/* Step 5: Engineering Veto Lattice */}
        <div style={{
          background: 'rgba(239, 68, 68, 0.04)',
          border: '1px solid rgba(239, 68, 68, 0.25)',
          borderRadius: '0.625rem',
          padding: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: '#dc2626' }}>05 SAFETY</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#dc2626" strokeWidth="1.8">
              <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
              <line x1="12" y1="8" x2="12" y2="12" />
              <line x1="12" y1="16" x2="12.01" y2="16" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#dc2626', marginBottom: '0.2rem' }}>
            Veto Lattice (G0–G6)
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            Deterministic rule veto overrides AI similarity
          </div>
        </div>

        {/* Step 6: Human Governance */}
        <div style={{
          background: 'var(--surface-subtle, #f8fafc)',
          border: '1px solid var(--border, #e2e8f0)',
          borderRadius: '0.625rem',
          padding: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: 'var(--text-muted, #64748b)' }}>06 REVIEW</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#f59e0b" strokeWidth="1.8">
              <path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2" />
              <circle cx="9" cy="7" r="4" />
              <polyline points="16 11 18 13 22 9" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: 'var(--text-primary, #0f172a)', marginBottom: '0.2rem' }}>
            Dual-Key RBAC
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            Reviewer claim + Admin approval workflow
          </div>
        </div>

        {/* Step 7: National Material Master */}
        <div style={{
          background: 'rgba(16, 185, 129, 0.06)',
          border: '1px solid rgba(16, 185, 129, 0.3)',
          borderRadius: '0.625rem',
          padding: '0.85rem'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
            <span style={{ fontSize: '0.65rem', fontWeight: 800, color: '#059669' }}>07 UNIFIED</span>
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="#059669" strokeWidth="1.8">
              <polygon points="12 2 2 7 12 12 22 7 12 2" />
              <polyline points="2 17 12 22 22 17" />
              <polyline points="2 12 12 17 22 12" />
            </svg>
          </div>
          <div style={{ fontSize: '0.8rem', fontWeight: 800, color: '#059669', marginBottom: '0.2rem' }}>
            National Code (NMC)
          </div>
          <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary, #475569)', lineHeight: 1.3 }}>
            NMC-BOLT-00000001 &bull; SAP 40-char sync
          </div>
        </div>
      </div>

      {/* Bottom Architectural Credibility Line */}
      <div style={{
        marginTop: '1.25rem',
        paddingTop: '0.75rem',
        borderTop: '1px solid var(--border, #e2e8f0)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        flexWrap: 'wrap',
        gap: '0.5rem',
        fontSize: '0.75rem',
        color: 'var(--text-muted, #64748b)'
      }}>
        <div>
          <strong style={{ color: 'var(--text-primary, #0f172a)' }}>Core SIH Philosophy:</strong>{' '}
          AI assists discovery. Engineering rules protect decisions. Humans govern the final decision.
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span>Public Source Demonstration Data</span>
          <span>&bull;</span>
          <span>Controlled Safety Scenarios</span>
        </div>
      </div>
    </div>
  );
}
