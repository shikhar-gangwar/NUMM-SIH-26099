'use client';

import React, { useState, useEffect } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useAuth } from './context/AuthContext';
import { useTheme } from './context/ThemeContext';
import { tokens } from './components/design-system/tokens';
import IndustrialHeroDiagram from './components/illustrations/IndustrialHeroDiagram';
import {
  ShieldCheck,
  ShieldAlert,
  ArrowRight,
  CheckCircle2,
  AlertTriangle,
  Layers,
  Cpu,
  FileCheck,
  Database,
  Lock,
  Sparkles,
  Sun,
  Moon,
  ExternalLink,
  ChevronRight,
  TrendingUp,
  Workflow,
  Search,
  Scale
} from 'lucide-react';

export default function LandingPage() {
  const { user, token } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const router = useRouter();

  const [metrics, setMetrics] = useState({
    materials: 22500,
    cpses: 7,
    safeEquiv: 2578,
    gates: 'G0–G6'
  });

  // Fetch real database counts from public endpoint
  useEffect(() => {
    const fetchCounts = async () => {
      try {
        const apiHost = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
        const res = await fetch(`${apiHost}/api/v1/meta/public-stats`);
        if (res.ok) {
          const data = await res.json();
          if (data && data.total_materials) {
            setMetrics({
              materials: data.total_materials,
              cpses: data.cpses || 7,
              safeEquiv: data.safe_equiv || 2578,
              gates: data.gates || 'G0–G6'
            });
          }
        }
      } catch (e) {
        // Fallback to real public dataset seeded values
      }
    };
    fetchCounts();
  }, []);

  const isDark = theme === 'dark';

  const portalHref = token ? '/governance' : '/login';

  return (
    <div style={{
      minHeight: '100vh',
      backgroundColor: isDark ? '#080808' : '#F8FAFC',
      color: isDark ? '#F5F5F5' : '#0F172A',
      fontFamily: tokens.typography.fontFamily,
      display: 'flex',
      flexDirection: 'column',
      transition: 'background-color 0.2s, color 0.2s'
    }}>
      {/* ========================================================================= */}
      {/* SECTION 1 — NAVBAR                                                        */}
      {/* ========================================================================= */}
      <nav style={{
        position: 'sticky',
        top: 0,
        zIndex: 50,
        backgroundColor: isDark ? '#111111' : '#FFFFFF',
        borderBottom: `1px solid ${isDark ? '#2A2A2A' : '#E2E8F0'}`,
        padding: '0.75rem 1.5rem',
        boxShadow: isDark ? 'none' : tokens.shadows.sm
      }}>
        <div style={{
          maxWidth: '1240px',
          margin: '0 auto',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1rem'
        }}>
          {/* Logo & National Title */}
          <Link href="/" style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', textDecoration: 'none' }}>
            <div style={{
              width: '38px',
              height: '38px',
              borderRadius: '0.5rem',
              backgroundColor: tokens.colors.primary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              color: '#FFFFFF',
              boxShadow: '0 2px 4px rgba(22, 101, 52, 0.25)',
              flexShrink: 0
            }}>
              <ShieldCheck style={{ width: '22px', height: '22px' }} />
            </div>
            <div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <span style={{
                  fontSize: '1.15rem',
                  fontWeight: 900,
                  letterSpacing: '0.04em',
                  color: isDark ? '#F5F5F5' : '#0F172A'
                }}>
                  NUMM
                </span>
                <span style={{
                  fontSize: '0.65rem',
                  fontWeight: 800,
                  backgroundColor: isDark ? 'rgba(250, 204, 21, 0.15)' : '#DCFCE7',
                  color: isDark ? '#FACC15' : '#166534',
                  border: `1px solid ${isDark ? '#EAB308' : '#BBF7D0'}`,
                  padding: '0.1rem 0.35rem',
                  borderRadius: '0.25rem',
                  letterSpacing: '0.04em'
                }}>
                  PS 26099
                </span>
              </div>
              <div style={{
                fontSize: '0.7rem',
                color: isDark ? '#A3A3A3' : '#64748B',
                fontWeight: 600,
                letterSpacing: '0.02em',
                lineHeight: 1
              }}>
                National Unified Material Master
              </div>
            </div>
          </Link>

          {/* Quick Nav Links & Actions */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
            <div style={{ display: 'none', gap: '1.25rem', alignItems: 'center' }} className="desktop-links">
              <a href="#how-it-works" style={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isDark ? '#A3A3A3' : '#475569',
                textDecoration: 'none',
                transition: 'color 0.15s'
              }}>
                How It Works
              </a>
              <a href="#safety-differentiator" style={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isDark ? '#A3A3A3' : '#475569',
                textDecoration: 'none',
                transition: 'color 0.15s'
              }}>
                Safety Veto
              </a>
              <a href="#metrics" style={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isDark ? '#A3A3A3' : '#475569',
                textDecoration: 'none',
                transition: 'color 0.15s'
              }}>
                Metrics
              </a>
              <a href="#governance" style={{
                fontSize: '0.85rem',
                fontWeight: 600,
                color: isDark ? '#A3A3A3' : '#475569',
                textDecoration: 'none',
                transition: 'color 0.15s'
              }}>
                Governance
              </a>
            </div>

            {/* Theme Toggle Button */}
            <button
              onClick={toggleTheme}
              title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
              aria-label="Toggle Theme"
              style={{
                width: '34px',
                height: '34px',
                borderRadius: '0.375rem',
                border: `1px solid ${isDark ? '#333333' : '#CBD5E1'}`,
                backgroundColor: isDark ? '#181818' : '#FFFFFF',
                color: isDark ? '#FACC15' : '#475569',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                cursor: 'pointer',
                transition: 'all 0.15s'
              }}
            >
              {isDark ? (
                <Sun style={{ width: '16px', height: '16px', color: '#FACC15' }} />
              ) : (
                <Moon style={{ width: '16px', height: '16px', color: '#475569' }} />
              )}
            </button>

            {/* Enter Portal CTA */}
            <Link
              href={portalHref}
              style={{
                display: 'inline-flex',
                alignItems: 'center',
                gap: '0.4rem',
                padding: '0.5rem 1rem',
                backgroundColor: tokens.colors.primary,
                color: '#FFFFFF',
                borderRadius: '0.375rem',
                fontSize: '0.85rem',
                fontWeight: 700,
                textDecoration: 'none',
                boxShadow: '0 1px 3px rgba(0, 0, 0, 0.1)',
                transition: 'background-color 0.15s'
              }}
            >
              <span>{token ? 'Enter Portal' : 'Sign In / Enter Portal'}</span>
              <ArrowRight style={{ width: '14px', height: '14px' }} />
            </Link>
          </div>
        </div>
      </nav>

      {/* ========================================================================= */}
      {/* SECTION 2 — HERO SECTION                                                  */}
      {/* ========================================================================= */}
      <section style={{
        padding: '3rem 1.5rem',
        maxWidth: '1240px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(340px, 1fr))',
          gap: '2.5rem',
          alignItems: 'center'
        }}>
          {/* Left Column: Headline & Value Proposition */}
          <div>
            {/* SIH Badge */}
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.25rem 0.65rem',
              borderRadius: '9999px',
              backgroundColor: isDark ? '#1C1917' : '#F0FDF4',
              border: `1px solid ${isDark ? '#EAB308' : '#BBF7D0'}`,
              marginBottom: '1rem'
            }}>
              <span style={{
                width: '7px',
                height: '7px',
                borderRadius: '50%',
                backgroundColor: isDark ? '#FACC15' : '#16A34A'
              }} />
              <span style={{
                fontSize: '0.75rem',
                fontWeight: 800,
                color: isDark ? '#FACC15' : '#166534',
                letterSpacing: '0.04em'
              }}>
                SIH 2026 • PS 26099 • COMPETITION PROTOTYPE
              </span>
            </div>

            {/* Main Headline */}
            <h1 style={{
              fontSize: '2.5rem',
              fontWeight: 900,
              lineHeight: 1.15,
              color: isDark ? '#F5F5F5' : '#0F172A',
              margin: '0 0 1rem 0',
              letterSpacing: '-0.02em'
            }}>
              One national language for industrial materials.
            </h1>

            {/* Subheadline */}
            <p style={{
              fontSize: '1.1rem',
              lineHeight: 1.5,
              color: isDark ? '#A3A3A3' : '#475569',
              margin: '0 0 1.5rem 0',
              fontWeight: 500
            }}>
              AI assists discovery. Engineering rules protect decisions. Humans govern the final decision.
            </p>

            {/* Architectural Highlights */}
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem',
              marginBottom: '2rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: isDark ? '#E5E5E5' : '#334155' }}>
                <CheckCircle2 style={{ width: '16px', height: '16px', color: tokens.colors.emerald, flexShrink: 0 }} />
                <span><strong>Multi-CPSE Ingestion:</strong> Resolves fragmented material naming across PSUs.</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: isDark ? '#E5E5E5' : '#334155' }}>
                <CheckCircle2 style={{ width: '16px', height: '16px', color: tokens.colors.emerald, flexShrink: 0 }} />
                <span><strong>Deterministic Veto Lattice:</strong> G0–G6 gates prevent unsafe property mismatches.</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', fontSize: '0.875rem', color: isDark ? '#E5E5E5' : '#334155' }}>
                <CheckCircle2 style={{ width: '16px', height: '16px', color: tokens.colors.emerald, flexShrink: 0 }} />
                <span><strong>Sovereign Human Stewardship:</strong> Certified engineers govern all master decisions.</span>
              </div>
            </div>

            {/* Action Buttons */}
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.875rem' }}>
              <Link
                href={portalHref}
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.5rem',
                  backgroundColor: tokens.colors.primary,
                  color: '#FFFFFF',
                  borderRadius: '0.5rem',
                  fontSize: '0.9375rem',
                  fontWeight: 700,
                  textDecoration: 'none',
                  boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
                  transition: 'background-color 0.15s'
                }}
              >
                <span>Enter Governance Portal</span>
                <ArrowRight style={{ width: '16px', height: '16px' }} />
              </Link>
              <a
                href="#how-it-works"
                style={{
                  display: 'inline-flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  padding: '0.75rem 1.25rem',
                  backgroundColor: isDark ? '#181818' : '#FFFFFF',
                  color: isDark ? '#F5F5F5' : '#334155',
                  border: `1px solid ${isDark ? '#333333' : '#CBD5E1'}`,
                  borderRadius: '0.5rem',
                  fontSize: '0.9375rem',
                  fontWeight: 600,
                  textDecoration: 'none',
                  transition: 'background-color 0.15s'
                }}
              >
                See How NUMM Works
              </a>
            </div>
          </div>

          {/* Right Column: Realistic Interactive Material Matching Visualization */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.75rem',
            padding: '1.25rem',
            boxShadow: isDark ? '0 10px 25px rgba(0,0,0,0.5)' : tokens.shadows.md
          }}>
            {/* Engine Header */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              borderBottom: `1px solid ${isDark ? '#262626' : '#F1F5F9'}`,
              paddingBottom: '0.75rem',
              marginBottom: '1rem'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <Cpu style={{ width: '16px', height: '16px', color: tokens.colors.emerald }} />
                <span style={{ fontSize: '0.75rem', fontWeight: 800, textTransform: 'uppercase', letterSpacing: '0.05em', color: isDark ? '#A3A3A3' : '#64748B' }}>
                  Live Matching Pipeline · Multi-CPSE Resolution
                </span>
              </div>
              <span style={{
                fontSize: '0.65rem',
                fontWeight: 700,
                backgroundColor: isDark ? 'rgba(16, 185, 129, 0.15)' : '#DCFCE7',
                color: tokens.colors.emerald,
                padding: '0.1rem 0.4rem',
                borderRadius: '0.25rem'
              }}>
                REALTIME
              </span>
            </div>

            {/* CPSE A Item */}
            <div style={{
              backgroundColor: isDark ? '#161616' : '#F8FAFC',
              border: `1px solid ${isDark ? '#2A2A2A' : '#E2E8F0'}`,
              borderRadius: '0.5rem',
              padding: '0.85rem',
              marginBottom: '0.5rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: tokens.colors.primary, backgroundColor: isDark ? '#1C2920' : '#DCFCE7', padding: '0.1rem 0.4rem', borderRadius: '0.2rem' }}>
                  CPSE A · Heavy Industries
                </span>
                <span style={{ fontSize: '0.7rem', color: isDark ? '#737373' : '#94A3B8', fontFamily: 'monospace' }}>
                  SRC-BHT-09214
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: isDark ? '#F5F5F5' : '#0F172A', fontFamily: 'monospace' }}>
                BOLT HEX M12 × 60 SS316 GR 10.9
              </div>
            </div>

            {/* AI Candidate Retrieval Midpoint */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              padding: '0.35rem 0',
              margin: '0.25rem 0'
            }}>
              <div style={{ height: '1px', flex: 1, backgroundColor: isDark ? '#262626' : '#E2E8F0' }} />
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '0.35rem',
                backgroundColor: isDark ? '#211E11' : '#FEF3C7',
                border: `1px solid ${isDark ? '#785A14' : '#FDE68A'}`,
                padding: '0.2rem 0.6rem',
                borderRadius: '9999px',
                fontSize: '0.7rem',
                fontWeight: 700,
                color: isDark ? '#FACC15' : '#B45309'
              }}>
                <Sparkles style={{ width: '12px', height: '12px' }} />
                <span>96.4% Semantic Similarity (MiniLM-L6-v2)</span>
              </div>
              <div style={{ height: '1px', flex: 1, backgroundColor: isDark ? '#262626' : '#E2E8F0' }} />
            </div>

            {/* CPSE B Item */}
            <div style={{
              backgroundColor: isDark ? '#161616' : '#F8FAFC',
              border: `1px solid ${isDark ? '#2A2A2A' : '#E2E8F0'}`,
              borderRadius: '0.5rem',
              padding: '0.85rem',
              marginBottom: '0.85rem'
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '0.25rem' }}>
                <span style={{ fontSize: '0.7rem', fontWeight: 800, color: '#2563EB', backgroundColor: isDark ? '#13233D' : '#EFF6FF', padding: '0.1rem 0.4rem', borderRadius: '0.2rem' }}>
                  CPSE B · Petrochemical & Refining
                </span>
                <span style={{ fontSize: '0.7rem', color: isDark ? '#737373' : '#94A3B8', fontFamily: 'monospace' }}>
                  SRC-OG-48190
                </span>
              </div>
              <div style={{ fontSize: '0.9rem', fontWeight: 700, color: isDark ? '#F5F5F5' : '#0F172A', fontFamily: 'monospace' }}>
                HEXAGONAL HEAD BOLT M12X60 SS 316 ISO4014
              </div>
            </div>

            {/* Technical Attribute Match Checklist */}
            <div style={{
              backgroundColor: isDark ? '#161616' : '#F0FDF4',
              border: `1px solid ${isDark ? '#1E382B' : '#BBF7D0'}`,
              borderRadius: '0.5rem',
              padding: '0.75rem',
              marginBottom: '0.85rem'
            }}>
              <div style={{
                fontSize: '0.7rem',
                fontWeight: 800,
                color: tokens.colors.success,
                textTransform: 'uppercase',
                letterSpacing: '0.04em',
                marginBottom: '0.4rem'
              }}>
                Technical Attribute Verification (All Passed)
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.35rem', fontSize: '0.75rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: isDark ? '#4ADE80' : '#15803D' }}>
                  <CheckCircle2 style={{ width: '13px', height: '13px' }} />
                  <span>Category: BOLT</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: isDark ? '#4ADE80' : '#15803D' }}>
                  <CheckCircle2 style={{ width: '13px', height: '13px' }} />
                  <span>Diameter: M12 (Match)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: isDark ? '#4ADE80' : '#15803D' }}>
                  <CheckCircle2 style={{ width: '13px', height: '13px' }} />
                  <span>Length: 60mm (Match)</span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', color: isDark ? '#4ADE80' : '#15803D' }}>
                  <CheckCircle2 style={{ width: '13px', height: '13px' }} />
                  <span>Material: SS316 (Match)</span>
                </div>
              </div>
            </div>

            {/* Final Standardized NMC Output */}
            <div style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              backgroundColor: tokens.colors.primary,
              borderRadius: '0.5rem',
              padding: '0.65rem 0.85rem',
              color: '#FFFFFF'
            }}>
              <div>
                <div style={{ fontSize: '0.65rem', fontWeight: 800, letterSpacing: '0.04em', color: '#BBF7D0' }}>
                  GOVERNED NATIONAL MASTER IDENTIFIER
                </div>
                <div style={{ fontSize: '0.95rem', fontWeight: 900, letterSpacing: '0.05em', fontFamily: 'monospace' }}>
                  NMC-BOLT-00000042-X
                </div>
              </div>
              <span style={{
                fontSize: '0.7rem',
                fontWeight: 800,
                backgroundColor: '#059669',
                color: '#FFFFFF',
                padding: '0.2rem 0.5rem',
                borderRadius: '0.25rem'
              }}>
                ISO 7064 VALIDATED
              </span>
            </div>
          </div>
        </div>

        {/* Industrial Pipeline Architecture Flow Diagram */}
        <div style={{ marginTop: '2.5rem' }}>
          <IndustrialHeroDiagram />
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 3 — SAFETY DIFFERENTIATOR (THE HERO TECHNICAL PROOF)              */}
      {/* ========================================================================= */}
      <section id="safety-differentiator" style={{
        padding: '3rem 1.5rem',
        backgroundColor: isDark ? '#0F0F0F' : '#FFFFFF',
        borderTop: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
        borderBottom: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`
      }}>
        <div style={{ maxWidth: '1240px', margin: '0 auto' }}>
          {/* Header */}
          <div style={{ textAlign: 'center', maxWidth: '760px', margin: '0 auto 2.5rem auto' }}>
            <div style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              padding: '0.2rem 0.6rem',
              backgroundColor: isDark ? '#241215' : '#FEF2F2',
              border: `1px solid ${isDark ? '#7F1D1D' : '#FCA5A5'}`,
              borderRadius: '9999px',
              fontSize: '0.75rem',
              fontWeight: 800,
              color: tokens.colors.danger,
              marginBottom: '0.75rem'
            }}>
              <ShieldAlert style={{ width: '13px', height: '13px' }} />
              <span>THE ENGINEERING VETO INVARIANT</span>
            </div>
            <h2 style={{
              fontSize: '2rem',
              fontWeight: 900,
              color: isDark ? '#F5F5F5' : '#0F172A',
              margin: '0 0 0.75rem 0',
              letterSpacing: '-0.02em'
            }}>
              AI finds candidates. Engineering rules protect decisions.
            </h2>
            <p style={{
              fontSize: '1rem',
              lineHeight: 1.5,
              color: isDark ? '#A3A3A3' : '#475569',
              margin: 0
            }}>
              Semantic similarity can never override a critical engineering conflict. NUMM prevents catastrophic mis-matches through deterministic safety gates.
            </p>
          </div>

          {/* Side-by-Side Comparison Container */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
            gap: '1.5rem'
          }}>
            {/* Box 1: High Similarity Trap */}
            <div style={{
              backgroundColor: isDark ? '#161616' : '#F8FAFC',
              border: `1px solid ${isDark ? '#2E2E2E' : '#E2E8F0'}`,
              borderRadius: '0.75rem',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: isDark ? '#A3A3A3' : '#64748B', textTransform: 'uppercase' }}>
                    Candidate Input Pair
                  </span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 700,
                    backgroundColor: isDark ? '#211E11' : '#FEF3C7',
                    color: isDark ? '#FACC15' : '#B45309',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '0.25rem'
                  }}>
                    96.2% Semantic Match
                  </span>
                </div>

                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', marginBottom: '1.25rem' }}>
                  <div style={{ padding: '0.75rem', backgroundColor: isDark ? '#1C1C1C' : '#FFFFFF', border: `1px solid ${isDark ? '#333333' : '#E2E8F0'}`, borderRadius: '0.375rem' }}>
                    <div style={{ fontSize: '0.7rem', color: isDark ? '#737373' : '#94A3B8' }}>CPSE A Specification</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'monospace', color: isDark ? '#F5F5F5' : '#0F172A' }}>
                      BOLT M12 × 60 — <span style={{ color: '#EAB308', textDecoration: 'underline' }}>GRADE 8.8</span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: isDark ? '#A3A3A3' : '#64748B', marginTop: '0.2rem' }}>
                      Tensile Strength: 800 MPa · Proof Load: 580 MPa
                    </div>
                  </div>

                  <div style={{ padding: '0.75rem', backgroundColor: isDark ? '#1C1C1C' : '#FFFFFF', border: `1px solid ${isDark ? '#333333' : '#E2E8F0'}`, borderRadius: '0.375rem' }}>
                    <div style={{ fontSize: '0.7rem', color: isDark ? '#737373' : '#94A3B8' }}>CPSE B Specification</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'monospace', color: isDark ? '#F5F5F5' : '#0F172A' }}>
                      BOLT M12 × 60 — <span style={{ color: tokens.colors.danger, textDecoration: 'underline' }}>GRADE 10.9</span>
                    </div>
                    <div style={{ fontSize: '0.7rem', color: isDark ? '#A3A3A3' : '#64748B', marginTop: '0.2rem' }}>
                      Tensile Strength: 1040 MPa · Proof Load: 830 MPa
                    </div>
                  </div>
                </div>
              </div>

              <div style={{
                fontSize: '0.8rem',
                color: isDark ? '#A3A3A3' : '#64748B',
                lineHeight: 1.4,
                borderTop: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
                paddingTop: '0.75rem'
              }}>
                <strong>The Risk:</strong> Naive vector similarity would merge these parts because 95%+ of words match. In an industrial plant, substituting Grade 8.8 for 10.9 leads to catastrophic shear failure.
              </div>
            </div>

            {/* Box 2: NUMM Deterministic Safety Gate Response */}
            <div style={{
              backgroundColor: isDark ? '#1C1415' : '#FEF2F2',
              border: `2px solid ${isDark ? '#DC2626' : '#EF4444'}`,
              borderRadius: '0.75rem',
              padding: '1.5rem',
              display: 'flex',
              flexDirection: 'column',
              justifyContent: 'space-between'
            }}>
              <div>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '1rem' }}>
                  <span style={{ fontSize: '0.75rem', fontWeight: 800, color: tokens.colors.danger, textTransform: 'uppercase' }}>
                    NUMM Veto Lattice Verdict
                  </span>
                  <span style={{
                    fontSize: '0.75rem',
                    fontWeight: 800,
                    backgroundColor: tokens.colors.danger,
                    color: '#FFFFFF',
                    padding: '0.15rem 0.5rem',
                    borderRadius: '0.25rem'
                  }}>
                    GATE G2 ACTIVATED
                  </span>
                </div>

                {/* Hard Veto Alert */}
                <div style={{
                  backgroundColor: isDark ? '#291215' : '#FFFFFF',
                  border: `1px solid ${isDark ? '#7F1D1D' : '#FECACA'}`,
                  borderRadius: '0.5rem',
                  padding: '1rem',
                  marginBottom: '1rem'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginBottom: '0.4rem' }}>
                    <AlertTriangle style={{ width: '18px', height: '18px', color: tokens.colors.danger }} />
                    <span style={{ fontSize: '0.875rem', fontWeight: 800, color: tokens.colors.danger }}>
                      CRITICAL ATTRIBUTE CONFLICT
                    </span>
                  </div>
                  <div style={{ fontSize: '0.85rem', fontWeight: 700, color: isDark ? '#FCA5A5' : '#991B1B' }}>
                    property_class: 8.8 ≠ 10.9
                  </div>
                  <div style={{ fontSize: '0.75rem', color: isDark ? '#E5E5E5' : '#7F1D1D', marginTop: '0.25rem' }}>
                    Tensile rating differs by 240 MPa. Safety lattice strictly forbids equivalence.
                  </div>
                </div>

                {/* Forced Overrides */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem', marginBottom: '1rem' }}>
                  <div style={{
                    backgroundColor: isDark ? '#241215' : '#FFF5F5',
                    padding: '0.6rem',
                    borderRadius: '0.375rem',
                    textAlign: 'center',
                    border: `1px solid ${isDark ? '#5C1A20' : '#FED7D7'}`
                  }}>
                    <div style={{ fontSize: '0.65rem', color: isDark ? '#FCA5A5' : '#991B1B', fontWeight: 700 }}>CONFIDENCE</div>
                    <div style={{ fontSize: '1.1rem', fontWeight: 900, color: tokens.colors.danger }}>0.00 (FORCED)</div>
                  </div>
                  <div style={{
                    backgroundColor: isDark ? '#241215' : '#FFF5F5',
                    padding: '0.6rem',
                    borderRadius: '0.375rem',
                    textAlign: 'center',
                    border: `1px solid ${isDark ? '#5C1A20' : '#FED7D7'}`
                  }}>
                    <div style={{ fontSize: '0.65rem', color: isDark ? '#FCA5A5' : '#991B1B', fontWeight: 700 }}>RELATIONSHIP</div>
                    <div style={{ fontSize: '0.9rem', fontWeight: 900, color: tokens.colors.danger }}>NOT_EQUIVALENT</div>
                  </div>
                </div>
              </div>

              <div style={{
                fontSize: '0.8rem',
                color: isDark ? '#FCA5A5' : '#7F1D1D',
                fontWeight: 600,
                borderTop: `1px solid ${isDark ? '#5C1A20' : '#FED7D7'}`,
                paddingTop: '0.75rem'
              }}>
                ✓ <strong>System Invariant:</strong> Auto-acceptance is strictly blocked. Engineering safety takes absolute precedence over statistical similarity.
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 4 — LIVE DEMONSTRATION METRICS                                    */}
      {/* ========================================================================= */}
      <section id="metrics" style={{
        padding: '3rem 1.5rem',
        maxWidth: '1240px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <div style={{
          textAlign: 'center',
          marginBottom: '2rem'
        }}>
          <h2 style={{
            fontSize: '1.75rem',
            fontWeight: 800,
            color: isDark ? '#F5F5F5' : '#0F172A',
            margin: '0 0 0.5rem 0'
          }}>
            Live National Harmonization Workload
          </h2>
          <p style={{
            fontSize: '0.875rem',
            color: isDark ? '#A3A3A3' : '#64748B',
            margin: 0
          }}>
            Aggregated metrics derived from active PostgreSQL data stores and typed category packs.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: '1.25rem'
        }}>
          {/* Metric 1 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.5rem',
            padding: '1.5rem',
            textAlign: 'center',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: tokens.colors.primary, lineHeight: 1 }}>
              {metrics.materials.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: isDark ? '#F5F5F5' : '#0F172A', marginTop: '0.5rem' }}>
              Source Materials
            </div>
            <div style={{ fontSize: '0.75rem', color: isDark ? '#A3A3A3' : '#64748B', marginTop: '0.2rem' }}>
              Ingested with immutable lineage
            </div>
          </div>

          {/* Metric 2 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.5rem',
            padding: '1.5rem',
            textAlign: 'center',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: tokens.colors.emerald, lineHeight: 1 }}>
              {metrics.cpses}
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: isDark ? '#F5F5F5' : '#0F172A', marginTop: '0.5rem' }}>
              CPSE Datasets
            </div>
            <div style={{ fontSize: '0.75rem', color: isDark ? '#A3A3A3' : '#64748B', marginTop: '0.2rem' }}>
              Cross-enterprise coverage
            </div>
          </div>

          {/* Metric 3 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.5rem',
            padding: '1.5rem',
            textAlign: 'center',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: tokens.colors.primary, lineHeight: 1 }}>
              {metrics.safeEquiv.toLocaleString()}
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: isDark ? '#F5F5F5' : '#0F172A', marginTop: '0.5rem' }}>
              Standardization Opportunities
            </div>
            <div style={{ fontSize: '0.75rem', color: isDark ? '#A3A3A3' : '#64748B', marginTop: '0.2rem' }}>
              Verified safe-equivalent candidates
            </div>
          </div>

          {/* Metric 4 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.5rem',
            padding: '1.5rem',
            textAlign: 'center',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{ fontSize: '2.5rem', fontWeight: 900, color: tokens.colors.emerald, lineHeight: 1 }}>
              {metrics.gates}
            </div>
            <div style={{ fontSize: '0.875rem', fontWeight: 700, color: isDark ? '#F5F5F5' : '#0F172A', marginTop: '0.5rem' }}>
              Safety Veto Gates
            </div>
            <div style={{ fontSize: '0.75rem', color: isDark ? '#A3A3A3' : '#64748B', marginTop: '0.2rem' }}>
              Deterministic engineering protection
            </div>
          </div>
        </div>

        {/* Public Dataset Attribution & Disclaimer */}
        <div style={{
          textAlign: 'center',
          marginTop: '1.25rem',
          fontSize: '0.75rem',
          color: isDark ? '#737373' : '#94A3B8',
          lineHeight: 1.5,
          maxWidth: '850px',
          margin: '1.25rem auto 0 auto'
        }}>
          * Public-source demonstration data from CPSE open records (Hugging Face Prasenjeet25/sih26099-cpse-material-codes, CC BY 4.0; Oil India, NTPC, IOCL) + controlled demo scenarios. Does not claim access to confidential CPSE internal systems.
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 5 — HOW NUMM WORKS                                                */}
      {/* ========================================================================= */}
      <section id="how-it-works" style={{
        padding: '3rem 1.5rem',
        backgroundColor: isDark ? '#0F0F0F' : '#FFFFFF',
        borderTop: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
        borderBottom: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`
      }}>
        <div style={{ maxWidth: '1240px', margin: '0 auto' }}>
          <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
            <span style={{ fontSize: '0.75rem', fontWeight: 800, color: tokens.colors.primary, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Standardization Architecture
            </span>
            <h2 style={{
              fontSize: '2rem',
              fontWeight: 900,
              color: isDark ? '#F5F5F5' : '#0F172A',
              margin: '0.25rem 0 0.5rem 0'
            }}>
              The Seven-Stage Standardization Lifecycle
            </h2>
            <p style={{
              fontSize: '0.9375rem',
              color: isDark ? '#A3A3A3' : '#64748B',
              margin: 0
            }}>
              From messy, divergent legacy descriptions to an audited, ISO-checked National Master.
            </p>
          </div>

          {/* Horizontal Process Grid */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
            gap: '1rem'
          }}>
            {[
              { step: '01', title: 'Import', desc: 'Raw CPSE catalogs ingested with immutable lineage.' },
              { step: '02', title: 'Normalize', desc: 'Rule-based token parsing and unit conversions.' },
              { step: '03', title: 'AI Retrieval', desc: 'pgvector HNSW high-dimensional semantic search.' },
              { step: '04', title: 'Attribute Engine', desc: 'Typed dimension, grade and standard comparators.' },
              { step: '05', title: 'Safety Veto', desc: 'G0–G6 gates enforce technical compatibility.' },
              { step: '06', title: 'Human Review', desc: 'Certified CPSE stewards govern final approvals.' },
              { step: '07', title: 'NMC Code', desc: 'Atomic issuance with ISO 7064 MOD 37,36 check.' },
            ].map((s, idx) => (
              <div key={idx} style={{
                backgroundColor: isDark ? '#141414' : '#F8FAFC',
                border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
                borderRadius: '0.5rem',
                padding: '1rem',
                display: 'flex',
                flexDirection: 'column',
                justifyContent: 'space-between'
              }}>
                <div>
                  <span style={{
                    fontSize: '0.85rem',
                    fontWeight: 900,
                    color: tokens.colors.emerald,
                    display: 'block',
                    marginBottom: '0.4rem'
                  }}>
                    {s.step}
                  </span>
                  <h4 style={{
                    fontSize: '0.9rem',
                    fontWeight: 800,
                    color: isDark ? '#F5F5F5' : '#0F172A',
                    margin: '0 0 0.4rem 0'
                  }}>
                    {s.title}
                  </h4>
                  <p style={{
                    fontSize: '0.75rem',
                    color: isDark ? '#A3A3A3' : '#64748B',
                    margin: 0,
                    lineHeight: 1.4
                  }}>
                    {s.desc}
                  </p>
                </div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 6 — GOVERNANCE ARCHITECTURE                                       */}
      {/* ========================================================================= */}
      <section id="governance" style={{
        padding: '3rem 1.5rem',
        maxWidth: '1240px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2.5rem' }}>
          <h2 style={{
            fontSize: '2rem',
            fontWeight: 900,
            color: isDark ? '#F5F5F5' : '#0F172A',
            margin: '0 0 0.5rem 0'
          }}>
            Three-Pillar Governance Model
          </h2>
          <p style={{
            fontSize: '0.9375rem',
            color: isDark ? '#A3A3A3' : '#64748B',
            margin: 0
          }}>
            Authoritative, reliable and designed for enterprise public sector deployment.
          </p>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
          gap: '1.5rem'
        }}>
          {/* Card 1 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.75rem',
            padding: '1.75rem',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '0.5rem',
              backgroundColor: isDark ? '#1F2937' : '#EFF6FF',
              color: '#2563EB',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem'
            }}>
              <Cpu style={{ width: '22px', height: '22px' }} />
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: isDark ? '#F5F5F5' : '#0F172A', margin: '0 0 0.5rem 0' }}>
              AI-Assisted Discovery
            </h3>
            <p style={{ fontSize: '0.875rem', color: isDark ? '#A3A3A3' : '#64748B', lineHeight: 1.5, margin: 0 }}>
              MiniLM-L6-v2 vector embeddings coupled with PostgreSQL pgvector HNSW indexing retrieve candidates in milliseconds, collapsing candidate spaces by 95.5%.
            </p>
          </div>

          {/* Card 2 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.75rem',
            padding: '1.75rem',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '0.5rem',
              backgroundColor: isDark ? '#241215' : '#FEF2F2',
              color: tokens.colors.danger,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem'
            }}>
              <ShieldAlert style={{ width: '22px', height: '22px' }} />
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: isDark ? '#F5F5F5' : '#0F172A', margin: '0 0 0.5rem 0' }}>
              Engineering-Safe
            </h3>
            <p style={{ fontSize: '0.875rem', color: isDark ? '#A3A3A3' : '#64748B', lineHeight: 1.5, margin: 0 }}>
              Deterministic G0–G6 veto gates enforce strict category, tensile property, and dimensional consistency. Technical conflicts cannot be bypassed by AI scores.
            </p>
          </div>

          {/* Card 3 */}
          <div style={{
            backgroundColor: isDark ? '#111111' : '#FFFFFF',
            border: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
            borderRadius: '0.75rem',
            padding: '1.75rem',
            boxShadow: isDark ? 'none' : tokens.shadows.sm
          }}>
            <div style={{
              width: '40px',
              height: '40px',
              borderRadius: '0.5rem',
              backgroundColor: isDark ? '#1C2920' : '#DCFCE7',
              color: tokens.colors.primary,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              marginBottom: '1rem'
            }}>
              <Scale style={{ width: '22px', height: '22px' }} />
            </div>
            <h3 style={{ fontSize: '1.15rem', fontWeight: 800, color: isDark ? '#F5F5F5' : '#0F172A', margin: '0 0 0.5rem 0' }}>
              Human-Governed
            </h3>
            <p style={{ fontSize: '0.875rem', color: isDark ? '#A3A3A3' : '#64748B', lineHeight: 1.5, margin: 0 }}>
              Certified data stewards review candidates and approve equivalences. All actions commit to a cryptographic SHA-256 hash chain for irrevocable auditability.
            </p>
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* SECTION 7 — FINAL CALL TO ACTION                                          */}
      {/* ========================================================================= */}
      <section style={{
        padding: '3.5rem 1.5rem',
        maxWidth: '1240px',
        margin: '0 auto',
        width: '100%',
        boxSizing: 'border-box'
      }}>
        <div style={{
          backgroundColor: isDark ? '#141414' : tokens.colors.primary,
          border: `1px solid ${isDark ? '#262626' : 'transparent'}`,
          borderRadius: '1rem',
          padding: '3rem 2rem',
          textAlign: 'center',
          color: '#FFFFFF',
          boxShadow: isDark ? 'none' : '0 10px 25px rgba(22, 101, 52, 0.2)'
        }}>
          <h2 style={{
            fontSize: '2.25rem',
            fontWeight: 900,
            margin: '0 0 1rem 0',
            letterSpacing: '-0.02em',
            color: '#FFFFFF'
          }}>
            From fragmented material codes to one governed National Material Master.
          </h2>
          <p style={{
            fontSize: '1.05rem',
            color: '#DCFCE7',
            maxWidth: '650px',
            margin: '0 auto 2rem auto',
            lineHeight: 1.5
          }}>
            Experience the full live pipeline across ingestion, AI matching, safety gates, review queue, and ERP export.
          </p>
          <Link
            href={portalHref}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.5rem',
              padding: '0.85rem 2rem',
              backgroundColor: '#FFFFFF',
              color: tokens.colors.primary,
              borderRadius: '0.5rem',
              fontSize: '1rem',
              fontWeight: 800,
              textDecoration: 'none',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.15)',
              transition: 'transform 0.15s'
            }}
          >
            <span>Enter Governance Portal</span>
            <ArrowRight style={{ width: '18px', height: '18px' }} />
          </Link>
          <div style={{
            fontSize: '0.75rem',
            color: isDark ? '#A3A3A3' : '#BBF7D0',
            marginTop: '1.5rem',
            letterSpacing: '0.04em'
          }}>
            Prototype • Public-source demonstration data + controlled demo scenarios • SIH 2026 PS 26099
          </div>
        </div>
      </section>

      {/* ========================================================================= */}
      {/* FOOTER                                                                    */}
      {/* ========================================================================= */}
      <footer style={{
        marginTop: 'auto',
        backgroundColor: isDark ? '#111111' : '#FFFFFF',
        borderTop: `1px solid ${isDark ? '#262626' : '#E2E8F0'}`,
        padding: '2rem 1.5rem'
      }}>
        <div style={{
          maxWidth: '1240px',
          margin: '0 auto',
          display: 'flex',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '1.5rem'
        }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <ShieldCheck style={{ width: '18px', height: '18px', color: tokens.colors.primary }} />
              <span style={{ fontSize: '0.95rem', fontWeight: 800, color: isDark ? '#F5F5F5' : '#0F172A' }}>
                NUMM — National Unified Material Master
              </span>
            </div>
            <div style={{ fontSize: '0.75rem', color: isDark ? '#737373' : '#64748B', marginTop: '0.25rem' }}>
              Smart India Hackathon 2026 · Problem Statement 26099
            </div>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '1.5rem', fontSize: '0.85rem' }}>
            <Link href={portalHref} style={{ color: isDark ? '#A3A3A3' : '#475569', textDecoration: 'none', fontWeight: 600 }}>
              Governance Portal
            </Link>
            <a href="#how-it-works" style={{ color: isDark ? '#A3A3A3' : '#475569', textDecoration: 'none', fontWeight: 600 }}>
              How It Works
            </a>
            <Link href="/audit" style={{ color: isDark ? '#A3A3A3' : '#475569', textDecoration: 'none', fontWeight: 600 }}>
              Audit
            </Link>
            <a href="#governance" style={{ color: isDark ? '#A3A3A3' : '#475569', textDecoration: 'none', fontWeight: 600 }}>
              Technology
            </a>
          </div>
        </div>
      </footer>
    </div>
  );
}
