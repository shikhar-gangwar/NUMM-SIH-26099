'use client';

import React, { useEffect, useState } from 'react';
import { useRouter, usePathname } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import DemoModeModal from './DemoModeModal';
import { useTheme } from '../context/ThemeContext';
import {
  ShieldCheck,
  LayoutDashboard,
  GitPullRequest,
  Box,
  Layers,
  BarChart3,
  FileCheck,
  Download,
  LogOut,
  User,
  CheckCircle2,
  RefreshCw,
  Sparkles,
  Sun,
  Moon
} from 'lucide-react';


interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const { user, token, logout, isLoading } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const router = useRouter();
  const pathname = usePathname();
  const [isDemoModalOpen, setIsDemoModalOpen] = useState(false);

  useEffect(() => {
    if (!isLoading && !token) {
      router.push('/login');
    }
  }, [isLoading, token, router]);

  if (isLoading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', background: '#0b1329', color: '#94a3b8' }}>
        <div style={{ textAlign: 'center' }}>
          <ShieldCheck style={{ width: '40px', height: '40px', color: '#38bdf8', marginBottom: '1rem', animation: 'pulse 2s infinite' }} />
          <p style={{ margin: 0, fontWeight: 500 }}>Verifying authenticated session...</p>
        </div>
      </div>
    );
  }

  if (!token || !user) {
    return null;
  }

  const [isExporting, setIsExporting] = useState(false);
  const [exportSuccess, setExportSuccess] = useState(false);

  const handleLogout = () => {
    logout();
    router.push('/login');
  };

  const handleExportCSV = async () => {
    if (isExporting) return;
    setIsExporting(true);
    try {
      const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
      const response = await fetch(`${apiHost}/api/v1/exports/crosswalk.csv`, {
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });
      if (response.ok) {
        const contentDisposition = response.headers.get('content-disposition');
        let filename = `national_material_crosswalk_${new Date().toISOString().slice(0, 10)}.csv`;
        if (contentDisposition) {
          const match = contentDisposition.match(/filename="?([^";]+)"?/);
          if (match && match[1]) filename = match[1];
        }
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        a.remove();
        setExportSuccess(true);
        setTimeout(() => setExportSuccess(false), 2500);
      } else {
        alert(`Failed to generate export file (HTTP ${response.status})`);
      }
    } catch (e) {
      console.error('Export error:', e);
      alert('Network error during crosswalk export');
    } finally {
      setIsExporting(false);
    }
  };

  const navSections = [
    {
      title: 'COMMAND CENTER',
      items: [
        { label: 'Dashboard', href: '/governance', icon: LayoutDashboard },
      ]
    },
    {
      title: 'DATA',
      items: [
        { label: 'Materials Master', href: '/materials', icon: Box },
      ]
    },
    {
      title: 'INTELLIGENCE',
      items: [
        { label: 'AI Matching Engine', href: '/matching', icon: Sparkles },
        { label: 'Review Queue', href: '/reviews', icon: GitPullRequest },
      ]
    },
    {
      title: 'MASTER DATA',
      items: [
        { label: 'National Material Master', href: '/national-materials', icon: Layers },
      ]
    },
    {
      title: 'INSIGHTS',
      items: [
        { label: 'Analytics & Procurement', href: '/analytics', icon: BarChart3 },
      ]
    },
    {
      title: 'GOVERNANCE',
      items: [
        { label: 'Audit Trail', href: '/audit', icon: FileCheck },
      ]
    },
    {
      title: 'INTEGRATION',
      items: [
        { label: 'Mock SAP S/4HANA', href: '/integration', icon: RefreshCw },
      ]
    }
  ];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column', backgroundColor: 'var(--background)', color: 'var(--text-primary)' }}>
      {/* Top Bar */}
      <header style={{
        height: '64px',
        borderBottom: '1px solid var(--border)',
        backgroundColor: 'var(--surface-1)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        padding: '0 1.75rem',
        position: 'sticky',
        top: 0,
        zIndex: 50,
        boxShadow: theme === 'dark' ? 'none' : '0 1px 2px 0 rgba(0, 0, 0, 0.04)'
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
          <div style={{
            background: theme === 'dark' ? 'linear-gradient(135deg, #171717 0%, #1e1e1e 100%)' : 'linear-gradient(135deg, #166534 0%, #14532d 100%)',
            padding: '0.45rem',
            borderRadius: '0.5rem',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            border: theme === 'dark' ? '1px solid #3a3a3a' : 'none',
            boxShadow: theme === 'dark' ? '0 2px 4px rgba(0, 0, 0, 0.4)' : '0 2px 4px rgba(22, 101, 52, 0.2)'
          }}>
            <ShieldCheck style={{ width: '22px', height: '22px', color: theme === 'dark' ? '#facc15' : '#ffffff' }} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '1.1rem', fontWeight: 900, color: theme === 'dark' ? '#facc15' : '#166534', letterSpacing: '-0.02em' }}>
                NUMM
              </span>
              <span style={{ fontSize: '0.85rem', fontWeight: 700, color: 'var(--text-primary)' }}>
                National Unified Material Master
              </span>
              <span style={{
                fontSize: '0.65rem',
                background: theme === 'dark' ? 'rgba(250, 204, 21, 0.12)' : '#dcfce7',
                color: theme === 'dark' ? '#facc15' : '#166534',
                border: theme === 'dark' ? '1px solid rgba(250, 204, 21, 0.3)' : '1px solid #bbf7d0',
                padding: '0.1rem 0.45rem',
                borderRadius: '0.25rem',
                fontWeight: 700,
                letterSpacing: '0.02em'
              }}>
                SIH 2026 PROTOTYPE
              </span>
            </div>
            <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)' }}>
              AI-Assisted Material Standardization & Governance Across CPSEs
            </div>
          </div>
        </div>

        {/* Global Actions & User Identity */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          {/* Active Engine Health Badge */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            padding: '0.35rem 0.65rem',
            background: theme === 'dark' ? 'rgba(34, 197, 94, 0.12)' : '#f0fdf4',
            border: theme === 'dark' ? '1px solid rgba(34, 197, 94, 0.3)' : '1px solid #bbf7d0',
            borderRadius: '0.375rem',
            fontSize: '0.725rem',
            fontWeight: 700,
            color: theme === 'dark' ? '#22c55e' : '#15803d'
          }}>
            <span style={{ width: '7px', height: '7px', borderRadius: '50%', background: '#22c55e' }} />
            <span>AI Engine Online</span>
          </div>

          {/* SIH Demo Mode Trigger */}
          <button
            onClick={() => setIsDemoModalOpen(true)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.45rem 0.85rem',
              background: theme === 'dark' ? 'linear-gradient(135deg, #facc15 0%, #eab308 100%)' : 'linear-gradient(135deg, #059669 0%, #047857 100%)',
              color: theme === 'dark' ? '#080808' : '#ffffff',
              border: 'none',
              borderRadius: '0.375rem',
              fontSize: '0.8rem',
              fontWeight: 800,
              cursor: 'pointer',
              boxShadow: theme === 'dark' ? '0 2px 8px rgba(250, 204, 21, 0.25)' : '0 2px 4px rgba(5, 150, 105, 0.25)',
              transition: 'all 0.15s'
            }}
          >
            <Sparkles style={{ width: '14px', height: '14px' }} />
            ⚡ SIH Demo Mode
          </button>

          {/* Export Crosswalk CSV */}
          <button
            onClick={handleExportCSV}
            disabled={isExporting}
            title="Download authoritative multi-CPSE legacy code crosswalk CSV (RFC 4180)"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.45rem 0.75rem',
              background: exportSuccess
                ? (theme === 'dark' ? 'rgba(34, 197, 94, 0.2)' : '#dcfce7')
                : 'var(--surface-2)',
              color: exportSuccess
                ? (theme === 'dark' ? '#4ade80' : '#15803d')
                : 'var(--text-primary)',
              border: exportSuccess
                ? (theme === 'dark' ? '1px solid rgba(34, 197, 94, 0.4)' : '1px solid #86efac')
                : '1px solid var(--border)',
              borderRadius: '0.375rem',
              fontSize: '0.8rem',
              fontWeight: 600,
              cursor: isExporting ? 'wait' : 'pointer',
              transition: 'all 0.2s cubic-bezier(0.16, 1, 0.3, 1)'
            }}
          >
            {isExporting ? (
              <RefreshCw style={{ width: '14px', height: '14px', animation: 'spin 1s linear infinite' }} />
            ) : exportSuccess ? (
              <CheckCircle2 style={{ width: '14px', height: '14px', color: '#10b981' }} />
            ) : (
              <Download style={{ width: '14px', height: '14px', color: 'var(--text-muted)' }} />
            )}
            {isExporting ? 'Exporting...' : exportSuccess ? 'Exported!' : 'Export Crosswalk'}
          </button>

          {/* Theme Toggle (Light / Dark) */}
          <button
            onClick={toggleTheme}
            title={`Switch to ${theme === 'light' ? 'Dark' : 'Light'} Mode`}
            aria-label="Toggle Theme"
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: '34px',
              height: '34px',
              background: theme === 'dark' ? '#171717' : '#ffffff',
              color: theme === 'dark' ? '#facc15' : '#475569',
              border: theme === 'dark' ? '1px solid #2a2a2a' : '1px solid #cbd5e1',
              borderRadius: '0.375rem',
              cursor: 'pointer',
              transition: 'all 0.15s'
            }}
          >
            {theme === 'dark' ? (
              <Sun style={{ width: '16px', height: '16px', color: '#facc15' }} />
            ) : (
              <Moon style={{ width: '16px', height: '16px', color: '#475569' }} />
            )}
          </button>

          {/* User Role Card */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.6rem',
            background: 'var(--surface-2)',
            padding: '0.35rem 0.85rem',
            borderRadius: '0.375rem',
            border: '1px solid var(--border)'
          }}>
            <User style={{ width: '15px', height: '15px', color: theme === 'dark' ? '#facc15' : '#166534' }} />
            <div style={{ display: 'flex', flexDirection: 'column' }}>
              <span style={{ fontSize: '0.8rem', fontWeight: 700, color: 'var(--text-primary)', lineHeight: 1.1 }}>{user.username}</span>
              <span style={{ fontSize: '0.625rem', color: 'var(--text-muted)' }}>
                {user.role === 'SUPER_ADMIN' ? 'Full Control' : user.role === 'REVIEWER' ? 'View Only' : 'Stewardship'}
              </span>
            </div>
            <span style={{
              fontSize: '0.65rem',
              padding: '0.15rem 0.45rem',
              background: user.role === 'SUPER_ADMIN'
                ? (theme === 'dark' ? '#facc15' : '#166534')
                : user.role === 'REVIEWER'
                  ? (theme === 'dark' ? 'rgba(56, 189, 248, 0.2)' : '#e0f2fe')
                  : '#0284c7',
              color: user.role === 'SUPER_ADMIN'
                ? (theme === 'dark' ? '#080808' : '#ffffff')
                : user.role === 'REVIEWER'
                  ? (theme === 'dark' ? '#38bdf8' : '#0369a1')
                  : '#ffffff',
              border: user.role === 'REVIEWER' ? `1px solid ${theme === 'dark' ? 'rgba(56, 189, 248, 0.4)' : '#bae6fd'}` : 'none',
              borderRadius: '0.25rem',
              fontWeight: 800,
              letterSpacing: '0.02em',
              whiteSpace: 'nowrap'
            }}>
              {user.role === 'SUPER_ADMIN' ? 'SUPER_ADMIN' : user.role === 'REVIEWER' ? 'REVIEWER — VIEW ONLY' : `${user.role}`}
            </span>
          </div>

          {/* Sign Out */}
          <button
            onClick={handleLogout}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '0.35rem',
              padding: '0.45rem 0.75rem',
              background: theme === 'dark' ? 'rgba(239, 68, 68, 0.15)' : '#fef2f2',
              color: '#ef4444',
              border: theme === 'dark' ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid #fecaca',
              borderRadius: '0.375rem',
              fontWeight: 600,
              fontSize: '0.8rem',
              cursor: 'pointer'
            }}
          >
            <LogOut style={{ width: '14px', height: '14px' }} />
            Sign Out
          </button>
        </div>
      </header>

      {/* Main Body */}
      <div style={{ display: 'flex', flex: 1 }}>
        {/* Sidebar */}
        <aside style={{
          width: '240px',
          borderRight: '1px solid var(--border)',
          backgroundColor: 'var(--surface-1)',
          padding: '1.25rem 0.75rem',
          display: 'flex',
          flexDirection: 'column',
          gap: '1.25rem'
        }}>
          {navSections.map((section, sIdx) => (
            <div key={sIdx}>
              <div style={{
                padding: '0 0.75rem 0.4rem',
                fontSize: '0.675rem',
                fontWeight: 800,
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.06em'
              }}>
                {section.title}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.2rem' }}>
                {section.items.map((item) => {
                  const Icon = item.icon;
                  const isActive = pathname === item.href || (item.href !== '/governance' && pathname.startsWith(item.href));
                  const activeBg = theme === 'dark' ? 'rgba(250, 204, 21, 0.12)' : '#dcfce7';
                  const activeColor = theme === 'dark' ? '#facc15' : '#166534';
                  const activeBorder = theme === 'dark' ? '3px solid #facc15' : '3px solid #166534';

                  return (
                    <button
                      key={item.href}
                      onClick={() => router.push(item.href)}
                      style={{
                        display: 'flex',
                        alignItems: 'center',
                        gap: '0.75rem',
                        padding: '0.55rem 0.75rem',
                        borderRadius: '0.375rem',
                        border: 'none',
                        background: isActive ? activeBg : 'transparent',
                        color: isActive ? activeColor : 'var(--text-secondary)',
                        fontSize: '0.85rem',
                        fontWeight: isActive ? 700 : 500,
                        cursor: 'pointer',
                        textAlign: 'left',
                        transition: 'all 0.15s',
                        borderLeft: isActive ? activeBorder : '3px solid transparent'
                      }}
                    >
                      <Icon style={{ width: '17px', height: '17px', color: isActive ? activeColor : 'var(--text-muted)' }} />
                      <span>{item.label}</span>
                    </button>
                  );
                })}
              </div>
            </div>
          ))}

          {/* Engine Status Footnote */}
          <div style={{
            marginTop: 'auto',
            padding: '0.85rem',
            background: 'var(--surface-2)',
            borderRadius: '0.5rem',
            border: '1px solid var(--border)',
            fontSize: '0.725rem'
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', color: theme === 'dark' ? '#22c55e' : '#15803d', fontWeight: 800, marginBottom: '0.2rem' }}>
              <span style={{ color: '#22c55e', fontSize: '0.85rem' }}>●</span>
              <span>AI Engine Online</span>
            </div>
            <div style={{ fontSize: '0.675rem', fontWeight: 700, color: 'var(--text-muted)' }}>
              SIH 2026 Prototype
            </div>
          </div>
        </aside>

        {/* Content Workspace Area */}
        <main style={{ flex: 1, padding: '1.75rem 2.25rem', overflowX: 'hidden', backgroundColor: 'var(--background)' }}>
          {children}
        </main>
      </div>

      {/* SIH Demo Mode Interactive Modal */}
      <DemoModeModal
        isOpen={isDemoModalOpen}
        onClose={() => setIsDemoModalOpen(false)}
      />
    </div>
  );
}
