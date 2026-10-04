'use client';

import React from 'react';

interface SvgProps {
  size?: number;
  color?: string;
  className?: string;
  style?: React.CSSProperties;
}

/**
 * Minimalist Bolt & Fastener illustration with thread pitch lines and hexagonal head
 */
export function BoltFastenerIllustration({ size = 48, color = 'currentColor', className, style }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Hex Bolt Head */}
      <path
        d="M16 8L24 4L32 8L32 14L24 18L16 14Z"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      <path d="M24 4V18" stroke={color} strokeWidth="1.5" strokeOpacity="0.4" />
      {/* Washer / Collar */}
      <rect x="14" y="18" width="20" height="3" rx="1" stroke={color} strokeWidth="1.5" />
      {/* Bolt Shank */}
      <rect x="18" y="21" width="12" height="22" rx="1" stroke={color} strokeWidth="2" />
      {/* Thread lines */}
      <path d="M18 26L30 28" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.6" />
      <path d="M18 31L30 33" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.6" />
      <path d="M18 36L30 38" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeOpacity="0.6" />
      {/* Grade Stamp indicator */}
      <circle cx="36" cy="12" r="6" stroke={color} strokeWidth="1.5" fill="none" strokeDasharray="2 2" />
      <text x="36" y="14" textAnchor="middle" fontSize="6" fontWeight="bold" fill={color} fontFamily="monospace">8.8</text>
    </svg>
  );
}

/**
 * Minimalist Pipe & Flange & Valve illustration
 */
export function PipeValveIllustration({ size = 48, color = 'currentColor', className, style }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Left Pipe Section */}
      <rect x="4" y="20" width="12" height="8" rx="1" stroke={color} strokeWidth="1.8" />
      <path d="M4 20V28" stroke={color} strokeWidth="2.5" />
      {/* Left Flange */}
      <rect x="15" y="16" width="3" height="16" rx="1" stroke={color} strokeWidth="1.8" fill="none" />
      {/* Center Valve Body (Hourglass) */}
      <path
        d="M18 18L30 30V18L18 30Z"
        stroke={color}
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Valve Stem & Handwheel */}
      <line x1="24" y1="24" x2="24" y2="10" stroke={color} strokeWidth="2" strokeLinecap="round" />
      <ellipse cx="24" cy="8" rx="8" ry="3" stroke={color} strokeWidth="1.8" fill="none" />
      {/* Right Flange */}
      <rect x="30" y="16" width="3" height="16" rx="1" stroke={color} strokeWidth="1.8" fill="none" />
      {/* Right Pipe Section */}
      <rect x="32" y="20" width="12" height="8" rx="1" stroke={color} strokeWidth="1.8" />
      <path d="M44 20V28" stroke={color} strokeWidth="2.5" />
      {/* Flow Arrow */}
      <path d="M19 40H29M29 40L26 37M29 40L26 43" stroke={color} strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" strokeOpacity="0.5" />
    </svg>
  );
}

/**
 * Minimalist Safety Veto Shield with Gate Interlocks
 */
export function VetoShieldIllustration({ size = 48, color = '#dc2626', className, style }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Outer Shield Outline */}
      <path
        d="M24 4L38 10V22C38 32 24 42 24 42C24 42 10 32 10 22V10L24 4Z"
        stroke={color}
        strokeWidth="2"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
      {/* Inner Gate Grid (G0-G6 lattice representation) */}
      <path d="M16 18H32" stroke={color} strokeWidth="1.5" strokeOpacity="0.4" />
      <path d="M18 24H30" stroke={color} strokeWidth="1.5" strokeOpacity="0.6" />
      <path d="M20 30H28" stroke={color} strokeWidth="1.5" strokeOpacity="0.8" />
      {/* Central Lock / Interlock Symbol */}
      <rect x="20" y="20" width="8" height="7" rx="1.5" stroke={color} strokeWidth="2" />
      <path d="M22 20V17C22 15.9 22.9 15 24 15C25.1 15 26 15.9 26 17V20" stroke={color} strokeWidth="1.8" />
      <circle cx="24" cy="23.5" r="1" fill={color} />
    </svg>
  );
}

