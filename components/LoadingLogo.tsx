export default function LoadingLogo({ size = 72 }: { size?: number }) {
  return (
    <div style={{ display: 'inline-flex', alignItems: 'center', justifyContent: 'center', width: size, height: size }}>
      <img
        src="/wertstapel-mark-4stufen-white.gif"
        alt=""
        width={30}
        height={30}
        style={{ display: 'block' }}
      />
    </div>
  )
}
