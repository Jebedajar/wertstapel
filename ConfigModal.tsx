'use client'

import { useState } from 'react'
import { PLANS, buildFilenames } from '@/lib/data'

type Phase = 'config' | 'stripe' | 'processing' | 'done'

interface Props { file: File | null; onClose: () => void }

const Eyebrow = ({ children }: { children: React.ReactNode }) => (
  <div className="eyebrow" style={{ marginBottom: 8 }}>{children}</div>
)

function Radio({ val, current, onSet }: { val: string; current: string; onSet: (v: string) => void }) {
  const sel = current === val
  return (
    <label onClick={() => onSet(val)}
      style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14, color: 'var(--ink)', userSelect: 'none' }}>
      <div style={{
        width: 16, height: 16, borderRadius: '50%', flexShrink: 0,
        border: `2px solid ${sel ? 'var(--gr)' : 'var(--ln2)'}`,
        background: sel ? 'var(--gr)' : '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {sel && <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />}
      </div>
      <span className="mono" style={{ fontSize: 13 }}>{val}</span>
      <span style={{ fontSize: 11, color: 'var(--mu)' }}>{val === 'SKR04' ? '(Kapitalges.)' : '(Personenges.)'}</span>
    </label>
  )
}

function DoneScreen({ filenames, onClose }: { filenames: ReturnType<typeof buildFilenames>; onClose: () => void }) {
  return (
    <div style={{ padding: '44px 36px', textAlign: 'center' }}>
      <div style={{ width: 64, height: 64, borderRadius: 18, background: 'var(--gr)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.8" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
      </div>
      <h3 className="display" style={{ fontSize: 28, marginBottom: 8, color: 'var(--ink)' }}>Export erfolgreich.</h3>
      <div style={{ fontSize: 14, color: 'var(--mu)', marginBottom: 28 }}>104 Belege · 264 Buchungssätze · alle Plausibilitätsprüfungen bestanden</div>
      {([['stapel', 'DATEV-Import'], ['plausi', 'Plausibilitätsbericht'], ['protokoll', 'Verarbeitungsprotokoll']] as const).map(([k, lb]) => (
        <div key={k} style={{ border: '1px solid var(--ln)', borderRadius: 12, padding: '12px 16px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 8, cursor: 'pointer', textAlign: 'left' }}>
          <div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--ink)' }}>{filenames[k]}</div>
            <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 2 }}>{lb}</div>
          </div>
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="var(--gr)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M12 5v14" /><path d="M19 12l-7 7-7-7" /></svg>
        </div>
      ))}
      <div style={{ fontSize: 11, color: 'var(--fa)', margin: '14px 0' }}>Download-Links per E-Mail · gültig 24 Stunden</div>
      <button onClick={onClose} style={{ width: '100%', padding: 14, border: '1px solid var(--ln)', borderRadius: 12, background: '#fff', fontSize: 14, fontWeight: 500, color: 'var(--ink2)' }}>
        Schließen
      </button>
    </div>
  )
}

function StripeScreen({ plan, onPay }: { plan: string; onPay: () => void }) {
  const [email, setEmail] = useState('')
  const p = PLANS.find(x => x.id === plan)!
  return (
    <div style={{ paddingBottom: 28 }}>
      <div style={{ background: '#635bff', padding: '20px 28px', borderRadius: '24px 24px 0 0', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
        <span style={{ color: '#fff', fontSize: 15, fontWeight: 700, letterSpacing: '-.01em', fontFamily: 'ui-monospace,monospace' }}>stripe</span>
        <span style={{ fontFamily: 'ui-monospace,monospace', fontSize: 13, color: 'rgba(255,255,255,.75)' }}>Checkout</span>
      </div>
      <div style={{ padding: '24px 28px 0' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '12px 14px', background: '#f6f9fc', borderRadius: 8, marginBottom: 22, border: '1px solid #e3e8ef' }}>
          <div>
            <div style={{ fontSize: 13, fontWeight: 600, color: '#1a1f36' }}>Wertstapel · {p.label}</div>
            <div style={{ fontSize: 11, color: '#697386', marginTop: 2 }}>{p.perExport}</div>
          </div>
          <div style={{ fontFamily: 'ui-monospace,monospace', fontSize: 15, fontWeight: 700, color: '#1a1f36' }}>{p.price} €</div>
        </div>
        <div style={{ marginBottom: 14 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: '#697386', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '.04em' }}>E-Mail</div>
          <input type="email" value={email} onChange={e => setEmail(e.target.value)} placeholder="ihre@kanzlei.de"
            style={{ width: '100%', padding: '10px 12px', border: '1px solid #e3e8ef', borderRadius: 6, fontSize: 14, outline: 'none', color: '#1a1f36', fontFamily: 'inherit' }} />
          <div style={{ fontSize: 11, color: '#9b9eb0', marginTop: 4 }}>Für Rechnung und Download-Links</div>
        </div>
        <div style={{ marginBottom: 20 }}>
          <div style={{ fontSize: 11, fontWeight: 500, color: '#697386', marginBottom: 5, textTransform: 'uppercase', letterSpacing: '.04em' }}>Kartendaten</div>
          <div style={{ border: '1px solid #e3e8ef', borderRadius: 6, overflow: 'hidden' }}>
            <input placeholder="1234 1234 1234 1234"
              style={{ width: '100%', padding: '10px 12px', border: 'none', fontSize: 14, outline: 'none', color: '#1a1f36', fontFamily: 'ui-monospace,monospace', borderBottom: '1px solid #e3e8ef' }} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr' }}>
              <input placeholder="MM / JJ" style={{ padding: '10px 12px', border: 'none', fontSize: 14, outline: 'none', fontFamily: 'ui-monospace,monospace', borderRight: '1px solid #e3e8ef' }} />
              <input placeholder="CVC" style={{ padding: '10px 12px', border: 'none', fontSize: 14, outline: 'none', fontFamily: 'ui-monospace,monospace' }} />
            </div>
          </div>
        </div>
        <div style={{ display: 'flex', gap: 8, marginBottom: 22 }}>
          <div style={{ flex: 1, padding: '8px 12px', border: '2px solid #635bff', borderRadius: 6, background: '#f5f4ff', fontSize: 12, fontWeight: 600, color: '#635bff', textAlign: 'center', cursor: 'pointer' }}>Kreditkarte</div>
          <div style={{ flex: 1, padding: '8px 12px', border: '1px solid #e3e8ef', borderRadius: 6, fontSize: 12, color: '#697386', textAlign: 'center', cursor: 'pointer' }}>SEPA-Lastschrift</div>
        </div>
        <button onClick={onPay} style={{ width: '100%', padding: 13, borderRadius: 6, background: '#635bff', color: '#fff', border: 'none', fontSize: 15, fontWeight: 600, marginBottom: 14 }}>
          {p.price} € bezahlen
        </button>
        <div style={{ textAlign: 'center', fontSize: 11, color: '#9b9eb0', paddingBottom: 4 }}>
          Abgesichert durch <strong>Stripe</strong>
        </div>
      </div>
    </div>
  )
}

export default function ConfigModal({ file, onClose }: Props) {
  const [skr,     setSkr]     = useState('SKR04')
  const [bank,    setBank]    = useState('1801')
  const [mandant, setMandant] = useState('')
  const [plan,    setPlan]    = useState('five')
  const [phase,   setPhase]   = useState<Phase>('config')
  const [editing, setEditing] = useState(false)

  const filenames = buildFilenames(mandant)
  const summary   = [skr, `Bankkonto ${bank}`, mandant.trim() || 'Mandantennummer —']

  return (
    <div className="modal-overlay">
      <div className="modal-box">

        {phase === 'done' && <DoneScreen filenames={filenames} onClose={onClose} />}

        {phase === 'stripe' && (
          <StripeScreen plan={plan} onPay={() => { setPhase('processing'); setTimeout(() => setPhase('done'), 2400) }} />
        )}

        {phase === 'processing' && (
          <div style={{ padding: '60px 40px', textAlign: 'center' }}>
            <div style={{ width: 64, height: 64, borderRadius: 18, background: 'var(--grs)', color: 'var(--gr)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20, animation: 'pulse 1.4s ease-in-out infinite' }}>
              <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                <path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z" /><polyline points="14 2 14 8 20 8" />
              </svg>
            </div>
            <h3 className="display" style={{ fontSize: 24, marginBottom: 8, color: 'var(--ink)' }}>PDF wird verarbeitet…</h3>
            <div style={{ fontSize: 14, color: 'var(--mu)' }}>Belege werden erkannt · Buchungslogik angewendet · DTVF-CSV erstellt</div>
          </div>
        )}

        {phase === 'config' && (
          <>
            {/* Header */}
            <div style={{ padding: '26px 32px', borderBottom: '1px solid var(--ln)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div>
                  <h3 className="display" style={{ fontSize: 24, marginBottom: 6, color: 'var(--ink)' }}>Ihr PDF ist bereit.</h3>
                  <div className="mono" style={{ fontSize: 12, color: 'var(--mu)' }}>{file?.name ?? 'Orderabrechnungen.pdf'}</div>
                </div>
                <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, color: 'var(--fa)', lineHeight: 1, padding: 4 }}>×</button>
              </div>
            </div>

            <div style={{ padding: '20px 32px 28px' }}>
              {/* Compact config */}
              <div style={{ padding: '14px 16px', borderRadius: 12, marginBottom: 22, background: 'var(--bg)', border: '1px solid var(--ln)' }}>
                {!editing ? (
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                    <span style={{ fontSize: 13, color: 'var(--ink2)', lineHeight: 1.6 }}>
                      {summary.map((p, i) => (
                        <span key={i}>
                          {i > 0 && <span style={{ color: 'var(--fa)', margin: '0 7px' }}>·</span>}
                          <span className={i === 0 ? 'mono' : ''} style={{ fontSize: 13, color: i === 2 && !mandant.trim() ? 'var(--fa)' : 'var(--ink2)' }}>{p}</span>
                        </span>
                      ))}
                    </span>
                    <button onClick={() => setEditing(true)} style={{ background: 'none', border: 'none', fontSize: 13, color: 'var(--gr)', display: 'flex', alignItems: 'center', gap: 4, flexShrink: 0 }}>
                      anpassen
                      <svg width="11" height="11" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round">
                        <path d="M11 4H4a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2v-7" />
                        <path d="M18.5 2.5a2.121 2.121 0 0 1 3 3L12 15l-4 1 1-4 9.5-9.5z" />
                      </svg>
                    </button>
                  </div>
                ) : (
                  <div>
                    <div style={{ marginBottom: 14 }}>
                      <Eyebrow>Kontenrahmen</Eyebrow>
                      <div style={{ display: 'flex', gap: 22, flexWrap: 'wrap' }}>
                        <Radio val="SKR04" current={skr} onSet={setSkr} />
                        <Radio val="SKR03" current={skr} onSet={setSkr} />
                      </div>
                    </div>
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 10 }}>
                      <div>
                        <Eyebrow>Bankkonto</Eyebrow>
                        <input value={bank} onChange={e => setBank(e.target.value)} placeholder="1801"
                          style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13, padding: '9px 11px', border: '1px solid var(--ln)', borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)' }} />
                      </div>
                      <div>
                        <Eyebrow>Mandantennr. <span style={{ textTransform: 'none', letterSpacing: 0, fontSize: 10, opacity: .6 }}>(optional)</span></Eyebrow>
                        <input value={mandant} onChange={e => setMandant(e.target.value)} placeholder="z. B. 31385"
                          style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13, padding: '9px 11px', border: '1px solid var(--ln)', borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)' }} />
                      </div>
                    </div>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                      {mandant.trim() && (
                        <div className="mono" style={{ fontSize: 11, color: 'var(--mu)', padding: '3px 8px', background: 'var(--bga)', borderRadius: 5 }}>
                          → {filenames.stapel}
                        </div>
                      )}
                      <button onClick={() => setEditing(false)} style={{ marginLeft: 'auto', background: 'none', border: 'none', fontSize: 12, color: 'var(--mu)' }}>fertig ✓</button>
                    </div>
                  </div>
                )}
              </div>

              {/* Paket */}
              <div style={{ marginBottom: 22 }}>
                <Eyebrow>Paket</Eyebrow>
                {PLANS.map(p => (
                  <div key={p.id} onClick={() => setPlan(p.id)} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '12px 16px', borderRadius: 12, marginBottom: 6, cursor: 'pointer',
                    border: plan === p.id ? '1.5px solid var(--gr)' : '1px solid var(--ln)',
                    background: plan === p.id ? 'var(--grs)' : '#fff', transition: 'all .12s',
                  }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {p.label}
                        {p.popular && <span className="mono" style={{ fontSize: 10, background: 'var(--gr)', color: '#fff', padding: '2px 7px', borderRadius: 4 }}>BELIEBT</span>}
                      </div>
                      <div className="mono" style={{ fontSize: 11, color: plan === p.id ? 'var(--gr)' : 'var(--mu)', marginTop: 3 }}>{p.perExport}</div>
                    </div>
                    <div className="mono" style={{ fontSize: 15, fontWeight: 600, color: 'var(--ink)', flexShrink: 0 }}>{p.price} €</div>
                  </div>
                ))}
              </div>

              <button onClick={() => setPhase('stripe')} style={{ width: '100%', padding: 16, borderRadius: 12, background: 'var(--ink)', color: '#fff', border: 'none', fontSize: 15, fontWeight: 600, letterSpacing: '-.01em', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10 }}>
                Jetzt bezahlen und exportieren
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
              </button>
              <div style={{ textAlign: 'center', fontSize: 11, color: 'var(--fa)', marginTop: 12 }}>
                Zahlung via Stripe · Rechnung per E-Mail · Pakete verfallen nicht
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  )
}
