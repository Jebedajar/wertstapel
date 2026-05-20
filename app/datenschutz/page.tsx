import LegalLayout from '@/components/LegalLayout'

export const metadata = {
  title: 'Datenschutzerklärung – Wertstapel',
}

export default function Page() {
  return (
    <LegalLayout>
      <style>{`
:root{--color-bg:#fafaf8;--color-surface:#ffffff;--color-border:#e4e2db;--color-text:#1a1a18;--color-muted:#6b6960;--color-accent:#1d4ed8;--color-accent-bg:#eff6ff;--color-warn:#92400e;--color-warn-bg:#fffbeb;--color-warn-border:#d97706;--font-serif:'Georgia','Times New Roman',serif;--font-sans:'Helvetica Neue',Helvetica,Arial,sans-serif;--radius:6px;--max-width:800px}
    *,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
    body{background:var(--color-bg);color:var(--color-text);font-family:var(--font-sans);font-size:15px;line-height:1.8;padding:48px 24px 96px;counter-reset:section}
    .dse-wrapper{max-width:var(--max-width);margin:0 auto;background:var(--color-surface);border:1px solid var(--color-border);border-radius:10px;padding:56px 64px}
    @media(max-width:680px){.dse-wrapper{padding:32px 20px}}
    .dse-header{border-bottom:2px solid var(--color-text);padding-bottom:28px;margin-bottom:40px}
    .dse-label{font-size:11px;font-weight:600;letter-spacing:0.12em;text-transform:uppercase;color:var(--color-muted);margin-bottom:10px}
    h1{font-family:var(--font-serif);font-size:26px;font-weight:normal;line-height:1.3}
    .dse-meta{font-size:13px;color:var(--color-muted);margin-top:8px}
    .dse-section{margin-bottom:44px}
    h2{font-family:var(--font-sans);font-size:13px;font-weight:700;letter-spacing:0.07em;text-transform:uppercase;color:var(--color-text);margin-bottom:18px;padding-bottom:8px;border-bottom:1px solid var(--color-border);counter-increment:section}
    h2::before{content:counter(section) ". ";color:var(--color-muted)}
    h3{font-size:14.5px;font-weight:700;color:var(--color-text);margin:20px 0 8px}
    p{font-size:14.5px;line-height:1.8;margin-bottom:12px;color:var(--color-text)}
    ul{padding-left:20px;margin-bottom:12px}
    li{font-size:14.5px;line-height:1.75;margin-bottom:5px}
    a{color:var(--color-accent);text-decoration:none}
    a:hover{text-decoration:underline}
    .notice{background:var(--color-accent-bg);border-left:3px solid var(--color-accent);padding:14px 18px;border-radius:0 var(--radius) var(--radius) 0;margin:16px 0;font-size:14px;line-height:1.75;color:#1e3a8a}
    .warn{background:var(--color-warn-bg);border-left:3px solid var(--color-warn-border);padding:14px 18px;border-radius:0 var(--radius) var(--radius) 0;margin:16px 0;font-size:14px;line-height:1.75;color:var(--color-warn)}
    .caps-block{font-size:13px;line-height:1.7;background:var(--color-bg);border:1px solid var(--color-border);padding:14px 18px;border-radius:var(--radius);margin:12px 0}
    .provider-card{border:1px solid var(--color-border);border-radius:var(--radius);padding:16px 20px;margin:16px 0;background:var(--color-bg)}
    .provider-card .provider-name{font-weight:700;font-size:14.5px;margin-bottom:4px}
    .provider-card .provider-address{font-size:13px;color:var(--color-muted);margin-bottom:10px;line-height:1.5}
    .overview-grid{display:grid;grid-template-columns:1fr 1fr;gap:1px;background:var(--color-border);border:1px solid var(--color-border);border-radius:var(--radius);overflow:hidden;margin-bottom:20px}
    @media(max-width:560px){.overview-grid{grid-template-columns:1fr}}
    .overview-cell{background:var(--color-surface);padding:14px 16px}
    .overview-cell .oc-label{font-size:11px;font-weight:700;letter-spacing:0.08em;text-transform:uppercase;color:var(--color-muted);margin-bottom:4px}
    .overview-cell p{font-size:13.5px;margin:0}
    .dse-footer{margin-top:52px;padding-top:20px;border-top:1px solid var(--color-border);font-size:12px;color:var(--color-muted);display:flex;justify-content:space-between;flex-wrap:wrap;gap:8px}
      `}</style>
      <div dangerouslySetInnerHTML={{ __html: `<div class="dse-wrapper">
  <div class="dse-header">
    <p class="dse-label">Rechtsdokument</p>
    <h1>Datenschutzerklärung</h1>
    <p class="dse-meta">wertstapel.de &middot; Stand: Mai 2026</p>
  </div>

  <div class="dse-section">
    <h2>Datenschutz auf einen Blick</h2>
    <h3>Allgemeine Hinweise</h3>
    <p>Die folgenden Hinweise geben einen Überblick darüber, was mit Ihren personenbezogenen Daten passiert, wenn Sie diese Website besuchen und unseren Dienst nutzen. Personenbezogene Daten sind alle Daten, mit denen Sie persönlich identifiziert werden können.</p>
    <h3>Datenerfassung auf dieser Website und im Dienst</h3>
    <div class="overview-grid">
      <div class="overview-cell"><p class="oc-label">Wer ist verantwortlich?</p><p>Spark Innovation GmbH, Lenneper Str. 32, 40591 Düsseldorf</p></div>
      <div class="overview-cell"><p class="oc-label">Wie erfassen wir Daten?</p><p>Durch Ihre aktive Eingabe (Registrierung, Upload) sowie automatisch beim Website-Besuch (Server-Logs)</p></div>
      <div class="overview-cell"><p class="oc-label">Wofür nutzen wir Daten?</p><p>Vertragserfüllung (SaaS-Betrieb), Zahlungsabwicklung, Kundenservice, Website-Analyse</p></div>
      <div class="overview-cell"><p class="oc-label">Ihre Rechte</p><p>Auskunft, Berichtigung, Löschung, Einschränkung, Datenübertragbarkeit, Widerspruch – jederzeit kostenfrei</p></div>
    </div>
    <p>Für Fragen zum Datenschutz wenden Sie sich jederzeit an uns: <a href="mailto:info@wertstapel.de">info@wertstapel.de</a></p>
  </div>

  <div class="dse-section">
    <h2>Hosting</h2>
    <h3>Hetzner</h3>
    <p>Wir hosten unsere Website und die gesamte Plattforminfrastruktur bei der Hetzner Online GmbH, Industriestr. 25, 91710 Gunzenhausen (nachfolgend „Hetzner"). Alle Daten werden ausschließlich auf Servern innerhalb der Europäischen Union verarbeitet (Rechenzentren in Deutschland und Finnland).</p>
    <p>Details entnehmen Sie der Datenschutzerklärung von Hetzner: <a href="https://www.hetzner.com/de/legal/privacy-policy/" target="_blank" rel="noopener noreferrer">hetzner.com/de/legal/privacy-policy</a>.</p>
    <p>Die Verwendung von Hetzner erfolgt auf Grundlage von Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an zuverlässigem EU-Hosting) sowie Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung). Wir haben mit Hetzner einen Auftragsverarbeitungsvertrag (AVV) gemäß Art. 28 DSGVO geschlossen.</p>
  </div>

  <div class="dse-section">
    <h2>Allgemeine Hinweise und Pflichtinformationen</h2>
    <h3>Hinweis zur verantwortlichen Stelle</h3>
    <p>Die verantwortliche Stelle für die Datenverarbeitung auf dieser Website und im Dienst ist:</p>
    <div class="provider-card">
      <p class="provider-name">Spark Innovation GmbH</p>
      <p class="provider-address">Lenneper Str. 32<br>40591 Düsseldorf<br>E-Mail: <a href="mailto:info@wertstapel.de">info@wertstapel.de</a></p>
    </div>
    <h3>Speicherdauer</h3>
    <p>Soweit innerhalb dieser Datenschutzerklärung keine speziellere Speicherdauer genannt wurde, verbleiben Ihre personenbezogenen Daten bei uns, bis der Zweck für die Datenverarbeitung entfällt. Wenn Sie ein berechtigtes Löschersuchen geltend machen oder eine Einwilligung widerrufen, werden Ihre Daten gelöscht, sofern keine gesetzlichen Aufbewahrungspflichten entgegenstehen (z.&thinsp;B. handels- oder steuerrechtliche Fristen von 6 oder 10 Jahren).</p>
    <h3>Rechtsgrundlagen der Datenverarbeitung</h3>
    <p>Wir verarbeiten personenbezogene Daten auf folgenden Rechtsgrundlagen:</p>
    <ul>
      <li><strong>Art. 6 Abs. 1 lit. a DSGVO</strong> – Einwilligung</li>
      <li><strong>Art. 6 Abs. 1 lit. b DSGVO</strong> – Vertragserfüllung und vorvertragliche Maßnahmen</li>
      <li><strong>Art. 6 Abs. 1 lit. c DSGVO</strong> – Erfüllung rechtlicher Verpflichtungen</li>
      <li><strong>Art. 6 Abs. 1 lit. f DSGVO</strong> – Berechtigte Interessen</li>
    </ul>
    <h3>Widerruf Ihrer Einwilligung</h3>
    <p>Sie können eine bereits erteilte Einwilligung jederzeit mit Wirkung für die Zukunft widerrufen.</p>
    <h3>Widerspruchsrecht gegen Datenerhebung in besonderen Fällen (Art. 21 DSGVO)</h3>
    <div class="caps-block">WENN DIE DATENVERARBEITUNG AUF GRUNDLAGE VON ART. 6 ABS. 1 LIT. E ODER F DSGVO ERFOLGT, HABEN SIE JEDERZEIT DAS RECHT, AUS GRÜNDEN, DIE SICH AUS IHRER BESONDEREN SITUATION ERGEBEN, GEGEN DIE VERARBEITUNG IHRER PERSONENBEZOGENEN DATEN WIDERSPRUCH EINZULEGEN. WENN SIE WIDERSPRUCH EINLEGEN, WERDEN WIR IHRE BETROFFENEN PERSONENBEZOGENEN DATEN NICHT MEHR VERARBEITEN, ES SEI DENN, WIR KÖNNEN ZWINGENDE SCHUTZWÜRDIGE GRÜNDE FÜR DIE VERARBEITUNG NACHWEISEN (WIDERSPRUCH NACH ART. 21 ABS. 1 DSGVO).</div>
    <h3>Beschwerderecht bei der Aufsichtsbehörde</h3>
    <p>Im Falle von Verstößen gegen die DSGVO steht Ihnen ein Beschwerderecht bei einer Datenschutzaufsichtsbehörde zu. Die für uns zuständige Aufsichtsbehörde ist:</p>
    <div class="provider-card">
      <p class="provider-name">Landesbeauftragter für Datenschutz und Informationsfreiheit Nordrhein-Westfalen (LfDI NRW)</p>
      <p class="provider-address">Postfach 20 04 44 &middot; 40102 Düsseldorf<br>Telefon: +49 211 38424-0<br>E-Mail: <a href="mailto:poststelle@ldi.nrw.de">poststelle@ldi.nrw.de</a><br><a href="https://www.ldi.nrw.de" target="_blank" rel="noopener noreferrer">www.ldi.nrw.de</a></p>
    </div>
    <h3>Recht auf Auskunft, Berichtigung, Löschung und Einschränkung</h3>
    <p>Sie haben jederzeit das Recht auf unentgeltliche Auskunft über Ihre gespeicherten personenbezogenen Daten sowie ggf. ein Recht auf Berichtigung, Löschung oder Einschränkung der Verarbeitung. Wenden Sie sich dazu an: <a href="mailto:info@wertstapel.de">info@wertstapel.de</a></p>
    <h3>SSL-/TLS-Verschlüsselung</h3>
    <p>Diese Website und alle Datenübertragungen zur Plattform nutzen aus Sicherheitsgründen ausschließlich TLS 1.2 oder höher (HTTPS).</p>
  </div>

  <div class="dse-section">
    <h2>Registrierung und Nutzerkonto</h2>
    <p>Für die Nutzung der Plattform <em>wertstapel.de</em> ist die Erstellung eines Nutzerkontos erforderlich. Dabei erheben wir folgende Daten:</p>
    <ul>
      <li>E-Mail-Adresse (dient als einzige Login-Kennung)</li>
      <li>Bestätigung der unternehmerischen Eigenschaft (Checkbox-Protokoll mit Zeitstempel)</li>
      <li>Bestätigung der AGB und des Auftragsverarbeitungsvertrags (AVV) mit Zeitstempel</li>
    </ul>
    <p>Ein Passwort wird nicht vergeben. Die Anmeldung erfolgt ausschließlich über einen per E-Mail zugesandten Einmal-Link (Magic Link), der 15 Minuten gültig ist. Rechnungsrelevante Daten werden ausschließlich durch Stripe im Rahmen des Bestellprozesses erhoben.</p>
    <p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).<br><strong>Speicherdauer:</strong> Die E-Mail-Adresse und das Kaufkonto werden nach Vertragsbeendigung innerhalb von 30 Tagen gelöscht. Rechnungsbelege unterliegen der gesetzlichen Aufbewahrungspflicht (§ 147 AO: 10 Jahre).</p>
  </div>

  <div class="dse-section">
    <h2>Authentifizierung und Session-Cookie</h2>
    <p>Die Anmeldung erfolgt passwortlos über einen <strong>Magic Link</strong>. Nach Eingabe Ihrer E-Mail-Adresse senden wir einen Einmal-Link, der nach <strong>15 Minuten</strong> ungültig wird.</p>
    <p>Nach erfolgreicher Anmeldung setzen wir einen verschlüsselten Session-Cookie (<strong>Name: ws_session</strong>) mit einer Laufzeit von <strong>365 Tagen</strong>. Der Cookie ist <code>HttpOnly</code> und <code>Secure</code> gesetzt – er ist für JavaScript nicht auslesbar.</p>
    <p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. b DSGVO sowie § 25 Abs. 2 Nr. 2 TDDDG (technisch erforderliche Cookies ohne Einwilligungspflicht).</p>
  </div>

  <div class="dse-section">
    <h2>Nutzung der SaaS-Plattform (Kernleistung)</h2>
    <div class="notice"><strong>B2B-Hinweis:</strong> Die Plattform richtet sich ausschließlich an Unternehmer im Sinne des § 14 BGB. Die im Rahmen der Plattformnutzung verarbeiteten Daten betreffen in der Regel betriebliche Finanzdaten des Kundenunternehmens. Zwischen dem Anbieter und dem Kunden besteht ein Auftragsverarbeitungsvertrag (AVV) gemäß Art. 28 DSGVO.</div>
    <h3>Verarbeitete Daten beim PDF-Upload und der Konvertierung</h3>
    <p>Wenn Sie PDF-Dokumente von Wertpapier-Transaktionen hochladen und konvertieren lassen, verarbeiten wir die in diesen Dokumenten enthaltenen Daten, insbesondere:</p>
    <ul>
      <li>Name und ggf. Adresse des Depotinhabers</li>
      <li>Depotnummer und Kontonummern (soweit im Dokument enthalten)</li>
      <li>Transaktionsdaten (Kaufdatum, Verkaufsdatum, Stückzahl, Preis, Gegenwert)</li>
      <li>Wertpapierbezeichnung, ISIN, WKN</li>
      <li>Dividenden- und Ertragsausschüttungen</li>
      <li>Steuerrelevante Kennzahlen (Teilfreistellungsquoten, Kapitalertragsteuer, Solidaritätszuschlag, Kirchensteuer)</li>
    </ul>
    <p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. b DSGVO sowie Art. 28 DSGVO (Auftragsverarbeitung gemäß AVV).</p>
    <h3>Speicherdauer der hochgeladenen Dokumente</h3>
    <ul>
      <li><strong>Hochgeladene PDF-Dokumente:</strong> werden nach erfolgreicher Verarbeitung unverzüglich, spätestens nach 24 Stunden, automatisch und unwiderruflich vom Server gelöscht.</li>
      <li><strong>Erzeugte CSV-/Exportdateien:</strong> werden für maximal 24 Stunden nach Auslieferung zum Download bereitgestellt und danach automatisch gelöscht.</li>
      <li><strong>Verarbeitungsprotokolle (Logs):</strong> werden für 90 Tage zu Zwecken der Fehleranalyse gespeichert und danach gelöscht.</li>
    </ul>
    <h3>Keine Steuerberatung</h3>
    <p>Die erzeugten Buchungsdatensätze sind automatisiert generierte Vorschläge. Sie stellen keine Steuerberatung dar und ersetzen nicht die Prüfung durch einen zugelassenen Steuerberater.</p>
    <h3>Kein automatisiertes Entscheidungsverfahren (Art. 22 DSGVO)</h3>
    <p>Die erzeugten Buchungsvorschläge stellen <strong>keine automatisierte Entscheidung im Sinne von Art. 22 DSGVO</strong> dar. Sie sind technische Verarbeitungsergebnisse, die zwingend einer menschlichen Prüfung durch den Auftraggeber oder dessen Steuerberater bedürfen.</p>
  </div>

  <div class="dse-section">
    <h2>Kontaktaufnahme per E-Mail</h2>
    <p>Wenn Sie uns per E-Mail kontaktieren, wird Ihre Anfrage inklusive aller daraus hervorgehenden personenbezogenen Daten zum Zwecke der Bearbeitung Ihres Anliegens bei uns gespeichert und verarbeitet. Diese Daten geben wir nicht ohne Ihre Einwilligung weiter.</p>
    <p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. b DSGVO (sofern die Anfrage mit einem Vertrag zusammenhängt) oder Art. 6 Abs. 1 lit. f DSGVO in allen übrigen Fällen.</p>
  </div>

  <div class="dse-section">
    <h2>Analyse-Tools</h2>
    <h3>Plausible Analytics</h3>
    <p>Wir verwenden Plausible Analytics zur datenschutzfreundlichen Analyse des Website-Traffics. Anbieter ist die <strong>Plausible Analytics OÜ</strong>, Västriku tn 2, 50403 Tartu, Estland (EU).</p>
    <p>Plausible Analytics ist bewusst so konzipiert, dass <strong>keine personenbezogenen Daten</strong> im datenschutzrechtlichen Sinne verarbeitet werden:</p>
    <ul>
      <li>Keine Cookies, kein LocalStorage, kein Fingerprinting</li>
      <li>IP-Adressen werden nicht gespeichert</li>
      <li>Keine User-IDs, keine sitzungsübergreifende Verfolgung</li>
      <li>Ausschließlich aggregierte Metriken (Seitenaufrufe, Verweildauer, Herkunftsland auf Länderebene)</li>
    </ul>
    <div class="notice">Da Plausible nach unserem Verständnis keine personenbezogenen Daten im Sinne von Art. 4 Nr. 1 DSGVO verarbeitet, bedarf der Einsatz weder einer Einwilligung noch eines AVV. Rechtsgrundlage für den Einsatz ist hilfsweise Art. 6 Abs. 1 lit. f DSGVO (berechtigtes Interesse an datenschutzkonformer Website-Analyse).</div>
    <p><strong>Widerspruchsrecht (Opt-Out):</strong> Sie können der Verarbeitung durch Plausible Analytics jederzeit widersprechen, indem Sie uns unter <a href="mailto:info@wertstapel.de">info@wertstapel.de</a> kontaktieren. Alternativ verhindert ein aktivierter „Do Not Track"-Header in Ihrem Browser die Erfassung durch Plausible vollständig.</p>
    <p>Datenschutzerklärung von Plausible: <a href="https://plausible.io/data-policy" target="_blank" rel="noopener noreferrer">plausible.io/data-policy</a></p>
  </div>

  <div class="dse-section">
    <h2>Transaktionale E-Mails (Brevo)</h2>
    <p>Für den Versand transaktionaler E-Mails (Registrierungsbestätigung, Rechnungen, Systembenachrichtigungen) nutzen wir den Dienst <strong>Brevo</strong> (ehemals Sendinblue).</p>
    <div class="provider-card">
      <p class="provider-name">Brevo SAS (ehem. Sendinblue)</p>
      <p class="provider-address">106 boulevard Haussmann<br>75008 Paris, Frankreich (EU)<br><a href="https://www.brevo.com/legal/privacypolicy/" target="_blank" rel="noopener noreferrer">Datenschutzerklärung</a> &middot; <a href="https://www.brevo.com/legal/termsofuse/" target="_blank" rel="noopener noreferrer">Brevo DPA</a></p>
    </div>
    <p>Brevo verarbeitet zum Zweck der E-Mail-Zustellung Ihren <strong>Namen</strong> und Ihre <strong>E-Mail-Adresse</strong> sowie den <strong>Inhalt der jeweiligen E-Mail</strong>. Brevo hat keinen Zugriff auf hochgeladene PDF-Dokumente oder erzeugte Buchungsdaten.</p>
    <p>Brevo SAS ist als französisches Unternehmen der DSGVO unmittelbar unterworfen. Eine Übermittlung personenbezogener Daten in Drittstaaten findet nicht statt. Wir haben mit Brevo einen Auftragsverarbeitungsvertrag (AVV) gemäß Art. 28 DSGVO geschlossen.</p>
    <p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. b DSGVO (Vertragserfüllung).</p>
  </div>

  <div class="dse-section">
    <h2>Zahlungsabwicklung</h2>
    <h3>Stripe</h3>
    <p>Die Zahlungsabwicklung erfolgt über den Zahlungsdienstleister:</p>
    <div class="provider-card">
      <p class="provider-name">Stripe Payments Europe, Ltd.</p>
      <p class="provider-address">The One Building, 1 Grand Canal Street Lower<br>Dublin 2, Irland (EU)<br><a href="https://stripe.com/de/privacy" target="_blank" rel="noopener noreferrer">Datenschutzerklärung</a> &middot; <a href="https://stripe.com/de/legal/dpa" target="_blank" rel="noopener noreferrer">Stripe DPA</a></p>
    </div>
    <p>Stripe verarbeitet ausschließlich die für die Zahlungsabwicklung erforderlichen Daten: Name, Rechnungsadresse, Zahlungsmitteldetails, Transaktionsbetrag und Transaktions-ID. Stripe hat keinen Zugriff auf hochgeladene PDF-Dokumente oder erzeugte Buchungsdaten.</p>
    <p><strong>Rechtsgrundlage:</strong> Art. 6 Abs. 1 lit. b DSGVO (Zahlungsabwicklung als Vertragsbestandteil).</p>
  </div>

  <div class="dse-section">
    <h2>Plugins und Tools</h2>
    <h3>Google Fonts (lokales Hosting)</h3>
    <p>Diese Website verwendet Google Fonts zur einheitlichen Darstellung von Schriftarten. Die Schriftarten sind <strong>lokal auf unserem Server installiert</strong>. Eine Verbindung zu Servern von Google findet dabei nicht statt; Google erhält keinerlei Daten über Ihren Websitebesuch.</p>
  </div>

  <div class="dse-section">
    <h2>Auftragsverarbeitung durch den Anbieter (B2B)</h2>
    <div class="notice">Dieser Abschnitt richtet sich ausschließlich an gewerbliche Kunden (Unternehmer im Sinne des § 14 BGB), die die Plattform zur Verarbeitung eigener oder betrieblicher Daten nutzen.</div>
    <p>Soweit Sie als Unternehmer die Plattform nutzen und dabei personenbezogene Daten hochladen und verarbeiten lassen, sind Sie im datenschutzrechtlichen Sinne der <strong>Verantwortliche</strong> (Art. 4 Nr. 7 DSGVO); wir sind Ihr <strong>Auftragsverarbeiter</strong> (Art. 4 Nr. 8 DSGVO).</p>
    <p>Zwischen Ihnen als Kunden und uns als Anbieter gilt daher der <strong>Auftragsverarbeitungsvertrag (AVV)</strong>, den Sie im Rahmen des Vertragsschlusses akzeptiert haben. Den jeweils aktuellen AVV können Sie unter <a href="/avv">wertstapel.de/avv</a> einsehen.</p>
  </div>

  <div class="dse-footer">
    <span>Stand: Mai 2026 &middot; wertstapel.de</span>
    <span>Spark Innovation GmbH &middot; Düsseldorf</span>
  </div>
</div>` }} />
    </LegalLayout>
  )
}
