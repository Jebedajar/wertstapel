'use client'

interface LogoMarkProps {
  height?: number
  color?: string
}

export function LogoMark({ height = 15, color = 'var(--green)' }: LogoMarkProps) {
  const w = Math.round(height * 18 / 22)
  return (
    <svg
      width={w}
      height={height}
      viewBox="0 0 18 22"
      fill="none"
      aria-hidden="true"
      style={{ display: 'block' }}
    >
      <rect width="18" height="15" rx="3" fill={color} />
      <rect y="18" width="18" height="4" rx="2" fill={color} opacity="0.32" />
    </svg>
  )
}

interface WordmarkProps {
  size?:      number
  color?:     string
  markColor?: string
}

export function Wordmark({
  size      = 15,
  color     = 'var(--ink)',
  markColor = 'var(--green)',
}: WordmarkProps) {
  return (
    <span style={{
      display:     'inline-flex',
      alignItems:  'center',
      gap:         7,
      color,
      lineHeight:  1,
    }}>
      <LogoMark height={Math.round(size * 1.45)} color={markColor} />
      <span style={{
        fontWeight:    700,
        fontSize:      size,
        letterSpacing: '.04em',
        textTransform: 'uppercase',
        lineHeight:    1,
      }}>
        WERTSTAPEL
      </span>
    </span>
  )
}
