'use client'

import { useState, useEffect, useRef } from 'react'

interface User {
  email: string
  credits: number
  flat_until: string | null
}

export default function NavAccount({ onScrollToUpload }: { onScrollToUpload: () => void }) {
  const [user,     setUser]     = useState<User | null>(null)
  const [loading,  setLoading]  = useState(true)
  const [open,     setOpen]     = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    fetch('/api/auth/me', { credentials: 'include' })
      .then(r => r.ok ? r.json() : null)
      .then(data => { setUser(data); setLoading(false) })
      .catch(() => setLoading(false))
  }, [])

  // Close dropdown on outside click
  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  const logout = async () => {
    await fetch('/api/auth/logout', { method: 'POST', credentials: 'include' })
    setUser(null)
    setOpen(false)
  }

  const hasCredits = user && (
    user.credits > 0 ||
    (user.flat_until && new Date(user.flat_until) >= new Date())
  )

  const creditLabel = user
    ? user.flat_until && new Date(user.flat_until) >= new Date()
      ? 'Flat'
      : `${user.credits}`
    : ''

  if (loading) return <div style={{ width: 80 }} />

  if (!user) {
    return (
      <a href="/login" style={{
        fontSize: 14, fontWeight: 500, color: 'var(--ink2)',
        textDecoration: 'none',
      }}>
        Login
      </a>
    )
  }

  return (
    <div ref={ref} style={{ position: 'relative' }}>
      <button
        onClick={() => setOpen(!open)}
        style={{
          display: 'flex', alignItems: 'center', gap: 8,
          background: hasCredits ? 'var(--grs)' : 'var(--bga)',
          border: `1px solid ${hasCredits ? 'var(--a2)' : 'var(--ln2)'}`,
          borderRadius: 999, padding: '7px 14px',
          cursor: 'pointer', fontSize: 13, fontWeight: 600,
          color: hasCredits ? 'var(--gr)' : 'var(--mu)',
          transition: 'all .15s',
        }}
      >
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none"
          stroke="currentColor" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
          <circle cx="12" cy="8" r="4" />
          <path d="M4 20c0-4 3.6-7 8-7s8 3 8 7" />
        </svg>
        {user.flat_until && new Date(user.flat_until) >= new Date()
          ? 'Jahresflat'
          : `Guthaben: ${user.credits}`
        }
      </button>

      {open && (
        <div style={{
          position: 'absolute', top: 'calc(100% + 10px)', right: 0,
          background: '#fff', border: '1px solid var(--ln)',
          borderRadius: 16, padding: '20px 22px', minWidth: 240,
          boxShadow: '0 8px 32px rgba(0,0,0,.12)', zIndex: 100,
        }}>
          {/* Credits display */}
          <div style={{ marginBottom: 18 }}>
            {user.flat_until && new Date(user.flat_until) >= new Date() ? (
              <>
                <div className="display" style={{ fontSize: 28, color: 'var(--ink)', marginBottom: 4 }}>Jahresflat</div>
                <div style={{ fontSize: 12, color: 'var(--mu)' }}>
                  Gültig bis {new Date(user.flat_until).toLocaleDateString('de-DE')}
                </div>
              </>
            ) : (
              <>
                <div className="display" style={{ fontSize: 28, color: user.credits > 0 ? 'var(--gr)' : 'var(--mu)', marginBottom: 4 }}>
                  {user.credits} {user.credits === 1 ? 'Export' : 'Exporte'}
                </div>
                <div style={{ fontSize: 12, color: 'var(--mu)' }}>verbleibend</div>
              </>
            )}
          </div>

          {/* Email */}
          <div style={{
            padding: '8px 10px', background: 'var(--bg)',
            borderRadius: 8, marginBottom: 16,
          }}>
            <div className="mono" style={{ fontSize: 11, color: 'var(--mu)', marginBottom: 2 }}>Angemeldet als</div>
            <div className="mono" style={{ fontSize: 12, color: 'var(--ink)', wordBreak: 'break-all' }}>{user.email}</div>
          </div>

          {/* CTA */}
          {(user.credits > 0 || (user.flat_until && new Date(user.flat_until) >= new Date())) && (
            <button
              onClick={() => { setOpen(false); onScrollToUpload() }}
              style={{
                width: '100%', padding: '11px', borderRadius: 10,
                background: 'var(--ink)', color: '#fff', border: 'none',
                cursor: 'pointer', fontSize: 13, fontWeight: 600,
                marginBottom: 10, display: 'flex', alignItems: 'center',
                justifyContent: 'center', gap: 8,
              }}
            >
              Neuen Export starten →
            </button>
          )}

          {user.credits === 0 && !user.flat_until && (
            <button
              onClick={() => { setOpen(false); onScrollToUpload() }}
              style={{
                width: '100%', padding: '11px', borderRadius: 10,
                background: 'var(--lm)', color: 'var(--ink)', border: 'none',
                cursor: 'pointer', fontSize: 13, fontWeight: 600,
                marginBottom: 10,
              }}
            >
              Guthaben aufladen →
            </button>
          )}

          {/* Logout */}
          <button onClick={logout} style={{
            background: 'none', border: 'none', cursor: 'pointer',
            fontSize: 12, color: 'var(--fa)', padding: 0, width: '100%',
            textAlign: 'center',
          }}>
            Abmelden
          </button>
        </div>
      )}
    </div>
  )
}
