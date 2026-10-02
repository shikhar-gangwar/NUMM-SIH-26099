import React from 'react';

export default function Home() {
  return (
    <main style={{ padding: '2rem', maxWidth: '1200px', margin: '0 auto' }}>
      <header style={{ borderBottom: '1px solid #e2e8f0', paddingBottom: '1rem', marginBottom: '2rem' }}>
        <h1 style={{ fontSize: '1.875rem', fontWeight: 700, color: '#1e293b' }}>
          National Unified Material Master Framework
        </h1>
        <p style={{ color: '#64748b' }}>SIH 2026 · PS 26099 — AI-Driven Material Standardization Across CPSEs</p>
      </header>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        <div style={{ background: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>System Status</h2>
          <p style={{ color: '#16a34a', fontWeight: 600 }}>✓ M0 Scaffold Initialized</p>
          <p style={{ fontSize: '0.875rem', color: '#64748b' }}>API Backend: Healthy (`/health` OK)</p>
        </div>

        <div style={{ background: '#ffffff', padding: '1.5rem', borderRadius: '0.5rem', boxShadow: '0 1px 3px rgba(0,0,0,0.1)' }}>
          <h2 style={{ fontSize: '1.25rem', fontWeight: 600, marginBottom: '0.5rem' }}>Quick Actions</h2>
          <a href="/login" style={{ display: 'inline-block', padding: '0.5rem 1rem', background: '#2563eb', color: '#fff', borderRadius: '0.375rem', textDecoration: 'none', fontWeight: 500 }}>
            Login to Governance Portal
          </a>
        </div>
      </div>
    </main>
  );
}
