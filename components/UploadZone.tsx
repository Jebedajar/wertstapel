'use client'

import { useState, useRef } from 'react'

interface UploadZoneProps {
  onFile: (file: File) => void
  large?: boolean
}

export function UploadZone({ onFile, large = false }: UploadZoneProps) {
  const [drag, setDrag] = useState(false)
  const ref = useRef<HTMLInputElement>(null)

  const iconSize = large ? 28 : 22
  const boxSize  = large ? 72 : 56
  const boxRadius= large ? 18 : 14

  return (
    <div
      role="button"
      tabIndex={0}
      aria-label="PDF hochladen"
      onClick={() => ref.current?.click()}
      onKeyDown={(e) => e.key === 'Enter' && ref.current?.click()}
      onDragOver={(e) => { e.preventDefault(); setDrag(true) }}
      onDragLeave={() => setDrag(false)}
      onDrop={(e) => {
        e.preventDefault()
        setDrag(false)
        const f = e.dataTransfer.files[0]
        if (f) onFile(f)
      }}
      style={{
        border:     `1.5px dashed ${drag ? 'var(--green)' : 'var(--line-2)'}`,
        borderRadius: 22,
        padding:    large ? '56px 40px' : '40px 28px',
        cursor:     'pointer',
        background: drag ? 'var(--green-soft)' : '#fff',
        transition: 'all .18s ease',
        boxShadow:  drag
          ? '0 0 0 6px rgba(37,99,235,.08)'
          : '0 1px 0 rgba(15,22,18,.04)',
        outline: 'none',
      }}
    >
      <input
        ref={ref}
        type="file"
        accept=".pdf"
        style={{ display: 'none' }}
        onChange={(e) => {
          const f = e.target.files?.[0]
          if (f) onFile(f)
        }}
      />
      <div style={{
        display:    'flex',
        alignItems: 'center',
        gap:        18,
        flexWrap:   'wrap',
      }}>
        {/* Upload icon box */}
        <div style={{
          width:          boxSize,
          height:         boxSize,
          borderRadius:   boxRadius,
          background:     'var(--green)',
          display:        'flex',
          alignItems:     'center',
          justifyContent: 'center',
          flexShrink:     0,
        }}>
          <svg
            width={iconSize}
            height={iconSize}
            viewBox="0 0 24 24"
            fill="none"
            stroke="#fff"
            strokeWidth="2.2"
            strokeLinecap="round"
            strokeLinejoin="round"
          >
            <path d="M12 19V5" />
            <path d="M5 12l7-7 7 7" />
          </svg>
        </div>

        {/* Text */}
        <div style={{ flex: 1, minWidth: 200, textAlign: 'left' }}>
          <div style={{
            fontSize:      large ? 22 : 18,
            fontWeight:    600,
            color:         'var(--ink)',
            marginBottom:  6,
            letterSpacing: '-.01em',
          }}>
            PDF hier ablegen oder klicken
          </div>
          <div className="mono" style={{ fontSize: large ? 13 : 12, color: 'var(--mute)' }}>
            Orderabrechnungen · beliebig viele Seiten · bis 100 MB
          </div>
        </div>

        {/* .PDF badge */}
        <div className="mono" style={{
          fontSize:      11,
          padding:       '8px 12px',
          background:    'var(--bg-alt)',
          borderRadius:  8,
          color:         'var(--ink-2)',
          letterSpacing: '.05em',
        }}>
          .PDF
        </div>
      </div>
    </div>
  )
}
