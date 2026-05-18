'use client'

import { useEffect, useState, useRef } from 'react'
import { useSearchParams } from 'next/navigation'
import { Suspense } from 'react'
import dynamic from 'next/dynamic'
import LoadingLogo from '@/components/LoadingLogo'

const ConfigModal = dynamic(() => import('@/components/ConfigModal'), { ssr: false })

type Status = 'awaiting_payment' | 'paid' | 'processing' | 'done' | 'error' | 'loading'

function SuccessContent() {
  const params  = useSearchParams()
  const jobId   = params.get('job_id')

  const [status,    setStatus]    = useState<Status>('loading')
  const [files,     setFiles]     = useState<string[]>([])
  const [newFile,   setNewFile]   = useState<File | null>(null)
  const [showModal, setShowModal] = useState(false)
  const fileRef = useRef<HTMLInputElement>(null)

  useEffect(() => {
    if (!jobId) return
    const poll = async () => {
      try {
        const res  = await fetch(`/api/status/${jobId}`)
        const data = await res.json()
        setStatus(data.status)
        if (data.files) setFiles(data.files)
        if (data.status !== 'done' && data.status !== 'error') setTimeout(poll, 3000)
      } catch {
        setStatus('error')
      }
    }
    poll()
  }, [jobId])

  // Auto-login once job is paid or further — sets ws_session cookie
  useEffect(() => {
    if (!jobId) return
    if (status === 'paid' || status === 'processing' || status === 'done') {
      fetch(`/api/auth/post-purchase/${jobId}`, { method: 'POST', credentials: 'include' })
        .catch(() => {})
    }
  }, [status, jobId])

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0]
    if (f && f.type === 'application/pdf') { setNewFile(f); setShowModal(true) }
  }

  const statusConfig: Record<Status, { icon: string; title: string; text: string }> = {
    loading:          { icon: '⏳', title: 'Verbinde…',           text: 'Status wird abgerufen.' },
    awaiting_payment: { icon: '💳', title: 'Zahlung ausstehend',  text: 'Warte auf Zahlungsbestätigung.' },
    paid:             { icon: '✅', title: 'Zahlung bestätigt',   text: 'Verarbeitung startet gleich.' },
    processing:       { icon: '⚙️', title: 'Wird verarbeitet…',  text: 'PDF wird analysiert.' },
    done:             { icon: '🎉', title: 'Fertig!',             text: 'Deine Dateien sind bereit.' },
    error:            { icon: '❌', title: 'Fehler',              text: 'Bei der Verarbeitung ist ein Fehler aufgetreten.' },
  }
  const cfg = statusConfig[status]

  return (
    <main style={{ minHeight: '100vh', background: 'var(--bg)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '24px 16px' }}>
      <div style={{ background: '#fff', borderRadius: 24, boxShadow: '0 20px 60px rgba(0,0,0,.1)', border: '1px solid var(--ln)', padding: '48px 40px', maxWidth: 520, width: '100%', textAlign: 'center' }}>

        {(status === 'loading' || status === 'paid' || status === 'processing') ? (
          <div style={{ marginBottom: 24 }}>
            <LoadingLogo size={80} />
          </div>
        ) : (
          <div style={{ fontSize: 48, marginBottom: 16 }}>{cfg.icon}</div>
        )}
        <h1 style={{ fontSize: 26, fontWeight: 700, letterSpacing: '-.02em', color: 'var(--ink)', marginBottom: 8 }}>{cfg.title}</h1>
        <p style={{ fontSize: 15, color: 'var(--mu)', marginBottom: 24 }}>{cfg.text}</p>

        {(status === 'processing' || status === 'paid') && (
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8, fontSize: 13, color: 'var(--mu)', marginBottom: 24 }}>
            <div style={{ width: 6, height: 6, borderRadius: '50%', background: 'var(--gr)', animation: 'pulse 1.4s ease-in-out infinite' }} />
            Wird aktualisiert…
          </div>
        )}

        {status === 'done' && files.length > 0 && (
          <div style={{ marginBottom: 24 }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 10, marginBottom: 16 }}>
              {files.map((f) => (
                <a
                  key={f}
                  href={`/api/download/${jobId}/${f}`}
                  download
                  style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: 12, background: 'var(--grs)', border: '1px solid var(--ln2)', borderRadius: 14, padding: '14px 16px', textDecoration: 'none', transition: 'background .15s' }}
                >
                  <span style={{ fontFamily: 'ui-monospace, monospace', fontSize: 13, color: 'var(--ink2)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{f}</span>
                  <div style={{ width: 36, height: 36, borderRadius: 10, background: 'var(--gr)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round">
                      <path d="M12 5v14" /><path d="M19 12l-7 7-7-7" />
                    </svg>
                  </div>
                </a>
              ))}
            </div>
            <p style={{ fontSize: 13, color: 'var(--fa)', lineHeight: 1.6 }}>
              Sie erhalten die Download-Links zusätzlich per Mail.<br />
              Die Links sind 24h gültig.
            </p>
          </div>
        )}

        {status === 'error' && (
          <div style={{ marginBottom: 24 }}>
            <a href="/" style={{ display: 'inline-block', background: 'var(--gr)', color: '#fff', padding: '14px 28px', borderRadius: 999, fontWeight: 600, fontSize: 14 }}>
              Nochmal versuchen
            </a>
          </div>
        )}

        {jobId && (
          <p style={{ fontSize: 11, color: 'var(--fa)', fontFamily: 'ui-monospace, monospace', wordBreak: 'break-all', marginBottom: 32 }}>
            Job-ID: {jobId}
          </p>
        )}

        <input ref={fileRef} type="file" accept=".pdf" style={{ display: 'none' }} onChange={handleFileChange} />

        <button
          onClick={() => fileRef.current?.click()}
          style={{ width: '100%', padding: '14px 24px', borderRadius: 999, background: 'var(--gr)', color: '#fff', border: 'none', fontSize: 15, fontWeight: 600, letterSpacing: '-.01em', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 10, marginBottom: 14 }}
        >
          Weiteren Export starten
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.6" strokeLinecap="round" strokeLinejoin="round"><line x1="5" y1="12" x2="19" y2="12" /><polyline points="12 5 19 12 12 19" /></svg>
        </button>

        <a href="/" style={{ fontSize: 13, color: 'var(--mu)', textDecoration: 'none' }}>
          ← zurück zu wertstapel.de
        </a>
      </div>

      {showModal && <ConfigModal file={newFile} onClose={() => { setShowModal(false); setNewFile(null); if (fileRef.current) fileRef.current.value = '' }} />}
    </main>
  )
}

export default function SuccessPage() {
  return (
    <Suspense fallback={<div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>Laden…</div>}>
      <SuccessContent />
    </Suspense>
  )
}
