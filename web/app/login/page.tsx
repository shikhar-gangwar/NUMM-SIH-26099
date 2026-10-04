'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { tokens } from '../components/design-system/tokens';
import { ShieldCheck, Eye, EyeOff, Lock, User, AlertCircle, ArrowRight, Loader2, Sparkles, Sun, Moon } from 'lucide-react';

export default function LoginPage() {
  const [username, setUsername] = useState('steward_admin');
  const [password, setPassword] = useState('DevSec_D1I6hALEJYSYhoLsYpWwkPc0');
  const [showPassword, setShowPassword] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  const { login, user, token } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const isDark = theme === 'dark';
  const router = useRouter();

  // If already authenticated, redirect to governance page
  useEffect(() => {
    if (token && user) {
      router.push('/governance');
    }
  }, [token, user, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!username.trim() || !password) {
      setErrorMsg('Please enter both username and password.');
      return;
    }

    setErrorMsg(null);
    setIsSubmitting(true);

    try {
      const result = await login(username.trim(), password);

      if (result.success) {
        router.push('/governance');
      } else {
        const safeError = typeof result.error === 'string'
          ? result.error
          : 'Invalid username or password';
        setErrorMsg(safeError);
        setPassword('');
      }
    } catch {
      setErrorMsg('Unable to connect to the authentication service. Please verify backend status.');
      setPassword('');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div style={{
      minHeight: '100vh',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      background: 'var(--background)',
      padding: '1.5rem',
      boxSizing: 'border-box',
      position: 'relative'
    }}>
      {/* Theme Toggle Top-Right */}
      <div style={{ position: 'absolute', top: '1.5rem', right: '1.5rem' }}>
        <button
          onClick={toggleTheme}
          aria-label="Toggle Theme"
          title={`Switch to ${isDark ? 'Light' : 'Dark'} Mode`}
          style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '38px',
            height: '38px',
            background: 'var(--surface-1)',
            border: '1px solid var(--border)',
            borderRadius: '0.5rem',
            cursor: 'pointer',
            color: isDark ? '#FACC15' : '#475569',
            boxShadow: tokens.shadows.sm,
            transition: 'all 0.15s ease'
          }}
        >
          {isDark ? <Sun style={{ width: '18px', height: '18px' }} /> : <Moon style={{ width: '18px', height: '18px' }} />}
        </button>
      </div>

      <div style={{
        width: '100%',
        maxWidth: '460px',
        background: 'var(--surface-1)',
        border: '1px solid var(--border)',
        borderRadius: '1rem',
        padding: '2.5rem 2rem',
        boxShadow: isDark ? '0 20px 40px -15px rgba(0, 0, 0, 0.7)' : tokens.shadows.lg,
        boxSizing: 'border-box'
      }}>
        {/* Header Branding */}
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            display: 'inline-flex',
            alignItems: 'center',
            justifyContent: 'center',
            width: '56px',
            height: '56px',
            borderRadius: '0.875rem',
            background: isDark ? 'linear-gradient(135deg, #FACC15 0%, #EAB308 100%)' : 'linear-gradient(135deg, #166534 0%, #14532D 100%)',
            boxShadow: isDark ? '0 4px 12px rgba(250, 204, 21, 0.25)' : '0 4px 12px rgba(22, 101, 52, 0.25)',
            marginBottom: '1rem'
          }}>
            <ShieldCheck style={{ width: '32px', height: '32px', color: isDark ? '#080808' : '#ffffff' }} />
          </div>

          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '0.5rem', marginBottom: '0.25rem' }}>
            <span style={{
              fontSize: '0.75rem',
              fontWeight: 800,
              padding: '0.15rem 0.5rem',
              borderRadius: '9999px',
              background: isDark ? 'rgba(250, 204, 21, 0.12)' : '#DCFCE7',
              color: isDark ? '#FACC15' : tokens.colors.primary,
              border: isDark ? '1px solid rgba(250, 204, 21, 0.3)' : '1px solid #BBF7D0',
              letterSpacing: '0.05em'
            }}>
              SIH 2026 PROTOTYPE
            </span>
          </div>

          <h1 style={{
            fontSize: '1.5rem',
            fontWeight: 800,
            color: 'var(--text-primary)',
            margin: '0.25rem 0 0.25rem 0',
            letterSpacing: '-0.02em'
          }}>
            NUMM
          </h1>
          <div style={{ fontSize: '0.9rem', fontWeight: 700, color: isDark ? '#FACC15' : tokens.colors.primary, marginBottom: '0.25rem' }}>
            National Unified Material Master
          </div>
          <p style={{
            fontSize: '0.8125rem',
            color: 'var(--text-secondary)',
            margin: 0,
            lineHeight: 1.4
          }}>
            AI-Assisted Material Standardization & Governance across CPSEs
          </p>
        </div>

        {/* Error Alert Banner */}
        {errorMsg && (
          <div role="alert" style={{
            display: 'flex',
            alignItems: 'flex-start',
            gap: '0.75rem',
            background: isDark ? 'rgba(239, 68, 68, 0.15)' : '#FEE2E2',
            border: isDark ? '1px solid rgba(239, 68, 68, 0.3)' : '1px solid #FECACA',
            borderRadius: '0.5rem',
            padding: '0.875rem 1rem',
            marginBottom: '1.5rem',
            color: isDark ? '#FCA5A5' : tokens.colors.danger,
            fontSize: '0.875rem',
            lineHeight: 1.4
          }}>
            <AlertCircle style={{ width: '20px', height: '20px', flexShrink: 0, marginTop: '2px', color: '#EF4444' }} />
            <div>{String(errorMsg)}</div>
          </div>
        )}

        {/* Login Form */}
        <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
          {/* Username Field */}
          <div>
            <label htmlFor="username" style={{
              display: 'block',
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '0.375rem'
            }}>
              CPSE Steward Username
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute',
                left: '0.875rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center'
              }}>
                <User style={{ width: '18px', height: '18px' }} />
              </div>
              <input
                id="username"
                name="username"
                type="text"
                autoComplete="username"
                autoFocus
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="e.g. steward_admin"
                disabled={isSubmitting}
                style={{
                  width: '100%',
                  padding: '0.75rem 0.875rem 0.75rem 2.5rem',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border)',
                  background: 'var(--surface-2)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9375rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
            </div>
          </div>

          {/* Password Field */}
          <div>
            <label htmlFor="password" style={{
              display: 'block',
              fontSize: '0.8125rem',
              fontWeight: 700,
              color: 'var(--text-primary)',
              marginBottom: '0.375rem'
            }}>
              Password
            </label>
            <div style={{ position: 'relative' }}>
              <div style={{
                position: 'absolute',
                left: '0.875rem',
                top: '50%',
                transform: 'translateY(-50%)',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center'
              }}>
                <Lock style={{ width: '18px', height: '18px' }} />
              </div>
              <input
                id="password"
                name="password"
                type={showPassword ? 'text' : 'password'}
                autoComplete="current-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter password"
                disabled={isSubmitting}
                style={{
                  width: '100%',
                  padding: '0.75rem 2.5rem 0.75rem 2.5rem',
                  borderRadius: '0.5rem',
                  border: '1px solid var(--border)',
                  background: 'var(--surface-2)',
                  color: 'var(--text-primary)',
                  fontSize: '0.9375rem',
                  outline: 'none',
                  boxSizing: 'border-box'
                }}
              />
              <button
                type="button"
                aria-label={showPassword ? 'Hide password' : 'Show password'}
                onClick={() => setShowPassword(!showPassword)}
                style={{
                  position: 'absolute',
                  right: '0.75rem',
                  top: '50%',
                  transform: 'translateY(-50%)',
                  background: 'none',
                  border: 'none',
                  color: 'var(--text-secondary)',
                  cursor: 'pointer',
                  padding: '0.25rem',
                  display: 'flex',
                  alignItems: 'center'
                }}
              >
                {showPassword ? <EyeOff style={{ width: '18px', height: '18px' }} /> : <Eye style={{ width: '18px', height: '18px' }} />}
              </button>
            </div>
          </div>

          {/* Submit Button */}
          <button
            type="submit"
            disabled={isSubmitting}
            style={{
              marginTop: '0.5rem',
              width: '100%',
              padding: '0.875rem',
              borderRadius: '0.5rem',
              border: 'none',
              background: isDark ? 'linear-gradient(135deg, #FACC15 0%, #EAB308 100%)' : 'linear-gradient(135deg, #166534 0%, #15803d 100%)',
              color: isDark ? '#080808' : '#ffffff',
              fontSize: '0.9375rem',
              fontWeight: 800,
              cursor: isSubmitting ? 'not-allowed' : 'pointer',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              gap: '0.5rem',
              boxShadow: isDark ? '0 2px 8px rgba(250, 204, 21, 0.25)' : tokens.shadows.sm,
              opacity: isSubmitting ? 0.8 : 1,
              transition: 'all 0.15s ease'
            }}
          >
            {isSubmitting ? (
              <>
                <Loader2 style={{ width: '18px', height: '18px', animation: 'spin 1s linear infinite' }} />
                <span>Signing in to Portal...</span>
              </>
            ) : (
              <>
                <span>Sign In to Governance Portal</span>
                <ArrowRight style={{ width: '18px', height: '18px' }} />
              </>
            )}
          </button>
        </form>

        {/* SIH Demo Credentials Quick Switcher */}
        <div style={{
          marginTop: '1.5rem',
          paddingTop: '1rem',
          borderTop: '1px solid var(--border)',
          display: 'flex',
          flexDirection: 'column',
          gap: '0.5rem'
        }}>
          <span style={{ fontSize: '0.75rem', fontWeight: 700, color: 'var(--text-secondary)', textTransform: 'uppercase', letterSpacing: '0.05em', textAlign: 'center' }}>
            Quick Demo Login Roles
          </span>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.5rem' }}>
            <button
              type="button"
              onClick={() => {
                setUsername('steward_admin');
                setPassword('DevSec_D1I6hALEJYSYhoLsYpWwkPc0');
                setErrorMsg(null);
              }}
              style={{
                padding: '0.45rem 0.5rem',
                borderRadius: '0.375rem',
                border: username === 'steward_admin' ? (isDark ? '1px solid #FACC15' : '1px solid #166534') : '1px solid var(--border)',
                background: username === 'steward_admin' ? (isDark ? 'rgba(250, 204, 21, 0.12)' : 'rgba(22, 101, 52, 0.1)') : 'var(--surface-2)',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: isDark ? '#FACC15' : '#166534' }}>steward_admin</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Role: SUPER_ADMIN</div>
            </button>
            <button
              type="button"
              onClick={() => {
                setUsername('reviewer_demo');
                setPassword('NUMM-Demo-Reviewer-2026!');
                setErrorMsg(null);
              }}
              style={{
                padding: '0.45rem 0.5rem',
                borderRadius: '0.375rem',
                border: username === 'reviewer_demo' ? '1px solid #38BDF8' : '1px solid var(--border)',
                background: username === 'reviewer_demo' ? (isDark ? 'rgba(56, 189, 248, 0.12)' : 'rgba(59, 130, 246, 0.1)') : 'var(--surface-2)',
                cursor: 'pointer',
                textAlign: 'left'
              }}
            >
              <div style={{ fontSize: '0.75rem', fontWeight: 700, color: isDark ? '#38BDF8' : '#2563eb' }}>reviewer_demo</div>
              <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>Role: REVIEWER</div>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
