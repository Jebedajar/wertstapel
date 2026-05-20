'use client'

import { useState, useRef, useCallback } from 'react'
import dynamic from 'next/dynamic'
const NavAccount = dynamic(() => import('@/components/NavAccount'), { ssr: false })
import { PLANS, FAQS } from '@/lib/data'

const ConfigModal = dynamic(() => import('@/components/ConfigModal'), { ssr: false })

/* ── Logo ── */
const LogoMark = ({ height = 15, color = 'var(--gr)' }: { height?: number; color?: string }) => {
  const w = Math.round(height * 18 / 22)
  return (
    <svg width={w} height={height} viewBox="0 0 18 22" fill="none" aria-hidden="true" style={{ display: 'block' }}>
      <rect width="18" height="15" rx="3" fill={color} />
      <rect y="18" width="18" height="4" rx="2" fill={color} opacity="0.32" />
    </svg>
  )
}
const Wordmark = ({ size = 15, color = 'var(--ink)', markColor = 'var(--gr)' }: { size?: number; color?: string; markColor?: string }) => (
  <span style={{ display: 'inline-flex', alignItems: 'center', gap: 7, color, lineHeight: 1 }}>
    <LogoMark height={Math.round(size * 1.45)} color={markColor} />
    <span style={{ fontWeight: 700, fontSize: size, letterSpacing: '.04em', textTransform: 'uppercase', lineHeight: 1 }}>WERTSTAPEL</span>
  </span>
)

/* ── Section header ── */
const SH = ({ kicker, title, sub, dark = false }: { kicker?: string; title: React.ReactNode; sub?: string; dark?: boolean }) => (
  <div className="sh-wrap" style={{ display: "flex", gap: 32, flexWrap: "wrap", justifyContent: "space-between" }}>
    <div className="sh-title">
      {kicker && <div className="mono" style={{ fontSize: 12, letterSpacing: '.08em', textTransform: 'uppercase', color: dark ? 'rgba(255,255,255,.55)' : 'var(--gr)', marginBottom: 14 }}>{kicker}</div>}
      <h2 className="display" style={{ fontSize: 'clamp(36px,5vw,68px)', color: dark ? '#fff' : 'var(--ink)' }}>{title}</h2>
    </div>
    {sub && <p className="sh-sub" style={{ fontSize: 16, lineHeight: 1.55, maxWidth: 340, color: dark ? 'rgba(255,255,255,.7)' : 'var(--mu)' }}>{sub}</p>}
  </div>
)

