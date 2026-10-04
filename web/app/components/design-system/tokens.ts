// Central Design Tokens for NUMM Design System
// "MODERN GOVERNMENT ENTERPRISE + AI INTELLIGENCE"
// Fully responsive to data-theme="dark" and data-theme="light" via CSS custom properties

export const tokens = {
  colors: {
    primary: 'var(--accent, #166534)',       // Forest Green in Light, Gold (#FACC15) in Dark
    primaryHover: 'var(--accent-hover, #14532D)',
    primaryLight: 'var(--accent-soft, #DCFCE7)',
    primaryBorder: 'var(--border, #BBF7D0)',
    
    emerald: 'var(--accent, #059669)',
    emeraldHover: 'var(--accent-hover, #047857)',
    emeraldLight: 'var(--accent-soft, #D1FAE5)',
    
    teal: 'var(--info, #0F766E)',
    tealLight: 'var(--info-bg, #CCFBF1)',
    
    pageBg: 'var(--background, #F7F9F8)',
    background: 'var(--background, #F7F9F8)',
    surface: 'var(--surface-1, #FFFFFF)',
    surfaceSubtle: 'var(--surface-2, #F1F4F2)',
    surfaceElevated: 'var(--surface-3, #E3E9E5)',
    
    border: 'var(--border, #D9E2DC)',
    borderDark: 'var(--border-strong, #C4D1C9)',
    
    textPrimary: 'var(--text-primary, #0F172A)',
    textSecondary: 'var(--text-secondary, #475569)',
    textMuted: 'var(--text-muted, #64748B)',
    textLight: 'var(--text-muted, #94A3B8)',
    
    success: 'var(--success, #15803D)',
    successBg: 'var(--success-bg, #F0FDF4)',
    successBorder: 'var(--success-border, #86EFAC)',
    
    warning: 'var(--warning, #D97706)',
    warningBg: 'var(--warning-bg, #FFFBEB)',
    warningBorder: 'var(--warning-border, #FCD34D)',
    
    danger: 'var(--danger, #DC2626)',
    dangerBg: 'var(--danger-bg, #FEF2F2)',
    dangerBorder: 'var(--danger-border, #FCA5A5)',
    
    info: 'var(--info, #2563EB)',
    infoBg: 'var(--info-bg, #EFF6FF)',
    infoBorder: 'var(--info-border, #93C5FD)',
  },
  shadows: {
    sm: '0 1px 2px 0 rgba(0, 0, 0, 0.05)',
    card: '0 1px 3px 0 rgba(0, 0, 0, 0.07), 0 1px 2px -1px rgba(0, 0, 0, 0.07)',
    md: '0 4px 6px -1px rgba(0, 0, 0, 0.08), 0 2px 4px -2px rgba(0, 0, 0, 0.05)',
    lg: '0 10px 15px -3px rgba(0, 0, 0, 0.08), 0 4px 6px -4px rgba(0, 0, 0, 0.04)',
  },
  typography: {
    fontFamily: "'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
  }
};
