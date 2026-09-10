'use client'

import { useState, useEffect } from 'react'
import { PLANS } from '@/lib/data'
import LoadingLogo from './LoadingLogo'

type Phase = 'config' | 'paying' | 'redirecting'

const VK_DEFAULTS: Record<string, string> = { SKR04: '1801', SKR03: '1200' }
const BANKBEREICH: Record<string, [number, number]> = {
  SKR03: [1000, 1299],
  SKR04: [1600, 1899],
}

function validateVK(value: string, skr: string): string {
  const nr = parseInt(value, 10)
  if (isNaN(nr) || String(nr) !== value.trim()) return 'Keine gültige Kontonummer.'
  const bereich = BANKBEREICH[skr]
  if (bereich && (nr < bereich[0] || nr > bereich[1])) {
    return `Konto ${value} liegt nicht im Bankkontenbereich des ${skr} (${bereich[0]}–${bereich[1]}).`
  }
  return ''
}

interface User {
  email: string
  credits: number
  flat_until: string | null
}

interface Props { files: File[]; onClose: () => void; user?: User | null }

const Eyebrow = ({ children }: { children: React.ReactNode }) => (
  <div style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 11, letterSpacing: '.08em', textTransform: 'uppercase' as const, color: 'var(--ink)', fontWeight: 600, marginBottom: 8 }}>
    {children}
  </div>
)

function Radio({ val, current, onSet }: { val: string; current: string; onSet: (v: string) => void }) {
  const sel = current === val
  return (
    <label onClick={() => onSet(val)}
      style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14, color: 'var(--ink)', userSelect: 'none' as const }}>
      <div style={{
        width: 16, height: 16, borderRadius: '50%', flexShrink: 0,
        border: `2px solid ${sel ? 'var(--gr)' : 'var(--ln2)'}`,
        background: sel ? 'var(--gr)' : '#fff',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
      }}>
        {sel && <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />}
      </div>
      <span style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13 }}>{val}</span>
      <span style={{ fontSize: 11, color: 'var(--mu)' }}>{val === 'SKR04' ? '(Kapitalges.)' : '(Personenges.)'}</span>
    </label>
  )
}

function CreditBadge({ user }: { user: User }) {
  const flatValid = user.flat_until && new Date(user.flat_until) >= new Date()
  const label = flatValid
    ? 'Jahresflat — dieser Export ist enthalten'
    : `Guthaben: ${user.credits} ${user.credits === 1 ? 'Export' : 'Exporte'} verbleibend`
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 8, padding: '10px 14px', borderRadius: 10, background: 'var(--grs)', border: '1px solid var(--a2)', marginBottom: 22 }}>
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="var(--gr)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round"><polyline points="20 6 9 17 4 12" /></svg>
      <span style={{ fontSize: 13, color: 'var(--gr)', fontWeight: 600 }}>{label}</span>
      {!flatValid && <span style={{ fontSize: 12, color: 'var(--mu)', marginLeft: 'auto' }}>1 Credit wird verwendet</span>}
    </div>
  )
}

