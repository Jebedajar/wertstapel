'use client'

import { useEffect, useState } from 'react'
import { useParams } from 'next/navigation'

type Status = 'awaiting_payment' | 'paid' | 'processing' | 'done' | 'error' | 'loading'

export default function StatusPage() {
  const { job_id } = useParams<{ job_id: string }>()
  const [status, setStatus] = useState<Status>('loading')
  const [files, setFiles] = useState<string[]>([])

  useEffect(() => {
    if (!job_id) return

    const poll = async () => {
      try {
        const res = await fetch(`/api/status/${job_id}`)
        const data = await res.json()
        setStatus(data.status)
        if (data.files) setFiles(data.files)
        if (data.status !== 'done' && data.status !== 'error') {
          setTimeout(poll, 3000)
        }
      } catch {
        setStatus('error')
      }
    }

    poll()
  }, [job_id])

  return (
    <main className="min-h-screen bg-gradient-to-br from-gray-50 to-brand-50 flex items-center justify-center px-4">
      <div className="bg-white rounded-2xl shadow-xl border border-gray-100 p-10 max-w-lg w-full text-center">
        <a href="/" className="text-brand-600 text-sm hover:underline mb-6 block">← Zurück</a>

        {status === 'loading' && <p>Lade Status…</p>}

        {status === 'done' && files.length > 0 && (
          <>
            <div className="text-5xl mb-4">🎉</div>
            <h1 className="text-2xl font-bold mb-2">Fertig!</h1>
            <p className="text-gray-600 mb-6">Deine Dateien sind bereit.</p>
            <div className="space-y-3">
              {files.map((f) => (
                <a
                  key={f}
                  href={`/api/download/${job_id}/${f}`}
                  download
                  className="flex items-center justify-between bg-brand-50 border border-brand-200 rounded-xl px-5 py-4 hover:bg-brand-100 transition-colors"
                >
                  <span className="font-mono text-sm text-brand-800 truncate">{f}</span>
                  <span className="text-brand-600 ml-3 shrink-0">⬇ Download</span>
                </a>
              ))}
              <p className="text-xs text-gray-400 mt-4">Download-Links sind 24 Stunden gültig.</p>
            </div>
          </>
        )}

        {(status === 'processing' || status === 'paid') && (
          <>
            <div className="text-5xl mb-4">⚙️</div>
            <h1 className="text-2xl font-bold mb-2">Wird verarbeitet…</h1>
            <div className="flex items-center justify-center gap-2 text-sm text-gray-500 mt-4">
              <div className="w-4 h-4 border-2 border-brand-500 border-t-transparent rounded-full animate-spin" />
              Seite aktualisiert automatisch
            </div>
          </>
        )}

        {status === 'awaiting_payment' && (
          <>
            <div className="text-5xl mb-4">💳</div>
            <h1 className="text-2xl font-bold mb-2">Zahlung ausstehend</h1>
            <p className="text-gray-600">Bitte schließe die Zahlung ab.</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="text-5xl mb-4">❌</div>
            <h1 className="text-2xl font-bold mb-2">Fehler</h1>
            <p className="text-gray-600 mb-4">Bei der Verarbeitung ist ein Fehler aufgetreten.</p>
            <a href="/" className="inline-block bg-brand-600 text-white px-6 py-3 rounded-xl font-semibold hover:bg-brand-700">
              Nochmal versuchen
            </a>
          </>
        )}

        <p className="text-xs text-gray-400 mt-6 font-mono break-all">Job-ID: {job_id}</p>
      </div>
    </main>
  )
}
