'use client';

import React from 'react';
import { tokens } from './tokens';

interface EvidenceBarsProps {
  semanticScore?: number;
  lexicalScore?: number;
  attributeScore?: number;
  categoryScore?: number;
  isVetoed?: boolean;
}

export default function EvidenceBars({
  semanticScore = 0.96,
  lexicalScore = 0.93,
  attributeScore = 0.89,
  categoryScore = 1.0,
  isVetoed = false
}: EvidenceBarsProps) {
  const bars = [
    { label: 'SEMANTIC SIMILARITY', score: semanticScore, color: '#0284c7' },
    { label: 'LEXICAL OVERLAP', score: lexicalScore, color: '#0d9488' },
    { label: 'ATTRIBUTE COMPATIBILITY', score: isVetoed ? 0.0 : attributeScore, color: isVetoed ? tokens.colors.danger : tokens.colors.primary, note: isVetoed ? 'VETO OVERRIDE' : undefined },
    { label: 'CATEGORY ALIGNMENT', score: categoryScore, color: tokens.colors.success },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1rem' }}>
      {bars.map((bar, idx) => {
        const pct = Math.round(bar.score * 100);
        return (
          <div key={idx}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.725rem', fontWeight: 700, color: tokens.colors.textSecondary, marginBottom: '0.25rem' }}>
              <span>{bar.label}</span>
              <span style={{ color: bar.color }}>
                {bar.note ? `${bar.note} (${pct}%)` : `${pct}%`}
              </span>
            </div>
            <div style={{ height: '8px', background: tokens.colors.surfaceSubtle, borderRadius: '4px', overflow: 'hidden', border: `1px solid ${tokens.colors.border}` }}>
              <div style={{
                height: '100%',
                width: `${pct}%`,
                background: bar.color,
                borderRadius: '4px',
                transition: 'width 0.4s ease'
              }} />
            </div>
          </div>
        );
      })}
    </div>
  );
}
