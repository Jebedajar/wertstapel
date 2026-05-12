export interface Plan {
  id:       string
  label:    string
  price:    string
  sub:      string
  perExport: string
  note:     string
  popular:  boolean
}

export const PLANS: Plan[] = [
  {
    id:        'single',
    label:     'Einzelexport',
    price:     '200',
    sub:       'pro Export',
    perExport: '200 € pro Export',
    note:      'Für den ersten Test',
    popular:   false,
  },
  {
    id:        'five',
    label:     '5er-Paket',
    price:     '750',
    sub:       '5 Exports',
    perExport: '150 € pro Export',
    note:      'Beliebtester Einstieg',
    popular:   true,
  },
  {
    id:        'twenty',
    label:     '20er-Paket',
    price:     '2.400',
    sub:       '20 Exports',
    perExport: '120 € pro Export',
    note:      'Kanzleien mit aktivem Depotvolumen',
    popular:   false,
  },
  {
    id:        'flat',
    label:     'Jahresflat',
    price:     '3.600',
    sub:       'Unbegrenzte Exports',
    perExport: 'Alle Exports inklusive',
    note:      'Ab ca. 20 Exports/Jahr rentabel',
    popular:   false,
  },
]

export const FAQS = [
  {
    q: 'Stimmen die Buchungen wirklich?',
    a: 'Jeder Buchungssatz wird gegen den Ausmachenden Betrag geprüft (Kurswert ± Gebühren = Ausmachender Betrag). Abweichungen über 0,05 € erscheinen im Plausibilitätsbericht. Die Buchungslogik wurde von einer Steuerberaterin gegen DATEV-Dokumentation 5300857 validiert — Buchwertabgang-Methode, §8b-konform, tranchengetrennt.',
  },
  {
    q: 'Was passiert mit den Daten?',
    a: 'Verarbeitung ausschließlich auf EU-Servern in Deutschland. PDF und Ergebnisdateien werden nach Auslieferung automatisch gelöscht. Kein Sprachmodell, kein Drittanbieter, kein Training. AVV auf Anfrage.',
  },
  {
    q: 'Mit welchen Banken funktioniert das?',
    a: 'Derzeit: Stadtsparkasse und alle Sparkassen-Gruppeninstitute (identisches PDF-Format). Weitere Banken befinden sich in Entwicklung. Reichen Sie ein anonymisiertes Muster-PDF ein — wir prüfen die Kompatibilität kostenfrei.',
  },
  {
    q: 'Was wenn ein Beleg nicht erkannt wird?',
    a: 'Nicht erkannte Seiten erscheinen mit Typ-Bezeichnung und Grund im Verarbeitungsprotokoll. Kein stiller Fehler. Was nicht automatisch buchbar ist, bleibt manuell buchbar — so wie bisher.',
  },
  {
    q: 'Welche Einstellungen kann ich vornehmen?',
    a: 'SKR03 oder SKR04, Bankkonto (Standard: 1801), optional Mandantennummer und Wirtschaftsjahresbeginn. Profil speicherbar für Folgenutzungen.',
  },
  {
    q: 'Darf ich das als Steuerberater einsetzen?',
    a: 'Wertstapel erbringt Datenverarbeitungsleistungen nach § 4 Nr. 11 StBerG. Der Buchungsstapel ist ein Buchungsvorschlag zur fachkundigen Prüfung — keine Steuerberatungsleistung. Die Verantwortung für den Jahresabschluss verbleibt beim Steuerberater.',
  },
  {
    q: 'Gibt es ein Seitenlimit?',
    a: 'Nein. 20 Seiten und 500 Seiten kosten denselben Exportpreis. Verarbeitungszeit: unter 5 Minuten auch für große PDFs. Andere Tools begrenzen nach Seitenzahl — wir nicht.',
  },
]

/** Build export filenames with optional mandant prefix */
export function buildFilenames(mandant: string, date: Date = new Date()) {
  const d   = date.toISOString().slice(0, 10).replace(/-/g, '')
  const pre = mandant.trim() ? `${mandant.trim()}_` : ''
  return {
    stapel:   `${pre}Buchungsstapel_${d}.csv`,
    plausi:   `${pre}Plausi_${d}.csv`,
    protokoll:`${pre}Protokoll_${d}.txt`,
  }
}
