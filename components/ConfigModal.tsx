'use client'

import { useState } from 'react'
import { PLANS, buildFilenames } from '@/lib/data'

type Phase = 'config' | 'stripe' | 'processing' | 'done'

interface ConfigModalProps {
  file:    File | null
  onClose: () => void
}

function EyebrowLabel({ children }: { children: React.ReactNode }) {
  return (
    <div style={{
      fontFamily: 'JetBrains Mono, monospace', fontSize: 11,
      letterSpacing: '.08em', textTransform: 'uppercase' as const,
      color: 'var(--mute)', marginBottom: 8,
    }}>{children}</div>
  )
}

function ProcessingScreen() {
  return (
    <div style={{ padding: '60px 40px', textAlign: 'center' }}>
      <div style={{
        width: 64, height: 64, borderRadius: 18, background: 'var(--green-soft)',
        color: 'var(--green)', display: 'inline-flex', alignItems: 'center',
        justifyContent: 'center', marginBottom: 20,
        animation: 'pulse 1.4s ease-in-out infinite',
      }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" />
          <polyline points="14 2 14 8 20 8" />
        </svg>
      </div>
      <h3 className="display" style={{ fontSize: 24, marginBottom: 8 }}>
        PDF wird verarbeitet…
      </h3>
      <div style={{ fontSize: 14, color: 'var(--mute)' }}>
        Belege werden erkannt · Buchungslogik angewendet · DTVF-CSV erstellt
      </div>
    </div>
  )
}

function DoneScreen({ onClose, filenames }: {
  onClose: () => void
  filenames: { stapel: string; plausi: string; protokoll: string }
}) {
  const files: [string, string][] = [
    [filenames.stapel,    'DATEV-Import'],
    [filenames.plausi,    'Plausibilitätsbericht'],
    [filenames.protokoll, 'Verarbeitungsprotokoll'],
  ]
  return (
    <div style={{ padding: '44px 36px', textAlign: 'center' }}>
      <div style={{
        width: 64, height: 64, borderRadius: 18, background: 'var(--green)',
        display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20,
      }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none"
          stroke="#fff" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round">
          <polyline points="20 6 9 17 4 12" />
        </svg>
      </div>
      <h3 className="display" style={{ fontSize: 28, marginBottom: 8 }}>
        Export erfolgreich.
      </h3>
      <div style={{ fontSize: 14, color: 'var(--mute)', marginBottom: 28 }}>
        104 Belege · 264 Buchungssätze · alle Plausibilitätsprüfungen bestanden
      </div>
      <div style={{ display: 'grid', gap: 8, marginBottom: 20 }}>
        {files.map(([fn, lb]) => (
          <button key={fn} style={{
            border: '1px solid var(--line)', borderRadius: 12, padding: '12px 16px',
            display: 'flex', justifyContent: 'space-between', alignItems: 'center',
            cursor: 'pointer', textAlign: 'left', background: '#fff', width: '100%',
          }}>
            <div>
              <div className="mono" style={{ fontSize: 12, color: 'var(--ink)' }}>{fn}</div>
              <div style={{ fontSize: 11, color: 'var(--mute)', marginTop: 2 }}>{lb}</div>
            </div>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
              stroke="var(--green)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
              <path d="M12 5v14" /><path d="M19 12l-7 7-7-7" />
            </svg>
          </button>
        ))}
      </div>
      <div style={{ fontSize: 11, color: 'var(--faint)', marginBottom: 20 }}>
        Download-Links per E-Mail · gültig 24 Stunden
      </div>
      <button onClick={onClose} style={{
        width: '100%', padding: '14px', border: '1px solid var(--line)',
        borderRadius: 12, background: '#fff', cursor: 'pointer',
        fontSize: 14, fontWeight: 500, color: 'var(--ink-2)',
      }}>Schließen</button>
    </div>
  )
}

export function ConfigModal({ file, onClose }: ConfigModalProps) {
  const [skr,      setSkr]      = useState<'SKR03' | 'SKR04'>('SKR04')
  const [bank,     setBank]     = useState('1801')
  const [mandant,  setMandant]  = useState('')
  const [plan,     setPlan]     = useState('five')
  const [phase,    setPhase]    = useState<Phase>('config')
  const [email,    setEmail]    = useState('')
  const [editing,  setEditing]  = useState(false)   // ← compact vs edit mode

  const filenames = buildFilenames(mandant)

  const handlePay = () => {
    setPhase('stripe')
  }

  // ── Summary line shown in compact mode ─────────────────────
  const summaryParts = [
    skr,
    `Bankkonto ${bank}`,
    mandant.trim() ? `Mandant ${mandant.trim()}` : 'Mandantennummer —',
  ]

  return (
    <div className="modal-overlay">
      <div className="modal-box">

        {phase === 'done' ? (
          <DoneScreen onClose={onClose} filenames={filenames} />
        ) : phase === 'processing' ? (
          <ProcessingScreen />
        ) : (
          <>
            {/* Header */}
            <div style={{ padding: '26px 32px', borderBottom: '1px solid var(--line)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 className="display" style={{ fontSize: 24, marginBottom: 6 }}>
                    Ihr PDF ist bereit.
                  </h3>
                  <div className="mono" style={{ fontSize: 12, color: 'var(--mute)' }}>
                    {file?.name ?? 'Orderabrechnungen.pdf'}
                  </div>
                </div>
                <button onClick={onClose} aria-label="Schließen" style={{
                  background: 'none', border: 'none', cursor: 'pointer',
                  fontSize: 22, color: 'var(--faint)', lineHeight: 1, padding: 4,
                }}>×</button>
              </div>
            </div>

            <div style={{ padding: '20px 32px 28px' }}>

              {/* ── Config block: compact or editing ─────────── */}
              <div style={{
                padding: '14px 16px', borderRadius: 12, marginBottom: 22,
                background: 'var(--bg)', border: '1px solid var(--line)',
              }}>
                {!editing ? (
                  /* Compact summary */
                  <div style={{
                    display: 'flex', justifyContent: 'space-between',
                    alignItems: 'center', flexWrap: 'wrap', gap: 8,
                  }}>
                    <span style={{ fontSize: 13, color: 'var(--ink-2)' }}>
                      {summaryParts.map((p, i) => (
                        <span key={i}>
                          {i > 0 && <span style={{ color: 'var(--faint)', margin: '0 6px' }}>·</span>}
                          <span style={{
                            fontFamily: i === 0 ? 'JetBrains Mono, monospace' : 'inherit',
                            fontSize: i === 0 ? 13 : 13,
                            color: i === 2 && !mandant.trim() ? 'var(--faint)' : 'var(--ink-2)',
                          }}>{p}</span>
                        </span>
                      ))}
                    </span>
                    <button onClick={() => setEditing(true)} style={{
                      background: 'none', border: 'none', cursor: 'pointer', padding: 0,
                      fontSize: 13, color: 'var(--green)', fontFamily: 'inherit',
                      display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0,
                    }}>
                      anpassen
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none"
                        stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  /* Edit mode */
                  <div>
                    {/* SKR as radio bullets */}
                    <div style={{ marginBottom: 16 }}>
                      <EyebrowLabel>Kontenrahmen</EyebrowLabel>
                      <div style={{ display: 'flex', gap: 20 }}>
                        {(['SKR04', 'SKR03'] as const).map(s => (
                          <label key={s} onClick={() => setSkr(s)} style={{
                            display: 'flex', alignItems: 'center', gap: 8,
                            cursor: 'pointer', fontSize: 14, color: 'var(--ink)',
                          }}>
                            <div style={{
                              width: 16, height: 16, borderRadius: '50%', flexShrink: 0,
                              border: `2px solid ${skr === s ? 'var(--green)' : 'var(--line-2)'}`,
                              background: skr === s ? 'var(--green)' : '#fff',
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                            }}>
                              {skr === s && (
                                <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />
                              )}
                            </div>
                            <span className="mono" style={{ fontSize: 13 }}>{s}</span>
                            <span style={{ fontSize: 11, color: 'var(--mute)' }}>
                              {s === 'SKR04' ? '(Kapitalges.)' : '(Personenges.)'}
                            </span>
                          </label>
                        ))}
                      </div>
                    </div>

                    {/* Bankkonto + Mandantennummer inline */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 12 }}>
                      <div>
                        <EyebrowLabel>Bankkonto</EyebrowLabel>
                        <input
                          value={bank}
                          onChange={e => setBank(e.target.value)}
                          placeholder="1801"
                          style={{
                            fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
                            padding: '9px 11px', border: '1px solid var(--line)',
                            borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)',
                          }}
                        />
                      </div>
                      <div>
                        <EyebrowLabel>
                          Mandantennr.{' '}
                          <span style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, opacity: .65 }}>
                            (optional)
                          </span>
                        </EyebrowLabel>
                        <input
                          value={mandant}
                          onChange={e => setMandant(e.target.value)}
                          placeholder="z. B. 31385"
                          style={{
                            fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
                            padding: '9px 11px', border: '1px solid var(--line)',
                            borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)',
                          }}
                        />
                      </div>
                    </div>

                    {/* Filename preview + close edit */}
                    <div style={{
                      display: 'flex', justifyContent: 'space-between',
                      alignItems: 'center', flexWrap: 'wrap', gap: 8,
                    }}>
                      {mandant.trim() && (
                        <div className="mono" style={{
                          fontSize: 11, color: 'var(--mute)',
                          padding: '4px 8px', background: 'var(--bg-alt)', borderRadius: 5,
                        }}>
                          → {filenames.stapel}
                        </div>
                      )}
                      <button onClick={() => setEditing(false)} style={{
                        marginLeft: 'auto', background: 'none', border: 'none',
                        cursor: 'pointer', fontSize: 12, color: 'var(--mute)',
                        fontFamily: 'inherit', padding: 0,
                      }}>
                        fertig ✓
                      </button>
                    </div>
                  </div>
                )}
              </div>

              {/* Paket */}
              <div style={{ marginBottom: 22 }}>
                <EyebrowLabel>Paket wählen</EyebrowLabel>
                <div style={{ display: 'grid', gap: 7 }}>
                  {PLANS.map(p => (
                    <div key={p.id} onClick={() => setPlan(p.id)} style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '12px 16px', borderRadius: 12, cursor: 'pointer',
                      border: plan === p.id
                        ? '1.5px solid var(--green)'
                        : '1px solid var(--line)',
                      background: plan === p.id ? 'var(--green-soft)' : '#fff',
                      transition: 'all .12s',
                    }}>
                      <div>
                        <div style={{
                          fontSize: 14, fontWeight: 600, color: 'var(--ink)',
                          display: 'flex', alignItems: 'center', gap: 8,
                        }}>
                          {p.label}
                          {p.popular && (
                            <span className="mono" style={{
                              fontSize: 10, background: 'var(--green)', color: '#fff',
                              padding: '2px 7px', borderRadius: 4,
                            }}>BELIEBT</span>
                          )}
                        </div>
                        <div className="mono" style={{
                          fontSize: 11,
                          color: plan === p.id ? 'var(--green)' : 'var(--mute)',
                          marginTop: 3, transition: 'color .12s',
                        }}>
                          {p.perExport}
                        </div>
                      </div>
                      <div className="mono" style={{ fontSize: 16, fontWeight: 600, color: 'var(--ink)', flexShrink: 0 }}>
                        {p.price} €
                      </div>
                    </div>
                  ))}
                </div>
              </div>

              {/* CTA */}
              <button onClick={handlePay} style={{
                width: '100%', padding: '16px', borderRadius: 12,
                background: 'var(--ink)', color: '#fff', border: 'none', cursor: 'pointer',
                fontSize: 15, fontWeight: 600, letterSpacing: '-.01em',
                display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10,
              }}>
                Jetzt bezahlen und exportieren
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none"
                  stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12" />
                  <polyline points="12 5 19 12 12 19" />
                </svg>
              </button>
              <div style={{
                textAlign: 'center', fontSize: 11,
                color: 'var(--faint)', marginTop: 12,
              }}>
                Zahlung via Stripe · Rechnung per E-Mail · Pakete verfallen nicht
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
