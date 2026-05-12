import type { Metadata } from 'next'
import { Manrope } from 'next/font/google'
import { JetBrains_Mono } from 'next/font/google'
import './globals.css'

const manrope = Manrope({
  subsets: ['latin'],
  weight: ['400', '500', '600', '700', '800'],
  variable: '--font-sans',
  display: 'swap',
})

const jetbrainsMono = JetBrains_Mono({
  subsets: ['latin'],
  weight: ['400', '500'],
  variable: '--font-mono',
  display: 'swap',
})

export const metadata: Metadata = {
  title: 'Wertstapel — Wertpapier-PDF rein. DATEV-Stapel raus.',
  description: 'Orderabrechnungen automatisch in einen importfähigen DATEV-Buchungsstapel überführen — §8b-konform, tranchengetrennt, mit Plausibilitätsprüfung. Keine Seitenbegrenzung.',
  openGraph: {
    title: 'Wertstapel — Wertpapier-PDF rein. DATEV-Stapel raus.',
    description: 'Orderabrechnungen automatisch in DATEV-Buchungsstapel überführen.',
    siteName: 'Wertstapel',
    locale: 'de_DE',
    type: 'website',
  },
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="de" className={`${manrope.variable} ${jetbrainsMono.variable}`}>
      <body style={{ fontFamily: 'var(--font-sans), Manrope, system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  )
}