/* ── Upload zone ── */
function UploadZone({ onFile }: { onFile: (f: File) => void }) {
  const [drag, setDrag] = useState(false)
  const ref = useRef<HTMLInputElement>(null)
  return (
    <div className={`upload-zone${drag ? ' drag' : ''}`}
      onClick={() => ref.current?.click()}
      onDragOver={e => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={e => { e.preventDefault(); setDrag(false); onFile(e.dataTransfer.files[0]) }}>
      <input ref={ref} type="file" accept=".pdf" style={{ display: 'none' }} onChange={e => { if (e.target.files?.[0]) onFile(e.target.files[0]) }} />
      <div className="upload-inner">
        <div style={{ width: 72, height: 72, borderRadius: 18, background: 'var(--gr)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
          <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5" /><path d="M5 12l7-7 7 7" /></svg>
        </div>
        <div style={{ flex: 1, minWidth: 160, textAlign: 'left' }}>
          <div style={{ fontSize: 'clamp(17px,2.5vw,22px)', fontWeight: 600, color: 'var(--ink)', marginBottom: 6, letterSpacing: '-.01em' }}>PDF hier ablegen oder klicken</div>
          <div className="mono" style={{ fontSize: 12, color: 'var(--mu)' }}>Orderabrechnungen · beliebig viele Seiten · bis 100 MB</div>
        </div>
        <div className="mono" style={{ fontSize: 11, padding: '8px 12px', background: 'var(--bga)', borderRadius: 8, color: 'var(--ink2)', letterSpacing: '.05em' }}>.PDF</div>
      </div>
    </div>
  )
}

/* ── FAQ item ── */
function FaqItem({ q, a }: { q: string; a: string }) {
  return (
    <div style={{ borderTop: '1px solid var(--ln)', padding: '24px 0' }}>
      <div style={{ fontSize: 'clamp(16px,2vw,20px)', fontWeight: 600, color: 'var(--ink)', letterSpacing: '-.015em', marginBottom: 14 }}>{q}</div>
      <p style={{ fontSize: 15, lineHeight: 1.65, color: 'var(--mu)' }}>{a}</p>
    </div>
  )
}

/* ── Checkmark ── */
const Chk = ({ color = 'var(--a2)' }: { color?: string }) => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke={color} strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round" style={{ marginTop: 3, flexShrink: 0 }}>
    <polyline points="20 6 9 17 4 12" />
  </svg>
)

/* ══════════════════════════════════════════════════
   MAIN PAGE
══════════════════════════════════════════════════ */
export default function Home() {
  const [file,      setFile]      = useState<File | null>(null)
  const [showModal, setShowModal] = useState(false)
  
  const [navOpen,   setNavOpen]   = useState(false)

  const handleFile = useCallback((f: File) => { if (f.type === 'application/pdf') { setFile(f); setShowModal(true) } }, [])
  const scrollUp = () => { setNavOpen(false); document.getElementById('hero-upload')?.scrollIntoView({ behavior: 'smooth', block: 'center' }) }

  return (
    <>
      {/* NAV */}
      <nav style={{ position: 'sticky', top: 0, zIndex: 50, background: 'rgba(244,242,236,.92)', backdropFilter: 'blur(10px)', borderBottom: '1px solid var(--ln)' }}>
        <div className="wrap" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', height: 68, position: 'relative' }}>
          <Wordmark />
          <div className={`nav-links${navOpen ? ' open' : ''}`}>
            {[['Wie es funktioniert', '#how'], ['Preise', '#pricing'], ['FAQ', '#faq']].map(([t, h]) => (
              <a key={t} href={h} className="nav-link" onClick={() => setNavOpen(false)}>{t}</a>
            ))}
            <NavAccount onScrollToUpload={scrollUp} />
            <button onClick={scrollUp} style={{ padding: '10px 18px', borderRadius: 999, background: 'var(--ink)', color: '#fff', border: 'none', fontSize: 13, fontWeight: 600, letterSpacing: '-.005em', display: 'inline-flex', alignItems: 'center', gap: 8, whiteSpace: 'nowrap' }}>
              Jetzt starten
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
            </button>
          </div>
          <button className="hamburger" onClick={() => setNavOpen(!navOpen)} aria-label="Menü">
            <span /><span /><span />
          </button>
        </div>
      </nav>

      {/* HERO */}
      <section className="sec hero-sec" style={{ background: "var(--bg)" }}>
        <div className="wrap" style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
          <h1 className="display fu hero-h1" style={{ lineHeight: 1.08, fontSize: 'clamp(38px,7vw,80px)', maxWidth: 900 }}>
            Wertpapier-PDF rein.<br />
            <span style={{ color: 'var(--gr)' }}>DATEV-Stapel raus.</span>
          </h1>
          <p className="fu1 hero-copy" style={{ fontSize: "clamp(16px,2vw,20px)", lineHeight: 1.55, color: "var(--ink2)", maxWidth: 680 }}>
            Schluss mit dem manuellen Buchen von Wertpapier-Transaktionen: Sie laden das PDF ihrer Depot-Bank hoch, wir liefern in 5 Minuten den DATEV-Stapel — fertig zum Import und mit Plausibilitätscheck. Keine Seitenbegrenzung. Kein Abo.
          </p>
          <div id="hero-upload" className="fu2" style={{ width: '100%', maxWidth: 720 }}>
            <UploadZone onFile={handleFile} />
            <div style={{ display: 'flex', gap: 20, marginTop: 22, flexWrap: 'wrap', justifyContent: 'center' }}>
              {['§8b-konform', 'Server in Deutschland', 'DSGVO-konform', 'Made in Germany'].map(t => (
                <div key={t} style={{ display: 'flex', alignItems: 'center', gap: 7 }}>
                  <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="var(--gr)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                  <span style={{ fontSize: 13, color: 'var(--mu)' }}>{t}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* STATS STRIP */}
      <section style={{ borderTop: '1px solid var(--ln)', borderBottom: '1px solid var(--ln)', background: 'var(--bga)' }}>
        <div className="wrap">
          <div className="grid-stat">
            {[['<5min', 'Verarbeitungszeit'], ['0', 'Seitenlimit'], ['5h', 'Zeitersparnis/Export'], ['§8b', 'KStG-konform']].map(([n, lb], i) => (
              <div key={i} className="stat-cell">
                <div className="display" style={{ fontSize: 'clamp(32px,4.5vw,58px)', marginBottom: 8, color: 'var(--ink)' }}>{n}</div>
                <div className="mono" style={{ fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase', color: 'var(--mu)' }}>{lb}</div>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* HOW IT WORKS */}
      <section id="how" className="sec">
        <div className="wrap">
          <SH kicker="3 Schritte. Keine Einarbeitung." title="Wie es funktioniert" sub="Vom PDF zur DATEV-Importdatei in unter 5 Minuten — egal ob 5 oder 5.000 Seiten." />
          <div className="grid-3">
            {[
              { n: '01', title: 'PDF hochladen',              desc: 'Laden Sie einfach das vollständige Orderabrechnungs-PDF Ihrer Bank hoch.' },
              { n: '02', title: 'Automatisierte Buchung',      desc: 'Die Buchungssätze werden automatisch auf Basis der offiziellen DATEV-Dokumentation erstellt. Keine KI, somit keine KI-Fehler.' },
              { n: '03', title: 'DATEV-Stapel herunterladen', desc: 'Die Export-Datei ist direkt importierbar in DATEV. Plausibilitätsbericht und Verarbeitungsprotokoll sichern ab.' },
            ].map((s, i) => (
              <div key={i} className="step-card">
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 40 }}>
                  <span className="mono" style={{ fontSize: 13, fontWeight: 500, color: 'var(--gr)' }}>— {s.n}</span>
                  <span style={{ width: 8, height: 8, borderRadius: '50%', background: 'var(--gr)' }} />
                </div>
                <h3 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-.02em', marginBottom: 12, color: 'var(--ink)' }}>{s.title}</h3>
                <p style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--mu)' }}>{s.desc}</p>
              </div>
            ))}
          </div>

          {/* Time savings block */}
          <div className="time-block" style={{ marginTop: 32, padding: '48px 40px', background: 'var(--ink)', borderRadius: 20, color: '#fff' }}>
            <div className="mono" style={{ fontSize: 12, letterSpacing: '.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,.55)', marginBottom: 36, textAlign: 'center' }}>
              Ihre Zeitersparnis mit Wertstapel
            </div>
            <div className="grid-time">
              {[
                { label: '5 Stunden', sub: 'Manuell · pro Export', filled: true },
                { label: '5 Minuten', sub: 'Mit Wertstapel', filled: false },
              ].map((col, ci) => (
                <div key={ci} style={{ textAlign: 'center' }}>
                  <div className="circles" style={{ display: 'flex', gap: 10, justifyContent: 'center', marginBottom: 18, flexWrap: 'wrap' }}>
                    {[0, 1, 2, 3, 4].map(i => (
                      <div key={i} className="circle" style={{
                        width: 48, height: 48, borderRadius: '50%',
                        background: col.filled ? 'rgba(255,255,255,.85)' : 'transparent',
                        border: col.filled ? 'none' : '1.5px solid rgba(255,255,255,.25)',
                        display: 'flex', alignItems: 'center', justifyContent: 'center',
                      }}>
                        {!col.filled && i === 0 && <div style={{ width: 9, height: 9, borderRadius: '50%', background: 'var(--a2)' }} />}
                      </div>
                    ))}
                  </div>
                  <div className="display" style={{ fontSize: 28, color: '#fff', marginBottom: 4 }}>{col.label}</div>
                  <div className="mono" style={{ fontSize: 11, letterSpacing: '.06em', textTransform: 'uppercase', color: col.filled ? 'rgba(255,255,255,.5)' : 'var(--a2)' }}>{col.sub}</div>
                </div>
              ))}
            </div>
            <div style={{ marginTop: 48, textAlign: 'center', borderTop: '1px solid rgba(255,255,255,.1)', paddingTop: 36 }}>
              <div className="display" style={{ fontSize: 'clamp(32px,5vw,64px)', color: '#fff', lineHeight: 1.05, marginBottom: 10 }}>200 Stunden pro Jahr sparen.</div>
              <div style={{ fontSize: 14, color: 'rgba(255,255,255,.55)' }}>Bei rund 10 GmbH-Mandanten mit quartalsweisen Exporten.</div>
            </div>
          </div>
        </div>
      </section>

      {/* OUTPUTS */}
      <section className="sec" style={{ background: '#fff', borderTop: '1px solid var(--ln)', borderBottom: '1px solid var(--ln)' }}>
        <div className="wrap">
          <SH kicker="3 Dateien. Jede mit ihrem Zweck." title="Was Sie bekommen." sub="Direkt importierbar in DATEV Kanzlei-Rechnungswesen. Plus Audit-Trail zur Sichtkontrolle." />
          <div className="grid-3">
            {[
              { fn: 'Buchungsstapel.csv', title: 'DATEV-Buchungsstapel',    desc: 'Direkt importierbar in DATEV Kanzlei-Rechnungswesen. Enthält ISIN, WKN, Stückzahl und Ausführungskurs. §8b-konform. Buchwertabgang-Methode, tranchengetrennte Verbuchung.', tag: 'DATEV-Import' },
              { fn: 'Plausibilitaet.csv', title: 'Plausibilitätsbericht',   desc: 'Jeder Beleg mit Status, Trancheninformation und Ausmachender Betrag. Abweichungen über 0,05 € werden markiert. Für die Sichtkontrolle vor dem Import.',                   tag: 'Vor dem Import' },
              { fn: 'Protokoll.txt',      title: 'Verarbeitungsprotokoll',  desc: 'Welche Seiten gebucht und welche warum übersprungen wurden. Inklusive Kurswerte, Gebühren, Veräußerungsgewinne, -verluste, Netto-Steuerergebnis.',                            tag: 'Audit-Trail' },
            ].map((it, i) => (
              <div key={i} className="out-card">
                <div style={{ display: 'inline-flex', alignSelf: 'flex-start', alignItems: 'center', gap: 8, background: 'var(--bg)', padding: '7px 12px', borderRadius: 8, marginBottom: 24 }}>
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--gr)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" /></svg>
                  <span className="mono" style={{ fontSize: 11, color: 'var(--ink2)' }}>{it.fn}</span>
                </div>
                <h3 style={{ fontSize: 22, fontWeight: 700, letterSpacing: '-.02em', marginBottom: 12, color: 'var(--ink)' }}>{it.title}</h3>
                <p style={{ fontSize: 14, lineHeight: 1.65, color: 'var(--mu)', flex: 1, marginBottom: 20 }}>{it.desc}</p>
                <span className="mono" style={{ alignSelf: 'flex-start', fontSize: 10, letterSpacing: '.08em', textTransform: 'uppercase', background: 'var(--grs)', color: 'var(--gr)', padding: '5px 10px', borderRadius: 6 }}>{it.tag}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* DIFFERENTIATOR */}
      <section className="sec" style={{ background: 'var(--grd)' }}>
        <div className="wrap">
          <SH title={<>Unser Ansatz.<br />Ihre Vorteile.</>} dark />
          <div className="grid-diff">
            {/* Label column — hidden on mobile via CSS */}
            <div className="diff-labels" style={{ gridTemplateRows: '44px 1fr 1fr 1fr', gap: 16 }}>
              <div />
              {['Verarbeitung', 'Volumen', 'Setup'].map(lb => (
                <div key={lb} className="mono" style={{ display: 'flex', alignItems: 'center', justifyContent: 'flex-end', fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase', color: 'rgba(255,255,255,.4)', paddingRight: 8 }}>{lb}</div>
              ))}
            </div>
            {[
              { col: 'Wertstapel', good: true, items: [
                { label: 'Deterministisch',  text: 'Feste Regeln auf Basis offizieller DATEV-Dokumentation. Buchungsvorschlag nachvollziehbar.' },
                { label: 'Kein Volumenlimit', text: 'Ein Export kostet immer dasselbe — egal ob 5 oder 5.000 Seiten.' },
                { label: 'Kein Setup',        text: 'PDF hochladen. Warten. Fertig. Neue Banken werden auf Anfrage implementiert.' },
              ]},
              { col: 'Andere Tools', good: false, items: [
                { label: 'KI-Kategorisierung', text: 'Schätzt, variiert, lernt — aber: keine prüfbare Logik, Ergebnisse können abweichen.' },
                { label: 'Seitenbegrenzung',    text: '400–4.000 Seiten je Monat oder Export. Je mehr Transaktionen, desto teurer.' },
                { label: 'Aufwendiges Setup',   text: 'Direkte Bankanbindung bedingt technischem Aufwand und Mithilfe des Mandanten.' },
              ]},
            ].map((col, ci) => (
              <div key={ci} style={{ display: 'grid', gridTemplateRows: '44px 1fr 1fr 1fr', gap: 16 }}>
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: 14, fontWeight: 700, color: col.good ? 'var(--a2)' : 'rgba(255,255,255,.5)' }}>{col.col}</div>
                {col.items.map((it, i) => (
                  <div key={i} className={`diff-card ${col.good ? 'good' : 'bad'}`}>
                    <div style={{ width: 36, height: 36, borderRadius: 10, flexShrink: 0, background: col.good ? 'var(--a2)' : 'rgba(255,255,255,.06)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                      {col.good
                        ? <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#0B1E47" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
                        : <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.6)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><line x1="18" y1="6" x2="6" y2="18" /><line x1="6" y1="6" x2="18" y2="18" /></svg>
                      }
                    </div>
                    <div>
                      <div style={{ fontSize: 16, fontWeight: 600, color: col.good ? '#fff' : 'rgba(255,255,255,.6)', marginBottom: 6 }}>{it.label}</div>
                      <div style={{ fontSize: 13.5, color: col.good ? 'rgba(255,255,255,.65)' : 'rgba(255,255,255,.4)', lineHeight: 1.55 }}>{it.text}</div>
                    </div>
                  </div>
                ))}
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* PRICING */}
      <section id="pricing" className="sec" style={{ background: 'var(--bg)' }}>
        <div className="wrap">
          <SH kicker="Preise" title={<>Kein Seitenlimit.<br />Auf keinem Paket.</>} sub="Ein Export kostet dasselbe — egal ob das PDF 5 oder 5.000 Seiten hat. Pakete verfallen nicht." />
          <div className="grid-4">
            {PLANS.map(p => (
              <div key={p.id} className={`plan-card${p.popular ? ' popular' : ''}`}>
                {p.popular && (
                  <div className="plan-badge" style={{ position: 'absolute', top: -12, left: 24, background: 'var(--lm)', color: 'var(--ink)', padding: '4px 12px', borderRadius: 999, fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 10, fontWeight: 600, letterSpacing: '.08em' }}>BELIEBT</div>
                )}
                <div style={{ fontSize: 15, fontWeight: 600, marginBottom: 18, opacity: p.popular ? .85 : 1, letterSpacing: '-.01em' }}>{p.label}</div>
                <div className="display" style={{ fontSize: 46, marginBottom: 6 }}>{p.price}<span style={{ fontSize: 20, opacity: .5, fontWeight: 500, marginLeft: 4 }}>€</span></div>
                <div className="mono" style={{ fontSize: 11, color: p.popular ? 'var(--lm)' : 'var(--gr)', marginBottom: 14, letterSpacing: '.04em' }}>{p.sub}</div>
                <div style={{ fontSize: 13, opacity: .65, flex: 1, marginBottom: 22, lineHeight: 1.5 }}>{p.note}</div>
                <button onClick={scrollUp} style={{ padding: 12, borderRadius: 10, fontSize: 13, fontWeight: 600, background: p.popular ? 'var(--lm)' : 'transparent', color: 'var(--ink)', border: p.popular ? 'none' : '1px solid var(--ln2)' }}>
                  Wählen →
                </button>
              </div>
            ))}
          </div>
          <div style={{ marginTop: 20, textAlign: 'center', fontSize: 13, color: 'var(--mu)' }}>
            Alle Pakete: keine Buchungsmengen-Limits · kein Ablaufdatum · Preise zzgl. MwSt. · Zahlung mit Kreditkarte oder Lastschrift
          </div>
        </div>
      </section>

      {/* FAQ */}
      <section id="faq" className="sec" style={{ background: '#fff', borderTop: '1px solid var(--ln)' }}>
        <div className="wrap">
          <SH kicker="FAQ" title={<>Häufig gestellte<br />Fragen.</>} />
          <div className="grid-2" style={{ gap: '0 48px' }}>
            {FAQS.map((f, i) => (
              <FaqItem key={i} q={f.q} a={f.a} />
            ))}
          </div>
        </div>
      </section>

      {/* PRE-FOOTER */}
      <section className="sec" style={{ background: 'var(--grd)', color: '#fff' }}>
        <div className="wrap">
          <div className="grid-2">
            {[
              { tag: 'Für GmbH-Eigentümer', title: 'Sparen Sie Ihrem Steuerberater Arbeit — und sich Honorar.', bullets: ['PDF hochladen, CSV herunterladen, weiterleiten', 'Kein Fachwissen nötig — Konfiguration in 2 Minuten', 'Sie behalten die Kontrolle über Ihre eigenen Daten'] },
              { tag: 'Für Steuerberater',   title: 'Mechanische Bucharbeit automatisieren — Beratungszeit gewinnen.', bullets: ['Buchungsvorschlag zur fachkundigen Prüfung', 'SKR03 & SKR04, alle Parameter konfigurierbar', 'DATEV-Importdatei direkt aus Ihrem Workflow'] },
            ].map((c, i) => (
              <div key={i} className="pf-card">
                <div className="mono" style={{ fontSize: 11, letterSpacing: '.1em', textTransform: 'uppercase', color: 'var(--a2)', marginBottom: 24 }}>● {c.tag}</div>
                <h3 className="display" style={{ fontSize: 'clamp(26px,3vw,38px)', color: '#fff', marginBottom: 28, lineHeight: 1.1 }}>{c.title}</h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 36px', display: 'grid', gap: 14 }}>
                  {c.bullets.map((b, j) => (
                    <li key={j} style={{ display: 'flex', alignItems: 'flex-start', gap: 12, fontSize: 15, color: 'rgba(255,255,255,.78)', lineHeight: 1.5 }}>
                      <Chk /><span>{b}</span>
                    </li>
                  ))}
                </ul>
                <button onClick={scrollUp} style={{ alignSelf: 'flex-start', marginTop: 'auto', padding: '14px 24px', borderRadius: 999, background: 'var(--a2)', color: 'var(--grd)', border: 'none', fontSize: 14, fontWeight: 600, display: 'inline-flex', alignItems: 'center', gap: 10 }}>
                  Ersten Export starten
                  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* FOOTER */}
      <footer style={{ background: 'var(--bg)', borderTop: '1px solid var(--ln)', padding: '40px 0' }}>
        <div className="wrap" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 16 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18, flexWrap: 'wrap' }}>
            <Wordmark size={13} />
            <span style={{ fontSize: 13, color: 'var(--fa)' }}>Buchungsstapel für Wertpapier­abrechnungen</span>
          </div>
          <div style={{ display: 'flex', gap: 20, flexWrap: 'wrap' }}>
            {['Impressum', 'Datenschutz', 'AGB', 'AVV'].map(t => (
              <a key={t} href={`/${t.toLowerCase()}`} style={{ fontSize: 13, color: 'var(--mu)' }}>{t}</a>
            ))}
          </div>
        </div>
      </footer>

      {showModal && <ConfigModal file={file} onClose={() => setShowModal(false)} />}
    </>
  )
}
