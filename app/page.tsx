'use client'

import { useState, useCallback } from 'react'
import { Wordmark } from '@/components/LogoMark'
import { UploadZone } from '@/components/UploadZone'
import { ConfigModal } from '@/components/ConfigModal'
import { PLANS, FAQS } from '@/lib/data'

// ── Shared section header ─────────────────────────────────────
function SectionHeader({
  kicker,
  title,
  sub,
  dark = false,
}: {
  kicker?: string
  title:   React.ReactNode
  sub?:    string
  dark?:   boolean
}) {
  return (
    <div style={{
      display:        'flex',
      gap:            32,
      marginBottom:   56,
      flexWrap:       'wrap',
      alignItems:     'flex-end',
      justifyContent: 'space-between',
    }}>
      <div style={{ flex: '1 1 600px' }}>
        {kicker && (
          <div className="mono" style={{
            fontSize:      12,
            letterSpacing: '.08em',
            textTransform: 'uppercase',
            color:         dark ? 'rgba(255,255,255,.55)' : 'var(--green)',
            marginBottom:  14,
          }}>
            {kicker}
          </div>
        )}
        <h2 className="display" style={{
          fontSize: 'clamp(40px,5vw,68px)',
          color:    dark ? '#fff' : 'var(--ink)',
        }}>
          {title}
        </h2>
      </div>
      {sub && (
        <p style={{
          fontSize:   16,
          lineHeight: 1.55,
          maxWidth:   340,
          color:      dark ? 'rgba(255,255,255,.7)' : 'var(--mute)',
        }}>
          {sub}
        </p>
      )}
    </div>
  )
}