/**
 * National Material Master Database + NMC Code
 */
export function NmcDatabaseIllustration({ size = 48, color = '#059669', className, style }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Database Stack */}
      <ellipse cx="24" cy="10" rx="14" ry="4.5" stroke={color} strokeWidth="2" />
      <path d="M10 10V20C10 22.5 16.3 24.5 24 24.5C31.7 24.5 38 22.5 38 20V10" stroke={color} strokeWidth="2" />
      <path d="M10 20V30C10 32.5 16.3 34.5 24 34.5C31.7 34.5 38 32.5 38 30V20" stroke={color} strokeWidth="2" />
      {/* Standardized Badge */}
      <rect x="14" y="34" width="20" height="9" rx="2" fill="none" stroke={color} strokeWidth="2" />
      <text x="24" y="40.5" textAnchor="middle" fontSize="6.5" fontWeight="900" fill={color} fontFamily="monospace">NMC</text>
    </svg>
  );
}

/**
 * CPSE Multi-Entity Network connected to Central Hub
 */
export function CpseNetworkIllustration({ size = 48, color = 'currentColor', className, style }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Central National Hub */}
      <circle cx="24" cy="24" r="7" stroke={color} strokeWidth="2" />
      <circle cx="24" cy="24" r="3" fill={color} />
      {/* Node 1: Oil India (Top Left) */}
      <circle cx="10" cy="12" r="5" stroke={color} strokeWidth="1.8" />
      <line x1="14" y1="15" x2="19" y2="20" stroke={color} strokeWidth="1.5" strokeDasharray="2 2" />
      {/* Node 2: NTPC (Top Right) */}
      <circle cx="38" cy="12" r="5" stroke={color} strokeWidth="1.8" />
      <line x1="34" y1="15" x2="29" y2="20" stroke={color} strokeWidth="1.5" strokeDasharray="2 2" />
      {/* Node 3: IOCL (Bottom Center) */}
      <circle cx="24" cy="40" r="5" stroke={color} strokeWidth="1.8" />
      <line x1="24" y1="35" x2="24" y2="31" stroke={color} strokeWidth="1.5" strokeDasharray="2 2" />
    </svg>
  );
}

/**
 * Cryptographic Audit Hash-Chain with SHA-256 verification seal
 */
export function AuditChainIllustration({ size = 48, color = '#2563eb', className, style }: SvgProps) {
  return (
    <svg
      width={size}
      height={size}
      viewBox="0 0 48 48"
      fill="none"
      xmlns="http://www.w3.org/2000/svg"
      className={className}
      style={style}
    >
      {/* Block 1 */}
      <rect x="6" y="8" width="14" height="12" rx="2" stroke={color} strokeWidth="1.8" />
      <line x1="10" y1="12" x2="16" y2="12" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="10" y1="15" x2="14" y2="15" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      {/* Connecting Chain Link */}
      <path d="M20 14H28" stroke={color} strokeWidth="2" strokeDasharray="2 2" />
      {/* Block 2 */}
      <rect x="28" y="8" width="14" height="12" rx="2" stroke={color} strokeWidth="1.8" />
      <line x1="32" y1="12" x2="38" y2="12" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      <line x1="32" y1="15" x2="36" y2="15" stroke={color} strokeWidth="1.5" strokeLinecap="round" />
      {/* Downward Chain Link */}
      <path d="M35 20V26" stroke={color} strokeWidth="2" strokeDasharray="2 2" />
      {/* Verified Seal Block */}
      <rect x="18" y="26" width="24" height="15" rx="3" stroke={color} strokeWidth="2" />
      <path d="M23 33.5L27 37.5L37 27.5" stroke={color} strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}
