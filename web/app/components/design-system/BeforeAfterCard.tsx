'use client';

import React from 'react';
import { CheckCircle2, GitMerge } from 'lucide-react';
import { tokens } from './tokens';

export default function BeforeAfterCard() {
  return (
    <div style={{
      background: tokens.colors.surface,
      border: `1px solid ${tokens.colors.border}`,
      borderRadius: '0.75rem',
      padding: '1.25rem 1.5rem',
      boxShadow: tokens.shadows.card,
      marginBottom: '1.5rem'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <h3 style={{ fontSize: '0.95rem', fontWeight: 800, margin: 0, color: tokens.colors.textPrimary }}>
            STANDARDIZATION IMPACT: BEFORE VS AFTER
          </h3>
          <p style={{ margin: '0.2rem 0 0 0', fontSize: '0.75rem', color: tokens.colors.textSecondary }}>
            How divergent legacy CPSE catalog descriptions collapse into a single National Unified Material
          </p>
        </div>
        <span style={{ fontSize: '0.7rem', padding: '0.2rem 0.5rem', background: tokens.colors.primaryLight, color: tokens.colors.primary, borderRadius: '0.25rem', fontWeight: 700, border: `1px solid ${tokens.colors.border}` }}>
          Real Database Entity Example
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr auto 1.2fr', gap: '1.25rem', alignItems: 'center' }}>
        {/* BEFORE: Divergent CPSE Descriptions */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          <div style={{ fontSize: '0.7rem', fontWeight: 800, color: tokens.colors.danger, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            BEFORE · DIVERGENT CPSE CATALOGS
          </div>

          <div style={{ background: tokens.colors.dangerBg, border: `1px solid ${tokens.colors.dangerBorder}`, borderRadius: '0.375rem', padding: '0.5rem 0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: tokens.colors.danger, fontWeight: 700, marginBottom: '0.15rem' }}>
              <span>CPSE: BHEL</span>
              <code>BHEL-BLT-0042</code>
            </div>
            <div style={{ fontSize: '0.775rem', color: tokens.colors.textPrimary, fontFamily: 'monospace' }}>
              HEX BOLT M12X60 GR 8.8 GALV
            </div>
          </div>

          <div style={{ background: tokens.colors.dangerBg, border: `1px solid ${tokens.colors.dangerBorder}`, borderRadius: '0.375rem', padding: '0.5rem 0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: tokens.colors.danger, fontWeight: 700, marginBottom: '0.15rem' }}>
              <span>CPSE: NTPC</span>
              <code>NTPC-FAST-9811</code>
            </div>
            <div style={{ fontSize: '0.775rem', color: tokens.colors.textPrimary, fontFamily: 'monospace' }}>
              M12 X 60MM HEXAGON HEAD BOLT GRADE 8.8
            </div>
          </div>

          <div style={{ background: tokens.colors.dangerBg, border: `1px solid ${tokens.colors.dangerBorder}`, borderRadius: '0.375rem', padding: '0.5rem 0.75rem' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: tokens.colors.danger, fontWeight: 700, marginBottom: '0.15rem' }}>
              <span>CPSE: IOCL</span>
              <code>IOCL-M12-BOLT</code>
            </div>
            <div style={{ fontSize: '0.775rem', color: tokens.colors.textPrimary, fontFamily: 'monospace' }}>
              BOLT HEX HD M12*60 8.8 GI
            </div>
          </div>
        </div>

        {/* HARMONIZATION TRANSITION */}
        <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center', padding: '0 0.5rem' }}>
          <div style={{
            width: '36px',
            height: '36px',
            borderRadius: '50%',
            background: tokens.colors.primaryLight,
            border: `1px solid ${tokens.colors.primaryBorder}`,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: tokens.colors.primary,
            marginBottom: '0.35rem'
          }}>
            <GitMerge style={{ width: '18px', height: '18px' }} />
          </div>
          <span style={{ fontSize: '0.65rem', fontWeight: 800, color: tokens.colors.primary, textTransform: 'uppercase' }}>
            NUMM Harmonization
          </span>
          <span style={{ fontSize: '0.6rem', color: tokens.colors.textMuted }}>
            Veto Verified
          </span>
        </div>

        {/* AFTER: Unified National Material */}
        <div style={{ background: tokens.colors.successBg, border: `1px solid ${tokens.colors.successBorder}`, borderRadius: '0.5rem', padding: '1rem' }}>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.5rem' }}>
            <div style={{ fontSize: '0.7rem', fontWeight: 800, color: tokens.colors.success, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              AFTER · UNIFIED NATIONAL MASTER
            </div>
            <span style={{ fontSize: '0.65rem', fontWeight: 700, background: tokens.colors.success, color: '#ffffff', padding: '0.15rem 0.4rem', borderRadius: '0.25rem' }}>
              SINGLE NMC
            </span>
          </div>

          <div style={{ background: tokens.colors.surface, border: `1px solid ${tokens.colors.border}`, borderRadius: '0.375rem', padding: '0.75rem', marginBottom: '0.5rem' }}>
            <div style={{ fontSize: '0.7rem', color: tokens.colors.textMuted, fontWeight: 600, marginBottom: '0.2rem' }}>
              NATIONAL MATERIAL CODE (ISO 7064 CHECK DIGIT)
            </div>
            <div style={{ fontSize: '1.05rem', fontWeight: 800, color: tokens.colors.primary, fontFamily: 'monospace' }}>
              NMC-BOLT-00000042-X
            </div>
            <div style={{ fontSize: '0.8rem', fontWeight: 600, color: tokens.colors.textPrimary, marginTop: '0.35rem' }}>
              HEX BOLT M12 X 60 GRADE 8.8 GALVANIZED
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.725rem', color: tokens.colors.textSecondary }}>
            <CheckCircle2 style={{ width: '14px', height: '14px', color: tokens.colors.success }} />
            <span>3 Legacy CPSE codes collapsed into 1 crosswalk entry (Zero Catalog Clutter)</span>
          </div>
        </div>
      </div>
    </div>
  );
}
