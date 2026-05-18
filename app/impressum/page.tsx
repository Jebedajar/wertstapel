import LegalLayout from '@/components/LegalLayout'

export const metadata = {
  title: 'Impressum – Wertstapel',
}

export default function Page() {
  return (
    <LegalLayout>
      <style>{`
:root {
      --color-bg:        #fafaf8;
      --color-surface:   #ffffff;
      --color-border:    #e4e2db;
      --color-text:      #1a1a18;
      --color-muted:     #6b6960;
      --color-accent:    #1d4ed8;
      --color-warn-bg:   #fffbeb;
      --color-warn-border:#d97706;
      --color-warn:      #92400e;
      --font-serif:      'Georgia', 'Times New Roman', serif;
      --font-sans:       'Helvetica Neue', Helvetica, Arial, sans-serif;
      --radius:          6px;
      --max-width:       680px;
    }

    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    body {
      background: var(--color-bg);
      color: var(--color-text);
      font-family: var(--font-sans);
      font-size: 15px;
      line-height: 1.75;
      padding: 48px 24px 96px;
    }

    .imp-wrapper {
      max-width: var(--max-width);
      margin: 0 auto;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: 10px;
      padding: 52px 60px;
    }

    @media (max-width: 620px) {
      .imp-wrapper { padding: 32px 20px; }
    }

    /* ── Header ── */
    .imp-header {
      border-bottom: 2px solid var(--color-text);
      padding-bottom: 24px;
      margin-bottom: 36px;
    }

    .imp-label {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 8px;
    }

    h1 {
      font-family: var(--font-serif);
      font-size: 26px;
      font-weight: normal;
    }

    /* ── Blocks ── */
    .imp-block {
      margin-bottom: 32px;
    }

    h2 {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 10px;
    }

    address {
      font-style: normal;
      font-size: 15px;
      line-height: 1.8;
    }

    p {
      font-size: 15px;
      line-height: 1.8;
      margin-bottom: 6px;
    }

    a {
      color: var(--color-accent);
      text-decoration: none;
    }
    a:hover { text-decoration: underline; }

    /* ── TODO marker ── */
    .todo {
      display: inline-block;
      background: var(--color-warn-bg);
      border: 1px solid var(--color-warn-border);
      color: var(--color-warn);
      font-size: 12px;
      font-weight: 700;
      padding: 1px 8px;
      border-radius: 4px;
      margin-left: 6px;
      vertical-align: middle;
    }

    /* ── Divider ── */
    hr {
      border: none;
      border-top: 1px solid var(--color-border);
      margin: 28px 0;
    }

    /* ── Footer ── */
    .imp-footer {
      margin-top: 40px;
      padding-top: 18px;
      border-top: 1px solid var(--color-border);
      font-size: 12px;
      color: var(--color-muted);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
    }
      `}</style>
      <div dangerouslySetInnerHTML={{ __html: `<div class="imp-wrapper">

  <!-- Header -->
  <div class="imp-header">
    <p class="imp-label">Pflichtangaben nach § 5 TMG</p>
    <h1>Impressum</h1>
  </div>


  <!-- Anbieter -->
  <div class="imp-block">
    <h2>Anbieter</h2>
    <address>
      Spark Innovation GmbH<br>
      Lenneper Str. 32<br>
      40591 Düsseldorf<br>
      Deutschland
    </address>
  </div>

  <hr>

  <!-- Registereintrag -->
  <div class="imp-block">
    <h2>Handelsregister</h2>
    <p>Handelsregister: HRB 83993</p>
    <p>Registergericht: Amtsgericht Düsseldorf</p>
  </div>

  <hr>

  <!-- Geschäftsführung -->
  <div class="imp-block">
    <h2>Vertreten durch</h2>
    <p>Martin Ferfers (Geschäftsführer)</p>
  </div>

  <hr>

  <!-- Kontakt -->
  <div class="imp-block">
    <h2>Kontakt</h2>
    <!--
      WICHTIG: Telefonnummer ist Pflichtangabe nach § 5 Abs. 1 Nr. 2 TMG.
      Vor Launch eintragen!
    -->
    <p>
      Telefon:
      <span class="todo">⚠ BITTE EINTRAGEN</span>
      <!-- Beispiel: +49 211 12345678 -->
    </p>
    <p>
      E-Mail:
      <a href="mailto:info@wertstapel.de">info@wertstapel.de</a>
    </p>
  </div>

  <hr>

  <!-- USt-ID -->
  <div class="imp-block">
    <h2>Umsatzsteuer-Identifikationsnummer</h2>
    <p>
      Umsatzsteuer-Identifikationsnummer gemäß § 27 a Umsatzsteuergesetz:<br>
      <strong>DE318933806</strong>
    </p>
  </div>

  <hr>

  <!-- ODR -->
  <div class="imp-block">
    <h2>Online-Streitbeilegung (OS-Plattform)</h2>
    <p>
      Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS) bereit:
      <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer">
        ec.europa.eu/consumers/odr
      </a>
    </p>
    <p>
      Unsere E-Mail-Adresse finden Sie oben im Abschnitt „Kontakt".
    </p>
  </div>

  <hr>

  <!-- Verbraucherschlichtung -->
  <div class="imp-block">
    <h2>Verbraucherschlichtung</h2>
    <p>
      Wir sind weder bereit noch verpflichtet, an Streitbeilegungsverfahren vor einer
      Verbraucherschlichtungsstelle teilzunehmen, da wir ausschließlich Verträge mit
      Unternehmern im Sinne des § 14 BGB schließen (kein B2C-Geschäft).
    </p>
  </div>


  <!-- Footer -->
  <div class="imp-footer">
    <span>Stand: Mai 2026</span>
    <span>Spark Innovation GmbH · Düsseldorf</span>
  </div>

</div><!-- /.imp-wrapper -->` }} />
    </LegalLayout>
  )
}