// ── Hero preview card ─────────────────────────────────────────
function HeroPreview() {
  const rows = [
    { tag: 'Kauf',     isin: 'DE000A1EWWW0', ax: '+1.842,55 €' },
    { tag: 'Verkauf',  isin: 'US0378331005', ax: '+12.408,90 €' },
    { tag: 'Dividende',isin: 'DE0008404005', ax: '+87,12 €' },
    { tag: 'Kauf',     isin: 'IE00B4L5Y983', ax: '+4.250,00 €' },
  ]
  return (
    <div style={{
      background:   '#fff',
      borderRadius: 24,
      border:       '1px solid var(--line)',
      padding:      22,
      boxShadow:    '0 30px 60px -30px rgba(15,46,27,.18), 0 2px 0 rgba(15,22,18,.03)',
      transform:    'rotate(.6deg)',
    }}>
      <div style={{
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
        marginBottom:   18,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <span className="dot live" />
          <span className="mono" style={{
            fontSize:      11,
            color:         'var(--mute)',
            letterSpacing: '.08em',
            textTransform: 'uppercase',
          }}>
            Verarbeitung · 1.4s
          </span>
        </div>
        <span className="mono" style={{ fontSize: 11, color: 'var(--faint)' }}>Q3-2026.pdf</span>
      </div>

      <div className="display" style={{ fontSize: 44, marginBottom: 4, letterSpacing: '-.04em' }}>264</div>
      <div style={{ fontSize: 13, color: 'var(--mute)', marginBottom: 22 }}>
        Buchungssätze aus 104 Belegen
      </div>

      <div style={{ borderTop: '1px solid var(--line)', paddingTop: 16, display: 'grid', gap: 10 }}>
        {rows.map((r, i) => (
          <div key={i} style={{
            display:    'flex',
            justifyContent: 'space-between',
            alignItems: 'center',
            gap:        12,
          }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10, minWidth: 0 }}>
              <span style={{
                fontSize:     10,
                fontWeight:   600,
                padding:      '3px 7px',
                borderRadius: 5,
                background:   'var(--green-soft)',
                color:        'var(--green)',
                fontFamily:   'JetBrains Mono, monospace',
                letterSpacing:'.04em',
              }}>
                {r.tag.toUpperCase()}
              </span>
              <span className="mono" style={{
                fontSize:     12,
                color:        'var(--ink-2)',
                overflow:     'hidden',
                textOverflow: 'ellipsis',
                whiteSpace:   'nowrap',
              }}>
                {r.isin}
              </span>
            </div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
              <span className="mono" style={{ fontSize: 12, fontWeight: 500, color: 'var(--ink)' }}>
                {r.ax}
              </span>
              <svg
                width="14" height="14" viewBox="0 0 24 24" fill="none"
                stroke="var(--green)" strokeWidth="3" strokeLinecap="round" strokeLinejoin="round"
              >
                <polyline points="20 6 9 17 4 12" />
              </svg>
            </div>
          </div>
        ))}
      </div>

      <div style={{
        marginTop:      18,
        padding:        '12px 14px',
        background:     'var(--green)',
        color:          '#fff',
        borderRadius:   12,
        display:        'flex',
        justifyContent: 'space-between',
        alignItems:     'center',
      }}>
        <div>
          <div className="mono" style={{ fontSize: 10, letterSpacing: '.08em', opacity: .7, textTransform: 'uppercase' }}>
            Bereit zum Download
          </div>
          <div style={{ fontSize: 13, fontWeight: 600, marginTop: 2 }}>
            31385_Buchungsstapel_20260429.csv
          </div>
        </div>
        <svg
          width="18" height="18" viewBox="0 0 24 24" fill="none"
          stroke="#fff" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"
        >
          <path d="M12 5v14" /><path d="M19 12l-7 7-7-7" />
        </svg>
      </div>
    </div>
  )
}

// ── FAQ accordion item ────────────────────────────────────────
function FaqItem({
  q, a, open, onToggle,
}: {
  q: string; a: string; open: boolean; onToggle: () => void
}) {
  return (
    <div style={{ borderTop: '1px solid var(--line)', padding: '24px 0' }}>
      <button
        onClick={onToggle}
        style={{
          width:      '100%',
          display:    'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          gap:        24,
          background: 'none',
          border:     'none',
          cursor:     'pointer',
          textAlign:  'left',
          padding:    0,
        }}
      >
        <span style={{
          fontSize:      'clamp(18px,2vw,22px)',
          fontWeight:    600,
          color:         'var(--ink)',
          letterSpacing: '-.015em',
        }}>
          {q}
        </span>
        <span style={{
          width:          36,
          height:         36,
          borderRadius:   '50%',
          border:         '1px solid var(--line-2)',
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'center',
          flexShrink:     0,
          transition:     'all .2s',
          background:     open ? 'var(--ink)' : 'transparent',
          color:          open ? '#fff' : 'var(--ink)',
        }}>
          <svg
            width="14" height="14" viewBox="0 0 24 24" fill="none"
            stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"
            style={{ transform: open ? 'rotate(45deg)' : 'none', transition: 'transform .25s' }}
          >
            <line x1="12" y1="5" x2="12" y2="19" />
            <line x1="5" y1="12" x2="19" y2="12" />
          </svg>
        </span>
      </button>
      {open && (
        <p style={{
          marginTop:  16,
          fontSize:   15,
          lineHeight: 1.65,
          color:      'var(--mute)',
          maxWidth:   760,
        }}>
          {a}
        </p>
      )}
    </div>
  )
}

// ── Main page ─────────────────────────────────────────────────
export default function Home() {
  const [file,      setFile]      = useState<File | null>(null)
  const [showModal, setShowModal] = useState(false)
  const [openFaq,   setOpenFaq]   = useState(0)

  const handleFile = useCallback((f: File) => {
    if (f.type === 'application/pdf') {
      setFile(f)
      setShowModal(true)
    }
  }, [])

  const scrollToUpload = () => {
    document.getElementById('hero-upload')?.scrollIntoView({ behavior: 'smooth', block: 'center' })
  }

  // ── Differentiator items ──────────────────────────────────
  const diffItems = [
    {
      ok:    false,
      label: 'KI-Kategorisierung',
      text:  'Schätzt, variiert, lernt — aber: keine prüfbare Logik, Ergebnisse können abweichen.',
    },
    {
      ok:    false,
      label: 'Seitenbegrenzung',
      text:  'Andere Tools: 400 – 4.000 Seiten/Monat. Je mehr Transaktionen, desto teurer.',
    },
    {
      ok:    true,
      label: 'Deterministisch',
      text:  'Feste Regeln je Belegtyp. Buchungsvorschlag nachvollziehbar. Steuerberater-konform.',
    },
    {
      ok:    true,
      label: 'Kein Volumenlimit',
      text:  'Ein Export kostet dasselbe — 20 oder 500 Seiten. Immer.',
    },
  ]

  return (
    <>
      {/* ── NAV ───────────────────────────────────────────── */}
      <nav style={{
        position:       'sticky',
        top:            0,
        zIndex:         50,
        background:     'rgba(244,242,236,.88)',
        backdropFilter: 'blur(10px)',
        borderBottom:   '1px solid var(--line)',
      }}>
        <div className="wrap" style={{
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'space-between',
          height:         68,
        }}>
          <Wordmark />
          <div style={{ display: 'flex', alignItems: 'center', gap: 32 }}>
            {[
              ['Wie es funktioniert', '#how'],
              ['Preise',              '#pricing'],
              ['FAQ',                 '#faq'],
            ].map(([t, h]) => (
              <a key={t} href={h} style={{ fontSize: 14, fontWeight: 500, color: 'var(--ink-2)' }}>
                {t}
              </a>
            ))}
            <button
              onClick={scrollToUpload}
              style={{
                padding:       '10px 18px',
                borderRadius:  999,
                background:    'var(--ink)',
                color:         '#fff',
                border:        'none',
                cursor:        'pointer',
                fontSize:      13,
                fontWeight:    600,
                letterSpacing: '-.005em',
                display:       'inline-flex',
                alignItems:    'center',
                gap:           8,
              }}
            >
              Jetzt starten
              <svg
                width="13" height="13" viewBox="0 0 24 24" fill="none"
                stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"
              >
                <line x1="5" y1="12" x2="19" y2="12" />
                <polyline points="12 5 19 12 12 19" />
              </svg>
            </button>
          </div>
        </div>
      </nav>

      {/* ── 01 HERO ───────────────────────────────────────── */}
      <section style={{ padding: '100px 0 80px', background: 'var(--bg)', overflow: 'hidden' }}>
        <div className="wrap" style={{
          display:   'grid',
          gridTemplateColumns: '1fr 420px',
          gap:       64,
          alignItems:'center',
        }}>
          {/* Left */}
          <div>
            <div className="fu mono" style={{
              fontSize:      12,
              letterSpacing: '.08em',
              textTransform: 'uppercase',
              color:         'var(--green)',
              marginBottom:  20,
              display:       'flex',
              alignItems:    'center',
              gap:           10,
            }}>
              <span className="dot" /> Sparkasse · SKR03 &amp; SKR04 · §8b KStG
            </div>

            <h1 className="fu-1 display" style={{
              fontSize:     'clamp(54px,7vw,96px)',
              color:        'var(--ink)',
              marginBottom: 28,
            }}>
              Wertpapier&shy;<br />abrechnungen.<br />
              <span style={{ color: 'var(--green)' }}>DATEV-Stapel.</span>
            </h1>

            <p className="fu-2" style={{
              fontSize:     18,
              lineHeight:   1.6,
              color:        'var(--mute)',
              maxWidth:     480,
              marginBottom: 40,
            }}>
              Orderabrechnungen automatisch in einen importfähigen DATEV-Buchungsstapel überführen.
              §8b-konform. Tranchengetrennt. Keine Seitenbegrenzung.
            </p>

            {/* Trust badges */}
            <div className="fu-3" style={{
              display:  'flex',
              flexWrap: 'wrap',
              gap:      12,
              marginBottom: 44,
            }}>
              {[
                'EU-Server Deutschland',
                'Deterministisch, kein LLM',
                'DATEV-importfähig',
              ].map((t) => (
                <span key={t} style={{
                  fontFamily:   'JetBrains Mono, monospace',
                  fontSize:     11,
                  letterSpacing:'.05em',
                  padding:      '6px 12px',
                  borderRadius: 999,
                  border:       '1px solid var(--line-2)',
                  color:        'var(--ink-2)',
                  background:   '#fff',
                }}>
                  ✓ {t}
                </span>
              ))}
            </div>

            {/* Upload zone */}
            <div id="hero-upload" className="fu-4">
              <UploadZone onFile={handleFile} large />
              <div style={{
                marginTop:  12,
                fontSize:   12,
                color:      'var(--faint)',
                textAlign:  'center',
              }}>
                Zahlung erst nach erfolgreicher Verarbeitung
              </div>
            </div>
          </div>

          {/* Right — preview card */}
          <div className="fu-2" style={{ position: 'relative' }}>
            <HeroPreview />
          </div>
        </div>
      </section>

      {/* ── Validation strip ────────────────────────────── */}
      <div style={{
        background:  'var(--green-deep)',
        padding:     '18px 0',
        borderTop:   '1px solid rgba(147,197,253,.1)',
      }}>
        <div className="wrap" style={{
          display:        'flex',
          justifyContent: 'center',
          alignItems:     'center',
          flexWrap:       'wrap',
          gap:            32,
        }}>
          <div style={{ fontSize: 13, color: 'rgba(255,255,255,.6)' }}>
            <span style={{ color: '#fff', fontWeight: 500 }}>Fachlich validiert:</span>{' '}
            Steuerberaterin, Düsseldorf · DATEV-Dokumentation 5300857 · Buchwertabgang-Methode
          </div>
          <div className="mono" style={{ fontSize: 12, color: 'rgba(147,197,253,.7)', letterSpacing: '.04em' }}>
            Tranchengetrennt · §8b-konform · Teilfreistellung erkannt
          </div>
        </div>
      </div>

      {/* ── 02 HOW IT WORKS ──────────────────────────────── */}
      <section id="how" style={{ padding: '120px 0', background: '#fff' }}>
        <div className="wrap">
          <SectionHeader
            kicker="Wie es funktioniert"
            title={<>Drei Schritte.<br />Keine Einarbeitung.</>}
            sub="Von der PDF-Datei zum fertigen DATEV-Import in unter fünf Minuten."
          />

          {/* Steps */}
          <div style={{
            display:             'grid',
            gridTemplateColumns: 'repeat(3,1fr)',
            gap:                 32,
            marginBottom:        64,
          }}>
            {[
              {
                n:    '01',
                t:    'PDF hochladen',
                d:    'Das vollständige Orderabrechnungs-PDF der Sparkasse — egal ob 20 oder 500 Seiten.',
              },
              {
                n:    '02',
                t:    'Konfigurieren',
                d:    'SKR03 oder SKR04. Bankkonto. Optional Mandantennummer. Vier Felder, Profil speicherbar.',
              },
              {
                n:    '03',
                t:    'Herunterladen',
                d:    'DATEV-Buchungsstapel, Plausibilitätsbericht und Verarbeitungsprotokoll. Direkt importierbar.',
              },
            ].map((s) => (
              <div key={s.n}>
                <div className="mono" style={{
                  fontSize:      11,
                  letterSpacing: '.1em',
                  color:         'var(--green)',
                  marginBottom:  14,
                }}>
                  {s.n}
                </div>
                <h3 style={{
                  fontSize:      22,
                  fontWeight:    700,
                  color:         'var(--ink)',
                  letterSpacing: '-.02em',
                  marginBottom:  10,
                }}>
                  {s.t}
                </h3>
                <p style={{ fontSize: 15, lineHeight: 1.6, color: 'var(--mute)' }}>{s.d}</p>
              </div>
            ))}
          </div>

          {/* Time comparison bar */}
          <div style={{
            display:        'flex',
            justifyContent: 'space-between',
            alignItems:     'center',
            padding:        '28px 36px',
            background:     'var(--bg)',
            borderRadius:   20,
            border:         '1px solid var(--line)',
            flexWrap:       'wrap',
            gap:            24,
          }}>
            <div>
              <div style={{ fontSize: 12, color: 'var(--mute)', marginBottom: 4 }}>
                Manuell pro GmbH-Mandant und Quartal
              </div>
              <div className="display" style={{ fontSize: 36, color: '#B91C1C' }}>
                2 – 5 Stunden
              </div>
            </div>
            <svg
              width="32" height="32" viewBox="0 0 24 24" fill="none"
              stroke="var(--line-2)" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"
            >
              <line x1="5" y1="12" x2="19" y2="12" />
              <polyline points="12 5 19 12 12 19" />
            </svg>
            <div>
              <div style={{ fontSize: 12, color: 'var(--mute)', marginBottom: 4 }}>
                Mit Wertstapel
              </div>
              <div className="display" style={{ fontSize: 36, color: 'var(--green)' }}>
                unter 5 Minuten
              </div>
            </div>
            <div style={{
              fontSize:   14,
              color:      'var(--mute)',
              maxWidth:   240,
              fontStyle:  'italic',
              lineHeight: 1.5,
            }}>
              Bei 10 GmbH-Mandanten: bis zu 200 Stunden Ersparnis pro Jahr.
            </div>
          </div>
        </div>
      </section>

      {/* ── 03 DIFFERENTIATOR ────────────────────────────── */}
      <section style={{ padding: '120px 0', background: 'var(--green-deep)', color: '#fff' }}>
        <div className="wrap">
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 80, alignItems: 'center' }}>
            <div>
              <SectionHeader
                kicker="Warum Wertstapel"
                title={<>Kein Raten.<br />Jeder Buchungssatz<br />berechenbar.</>}
                dark
                sub="Andere Tools nutzen KI und begrenzen nach Seitenzahl. Wertstapel rechnet deterministisch nach festen Regeln — reproduzierbar, prüfbar, §8b-konform."
              />
              <div className="mono" style={{
                fontSize:   12,
                color:      'rgba(147,197,253,.7)',
                letterSpacing: '.05em',
              }}>
                §8b KStG · Buchwertabgang · Tranchengetrennt · Teilfreistellung
              </div>
            </div>

            <div style={{ display: 'grid', gap: 12 }}>
              {diffItems.map((it) => (
                <div key={it.label} style={{
                  background: it.ok
                    ? 'rgba(255,255,255,.06)'
                    : 'rgba(0,0,0,.2)',
                  border:     `1px solid ${it.ok
                    ? 'rgba(147,197,253,.2)'
                    : 'rgba(255,255,255,.06)'}`,
                  borderRadius: 16,
                  padding:      '18px 20px',
                  display:      'flex',
                  gap:          16,
                  alignItems:   'flex-start',
                }}>
                  <div style={{
                    width:          36,
                    height:         36,
                    borderRadius:   10,
                    background:     it.ok
                      ? 'rgba(147,197,253,.15)'
                      : 'rgba(239,68,68,.15)',
                    display:        'flex',
                    alignItems:     'center',
                    justifyContent: 'center',
                    flexShrink:     0,
                  }}>
                    {it.ok ? (
                      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--accent-2)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round">
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                    ) : (
                      <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="rgba(255,255,255,.6)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                        <line x1="18" y1="6" x2="6" y2="18" />
                        <line x1="6" y1="6" x2="18" y2="18" />
                      </svg>
                    )}
                  </div>
                  <div>
                    <div style={{ fontSize: 16, fontWeight: 600, color: '#fff', marginBottom: 6, letterSpacing: '-.01em' }}>
                      {it.label}
                    </div>
                    <div style={{ fontSize: 13.5, color: 'rgba(255,255,255,.65)', lineHeight: 1.55 }}>
                      {it.text}
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* ── 04 PRICING ───────────────────────────────────── */}
      <section id="pricing" style={{ padding: '120px 0', background: 'var(--bg)' }}>
        <div className="wrap">
          <SectionHeader
            kicker="Preise"
            title={<>Kein Seitenlimit.<br />Auf keinem Paket.</>}
            sub="Ein Export kostet dasselbe — egal ob das PDF 5 oder 500 Seiten hat. Pakete verfallen nicht."
          />

          <div style={{
            display:             'grid',
            gridTemplateColumns: 'repeat(4,1fr)',
            gap:                 16,
          }}>
            {PLANS.map((p) => (
              <div key={p.id} style={{
                position:       'relative',
                background:     p.popular ? 'var(--ink)' : '#fff',
                color:          p.popular ? '#fff' : 'var(--ink)',
                border:         p.popular ? '1px solid var(--ink)' : '1px solid var(--line)',
                borderRadius:   20,
                padding:        '32px 26px',
                display:        'flex',
                flexDirection:  'column',
              }}>
                {p.popular && (
                  <div style={{
                    position:      'absolute',
                    top:           -12,
                    left:          24,
                    background:    'var(--lime)',
                    color:         'var(--ink)',
                    padding:       '4px 12px',
                    borderRadius:  999,
                    fontFamily:    'JetBrains Mono, monospace',
                    fontSize:      10,
                    fontWeight:    600,
                    letterSpacing: '.08em',
                  }}>
                    BELIEBT
                  </div>
                )}
                <div style={{
                  fontSize:      15,
                  fontWeight:    600,
                  marginBottom:  18,
                  opacity:       p.popular ? .85 : 1,
                  letterSpacing: '-.01em',
                }}>
                  {p.label}
                </div>
                <div className="display" style={{ fontSize: 46, marginBottom: 4 }}>
                  {p.price}
                  <span style={{ fontSize: 20, opacity: .5, fontWeight: 500, marginLeft: 4 }}>€</span>
                </div>
                {/* per-export cost */}
                <div className="mono" style={{
                  fontSize:      11,
                  color:         p.popular ? 'var(--lime)' : 'var(--green)',
                  marginBottom:  14,
                  letterSpacing: '.04em',
                }}>
                  {p.perExport}
                </div>
                <div style={{
                  fontSize:   13,
                  opacity:    .65,
                  flex:       1,
                  marginBottom: 22,
                  lineHeight: 1.5,
                }}>
                  {p.note}
                </div>
                <button
                  onClick={scrollToUpload}
                  style={{
                    padding:      '12px',
                    borderRadius: 10,
                    cursor:       'pointer',
                    fontSize:     13,
                    fontWeight:   600,
                    background:   p.popular ? 'var(--lime)' : 'transparent',
                    color:        'var(--ink)',
                    border:       p.popular ? 'none' : '1px solid var(--line-2)',
                    letterSpacing:'-.005em',
                  }}
                >
                  Wählen →
                </button>
              </div>
            ))}
          </div>

          <div style={{ marginTop: 20, textAlign: 'center', fontSize: 13, color: 'var(--mute)' }}>
            Alle Pakete: keine Buchungsmengen-Limits · kein Ablaufdatum · Rechnung per E-Mail · Zahlung mit Kreditkarte oder Lastschrift
          </div>
        </div>
      </section>

      {/* ── 05 FAQ ───────────────────────────────────────── */}
      <section id="faq" style={{ padding: '120px 0', background: '#fff', borderTop: '1px solid var(--line)' }}>
        <div className="wrap">
          <SectionHeader
            kicker="FAQ"
            title={<>Häufig gestellte<br />Fragen.</>}
          />
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: '0 48px' }}>
            {FAQS.map((f, i) => (
              <FaqItem
                key={i}
                q={f.q}
                a={f.a}
                open={openFaq === i}
                onToggle={() => setOpenFaq(openFaq === i ? -1 : i)}
              />
            ))}
          </div>
        </div>
      </section>

      {/* ── PRE-FOOTER ───────────────────────────────────── */}
      <section style={{ padding: '120px 0', background: 'var(--green-deep)', color: '#fff' }}>
        <div className="wrap">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2,1fr)', gap: 32 }}>
            {[
              {
                tag:     'Für GmbH-Eigentümer',
                title:   'Sparen Sie Ihrem Steuerberater Arbeit — und sich Honorar.',
                bullets: [
                  'PDF hochladen, CSV herunterladen, weiterleiten',
                  'Kein Fachwissen nötig — Konfiguration in 2 Minuten',
                  'Sie behalten die Kontrolle über Ihre eigenen Daten',
                ],
              },
              {
                tag:     'Für Steuerberater',
                title:   'Mechanische Bucharbeit automatisieren — Beratungszeit gewinnen.',
                bullets: [
                  'Buchungsvorschlag zur fachkundigen Prüfung',
                  'SKR03 & SKR04, alle Parameter konfigurierbar',
                  'DATEV-Importdatei direkt aus Ihrem Workflow',
                ],
              },
            ].map((c, i) => (
              <div key={i} style={{
                background:     'rgba(255,255,255,.04)',
                border:         '1px solid rgba(147,197,253,.18)',
                borderRadius:   22,
                padding:        '44px 40px',
                display:        'flex',
                flexDirection:  'column',
              }}>
                <div className="mono" style={{
                  fontSize:      11,
                  letterSpacing: '.1em',
                  textTransform: 'uppercase',
                  color:         'var(--accent-2)',
                  marginBottom:  24,
                }}>
                  ● {c.tag}
                </div>
                <h3 className="display" style={{
                  fontSize:     'clamp(28px,3vw,38px)',
                  color:        '#fff',
                  marginBottom: 28,
                  lineHeight:   1.1,
                }}>
                  {c.title}
                </h3>
                <ul style={{ listStyle: 'none', padding: 0, margin: '0 0 36px', display: 'grid', gap: 14 }}>
                  {c.bullets.map((b, j) => (
                    <li key={j} style={{
                      display:    'flex',
                      alignItems: 'flex-start',
                      gap:        12,
                      fontSize:   15,
                      color:      'rgba(255,255,255,.78)',
                      lineHeight: 1.5,
                    }}>
                      <svg
                        width="16" height="16" viewBox="0 0 24 24" fill="none"
                        stroke="var(--accent-2)" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"
                        style={{ marginTop: 3, flexShrink: 0 }}
                      >
                        <polyline points="20 6 9 17 4 12" />
                      </svg>
                      <span>{b}</span>
                    </li>
                  ))}
                </ul>
                <button
                  onClick={scrollToUpload}
                  style={{
                    alignSelf:      'flex-start',
                    marginTop:      'auto',
                    padding:        '14px 24px',
                    borderRadius:   999,
                    background:     'var(--accent-2)',
                    color:          'var(--green-deep)',
                    border:         'none',
                    cursor:         'pointer',
                    fontSize:       14,
                    fontWeight:     600,
                    letterSpacing:  '-.005em',
                    display:        'inline-flex',
                    alignItems:     'center',
                    gap:            10,
                  }}
                >
                  Ersten Export starten
                  <svg
                    width="14" height="14" viewBox="0 0 24 24" fill="none"
                    stroke="currentColor" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"
                  >
                    <line x1="5" y1="12" x2="19" y2="12" />
                    <polyline points="12 5 19 12 12 19" />
                  </svg>
                </button>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── FOOTER ───────────────────────────────────────── */}
      <footer style={{ background: 'var(--bg)', borderTop: '1px solid var(--line)', padding: '40px 0' }}>
        <div className="wrap" style={{
          display:        'flex',
          justifyContent: 'space-between',
          alignItems:     'center',
          flexWrap:       'wrap',
          gap:            16,
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 18 }}>
            <Wordmark size={13} />
            <span style={{ fontSize: 13, color: 'var(--faint)' }}>
              Buchungsstapel für Wertpapier&shy;abrechnungen
            </span>
          </div>
          <div style={{ display: 'flex', gap: 24 }}>
            {['Impressum', 'Datenschutz', 'AGB', 'AVV'].map((t) => (
              <a key={t} href="#" style={{ fontSize: 13, color: 'var(--mute)' }}>{t}</a>
            ))}
          </div>
        </div>
      </footer>

      {/* ── Modal ────────────────────────────────────────── */}
      {showModal && (
        <ConfigModal file={file} onClose={() => setShowModal(false)} />
      )}
    </>
  )
}