export default function ConfigModal({ files, onClose, user }: Props) {
  const [skr,           setSkr]           = useState('SKR04')
  const [bank,          setBank]          = useState('1801')
  const [vkTouched,     setVkTouched]     = useState(false)
  const [vkError,       setVkError]       = useState('')
  const [vermoegensart, setVermoegensart] = useState('UV')
  const [bewertung,     setBewertung]     = useState('fifo')
  const [mandant,       setMandant]       = useState('')
  const [plan,          setPlan]          = useState('five')
  const [email,         setEmail]         = useState('')
  const [consent,       setConsent]       = useState(false)
  const [editing,       setEditing]       = useState(false)
  const [phase,         setPhase]         = useState<Phase>('config')
  const [error,         setError]         = useState('')

  useEffect(() => {
    if (!vkTouched) setBank(VK_DEFAULTS[skr] ?? '')
  }, [skr, vkTouched])

  const handleVkChange = (val: string) => {
    setBank(val)
    setVkTouched(true)
    setVkError('')
  }

  const selectedPlan = PLANS.find(p => p.id === plan)!
  const multi = files.length > 1

  const hasCredits = user && (
    user.credits > 0 ||
    (user.flat_until && new Date(user.flat_until) >= new Date())
  )

  const handleDirectExport = async () => {
    if (files.length === 0) { setError('Keine Datei ausgewählt.'); return }
    const vkErr = validateVK(bank, skr)
    if (vkErr) { setVkError(vkErr); setEditing(true); return }
    setError('')
    setPhase('paying')
    try {
      const form = new FormData()
      files.forEach(f => form.append('files', f))
      form.append('skr', skr)
      form.append('bank', bank)
      form.append('vermoegensart', vermoegensart)
      form.append('bewertung', bewertung)
      form.append('mandant', mandant.trim())

      const res = await fetch('/api/export/start', { method: 'POST', body: form, credentials: 'include' })
      let data: { detail?: string; job_id?: string }
      try { data = await res.json() } catch { data = { detail: 'Serverfehler – bitte versuche es erneut.' } }

      if (!res.ok) throw new Error(data.detail ?? `Fehler ${res.status}`)
      setPhase('redirecting')
      window.location.href = data.job_id ? `/success?job_id=${data.job_id}` : '/success'
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler')
      setPhase('config')
    }
  }

  const handlePay = async () => {
    if (!email.trim() || !email.includes('@')) {
      setError('Bitte gib eine gültige E-Mail-Adresse ein.')
      return
    }
    if (files.length === 0) {
      setError('Keine Datei ausgewählt.')
      return
    }
    const vkErr = validateVK(bank, skr)
    if (vkErr) { setVkError(vkErr); setEditing(true); return }
    setError('')
    setPhase('paying')
    try {
      const form = new FormData()
      files.forEach(f => form.append('files', f))
      form.append('email', email.trim())
      form.append('plan', plan)
      form.append('skr', skr)
      form.append('bank', bank)
      form.append('vermoegensart', vermoegensart)
      form.append('bewertung', bewertung)
      form.append('mandant', mandant.trim())
      form.append('consent', 'true')

      const res = await fetch('/api/upload', { method: 'POST', body: form })
      let data: { detail?: string; checkout_url?: string }
      try { data = await res.json() } catch { data = { detail: 'Serverfehler – bitte versuche es erneut.' } }

      if (!res.ok) throw new Error(data.detail ?? `Fehler ${res.status}`)
      setPhase('redirecting')
      window.location.href = data.checkout_url!
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : 'Unbekannter Fehler')
      setPhase('config')
    }
  }

  if (phase === 'paying' || phase === 'redirecting') {
    return (
      <div className="modal-overlay">
        <div className="modal-box">
          <div style={{ padding: '64px 40px', textAlign: 'center' }}>
            <div style={{ marginBottom: 24 }}>
              <LoadingLogo size={80} />
            </div>
            <h3 className="display" style={{ fontSize: 24, marginBottom: 8, color: 'var(--ink)' }}>
              {phase === 'paying' ? (multi ? 'Dateien werden hochgeladen…' : 'Datei wird hochgeladen…') : (hasCredits ? 'Verarbeitung gestartet…' : 'Weiterleitung zu Stripe…')}
            </h3>
            <div style={{ fontSize: 14, color: 'var(--mu)' }}>Einen Moment bitte.</div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="modal-overlay">
      <div className="modal-box">
        {/* Header */}
        <div style={{ padding: '26px 32px', borderBottom: '1px solid var(--ln)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 className="display" style={{ fontSize: 24, marginBottom: 6, color: 'var(--ink)' }}>
                {multi ? 'Ihre Dateien sind bereit.' : 'Ihre Datei ist bereit.'}
              </h3>
              <div style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 12, color: 'var(--mu)' }}>
                {multi ? `(${files.length}) Dateien` : (files[0]?.name ?? 'Orderabrechnungen.pdf')}
              </div>
            </div>
            <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, color: 'var(--fa)', lineHeight: 1, padding: 4, cursor: 'pointer' }}>×</button>
          </div>
        </div>

        <div style={{ padding: '20px 32px 28px' }}>
          {/* Config block */}
          <div style={{ padding: '14px 16px', borderRadius: 12, marginBottom: 22, background: 'var(--bg)', border: '1px solid var(--ln)' }}>
            {!editing ? (
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: 8 }}>
                <span style={{ fontSize: 13, color: 'var(--ink2)', lineHeight: 1.6 }}>
                  {[
                    skr,
                    vermoegensart === 'AV' ? 'Anlagevermögen' : 'Umlaufvermögen',
                    `VK ${bank}`,
                    bewertung === 'fifo' ? 'FIFO' : 'Gleit. Ø',
                  ].map((p, i) => (
                    <span key={i}>
                      {i > 0 && <span style={{ color: 'var(--fa)', margin: '0 7px' }}>·</span>}
                      <span style={{ fontFamily: i === 0 || i === 2 ? 'var(--font-mono),ui-monospace,monospace' : 'inherit', fontSize: 13, color: 'var(--ink2)' }}>{p}</span>
                    </span>
                  ))}
                </span>
                <button onClick={() => setEditing(true)} style={{ background: 'none', border: 'none', fontSize: 13, color: 'var(--gr)', cursor: 'pointer', flexShrink: 0, textDecoration: 'underline' }}>
                  anpassen
                </button>
              </div>
            ) : (
              <div>
                {/* SKR */}
                <div style={{ marginBottom: 14 }}>
                  <Eyebrow>Kontenrahmen</Eyebrow>
                  <div style={{ display: 'flex', gap: 22, flexWrap: 'wrap' }}>
                    <Radio val="SKR04" current={skr} onSet={setSkr} />
                    <Radio val="SKR03" current={skr} onSet={setSkr} />
                  </div>
                </div>
                {/* Vermögensart */}
                <div style={{ marginBottom: 14 }}>
                  <Eyebrow>Vermögensart</Eyebrow>
                  <div style={{ display: 'flex', gap: 22, flexWrap: 'wrap' }}>
                    {[['UV', 'Umlaufvermögen'], ['AV', 'Anlagevermögen']].map(([val, label]) => {
                      const sel = vermoegensart === val
                      return (
                        <label key={val} onClick={() => setVermoegensart(val)}
                          style={{ display: 'flex', alignItems: 'center', gap: 8, cursor: 'pointer', fontSize: 14, color: 'var(--ink)', userSelect: 'none' as const }}>
                          <div style={{
                            width: 16, height: 16, borderRadius: '50%', flexShrink: 0,
                            border: `2px solid ${sel ? 'var(--gr)' : 'var(--ln2)'}`,
                            background: sel ? 'var(--gr)' : '#fff',
                            display: 'flex', alignItems: 'center', justifyContent: 'center',
                          }}>
                            {sel && <div style={{ width: 6, height: 6, borderRadius: '50%', background: '#fff' }} />}
                          </div>
                          <span style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13 }}>{val}</span>
                          <span style={{ fontSize: 11, color: 'var(--mu)' }}>{label}</span>
                        </label>
                      )
                    })}
                  </div>
                </div>
                {/* Bewertungsmethode */}
                <div style={{ marginBottom: 14 }}>
                  <Eyebrow>Bewertungsmethode</Eyebrow>
                  <select value={bewertung} onChange={e => setBewertung(e.target.value)}
                    style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13, padding: '9px 11px', border: '1px solid var(--ln)', borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)', background: '#fff' }}>
                    <option value="fifo">FIFO</option>
                    <option value="gleitender_durchschnitt">Gleitender Durchschnitt</option>
                  </select>
                  <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 5 }}>
                    Die einmal gewählte Methode ist beizubehalten (§ 252 Abs. 1 Nr. 6 HGB).
                  </div>
                </div>
                {/* VK + Mandant */}
                <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12, marginBottom: 10 }}>
                  <div>
                    <Eyebrow>Verrechnungskonto</Eyebrow>
                    <input value={bank}
                      onChange={e => handleVkChange(e.target.value)}
                      onBlur={() => { if (bank) setVkError(validateVK(bank, skr)) }}
                      placeholder={VK_DEFAULTS[skr] ?? '1801'}
                      style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13, padding: '9px 11px', border: `1px solid ${vkError ? '#ef4444' : 'var(--ln)'}`, borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)' }} />
                    {vkError && <div style={{ fontSize: 11, color: '#dc2626', marginTop: 4 }}>{vkError}</div>}
                    {!vkError && <div style={{ fontSize: 11, color: 'var(--mu)', marginTop: 4 }}>Eigenes Bankkonto des Depots</div>}
                  </div>
                  <div>
                    <Eyebrow>Mandantennr. <span style={{ textTransform: 'none' as const, letterSpacing: 0, fontSize: 10, opacity: .6 }}>(optional)</span></Eyebrow>
                    <input value={mandant} onChange={e => setMandant(e.target.value)} placeholder="z. B. 31385"
                      style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 13, padding: '9px 11px', border: '1px solid var(--ln)', borderRadius: 8, outline: 'none', width: '100%', color: 'var(--ink)' }} />
                  </div>
                </div>
                <button onClick={() => setEditing(false)} style={{ background: 'none', border: 'none', fontSize: 12, color: 'var(--mu)', cursor: 'pointer', marginLeft: 'auto', display: 'block' }}>fertig ✓</button>
              </div>
            )}
          </div>

          {hasCredits ? (
            /* ── Credit flow: logged-in user with balance ── */
            <>
              <CreditBadge user={user!} />

              {error && (
                <div style={{ marginBottom: 16, padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#dc2626' }}>
                  {error}
                </div>
              )}

              <button
                onClick={handleDirectExport}
                style={{ width: '100%', padding: 16, borderRadius: 12, border: 'none', fontSize: 15, fontWeight: 600, letterSpacing: '-.01em', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, background: 'var(--ink)', color: '#fff', cursor: 'pointer' }}
              >
                Export starten
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                </svg>
              </button>
              <div style={{ textAlign: 'center', marginTop: 12, fontSize: 11, color: 'var(--fa)' }}>
                Verarbeitung unter 5 Minuten · Download-Links per E-Mail
              </div>
            </>
          ) : (
            /* ── Stripe flow: no credits / not logged in ── */
            <>
              {/* Paket */}
              <div style={{ marginBottom: 22 }}>
                <Eyebrow>Paket</Eyebrow>
                {PLANS.map(p => (
                  <div key={p.id} onClick={() => setPlan(p.id)} style={{
                    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                    padding: '12px 16px', borderRadius: 12, marginBottom: 6, cursor: 'pointer',
                    border: plan === p.id ? '2px solid var(--gr)' : '1px solid var(--ln)',
                    background: plan === p.id ? 'var(--grs)' : '#fff',
                    transition: 'all .12s',
                  }}>
                    <div>
                      <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)', display: 'flex', alignItems: 'center', gap: 8 }}>
                        {p.label}
                        {p.popular && <span style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 10, background: 'var(--gr)', color: '#fff', padding: '2px 7px', borderRadius: 4 }}>BELIEBT</span>}
                      </div>
                      <div style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 11, color: plan === p.id ? 'var(--gr)' : 'var(--mu)', marginTop: 3 }}>{p.perExport}</div>
                    </div>
                    <div style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 15, fontWeight: 600, color: 'var(--ink)', flexShrink: 0 }}>{p.price} €</div>
                  </div>
                ))}
                <p style={{ fontSize: 12, color: 'var(--fa)', marginTop: 6 }}>· Preise zzgl. MwSt.</p>
              </div>

              {/* Email */}
              <div style={{ marginBottom: 20 }}>
                <Eyebrow>E-Mail für Rechnung &amp; Download-Link</Eyebrow>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  placeholder="ihre@kanzlei.de"
                  style={{ width: '100%', padding: '10px 12px', border: `1.5px solid ${error && !email ? '#ef4444' : 'var(--ln2)'}`, borderRadius: 8, fontSize: 14, outline: 'none', color: 'var(--ink)', fontFamily: 'inherit', boxSizing: 'border-box' as const }}
                />
              </div>

              {error && (
                <div style={{ marginBottom: 16, padding: '10px 14px', background: '#fef2f2', border: '1px solid #fecaca', borderRadius: 8, fontSize: 13, color: '#dc2626' }}>
                  {error}
                </div>
              )}

              {/* Consent */}
              <label onClick={() => setConsent(c => !c)} style={{ display: 'flex', alignItems: 'flex-start', gap: 10, cursor: 'pointer', marginBottom: 16, userSelect: 'none' as const }}>
                <div style={{ width: 22, height: 22, borderRadius: 5, flexShrink: 0, marginTop: 1, border: `2px solid ${consent ? 'var(--gr)' : 'var(--ln2)'}`, background: consent ? 'var(--gr)' : '#fff', display: 'flex', alignItems: 'center', justifyContent: 'center', transition: 'all .12s' }}>
                  {consent && <svg width="12" height="12" viewBox="0 0 12 12" fill="none" stroke="#fff" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="2 6 5 9 10 3" /></svg>}
                </div>
                <span style={{ fontSize: 13, color: 'var(--ink2)', lineHeight: 1.55 }}>
                  Ich kaufe als Unternehmer (§&nbsp;14 BGB) und akzeptiere die{' '}
                  <a href="/agb" target="_blank" rel="noopener" onClick={e => e.stopPropagation()} style={{ color: 'var(--ink2)', textDecoration: 'underline' }}>AGB</a>, den{' '}
                  <a href="/avv" target="_blank" rel="noopener" onClick={e => e.stopPropagation()} style={{ color: 'var(--ink2)', textDecoration: 'underline' }}>Auftragsverarbeitungsvertrag</a> sowie die{' '}
                  <a href="/datenschutz" target="_blank" rel="noopener" onClick={e => e.stopPropagation()} style={{ color: 'var(--ink2)', textDecoration: 'underline' }}>Datenschutzerklärung</a>.
                </span>
              </label>

              <button
                onClick={handlePay}
                disabled={!consent}
                style={{ width: '100%', padding: 16, borderRadius: 12, border: 'none', fontSize: 15, fontWeight: 600, letterSpacing: '-.01em', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, background: consent ? 'var(--ink)' : 'var(--ln2)', color: consent ? '#fff' : 'var(--mu)', cursor: consent ? 'pointer' : 'not-allowed', transition: 'all .15s' }}
              >
                {selectedPlan.price} € bezahlen und exportieren
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="5" y1="12" x2="19" y2="12"/><polyline points="12 5 19 12 12 19"/>
                </svg>
              </button>
              <div style={{ textAlign: 'center', marginTop: 16 }}>
                <p style={{ fontSize: 14, color: 'var(--ink2)', fontWeight: 500, lineHeight: 1.6, marginBottom: 0 }}>
                  Sie erhalten die Download-Links zusätzlich per Mail.<br />Die Links sind 24h gültig.
                </p>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
