export const PLANS = [
  { id: 'single', label: 'Einzelexport',  price: '200',   sub: 'pro Export',          perExport: '200 € pro Export',      note: 'Für den ersten Test',                popular: false },
  { id: 'five',   label: '5er-Paket',     price: '750',   sub: '= 150 € pro Export',  perExport: '150 € pro Export',      note: 'Beliebtester Einstieg',              popular: true  },
  { id: 'twenty', label: '20er-Paket',    price: '2.400', sub: '= 120 € pro Export',  perExport: '120 € pro Export',      note: 'Kanzleien mit aktivem Depot­volumen',popular: false },
  { id: 'flat',   label: 'Jahresflat',    price: '3.600', sub: '1 Jahr unbegrenzte Exports',  perExport: '1 Jahr unbegrenzte Exports', note: 'Ab ca. 20 Exports/Jahr rentabel',   popular: false },
]

export const FAQS = [
  { q: 'Stimmen die Buchungen wirklich?',
    a: 'Die Buchungen basieren auf der offiziellen DATEV-Dokumentation (5300857). Jeder Buchungssatz wird gegen den Ausmachenden Betrag überprüft. Alle Abweichungen über 0,05 € lassen sich im Plausibilitätsbericht nachvollziehen. Gebucht wird nach Buchwertabgang-Methode, §8b-konform und tranchengetrennt.' },
  { q: 'Was passiert mit den Daten?',
    a: 'Die Verarbeitung erfolgt ausschließlich auf EU-Servern in Deutschland. Das PDF und die Ergebnisdateien werden nach Auslieferung automatisch gelöscht. Kein KI-Sprachmodell und kein Drittanbieter arbeitet mit den Daten.' },
  { q: 'Mit welchen Banken funktioniert das?',
    a: 'Derzeit funktioniert Wertstapel mit Dokumenten aller Sparkassen, Comdirect und Flatex. Weitere Banken befinden sich in Entwicklung bzw. können auf Wunsch eingebunden werden. Reichen Sie ein anonymisiertes Muster-PDF ein – wir prüfen die Kompatibilität kostenfrei: muster@wertstapel.de' },
  { q: 'Welche Dokumente muss ich hochladen?',
    a: 'Hier findest Du die relevanten Dokumente bei Deiner Bank / Deinem Broker:\n– Sparkassen: Nachrichten > Postfach > Filter „Wertpapierdokumente”, Datum und Depotinhaber setzen > alle PDFs herunterladen. Alternativ kann Ihr Bankberater eine aggregierte PDF mit allen Transaktionen zur Verfügung stellen.\n– Comdirect: Depot > Abrechnungsdatum > Zeitraum auswählen > unten „CSV exportieren”\n– Flatex: Post > Dokumentenarchiv bzw. Postfach > Filter „Kauf-/Verkaufabrechnung”, „Dividenden/Ertragsgutschrift” wählen.' },
  { q: 'Was wenn ein Beleg nicht erkannt wird?',
    a: 'Nicht erkannte Seiten erscheinen mit Typ-Bezeichnung und Grund im Verarbeitungsprotokoll. Es gibt somit keine „stillen Fehler”. Was nicht automatisch buchbar ist, bleibt manuell buchbar — so wie bisher.' },
  { q: 'Welche Einstellungen kann ich vornehmen?',
    a: 'Wenn Sie eine Datei hochladen, öffnet sich ein Dialogfeld, in dem Sie einige Einstellungen vornehmen können. Sie können die Standard-Einstellungen problemlos belassen. Als Steuerberater sparen Sie durch die Einstellungen mit minimalem Aufwand Zeit beim Import. Mögliche Einstellungen: SKR04 (Kapitalgesellschaften wie GmbH – Standard) oder SKR03 (Personengesellschaften), Bankkonto (Standard: 1801), Mandantennummer.' },
  { q: 'Darf ich das als Steuerberater einsetzen?',
    a: 'Ja, Sie dürfen. Der Buchungsstapel ist ein Buchungsvorschlag zur fachkundigen Prüfung durch den Steuerberater — keine Steuerberatungsleistung. Wertstapel verarbeitet Daten maschinell; die fachliche Verantwortung für den Jahresabschluss verbleibt beim Steuerberater.' },
  { q: 'Gibt es ein Limit je Export?',
    a: 'Nein. Egal ob 50 oder 5.000 Transaktionen – der Export kostet dasselbe. Die Verarbeitungszeit liegt in der Regel auch für große Dateien deutlich unter 5 Minuten.' },
]

export function buildFilenames(mandant: string) {
  const d   = new Date().toISOString().slice(0, 10).replace(/-/g, '')
  const pre = mandant.trim() ? `${mandant.trim()}_` : ''
  return {
    stapel:    `${pre}Buchungsstapel_${d}.csv`,
    plausi:    `${pre}Plausi_${d}.csv`,
    protokoll: `${pre}Protokoll_${d}.txt`,
  }
}
