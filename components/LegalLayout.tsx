import Link from 'next/link'

const LogoMark = ({ height = 15, color = 'var(--gr)' }: { height?: number; color?: string }) => {
  const w = Math.round(height * 18 / 22)
  return (
    <svg width={w} height={height} viewBox="0 0 18 22" fill="none" aria-hidden="true" style={{ display: 'block' }}>
      <rect width="18" height="15" rx="3" fill={color} />
      <rect y="18" width="18" height="4" rx="2" fill={color} opacity="0.32" />
    </svg>
  )
}

const Wordmark = ({ size = 15 }: { size?: number }) => (
  <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, color: 'var(--ink)', lineHeight: 1, textDecoration: 'none' }}>
    <LogoMark height={Math.round(size * 1.45)} />
    <span style={{ fontWeight: 700, fontSize: size, letterSpacing: '.04em', textTransform: 'uppercase', lineHeight: 1 }}>WERTSTAPEL</span>
  </Link>
)

export default function LegalLayout({ children }: { children: React.ReactNode }) {
  return (
    <>
      <nav style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(244,242,236,.92)', backdropFilter: 'blur(10px)', borderBottom: '1px solid var(--ln)' }}>
        <div className="wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 68 }}>
          <Wordmark />
          <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 6, fontSize: 14, color: 'var(--mu)', textDecoration: 'none' }}>
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <line x1="19" y1="12" x2="5" y2="12" /><polyline points="12 19 5 12 12 5" />
            </svg>
            Zurück
          </Link>
        </div>
      </nav>

      <main style={{ minHeight: 'calc(100vh - 149px)', background: 'var(--bg)', padding: '48px 0 96px' }}>
        {children}
      </main>

      <footer style={{ background: 'var(--bg)', borderTop: '1px solid var(--ln)', padding: '40px 0' }}>
        <div className="wrap" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <Wordmark size={13} />
            <span style={{ fontSize: 13, color: 'var(--fa)' }}>Buchungsstapel für Wertpapier­abrechnungen</span>
          </div>
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            {[['Impressum', '/impressum'], ['Datenschutz', '/datenschutz'], ['AGB', '/agb'], ['AVV', '/avv']].map(([t, h]) => (
              <Link key={t} href={h} style={{ fontSize: 13, color: 'var(--mu)', textDecoration: 'none' }}>{t}</Link>
            ))}
          </div>
        </div>
      </footer>
    </>
  )
}
