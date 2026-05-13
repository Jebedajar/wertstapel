'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'

const LogoMark = () => (
  <svg width="13" height="16" viewBox="0 0 18 22" fill="none" aria-hidden="true">
    <rect width="18" height="15" rx="3" fill="var(--gr)" />
    <rect y="18" width="18" height="4" rx="2" fill="var(--gr)" opacity="0.32" />
  </svg>
)

export default function LoginPage() {
  const [email,   setEmail]   = useState('')
  const [phase,   setPhase]   = useState<'input' | 'sending' | 'sent' | 'error'>('input')
  const [message, setMessage] = useState('')

  // If already logged in, redirect to home
  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? window.location.href = '/' : null)
      .catch(() => null)
  }, [])

  const handleSubmit = async () => {
    if (!email.includes('@')) return
    setPhase('sending')
    try {
      const res = await fetch('/api/auth/magic-link', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ email }),
      })
      if (res.ok) {
        setPhase('sent')
      } else {
        const data = await res.json()
        setMessage(data.detail || 'Unbekannter Fehler')
        setPhase('error')
      }
    } catch {
      setMessage('Verbindungsfehler. Bitte versuchen Sie es erneut.')
      setPhase('error')
    }
  }

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', flexDirection: 'column' }}>

      {/* Minimal nav */}
      <nav style={{ borderBottom: '1px solid var(--ln)', padding: '0 24px', height: 60, display: 'flex', alignItems: 'center' }}>
        <Link href="/" style={{ display: 'inline-flex', alignItems: 'center', gap: 7, textDecoration: 'none', color: 'var(--ink)' }}>
          <LogoMark />
          <span style={{ fontWeight: 700, fontSize: 13, letterSpacing: '.04em', textTransform: 'uppercase' }}>WERTSTAPEL</span>
        </Link>
      </nav>

      {/* Center card */}
      <div style={{ flex: 1, display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '40px 20px' }}>
        <div style={{ width: '100%', maxWidth: 400, background: '#fff', borderRadius: 20, padding: '40px 36px', border: '1px solid var(--ln)', boxShadow: '0 4px 24px rgba(0,0,0,.06)' }}>

          {phase === 'sent' ? (
            <div style={{ textAlign: 'center' }}>
              <div style={{ width: 56, height: 56, borderRadius: 16, background: 'var(--grs)', display: 'inline-flex', alignItems: 'center', justifyContent: 'center', marginBottom: 20 }}>
                <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="var(--gr)" strokeWidth="2.2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z" />
                  <polyline points="22,6 12,13 2,6" />
                </svg>
              </div>
              <h1 className="display" style={{ fontSize: 24, marginBottom: 10, color: 'var(--ink)' }}>
                Link verschickt.
              </h1>
              <p style={{ fontSize: 14, color: 'var(--mu)', lineHeight: 1.6, marginBottom: 24 }}>
                Wir haben einen Login-Link an<br />
                <strong style={{ color: 'var(--ink)' }}>{email}</strong><br />
                geschickt. Bitte prüfen Sie Ihr Postfach.
              </p>
              <div style={{ fontSize: 12, color: 'var(--fa)' }}>
                Der Link ist 15 Minuten gültig.
              </div>
            </div>

          ) : (
            <>
              <h1 className="display" style={{ fontSize: 26, marginBottom: 8, color: 'var(--ink)' }}>
                Anmelden
              </h1>
              <p style={{ fontSize: 14, color: 'var(--mu)', marginBottom: 28, lineHeight: 1.55 }}>
                Geben Sie Ihre E-Mail-Adresse ein. Wir schicken Ihnen einen Login-Link — kein Passwort nötig.
              </p>

              <div style={{ marginBottom: 16 }}>
                <div className="eyebrow" style={{ marginBottom: 8 }}>E-Mail-Adresse</div>
                <input
                  type="email"
                  value={email}
                  onChange={e => setEmail(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSubmit()}
                  placeholder="ihre@kanzlei.de"
                  autoFocus
                  style={{
                    width: '100%', padding: '12px 14px',
                    border: '1px solid var(--ln)', borderRadius: 10,
                    fontSize: 15, outline: 'none', color: 'var(--ink)',
                    fontFamily: 'inherit',
                  }}
                />
              </div>

              {phase === 'error' && (
                <div style={{ fontSize: 13, color: '#B91C1C', marginBottom: 14, padding: '8px 12px', background: '#FEF2F2', borderRadius: 8 }}>
                  {message}
                </div>
              )}

              <button
                onClick={handleSubmit}
                disabled={phase === 'sending' || !email.includes('@')}
                style={{
                  width: '100%', padding: '13px', borderRadius: 10,
                  background: email.includes('@') ? 'var(--ink)' : 'var(--ln)',
                  color: email.includes('@') ? '#fff' : 'var(--fa)',
                  border: 'none', cursor: email.includes('@') ? 'pointer' : 'default',
                  fontSize: 14, fontWeight: 600, transition: 'all .15s',
                  display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8,
                }}
              >
                {phase === 'sending' ? 'Wird gesendet…' : 'Login-Link senden →'}
              </button>

              <div style={{ marginTop: 24, textAlign: 'center', fontSize: 12, color: 'var(--fa)', lineHeight: 1.6 }}>
                Nutzen Sie die E-Mail-Adresse<br />mit der Sie Ihr Paket erworben haben.
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  )
}
