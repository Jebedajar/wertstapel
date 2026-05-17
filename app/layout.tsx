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
      <head>
        <link rel="icon" type="image/svg+xml" href="/favicons/favicon.svg" />
        <link rel="icon" type="image/png" sizes="32x32" href="/favicons/favicon-32.png" />
        <link rel="icon" type="image/png" sizes="16x16" href="/favicons/favicon-16.png" />
        <link rel="shortcut icon" href="/favicons/favicon-32.png" />
        <link rel="apple-touch-icon" sizes="180x180" href="/favicons/apple-touch-icon.png" />
        <link rel="manifest" href="/favicons/site.webmanifest" />
        <meta name="theme-color" content="#2563EB" />
        {/* Privacy-friendly analytics by Plausible */}
        <script async src="https://plausible.io/js/pa-Dw7oMD_Cb8xzg_1qOcC71.js" />
        <script dangerouslySetInnerHTML={{ __html: `window.plausible=window.plausible||function(){(plausible.q=plausible.q||[]).push(arguments)},plausible.init=plausible.init||function(i){plausible.o=i||{}};plausible.init()` }} />
      </head>
      <body style={{ fontFamily: 'var(--font-sans), Manrope, system-ui, sans-serif' }}>
        {children}
      </body>
    </html>
  )
}
