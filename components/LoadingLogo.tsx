export default function LoadingLogo({ size = 72 }: { size?: number }) {
  const w = Math.round(size * 18 / 22)
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: size, height: size }}>
      <svg
        width={w}
        height={size}
        viewBox="0 0 18 22"
        fill="none"
        style={{ animation: 'logoGrow 1.6s cubic-bezier(.4,0,.2,1) infinite', transformOrigin: 'center' }}
      >
        <rect width="18" height="15" rx="3" fill="#2563EB" />
        <rect y="18" width="18" height="4" rx="2" fill="#2563EB" opacity="0.32" />
      </svg>
      <style>{`
        @keyframes logoGrow {
          0%   { transform: scale(0.08); opacity: 0.3; }
          55%  { transform: scale(1);    opacity: 1;   }
          75%  { transform: scale(1);    opacity: 1;   }
          100% { transform: scale(0.08); opacity: 0.3; }
        }
      `}</style>
    </div>
  )
}
