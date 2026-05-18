export const metadata = {
  title: 'AVV – Wertstapel',
}

export default function Page() {
  return (
    <>
      <style>{`
:root {
      --color-bg:        #fafaf8;
      --color-surface:   #ffffff;
      --color-border:    #e4e2db;
      --color-text:      #1a1a18;
      --color-muted:     #6b6960;
      --color-accent:    #1d4ed8;
      --color-accent-bg: #eff6ff;
      --color-warn:      #92400e;
      --color-warn-bg:   #fffbeb;
      --color-warn-border: #d97706;
      --font-serif:      'Georgia', 'Times New Roman', serif;
      --font-sans:       'Helvetica Neue', Helvetica, Arial, sans-serif;
      --font-mono:       'Courier New', Courier, monospace;
      --radius:          6px;
      --max-width:       820px;
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

    .avv-wrapper {
      max-width: var(--max-width);
      margin: 0 auto;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: 10px;
      padding: 56px 64px;
    }

    @media (max-width: 680px) {
      .avv-wrapper { padding: 32px 20px; }
    }

    /* ── Header ── */
    .avv-header {
      border-bottom: 2px solid var(--color-text);
      padding-bottom: 28px;
      margin-bottom: 36px;
    }

    .avv-label {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 10px;
    }

    h1 {
      font-family: var(--font-serif);
      font-size: 24px;
      font-weight: normal;
      line-height: 1.3;
    }

    .avv-subline {
      font-size: 13px;
      color: var(--color-muted);
      margin-top: 8px;
    }

    /* ── Parties block ── */
    .parties-block {
      display: grid;
      grid-template-columns: 1fr 1fr;
      gap: 24px;
      margin: 28px 0 36px;
      padding: 20px 24px;
      background: var(--color-bg);
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
    }

    @media (max-width: 580px) {
      .parties-block { grid-template-columns: 1fr; }
    }

    .party-col .party-role {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.1em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 6px;
    }

    .party-col address {
      font-style: normal;
      font-size: 13.5px;
      line-height: 1.6;
    }

    .party-sep {
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 12px;
      color: var(--color-muted);
      font-weight: 600;
    }

    /* ── Sections ── */
    .avv-section {
      margin-bottom: 40px;
    }

    h2 {
      font-family: var(--font-sans);
      font-size: 13px;
      font-weight: 700;
      letter-spacing: 0.07em;
      text-transform: uppercase;
      color: var(--color-text);
      margin-bottom: 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--color-border);
    }

    /* ── Clauses ── */
    .clause {
      display: grid;
      grid-template-columns: 44px 1fr;
      gap: 0 10px;
      margin-bottom: 14px;
    }

    .clause-num {
      font-size: 12px;
      font-weight: 600;
      color: var(--color-muted);
      padding-top: 2px;
      white-space: nowrap;
    }

    .clause-text {
      font-size: 14px;
      line-height: 1.75;
    }

    /* ── Notice / warning boxes ── */
    .notice {
      background: var(--color-accent-bg);
      border-left: 3px solid var(--color-accent);
      padding: 14px 18px;
      border-radius: 0 var(--radius) var(--radius) 0;
      margin-bottom: 14px;
      font-size: 14px;
      line-height: 1.7;
      color: #1e3a8a;
    }

    .warn {
      background: var(--color-warn-bg);
      border-left: 3px solid var(--color-warn-border);
      padding: 14px 18px;
      border-radius: 0 var(--radius) var(--radius) 0;
      margin-bottom: 14px;
      font-size: 14px;
      line-height: 1.7;
      color: var(--color-warn);
    }

    /* ── Tables ── */
    table {
      width: 100%;
      border-collapse: collapse;
      font-size: 13.5px;
      margin-top: 12px;
      margin-bottom: 16px;
    }

    th {
      background: var(--color-bg);
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--color-muted);
      padding: 10px 14px;
      text-align: left;
      border: 1px solid var(--color-border);
    }

    td {
      padding: 10px 14px;
      border: 1px solid var(--color-border);
      vertical-align: top;
      line-height: 1.6;
    }

    td ul {
      padding-left: 16px;
      margin: 0;
    }

    td ul li {
      margin-bottom: 4px;
    }

    /* ── Annexes ── */
    .annex {
      margin-top: 48px;
      padding-top: 32px;
      border-top: 2px dashed var(--color-border);
    }

    .annex-label {
      font-size: 11px;
      font-weight: 700;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--color-accent);
      margin-bottom: 8px;
    }

    .annex h2 {
      font-size: 16px;
      letter-spacing: 0;
      text-transform: none;
      font-family: var(--font-serif);
      font-weight: normal;
      border-bottom: 1px solid var(--color-border);
      padding-bottom: 12px;
      margin-bottom: 20px;
    }

    /* TOM list */
    .tom-cat {
      margin-bottom: 22px;
    }

    .tom-cat h3 {
      font-size: 12px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 8px;
    }

    .tom-cat ul {
      padding-left: 18px;
    }

    .tom-cat li {
      font-size: 13.5px;
      line-height: 1.65;
      margin-bottom: 5px;
    }

    /* ── Acceptance block ── */
    .acceptance-block {
      margin-top: 44px;
      padding: 24px 28px;
      background: var(--color-bg);
      border: 1px solid var(--color-border);
      border-radius: var(--radius);
    }

    .acceptance-block h3 {
      font-size: 13px;
      font-weight: 700;
      margin-bottom: 10px;
    }

    .acceptance-block p {
      font-size: 13.5px;
      line-height: 1.7;
      color: var(--color-muted);
    }

    /* ── Footer ── */
    .avv-footer {
      margin-top: 48px;
      padding-top: 20px;
      border-top: 1px solid var(--color-border);
      font-size: 12px;
      color: var(--color-muted);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
    }
      `}</style>
      <div dangerouslySetInnerHTML={{ __html: `<div class="avv-wrapper">

  <!-- Header -->
  <div class="avv-header">
    <p class="avv-label">Datenschutzvertrag · Art. 28 Abs. 3 DSGVO</p>
    <h1>Auftragsverarbeitungsvertrag (AVV)</h1>
    <p class="avv-subline">
      im Sinne von Art. 28 Abs. 3 DSGVO zwischen dem Kunden als Verantwortlichem
      und der Spark Innovation GmbH als Auftragsverarbeiter
    </p>
  </div>


  <!-- Parties -->
  <div class="parties-block">
    <div class="party-col">
      <p class="party-role">Auftraggeber (Verantwortlicher)</p>
      <address>
        [Firma des Kunden]<br>
        [Straße, Nr.]<br>
        [PLZ, Ort]<br>
        (nachfolgend <strong>„Auftraggeber"</strong>)
      </address>
    </div>
    <div class="party-sep">und</div>
    <div class="party-col">
      <p class="party-role">Auftragnehmer (Auftragsverarbeiter)</p>
      <address>
        <strong>Spark Innovation GmbH</strong><br>
        Lenneper Str. 32<br>
        40591 Düsseldorf<br>
        E-Mail: <a href="mailto:info@wertstapel.de">info@wertstapel.de</a><br>
        (nachfolgend <strong>„Auftragnehmer"</strong>)
      </address>
    </div>
  </div>


  <!-- §1 Gegenstand und Laufzeit -->
  <div class="avv-section">
    <h2>§ 1 &nbsp;Gegenstand und Laufzeit</h2>

    <div class="clause">
      <span class="clause-num">1.1</span>
      <span class="clause-text">
        Gegenstand dieses Vertrags ist die Verarbeitung personenbezogener Daten im Auftrag des
        Auftraggebers durch den Auftragnehmer gemäß Art. 28 DSGVO im Rahmen der Nutzung der
        Online-Plattform <em>wertstapel.de</em>. Die genaue Beschreibung von Art, Umfang und Zweck
        der Verarbeitung sowie die Kategorien betroffener Personen und Datenarten sind
        <strong>Anlage 1</strong> zu entnehmen.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">1.2</span>
      <span class="clause-text">
        Verantwortlicher im Sinne des Art. 4 Nr. 7 DSGVO ist der Auftraggeber.
        Der Auftragnehmer verarbeitet die ihm überlassenen personenbezogenen Daten ausschließlich
        auf Grundlage dokumentierter Weisungen des Auftraggebers und der Bestimmungen dieses
        Vertrags.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">1.3</span>
      <span class="clause-text">
        Dieser AVV ist untrennbarer Bestandteil des Hauptvertrags (AGB). Er tritt mit Vertragsschluss
        in Kraft und endet automatisch mit Beendigung des Hauptvertrags, ohne dass es einer
        gesonderten Kündigung bedarf.
      </span>
    </div>
  </div>


  <!-- §2 Verarbeitungsort -->
  <div class="avv-section">
    <h2>§ 2 &nbsp;Verarbeitungsort</h2>

    <div class="clause">
      <span class="clause-num">2.1</span>
      <span class="clause-text">
        Die Verarbeitung personenbezogener Daten durch den Auftragnehmer findet ausschließlich
        auf dem Gebiet der Europäischen Union oder eines Vertragsstaats des EWR-Abkommens statt.
        Der primäre Verarbeitungsort ist Deutschland (Hetzner Online GmbH,
        Rechenzentrum Nürnberg / Falkenstein).
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">2.2</span>
      <span class="clause-text">
        Eine Verarbeitung außerhalb der EU/des EWR ist nur zulässig, wenn die Voraussetzungen
        der Art. 44 ff. DSGVO erfüllt sind und der Auftraggeber vorher schriftlich zugestimmt hat.
        Der Zahlungsdienstleister Stripe Payments Europe, Ltd. (Irland) unterliegt als
        EU-Unternehmen der DSGVO; er verarbeitet ausschließlich Zahlungsdaten und hat keinen
        Zugriff auf die Depot- oder Buchungsdaten. Für etwaige US-Datentransfers durch die
        Stripe-Konzernmutter (Stripe, Inc., USA) ist Stripe Privacy Shield / Standard Contractual
        Clauses maßgeblich; hierzu hat Stripe einen eigenen DPA abgeschlossen, der unter
        stripe.com/de/legal/dpa abrufbar ist.
      </span>
    </div>
  </div>


  <!-- §3 Weisungen -->
  <div class="avv-section">
    <h2>§ 3 &nbsp;Weisungen des Auftraggebers</h2>

    <div class="clause">
      <span class="clause-num">3.1</span>
      <span class="clause-text">
        Der Auftraggeber ist gegenüber dem Auftragnehmer weisungsbefugt bezüglich Art, Umfang
        und Modalitäten der Datenverarbeitung. Weisungen sind schriftlich oder per E-Mail zu
        erteilen. Mündliche Weisungen sind unverzüglich schriftlich zu bestätigen.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">3.2</span>
      <span class="clause-text">
        Der Auftragnehmer informiert den Auftraggeber unverzüglich, wenn eine Weisung nach seiner
        Einschätzung gegen gesetzliche Vorschriften verstößt. Er ist berechtigt, die Ausführung
        bis zur schriftlichen Bestätigung oder Änderung der Weisung auszusetzen.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">3.3</span>
      <span class="clause-text">
        Eine Verarbeitung, die von den Weisungen des Auftraggebers abweicht, ist nur zulässig,
        wenn der Auftragnehmer nach dem Recht der EU oder eines Mitgliedstaats dazu verpflichtet
        ist; in diesem Fall unterrichtet er den Auftraggeber vorab, sofern das betreffende Recht
        dies nicht verbietet.
      </span>
    </div>
  </div>


  <!-- §4 Pflichten des Auftragnehmers -->
  <div class="avv-section">
    <h2>§ 4 &nbsp;Allgemeine Pflichten des Auftragnehmers</h2>

    <div class="clause">
      <span class="clause-num">4.1</span>
      <span class="clause-text">
        Der Auftragnehmer verarbeitet personenbezogene Daten ausschließlich für die in Anlage 1
        genannten Zwecke und nicht für eigene Zwecke. Kopien oder Duplikate der Daten werden
        ohne Wissen des Auftraggebers nicht erstellt, soweit dies nicht technisch für die
        Leistungserbringung (z.&thinsp;B. Backups) erforderlich ist.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">4.2</span>
      <span class="clause-text">
        Der Auftragnehmer gewährleistet, dass alle zur Verarbeitung befugten Personen zur
        Vertraulichkeit verpflichtet sind oder einer gesetzlichen Verschwiegenheitspflicht
        unterliegen (Art. 28 Abs. 3 lit. b DSGVO). Mitarbeiter erhalten nur Zugang zu
        personenbezogenen Daten, soweit dies für ihre jeweilige Aufgabe unbedingt erforderlich
        ist (Least-Privilege-Prinzip).
      </span>
    </div>

    <div class="clause notice">
      <span class="clause-num">4.3</span>
      <span class="clause-text">
        <strong>Steuergeheimnis und berufliche Schweigepflicht:</strong><br>
        Soweit der Auftraggeber als Steuerberater, Wirtschaftsprüfer oder in einem anderen
        Berufsfeld mit gesetzlicher Schweigepflicht tätig ist, sind die im Rahmen der
        Plattformnutzung verarbeiteten Mandantendaten dem Steuergeheimnis gemäß § 30 AO
        und der Verschwiegenheitspflicht gemäß § 57 Abs. 1 StBerG unterworfen. Der
        Auftragnehmer verpflichtet sich, diese besonderen Anforderungen zu beachten und alle
        eingesetzten Mitarbeiter und Subunternehmer entsprechend zu binden.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">4.4</span>
      <span class="clause-text">
        Der Auftragnehmer setzt die in <strong>Anlage 2</strong> beschriebenen technischen und
        organisatorischen Maßnahmen (TOM) um und überprüft diese regelmäßig (mindestens
        jährlich) sowie anlassbezogen. Wesentliche Änderungen an den TOM werden dem
        Auftraggeber vorab mitgeteilt.
      </span>
    </div>
  </div>


  <!-- §5 Kontrollrechte -->
  <div class="avv-section">
    <h2>§ 5 &nbsp;Kontrollrechte des Auftraggebers</h2>

    <div class="clause">
      <span class="clause-num">5.1</span>
      <span class="clause-text">
        Der Auftraggeber ist berechtigt, die Einhaltung der Bestimmungen dieses Vertrags und
        der gesetzlichen Datenschutzvorgaben jederzeit in angemessenem Umfang zu kontrollieren,
        insbesondere durch Einholen von Auskünften, Einsicht in Dokumentation oder –
        nach Terminvereinbarung und unter Verhältnismäßigkeitsvorbehalt – durch Vor-Ort-Prüfungen.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">5.2</span>
      <span class="clause-text">
        Der Auftragnehmer kann Kontrollrechte auch durch Vorlage eines aktuellen
        Datenschutz-Audits oder einer ISO-27001-Zertifizierung oder eines vergleichbaren
        Nachweises eines unabhängigen Dritten erfüllen, sofern der Auftraggeber damit
        einverstanden ist.
      </span>
    </div>
  </div>


  <!-- §6 Unterauftragsverarbeiter -->
  <div class="avv-section">
    <h2>§ 6 &nbsp;Einsatz von Unterauftragsverarbeitern</h2>

    <div class="clause">
      <span class="clause-num">6.1</span>
      <span class="clause-text">
        Der Auftragnehmer ist zum Einsatz von Unterauftragsverarbeitern berechtigt.
        Die zum Zeitpunkt des Vertragsschlusses bestehenden Unterauftragsverarbeiter sind in
        <strong>Anlage 3</strong> aufgeführt. Mit Vertragsschluss erteilt der Auftraggeber
        seine Zustimmung zu deren Einsatz.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">6.2</span>
      <span class="clause-text">
        Beabsichtigt der Auftragnehmer, neue Unterauftragsverarbeiter einzusetzen oder bestehende
        zu ersetzen, informiert er den Auftraggeber mindestens <strong>vier Wochen</strong> vorher
        per E-Mail. Der Auftraggeber kann innerhalb von zwei Wochen nach dieser Mitteilung
        Widerspruch einlegen, wenn er begründete datenschutzrechtliche Einwände hat. In diesem
        Fall suchen die Parteien eine einvernehmliche Lösung; gelingt dies nicht, steht dem
        Auftraggeber ein außerordentliches Kündigungsrecht des Hauptvertrags zu.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">6.3</span>
      <span class="clause-text">
        Unterauftragsverarbeiter in Drittstaaten dürfen nur eingesetzt werden, wenn die
        Anforderungen der Art. 44 ff. DSGVO erfüllt sind und der Auftraggeber ausdrücklich
        zugestimmt hat. Der Auftragnehmer stellt sicher, dass Unterauftragsverarbeiter durch
        vertragliche Regelungen denselben Datenschutzverpflichtungen unterworfen werden,
        die dieser Vertrag dem Auftragnehmer auferlegt.
      </span>
    </div>
  </div>


  <!-- §7 Betroffenenrechte -->
  <div class="avv-section">
    <h2>§ 7 &nbsp;Unterstützung bei Betroffenenrechten</h2>

    <div class="clause">
      <span class="clause-num">7.1</span>
      <span class="clause-text">
        Der Auftragnehmer unterstützt den Auftraggeber bei der Erfüllung der Rechte betroffener
        Personen gemäß Art. 12–22 DSGVO (insbesondere Auskunft, Berichtigung, Löschung,
        Einschränkung, Datenübertragbarkeit) in dem Maß, wie dies mit Blick auf die Art der
        Verarbeitung möglich ist.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">7.2</span>
      <span class="clause-text">
        Ersucht eine betroffene Person, eine Behörde oder ein sonstiger Dritter den
        Auftragnehmer direkt um Auskunft, Berichtigung oder Löschung, leitet der Auftragnehmer
        die Anfrage unverzüglich – in der Regel innerhalb von 48 Stunden – an den Auftraggeber
        weiter und führt keine eigenen Maßnahmen ohne dessen Weisung durch.
      </span>
    </div>
  </div>


  <!-- §8 Meldepflichten -->
  <div class="avv-section">
    <h2>§ 8 &nbsp;Meldepflichten und Datenpannen</h2>

    <div class="clause warn">
      <span class="clause-num">8.1</span>
      <span class="clause-text">
        <strong>72-Stunden-Pflicht (Art. 33 DSGVO):</strong><br>
        Der Auftragnehmer meldet dem Auftraggeber jede Verletzung des Schutzes personenbezogener
        Daten (Datenpanne) <strong>unverzüglich, spätestens jedoch innerhalb von 24 Stunden</strong>
        nach Bekanntwerden per E-Mail an die vom Auftraggeber benannte Kontaktadresse.
        Diese kurze Frist ist notwendig, damit der Auftraggeber seine gesetzliche
        72-Stunden-Meldefrist gegenüber der Datenschutzbehörde (Art. 33 DSGVO) einhalten kann.
        Die Meldung enthält mindestens: Art der Verletzung, betroffene Datenkategorien,
        ungefähre Anzahl der betroffenen Personen und Datensätze sowie ergriffene oder
        geplante Abhilfemaßnahmen.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">8.2</span>
      <span class="clause-text">
        Verstöße gegen diesen Vertrag, gegen Weisungen des Auftraggebers oder gegen sonstige
        datenschutzrechtliche Bestimmungen sind dem Auftraggeber ebenfalls unverzüglich
        mitzuteilen, unabhängig davon, ob der Verstoß durch eigene Mitarbeiter oder durch
        Unterauftragsverarbeiter begangen wurde.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">8.3</span>
      <span class="clause-text">
        Der Auftragnehmer informiert den Auftraggeber unverzüglich, wenn Aufsichtsmaßnahmen
        einer Datenschutzbehörde bevorstehen oder eingeleitet werden, soweit diese die
        auftragsgemäß verarbeiteten Daten betreffen könnten.
      </span>
    </div>
  </div>


  <!-- §9 Vertragsbeendigung -->
  <div class="avv-section">
    <h2>§ 9 &nbsp;Vertragsbeendigung und Datenlöschung</h2>

    <div class="clause">
      <span class="clause-num">9.1</span>
      <span class="clause-text">
        Nach Beendigung des Hauptvertrags löscht der Auftragnehmer alle im Rahmen der
        Auftragsverarbeitung gespeicherten personenbezogenen Daten des Auftraggebers –
        einschließlich hochgeladener Dokumente, erzeugter Exportdateien und Protokolldaten –
        spätestens innerhalb von 30 Tagen nach Vertragsende, sofern keine gesetzliche
        Aufbewahrungspflicht entgegensteht.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">9.2</span>
      <span class="clause-text">
        Der Auftragnehmer bestätigt die vollständige Löschung auf Verlangen des Auftraggebers
        schriftlich (E-Mail genügt) mit Datumsangabe. Soweit gesetzliche Aufbewahrungspflichten
        bestehen, werden die betreffenden Daten bis zum Ablauf der jeweiligen Frist gesperrt
        und danach unverzüglich gelöscht.
      </span>
    </div>
  </div>


  <!-- §10 Schlussbestimmungen -->
  <div class="avv-section">
    <h2>§ 10 &nbsp;Schlussbestimmungen</h2>

    <div class="clause">
      <span class="clause-num">10.1</span>
      <span class="clause-text">
        Änderungen dieses Vertrags und seiner Anlagen bedürfen der Textform (E-Mail genügt).
        Änderungen der Anlagen durch den Auftragnehmer (z.&thinsp;B. Aktualisierung der
        Subunternehmerliste) werden dem Auftraggeber gemäß § 6.2 mitgeteilt.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">10.2</span>
      <span class="clause-text">
        Es gilt das Recht der Bundesrepublik Deutschland. Gerichtsstand ist der Sitz des
        Auftragnehmers (Düsseldorf), soweit gesetzlich zulässig.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">10.3</span>
      <span class="clause-text">
        Sollte sich die DSGVO oder in Bezug genommene Vorschriften während der Laufzeit
        ändern, gelten die Verweise auch für die jeweiligen Nachfolgeregelungen. Soweit
        einzelne Bestimmungen unwirksam sind, bleibt die Wirksamkeit des Vertrags im
        Übrigen unberührt.
      </span>
    </div>

    <div class="clause">
      <span class="clause-num">10.4</span>
      <span class="clause-text">
        Für die Haftung gilt Art. 82 DSGVO sowie ergänzend die Haftungsregelungen des
        Hauptvertrags (AGB des Anbieters).
      </span>
    </div>
  </div>


  <!-- Acceptance -->
  <div class="acceptance-block">
    <h3>Vertragsschluss (Online-Akzeptanz)</h3>
    <p>
      Dieser AVV kommt nicht durch handschriftliche Unterschrift, sondern durch aktive
      Bestätigung im Rahmen des Bestellprozesses auf <em>wertstapel.de</em> zustande.
      Der Auftraggeber bestätigt mit dem Abschluss des Hauptvertrags durch Markierung der
      entsprechenden Checkbox, dass er diesen AVV in der zum Zeitpunkt des Vertragsschlusses
      gültigen Fassung gelesen und akzeptiert hat. Zeitpunkt und IP-Adresse der Bestätigung
      werden vom Anbieter protokolliert und auf Anfrage mitgeteilt.
    </p>
  </div>


  <!-- ═══════════════════════════════════════
       ANLAGE 1
  ════════════════════════════════════════ -->
  <div class="annex">
    <p class="annex-label">Anlage 1</p>
    <h2>Auftragsdetails: Art, Zweck und Umfang der Verarbeitung</h2>

    <table>
      <thead>
        <tr>
          <th style="width:30%">Dimension</th>
          <th>Konkrete Ausprägung</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td><strong>Gegenstand und Zweck</strong></td>
          <td>
            Automatisierte Verarbeitung von Wertpapier-Transaktionsdokumenten (PDF)
            zur Erzeugung von DATEV-kompatiblen Buchungsdatensätzen (CSV/Buchungsstapel)
            zum Zweck der Buchführungsvorbereitung für GmbH-Inhaber und deren Steuerberater.
          </td>
        </tr>
        <tr>
          <td><strong>Art der Verarbeitung</strong></td>
          <td>
            Erheben (Upload), Speichern, Auslesen, Transformieren (PDF → strukturierte Daten),
            Zusammenführen, Ausgabe (CSV-Export), Löschen der Eingangsdokumente nach Verarbeitung
          </td>
        </tr>
        <tr>
          <td><strong>Verarbeitete Datenarten</strong></td>
          <td>
            <ul>
              <li>Name und Adresse des Depotinhabers</li>
              <li>Depotnummer / Kundennummer bei der Bank</li>
              <li>IBAN und Kontonummern (soweit im Dokument enthalten)</li>
              <li>Transaktionsdaten (Kaufdatum, Verkaufsdatum, Ausführungspreis, Stückzahl)</li>
              <li>Wertpapierbezeichnung, ISIN, WKN</li>
              <li>Dividenden- und Ertragsausschüttungen</li>
              <li>Steuerrelevante Kennzahlen (Teilfreistellungsquoten, Anschaffungskosten,
                  Vorabpauschale, Kirchensteuer, Kapitalertragsteuer, Solidaritätszuschlag)</li>
              <li>Buchungstexte und Referenznummern</li>
            </ul>
          </td>
        </tr>
        <tr>
          <td><strong>Besondere Datenkategorien (Art. 9 DSGVO)</strong></td>
          <td>
            Keine besonderen Kategorien im Sinne von Art. 9 DSGVO. Es handelt sich ausschließlich
            um Finanztransaktionsdaten. Dennoch sind die Daten als <em>wirtschaftlich sensibel</em>
            einzustufen und entsprechend zu schützen.
          </td>
        </tr>
        <tr>
          <td><strong>Betroffene Personengruppen</strong></td>
          <td>
            <ul>
              <li>GmbH-Gesellschafter / GmbH-Eigentümer als Depotinhaber</li>
              <li>Ggf. Geschäftsführer der GmbH (bei betrieblichen Depots)</li>
              <li>Ggf. Mandanten von Steuerberatungskanzleien (wenn der Auftraggeber
                  eine Kanzlei ist)</li>
            </ul>
          </td>
        </tr>
        <tr>
          <td><strong>Speicherdauer der Eingangsdaten</strong></td>
          <td>
            Hochgeladene PDF-Dokumente werden nach erfolgreicher Verarbeitung unmittelbar,
            spätestens aber nach 24 Stunden, serverseitig gelöscht. CSV-Exportdateien und
            Verarbeitungsprotokolle werden für maximal 30 Tage nach Erzeugung vorgehalten
            und danach automatisch gelöscht, sofern der Nutzer nicht vorher manuell löscht.
          </td>
        </tr>
        <tr>
          <td><strong>Rechtsgrundlage beim Auftraggeber</strong></td>
          <td>
            Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung) oder Art. 6 Abs. 1 lit. f DSGVO
            (berechtigtes Interesse an ordnungsgemäßer Buchführungsvorbereitung);
            ggf. Art. 6 Abs. 1 lit. c DSGVO (rechtliche Verpflichtung zur Buchführung,
            § 238 HGB, § 140 AO)
          </td>
        </tr>
      </tbody>
    </table>
  </div>


  <!-- ═══════════════════════════════════════
       ANLAGE 2 – TOM
  ════════════════════════════════════════ -->
  <div class="annex">
    <p class="annex-label">Anlage 2</p>
    <h2>Technische und organisatorische Maßnahmen (TOM) nach Art. 32 DSGVO</h2>

    <p style="font-size:13.5px; color:var(--color-muted); margin-bottom:20px;">
      Stand: Mai 2026 · Überprüfungsintervall: jährlich sowie anlassbezogen
    </p>

    <div class="tom-cat">
      <h3>1. Zutrittskontrolle (physischer Schutz)</h3>
      <ul>
        <li>Serverinfrastruktur ausschließlich in zertifizierten Rechenzentren der Hetzner Online GmbH (ISO 27001, DE/EU)</li>
        <li>Kein physischer Zugang des Anbieters zu Serverkabinetten; Zugang nur durch autorisiertes Hetzner-Personal mit biometrischer und chipkartenbasierter Zutrittskontrolle</li>
        <li>Büroräume des Anbieters: elektronisches Schließsystem mit personenbezogenen Zutrittsberechtigungen</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>2. Zugangskontrolle (IT-Systeme)</h3>
      <ul>
        <li>Anmeldung an allen Produktivsystemen ausschließlich mit individuellem Benutzernamen und starkem Passwort (min. 12 Zeichen, Komplexitätsanforderungen)</li>
        <li>Zwei-Faktor-Authentifizierung (2FA) für alle Administrationszugänge und kritischen Systeme</li>
        <li>Automatische Bildschirmsperre nach Inaktivität (max. 5 Minuten)</li>
        <li>Anzahl der Systemadministratoren auf das betrieblich notwendige Minimum reduziert</li>
        <li>Passwörter werden ausschließlich in gehasherter Form (bcrypt, min. Kostenfaktor 12) gespeichert</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>3. Zugriffskontrolle (Berechtigungen)</h3>
      <ul>
        <li>Rollenbasiertes Berechtigungskonzept (RBAC): Mitarbeiter erhalten nur Zugriff auf Daten, die für ihre konkrete Aufgabe erforderlich sind (Least-Privilege-Prinzip)</li>
        <li>Strikter Mandanten-Datentrennung: Kundendaten werden in isolierten Datenbankbereichen gehalten; kein mandantenübergreifender Zugriff technisch möglich</li>
        <li>Regelmäßige Überprüfung und Entzug von Berechtigungen bei Rollenwechsel oder Ausscheiden von Mitarbeitern</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>4. Weitergabekontrolle (Verschlüsselung und Transport)</h3>
      <ul>
        <li>Alle Datenübertragungen zwischen Client und Server ausschließlich über TLS 1.2 oder höher (HTTPS); HTTP-Verbindungen werden automatisch auf HTTPS umgeleitet</li>
        <li>HSTS (HTTP Strict Transport Security) ist aktiviert</li>
        <li>Hochgeladene Dateien und Datenbankbestände werden at-rest verschlüsselt (AES-256)</li>
        <li>Datenübertragungen an Subunternehmer nur über gesicherte, verschlüsselte Verbindungen</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>5. Eingabe- und Protokollkontrolle</h3>
      <ul>
        <li>Lückenlose Protokollierung von Upload-, Verarbeitungs- und Exportvorgängen mit Zeitstempel und Benutzer-ID</li>
        <li>Protokollierung aller Administrationszugriffe auf Produktivsysteme</li>
        <li>Protokolldaten werden mindestens 90 Tage aufbewahrt und sind unveränderbar (append-only)</li>
        <li>Nachvollziehbarkeit von Dateneingaben, Änderungen und Löschvorgängen gewährleistet</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>6. Verfügbarkeitskontrolle und Belastbarkeit</h3>
      <ul>
        <li>Tägliche automatische Backups aller Produktivdaten; Backup-Aufbewahrung: 30 Tage</li>
        <li>Backups werden verschlüsselt und geografisch getrennt vom Primärsystem gespeichert (anderes Hetzner-Rechenzentrum)</li>
        <li>Regelmäßige Wiederherstellungstests (Restore-Tests) mindestens vierteljährlich</li>
        <li>Monitoring der Systemverfügbarkeit rund um die Uhr mit automatisierten Alarmen</li>
        <li>Angestrebte Verfügbarkeit: 99 % im Jahresmittel</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>7. Datenschutz bei Subunternehmern</h3>
      <ul>
        <li>Auswahl von Subunternehmern ausschließlich nach Datenschutz- und Sicherheitskriterien</li>
        <li>Abschluss von DSGVO-konformen AVVs mit allen relevanten Subunternehmern vor Beauftragung</li>
        <li>Regelmäßige Überprüfung der Subunternehmer-Compliance (mindestens jährlich)</li>
      </ul>
    </div>

    <div class="tom-cat">
      <h3>8. Organisatorische Maßnahmen</h3>
      <ul>
        <li>Datenschutz-Schulung aller Mitarbeiter vor Aufnahme der Tätigkeit und jährlich wiederkehrend</li>
        <li>Dokumentierte Verpflichtung aller Mitarbeiter zur Vertraulichkeit und Einhaltung des Datenschutzes</li>
        <li>Incident-Response-Plan für Datenpannen mit definierten Eskalationswegen und der 24-Stunden-Meldepflicht an den Auftraggeber</li>
        <li>Regelmäßige Sicherheitsupdates und Patch-Management für alle eingesetzten Software-Komponenten</li>
        <li>Datenschutz-by-Design und Datenschutz-by-Default als Grundprinzipien der Systementwicklung</li>
      </ul>
    </div>
  </div>


  <!-- ═══════════════════════════════════════
       ANLAGE 3 – Subunternehmer
  ════════════════════════════════════════ -->
  <div class="annex">
    <p class="annex-label">Anlage 3</p>
    <h2>Liste der Unterauftragsverarbeiter zum Zeitpunkt des Vertragsschlusses</h2>

    <table>
      <thead>
        <tr>
          <th>Unternehmen / Anschrift</th>
          <th>Beschreibung der Leistung</th>
          <th>Land</th>
          <th>Rechtsgrundlage</th>
        </tr>
      </thead>
      <tbody>
        <tr>
          <td>
            <strong>Hetzner Online GmbH</strong><br>
            Industriestr. 25<br>
            91710 Gunzenhausen<br>
            <a href="https://www.hetzner.com/de/legal/privacy-policy" target="_blank" rel="noopener">DPA / Datenschutz</a>
          </td>
          <td>
            Cloud-Hosting und Serverinfrastruktur; Speicherung und Verarbeitung aller
            Kunden- und Prozessdaten auf Hetzner-Servern in deutschen und finnischen
            Rechenzentren
          </td>
          <td>Deutschland / EU</td>
          <td>Art. 28 DSGVO (AVV mit Hetzner abgeschlossen)</td>
        </tr>
        <tr>
          <td>
            <strong>Stripe Payments Europe, Ltd.</strong><br>
            The One Building, 1 Grand Canal Street Lower<br>
            Dublin 2, Irland<br>
            <a href="https://stripe.com/de/legal/dpa" target="_blank" rel="noopener">Stripe DPA</a>
          </td>
          <td>
            Zahlungsabwicklung und Abonnementverwaltung. Stripe verarbeitet
            <em>ausschließlich</em> Zahlungsdaten (Name, Rechnungsadresse, Zahlungsmittel,
            Transaktions-ID). Stripe hat keinen Zugriff auf Depot- oder Buchungsdaten.
          </td>
          <td>Irland (EU)</td>
          <td>Art. 28 DSGVO (Stripe DPA); für US-Datentransfers: SCCs (Stripe, Inc.)</td>
        </tr>
        <tr>
          <td>
            <strong>Plausible Analytics OÜ</strong><br>
            Västriku tn 2, 50403 Tartu<br>
            Estland<br>
            <a href="https://plausible.io/data-policy" target="_blank" rel="noopener">Plausible Datenschutz</a>
          </td>
          <td>
            Datenschutzfreundliche Website-Analyse (Besucherstatistiken). Plausible
            verarbeitet <em>keine</em> personenbezogenen Daten im DSGVO-Sinne
            (kein Cookie-Einsatz, keine persistente Nutzer-ID, keine Verknüpfung mit
            Kundendaten). Es werden ausschließlich aggregierte, nicht-personalisierte
            Metriken erhoben (Seitenaufrufe, Verweildauer, Herkunftsland auf
            Länderebene). Plausible speichert keine IP-Adressen.
            <br><br>
            <strong>Hinweis:</strong> Da Plausible keine personenbezogenen Daten
            verarbeitet, ist ein AVV nach Art. 28 DSGVO streng genommen nicht
            erforderlich; die Aufführung erfolgt aus Transparenzgründen.
          </td>
          <td>Estland (EU)</td>
          <td>
            Kein AVV erforderlich (keine PbD-Verarbeitung); hilfsweise
            Art. 28 DSGVO (Plausible DPA verfügbar)
          </td>
        </tr>
        <tr>
          <td>
            <strong>Brevo SAS</strong> (ehem. Sendinblue)<br>
            106 boulevard Haussmann<br>
            75008 Paris, Frankreich<br>
            <a href="https://www.brevo.com/legal/termsofuse/" target="_blank" rel="noopener">Brevo DPA</a>
          </td>
          <td>
            Transaktionaler E-Mail-Versand (Rechnungsbestätigungen, Registrierungs-E-Mails,
            Systembenachrichtigungen, AVV-Änderungsmitteilungen). Brevo verarbeitet
            hierfür Name und E-Mail-Adresse des Empfängers sowie den jeweiligen
            E-Mail-Inhalt. Kein Zugriff auf Depot- oder Buchungsdaten.
          </td>
          <td>Frankreich (EU) 🇫🇷</td>
          <td>
            Art. 28 DSGVO (Brevo DPA)<br>
            Kein Drittlandtransfer
          </td>
        </tr>
      </tbody>
    </table>

    <p style="font-size:12.5px; color:var(--color-muted); margin-top:12px;">
      <em>Diese Liste wird bei Änderungen gemäß § 6.2 dieses AVV aktualisiert und den
      Kunden mit einer Vorlaufzeit von mindestens vier Wochen mitgeteilt.
      Die jeweils aktuelle Version ist unter wertstapel.de/avv abrufbar.</em>
    </p>
  </div>


  <!-- Footer -->
  <div class="avv-footer">
    <span>Stand: Mai 2026 · Anlage zum Hauptvertrag (AGB)</span>
    <span>Spark Innovation GmbH · Düsseldorf</span>
  </div>

</div><!-- /.avv-wrapper -->` }} />
    </>
  )
}
