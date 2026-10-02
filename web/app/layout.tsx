import React from 'react';

export const metadata = {
  title: 'SIH 2026 - National Unified Material Master Framework',
  description: 'AI-Driven Standardization and Harmonization of Material Codes Across CPSEs',
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ margin: 0, fontFamily: 'system-ui, -apple-system, sans-serif', backgroundColor: '#f8fafc', color: '#0f172a' }}>
        {children}
      </body>
    </html>
  );
}
