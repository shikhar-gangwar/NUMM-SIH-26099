'use client';

import React, { useEffect } from 'react';
import Link from 'next/link';
import { AlertTriangle, RefreshCw, LayoutDashboard } from 'lucide-react';

export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    // Log error to client console or monitoring service
    console.error('Unhandled route exception:', error);
  }, [error]);

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: '#0b1329',
      color: '#f8fafc',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '2rem'
    }}>
      <div style={{
        maxWidth: '520px',
        width: '100%',
        backgroundColor: '#0f172a',
        border: '1px solid #1e293b',
        borderRadius: '0.75rem',
        padding: '2rem',
        textAlign: 'center',
        boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.5)'
      }}>
        <div style={{
          display: 'inline-flex',
          alignItems: 'center',
          justifyContent: 'center',
          width: '56px',
          height: '56px',
          borderRadius: '50%',
          backgroundColor: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.3)',
          marginBottom: '1.25rem'
        }}>
          <AlertTriangle style={{ width: '28px', height: '28px', color: '#f87171' }} />
        </div>

        <h1 style={{ fontSize: '1.25rem', fontWeight: 700, margin: '0 0 0.5rem 0', color: '#f8fafc' }}>
          Application Exception Intercepted
        </h1>

        <p style={{ color: '#94a3b8', fontSize: '0.875rem', margin: '0 0 1.5rem 0', lineHeight: 1.5 }}>
          An error occurred while loading this view. The system remains stable and logged events have been preserved.
        </p>

        {error.message && (
          <div style={{
            backgroundColor: '#1e293b',
            border: '1px solid #334155',
            borderRadius: '0.375rem',
            padding: '0.75rem 1rem',
            fontSize: '0.8125rem',
            fontFamily: 'monospace',
            color: '#fca5a5',
            marginBottom: '1.5rem',
            textAlign: 'left',
            overflowX: 'auto'
          }}>
            {error.message}
          </div>
        )}

        <div style={{ display: 'flex', gap: '0.75rem', justifyContent: 'center' }}>
          <button
            onClick={() => reset()}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.625rem 1.25rem',
              backgroundColor: '#0284c7',
              color: '#ffffff',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              cursor: 'pointer'
            }}
          >
            <RefreshCw style={{ width: '16px', height: '16px' }} />
            Retry Action
          </button>

          <Link
            href="/governance"
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.625rem 1.25rem',
              backgroundColor: '#1e293b',
              color: '#e2e8f0',
              border: '1px solid #334155',
              borderRadius: '0.375rem',
              fontSize: '0.875rem',
              fontWeight: 600,
              textDecoration: 'none'
            }}
          >
            <LayoutDashboard style={{ width: '16px', height: '16px' }} />
            Go to Dashboard
          </Link>
        </div>
      </div>
    </div>
  );
}
