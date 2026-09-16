'use client'

import { useRef } from 'react'
import { BROKERS } from '@/lib/data'

interface Props {
  onClose: () => void
  onFilesSelected: (files: File[]) => void
}

const ACCEPT = '.pdf,.xlsx,.xls,.csv'
const FILE_RE = /\.(pdf|xlsx|xls|csv)$/i

export default function BrokerModal({ onClose, onFilesSelected }: Props) {
  const inputRef = useRef<HTMLInputElement>(null)

  const openPicker = () => inputRef.current?.click()

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const fs = Array.from(e.target.files || []).filter(f => FILE_RE.test(f.name))
    e.target.value = ''
    if (fs.length) onFilesSelected(fs)
  }

  return (
    <div className="modal-overlay" onClick={onClose}>
      <div className="modal-box" onClick={e => e.stopPropagation()}>
        <div style={{ padding: '26px 32px', borderBottom: '1px solid var(--ln)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', position: 'sticky', top: 0, background: '#fff', borderRadius: '24px 24px 0 0' }}>
          <h3 className="display" style={{ fontSize: 22, color: 'var(--ink)' }}>Welche Datei wird benötigt?</h3>
          <button onClick={onClose} style={{ background: 'none', border: 'none', fontSize: 22, color: 'var(--fa)', lineHeight: 1, padding: 4, cursor: 'pointer', flexShrink: 0 }}>×</button>
        </div>

        <div style={{ padding: '20px 32px 28px' }}>

          <div
            onClick={openPicker}
            onDragOver={e => e.preventDefault()}
            onDrop={e => { e.preventDefault(); const fs = Array.from(e.dataTransfer.files).filter(f => FILE_RE.test(f.name)); if (fs.length) onFilesSelected(fs) }}
            style={{ border: '1.5px dashed var(--ln2)', borderRadius: 16, padding: 20, cursor: 'pointer', background: '#fff', display: 'flex', alignItems: 'center', gap: 14, marginBottom: 22, transition: 'all .15s ease' }}
          >
            <div style={{ width: 40, height: 40, borderRadius: 10, background: 'var(--gr)', display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#fff" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round"><path d="M12 19V5" /><path d="M5 12l7-7 7 7" /></svg>
            </div>
            <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)' }}>Datei hier ablegen oder klicken</div>
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {BROKERS.map(b => (
              <div
                key={b.id}
                onClick={openPicker}
                style={{ border: '1px solid var(--ln)', borderRadius: 14, padding: 16, cursor: 'pointer', transition: 'all .15s ease' }}
                onMouseEnter={e => { e.currentTarget.style.borderColor = 'var(--gr)'; e.currentTarget.style.background = 'var(--grs)' }}
                onMouseLeave={e => { e.currentTarget.style.borderColor = 'var(--ln)'; e.currentTarget.style.background = 'transparent' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 8 }}>
                  <img src={b.logo} alt={b.name} style={{ height: 22, maxWidth: 96, objectFit: 'contain', flexShrink: 0 }} />
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--ink)', flex: 1 }}>{b.name}</div>
                  <span style={{ fontFamily: 'var(--font-mono),ui-monospace,monospace', fontSize: 10, letterSpacing: '.06em', textTransform: 'uppercase', color: 'var(--gr)', background: 'var(--grs)', padding: '4px 8px', borderRadius: 6, flexShrink: 0 }}>{b.format}</span>
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="var(--fa)" strokeWidth="2.4" strokeLinecap="round" strokeLinejoin="round" style={{ flexShrink: 0 }}><path d="M12 19V5" /><path d="M5 12l7-7 7 7" /></svg>
                </div>
                <div style={{ fontSize: 13, lineHeight: 1.6, color: 'var(--mu)' }}>{b.desc}</div>
              </div>
            ))}
          </div>

        </div>

        <input ref={inputRef} type="file" accept={ACCEPT} multiple style={{ display: 'none' }} onChange={handleChange} />
      </div>
    </div>
  )
}
