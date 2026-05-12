import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'Wertstapel — Wertpapierabrechnungen. DATEV-Stapel.',
  description: 'Orderabrechnungen automatisch in einen importfähigen DATEV-Buchungsstapel überführen — §8b-konform, tranchengetrennt, mit Plausibilitätsprüfung. Keine Seitenbegrenzung.',
  openGraph: {
    title: 'Wertstapel — Wertpapierabrechnungen. DATEV-Stapel.',
    description: 'Orderabrechnungen automatisch in DATEV-Buchungsstapel überführen.',
    siteName: 'Wertstapel',
    locale: 'de_DE',
    type: 'website',
  },
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="de">
      <body>{children}</body>
    </html>
  )
}
