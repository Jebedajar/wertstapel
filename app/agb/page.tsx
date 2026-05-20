import LegalLayout from '@/components/LegalLayout'

export const metadata = {
  title: 'AGB – Wertstapel',
}

export default function Page() {
  return (
    <LegalLayout>
      <style>{`
/* ── Design Tokens ── */
    :root {
      --color-bg:        #fafaf8;
      --color-surface:   #ffffff;
      --color-border:    #e4e2db;
      --color-text:      #1a1a18;
      --color-muted:     #6b6960;
      --color-accent:    #1d4ed8;
      --color-accent-bg: #eff6ff;
      --font-serif:      'Georgia', 'Times New Roman', serif;
      --font-sans:       'Helvetica Neue', Helvetica, Arial, sans-serif;
      --radius:          6px;
      --max-width:       780px;
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

    .agb-wrapper {
      max-width: var(--max-width);
      margin: 0 auto;
      background: var(--color-surface);
      border: 1px solid var(--color-border);
      border-radius: 10px;
      padding: 56px 64px;
    }

    @media (max-width: 680px) {
      .agb-wrapper { padding: 32px 24px; }
    }

    .agb-header {
      border-bottom: 2px solid var(--color-text);
      padding-bottom: 28px;
      margin-bottom: 40px;
    }

    .agb-label {
      font-size: 11px;
      font-weight: 600;
      letter-spacing: 0.12em;
      text-transform: uppercase;
      color: var(--color-muted);
      margin-bottom: 10px;
    }

    h1 {
      font-family: var(--font-serif);
      font-size: 26px;
      font-weight: normal;
      line-height: 1.3;
      color: var(--color-text);
    }

    .agb-meta {
      margin-top: 14px;
      font-size: 13px;
      color: var(--color-muted);
    }

    .agb-section {
      margin-bottom: 44px;
    }

    h2 {
      font-family: var(--font-sans);
      font-size: 14px;
      font-weight: 700;
      letter-spacing: 0.06em;
      text-transform: uppercase;
      color: var(--color-text);
      margin-bottom: 18px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--color-border);
    }

    .agb-clause {
      display: grid;
      grid-template-columns: 40px 1fr;
      gap: 0 12px;
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
      font-size: 14.5px;
      line-height: 1.75;
      color: var(--color-text);
    }

    .notice-box {
      background: var(--color-accent-bg);
      border-left: 3px solid var(--color-accent);
      border-radius: 0 var(--radius) var(--radius) 0;
      padding: 16px 20px;
      margin-bottom: 14px;
    }

    .notice-box .clause-text {
      color: #1e3a8a;
    }

    .agb-footer {
      margin-top: 52px;
      padding-top: 24px;
      border-top: 1px solid var(--color-border);
      font-size: 12px;
      color: var(--color-muted);
      display: flex;
      justify-content: space-between;
      flex-wrap: wrap;
      gap: 8px;
    }
      `}</style>
      <div dangerouslySetInnerHTML={{ __html: `<div class="agb-wrapper">
  <div class="agb-header">
    <p class="agb-label">Rechtsdokument</p>
    <h1>Allgemeine Geschäftsbedingungen</h1>
    <p class="agb-meta">
      Spark Innovation GmbH &middot; Lenneper Str. 32 &middot; 40591 Düsseldorf<br>
      E-Mail: <a href="mailto:info@wertstapel.de">info@wertstapel.de</a><br>
      (nachfolgend <strong>„Anbieter"</strong>) gegenüber seinen Kunden (nachfolgend <strong>„Kunde"</strong>)
    </p>
  </div>

  <div class="agb-section">
    <h2>§ 1 &nbsp;Allgemeines</h2>
    <div class="agb-clause">
      <span class="clause-num">1.1</span>
      <span class="clause-text">Diese Allgemeinen Geschäftsbedingungen (AGB) gelten für alle Verträge, die zwischen dem Kunden und dem Anbieter über die Nutzung der Online-Plattform <em>wertstapel.de</em> geschlossen werden.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">1.2</span>
      <span class="clause-text">Der Anbieter schließt ausschließlich Verträge mit Unternehmern im Sinne des § 14 BGB (Kaufleute, juristische Personen sowie Personengesellschaften, die in Ausübung ihrer gewerblichen oder selbständigen beruflichen Tätigkeit handeln). Der Abschluss von Verträgen mit Verbrauchern im Sinne des § 13 BGB ist ausgeschlossen. Der Kunde bestätigt beim Vertragsschluss durch aktive Markierung der entsprechenden Checkbox, dass er in unternehmerischer Eigenschaft handelt.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">1.3</span>
      <span class="clause-text">Soweit neben diesen AGB weitere Vertragsdokumente (insbesondere ein Auftragsverarbeitungsvertrag gemäß Art. 28 DSGVO) Vertragsbestandteil geworden sind, gehen deren Regelungen im Widerspruchsfall diesen AGB vor.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">1.4</span>
      <span class="clause-text">Von diesen AGB abweichende Geschäftsbedingungen des Kunden erkennt der Anbieter – vorbehaltlich einer ausdrücklichen schriftlichen Zustimmung – nicht an.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 2 &nbsp;Vertragsgegenstand, Leistungsumfang und Nutzungsrecht</h2>
    <div class="agb-clause">
      <span class="clause-num">2.1</span>
      <span class="clause-text">Der Anbieter betreibt die SaaS-Plattform <em>wertstapel.de</em>, die es dem Kunden ermöglicht, PDF-Dokumente von Wertpapier-Transaktionen in strukturierte Buchungsdatensätze zu konvertieren, die in DATEV Kanzlei-Rechnungswesen eingelesen werden können.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">2.2</span>
      <span class="clause-text">Der Anbieter stellt die Plattform als technischen Dienst bereit. Ein Anspruch auf ununterbrochene Verfügbarkeit besteht nicht; der Anbieter strebt jedoch eine Verfügbarkeit von 99 % im Jahresmittel an, gemessen außerhalb geplanter Wartungsfenster. Für planmäßige Wartungsarbeiten wird der Anbieter nach Möglichkeit Vorabankündigungen per E-Mail oder auf der Plattform vornehmen.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">2.3</span>
      <span class="clause-text">Der Anbieter erbringt die vertragsgemäßen Leistungen mit größtmöglicher Sorgfalt und Gewissenhaftigkeit nach dem jeweils aktuellen Stand der Technik.</span>
    </div>
    <div class="notice-box agb-clause">
      <span class="clause-num">2.4</span>
      <span class="clause-text"><strong>Wichtiger Hinweis – Buchungsvorschläge, keine Steuerberatung:</strong><br>Die vom System erzeugten Buchungsdatensätze stellen ausschließlich automatisiert generierte <em>Vorschläge</em> dar, die auf den vom Kunden hochgeladenen Dokumenten basieren. Sie ersetzen weder eine steuerrechtliche Prüfung noch eine steuerliche Beratung durch einen zugelassenen Steuerberater oder Wirtschaftsprüfer. Der Kunde ist verpflichtet, sämtliche erzeugten Buchungsvorschläge vor der Übernahme in seine Buchhaltungssoftware eigenverantwortlich auf Vollständigkeit und Richtigkeit zu prüfen. Der Anbieter erbringt keine Steuerberatungsleistungen im Sinne des Steuerberatungsgesetzes (StBerG).</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">2.5</span>
      <span class="clause-text">Der Anbieter räumt dem Kunden für die Dauer des Vertrags ein einfaches (nicht-ausschließliches), nicht übertragbares und nicht unterlizenzierbares Recht ein, die Plattform im Rahmen der erworbenen Leistung für eigene betriebliche Zwecke zu nutzen. Steuerberater, Steuerfachangestellte und Wirtschaftsprüfer sind berechtigt, die Plattform im Rahmen ihrer Mandatsbetreuung einzusetzen, sofern sie beim Vertragsschluss in dieser beruflichen Eigenschaft handeln. Der Kunde ist nicht berechtigt, die Plattform zu vervielfältigen, weiterzuveräußern oder Dritten anderweitig zugänglich zu machen.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 3 &nbsp;Mitwirkungspflichten des Kunden</h2>
    <div class="agb-clause">
      <span class="clause-num">3.1</span>
      <span class="clause-text">Es obliegt dem Kunden, die für die Leistungserbringung hochzuladenden Dokumente, Daten und sonstigen Inhalte vollständig und in lesbarer Qualität bereitzustellen. Für Fehler oder Unvollständigkeiten im Ergebnis, die auf unvollständigen, unlesbaren oder fehlerhaften Eingabedokumenten beruhen, trägt der Kunde die alleinige Verantwortung.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">3.2</span>
      <span class="clause-text">Der Kunde ist verpflichtet, seine Zugangsdaten zur Plattform vertraulich zu behandeln und vor dem Zugriff Dritter zu schützen. Bei Verdacht auf Missbrauch ist der Anbieter unverzüglich zu informieren.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 4 &nbsp;Vergütung und Zahlung</h2>
    <div class="agb-clause">
      <span class="clause-num">4.1</span>
      <span class="clause-text">Die Vergütung richtet sich nach dem zum Zeitpunkt der Bestellung gültigen Preismodell, das auf der Website des Anbieters ausgewiesen ist. Es gilt ausschließlich das Preismodell in der Fassung zum Zeitpunkt des Vertragsschlusses. Alle Preise verstehen sich zuzüglich der jeweils gesetzlich geschuldeten Umsatzsteuer.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">4.2</span>
      <span class="clause-text">Die Vergütung wird als <strong>Einmalzahlung im Voraus</strong> fällig. Pakete (Einzelexport, 5er-Paket, 20er-Paket) beinhalten eine festgelegte Anzahl von Exporten ohne zeitliches Verfalldatum. Die Jahresflat berechtigt zur unbegrenzten Nutzung für 12 Monate ab Kaufdatum und verlängert sich <strong>nicht automatisch</strong>. Bei vorzeitiger Neubuchung der Jahresflat werden die neuen 12 Monate Laufzeit an den bestehenden Zeitraum angehängt.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">4.3</span>
      <span class="clause-text">Die Zahlung wird über den Zahlungsdienstleister <strong>Stripe Payments Europe, Ltd.</strong> (The One Building, 1 Grand Canal Street Lower, Dublin 2, Irland) abgewickelt. Der Kaufbetrag wird einmalig zum Zeitpunkt der Bestellung eingezogen.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">4.4</span>
      <span class="clause-text">Steuerlich verwertbare Rechnungsbelege werden nach jedem Zahlungseingang automatisch per E-Mail an die vom Kunden hinterlegte E-Mail-Adresse übermittelt.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 5 &nbsp;Haftung und Freistellung</h2>
    <div class="agb-clause">
      <span class="clause-num">5.1</span>
      <span class="clause-text">Der Anbieter haftet aus jedem Rechtsgrund uneingeschränkt bei Vorsatz oder grober Fahrlässigkeit, bei vorsätzlicher oder fahrlässiger Verletzung des Lebens, des Körpers oder der Gesundheit, aufgrund eines Garantieversprechens (soweit diesbezüglich nichts anderes geregelt ist) sowie aufgrund zwingender gesetzlicher Haftung (insbesondere nach dem Produkthaftungsgesetz). Verletzt der Anbieter fahrlässig eine wesentliche Vertragspflicht, ist die Haftung auf den vertragstypischen, vorhersehbaren Schaden begrenzt. Wesentliche Vertragspflichten sind solche, deren Erfüllung die ordnungsgemäße Durchführung des Vertrags überhaupt erst ermöglicht und auf deren Einhaltung der Kunde regelmäßig vertrauen darf. Im Übrigen ist die Haftung des Anbieters ausgeschlossen.</span>
    </div>
    <div class="agb-clause notice-box">
      <span class="clause-num">5.2</span>
      <span class="clause-text"><strong>Haftungsausschluss für Buchungsvorschläge:</strong><br>Die Haftung des Anbieters für Schäden, die dadurch entstehen, dass der Kunde erzeugte Buchungsvorschläge ohne vorherige eigenverantwortliche Prüfung oder ohne Einbeziehung eines zugelassenen Steuerberaters in seine Buchhaltungssoftware übernimmt, ist ausgeschlossen, es sei denn, dem Anbieter ist Vorsatz oder grobe Fahrlässigkeit nachzuweisen. Die Gesamthaftung des Anbieters gegenüber dem Kunden ist, soweit gesetzlich zulässig, der Höhe nach auf die vom Kunden im letzten Vertragsjahr vor Eintritt des Schadensereignisses tatsächlich gezahlte Vergütung begrenzt.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">5.3</span>
      <span class="clause-text">Der Kunde stellt den Anbieter von jeglichen Ansprüchen Dritter frei, die gegen den Anbieter aufgrund von Verstößen des Kunden gegen diese AGB oder gegen geltendes Recht – insbesondere gegen das Steuerberatungsgesetz, datenschutzrechtliche Vorschriften oder Rechte Dritter – geltend gemacht werden.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 6 &nbsp;Vertragsdauer, Nutzungsende und Datenlöschung</h2>
    <div class="agb-clause">
      <span class="clause-num">6.1</span>
      <span class="clause-text"><strong>Pakete (Einzelexport, 5er-Paket, 20er-Paket):</strong> Der Vertrag endet mit vollständigem Verbrauch aller enthaltenen Exporte. Da es sich um Einmalzahlungen ohne wiederkehrende Vertragslaufzeit handelt, bedarf es keiner Kündigung. Nicht verbrauchte Exporte verfallen nicht und bleiben bis zur Nutzung gültig.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">6.2</span>
      <span class="clause-text"><strong>Jahresflat:</strong> Die Nutzungsberechtigung läuft <strong>12 Monate ab Kaufdatum</strong> und endet automatisch, ohne dass es einer Kündigung bedarf. Es erfolgt keine automatische Verlängerung. Bei vorzeitiger Neubuchung der Jahresflat werden die neuen 12 Monate an den noch laufenden Zeitraum angehängt.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">6.3</span>
      <span class="clause-text">Das Recht beider Parteien zur außerordentlichen Kündigung aus wichtigem Grund bleibt unberührt. Ein wichtiger Grund liegt für den Anbieter insbesondere vor bei missbräuchlicher Nutzung der Plattform, bei Verstößen gegen diese AGB oder bei Weitergabe von Zugangsdaten an nicht berechtigte Dritte.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">6.4</span>
      <span class="clause-text">Hochgeladene PDF-Dokumente werden unmittelbar nach erfolgreicher Verarbeitung, spätestens jedoch nach 24 Stunden, automatisch und unwiderruflich gelöscht. Erzeugte Exportdateien werden 24 Stunden nach Auslieferung automatisch gelöscht. Kontodaten werden nach Vertragsbeendigung innerhalb von 30 Tagen gelöscht, sofern keine gesetzlichen Aufbewahrungsfristen entgegenstehen (§ 147 AO: 10 Jahre für Rechnungsbelege).</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 7 &nbsp;Vertraulichkeit und Datenschutz</h2>
    <div class="agb-clause">
      <span class="clause-num">7.1</span>
      <span class="clause-text">Der Anbieter behandelt alle ihm im Zusammenhang mit dem Vertrag zur Kenntnis gelangenden Informationen und Daten streng vertraulich. Er verpflichtet sich, die Geheimhaltungspflicht sämtlichen Mitarbeitern und Subunternehmern aufzuerlegen, die Zugang zu vertragsrelevanten Informationen haben. Die Geheimhaltungspflicht gilt zeitlich unbegrenzt über die Dauer dieses Vertrages hinaus.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">7.2</span>
      <span class="clause-text">Der Anbieter verpflichtet sich, bei der Durchführung des Vertrags sämtliche einschlägigen datenschutzrechtlichen Vorschriften einzuhalten, insbesondere die DSGVO und das BDSG. Die Verarbeitung aller Kundendaten erfolgt ausschließlich auf Servern innerhalb der Europäischen Union.</span>
    </div>
    <div class="agb-clause notice-box">
      <span class="clause-num">7.3</span>
      <span class="clause-text"><strong>Auftragsverarbeitung (Art. 28 DSGVO):</strong><br>Soweit der Anbieter im Rahmen der Leistungserbringung personenbezogene Daten im Auftrag des Kunden verarbeitet, schließen die Parteien einen gesonderten Auftragsverarbeitungsvertrag (AVV) gemäß Art. 28 DSGVO. Dieser AVV ist zwingender Bestandteil des Vertragsverhältnisses. Der Kunde bestätigt mit Vertragsschluss, den AVV in der zum Zeitpunkt des Vertragsschlusses auf der Website des Anbieters abrufbaren Fassung gelesen und akzeptiert zu haben.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 8 &nbsp;Schlussbestimmungen</h2>
    <div class="agb-clause">
      <span class="clause-num">8.1</span>
      <span class="clause-text">Es gilt das Recht der Bundesrepublik Deutschland unter Ausschluss des UN-Kaufrechts (CISG).</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">8.2</span>
      <span class="clause-text">Sollte eine Bestimmung dieser AGB unwirksam sein oder werden, so wird die Gültigkeit der übrigen AGB hiervon nicht berührt. An die Stelle der unwirksamen Bestimmung tritt, soweit möglich, eine dieser wirtschaftlich möglichst nahekommende wirksame Regelung.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">8.3</span>
      <span class="clause-text">Sofern der Kunde Kaufmann, juristische Person des öffentlichen Rechts oder öffentlich-rechtliches Sondervermögen ist oder keinen allgemeinen Gerichtsstand in Deutschland hat, vereinbaren die Parteien den Sitz des Anbieters (Düsseldorf) als ausschließlichen Gerichtsstand für sämtliche Streitigkeiten aus diesem Vertragsverhältnis.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">8.4</span>
      <span class="clause-text">Der Anbieter ist berechtigt, diese AGB aus sachlich gerechtfertigten Gründen zu ändern. Bestandskunden werden hierüber spätestens <strong>vier Wochen</strong> vor Inkrafttreten der Änderung per E-Mail benachrichtigt. Sofern der Bestandskunde nicht innerhalb der gesetzten Frist widerspricht, gilt seine Zustimmung zur Änderung als erteilt.</span>
    </div>
  </div>

  <div class="agb-section">
    <h2>§ 9 &nbsp;Informationen zur Online-Streitbeilegung</h2>
    <div class="agb-clause">
      <span class="clause-num">9.1</span>
      <span class="clause-text">Die Europäische Kommission stellt eine Plattform zur Online-Streitbeilegung (OS-Plattform) bereit, erreichbar unter: <a href="https://ec.europa.eu/consumers/odr" target="_blank" rel="noopener noreferrer">https://ec.europa.eu/consumers/odr</a>.</span>
    </div>
    <div class="agb-clause">
      <span class="clause-num">9.2</span>
      <span class="clause-text">Der Anbieter ist weder verpflichtet noch bereit, an Streitbeilegungsverfahren vor einer Verbraucherschlichtungsstelle teilzunehmen, da ausschließlich Verträge mit Unternehmern geschlossen werden (§ 1.2 dieser AGB).</span>
    </div>
  </div>

  <div class="agb-footer">
    <span>Stand: Mai 2026</span>
    <span>Spark Innovation GmbH &middot; Düsseldorf</span>
  </div>
</div>` }} />
    </LegalLayout>
  )
}
