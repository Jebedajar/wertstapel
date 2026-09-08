"""
einrichtungsblatt.py — Erzeugt das PDF, das der Mandant an seine Kanzlei gibt.

Zwei Teile:
  1. Die Konten, die einmalig anzulegen sind (Status "anzulegen" in der
     Kontenmatrix). Nur die Instrumentenklassen, die im Export tatsächlich
     vorkommen — wer keine Anleihen hält, soll auch keine Anleihenkonten
     anlegen.
  2. Eine Übersicht, auf welche Standardkonten Wertstapel bucht, damit die
     Kanzlei die Zuordnung nachvollziehen kann, ohne den Stapel zu öffnen.

Fällt reportlab aus, wird still auf CSV zurückgefallen — ein fehlendes PDF
darf keinen Export scheitern lassen.
"""
from __future__ import annotations

import csv
from datetime import date
from pathlib import Path
from typing import List, Optional

from konten import Kontenmatrix, KontenKontext, KontoNichtDefiniert

TITEL = "Wertstapel — Kontenblatt für die Kanzlei"

EINLEITUNG = (
    "Wertstapel wandelt Wertpapierabrechnungen in einen DATEV-Buchungsstapel "
    "(Format DTVF v7.00) um. Die Buchungen folgen der Buchwertabgang-Methode "
    "nach DATEV-Dokument 5300857 und trennen vier Instrumentenklassen, weil "
    "§ 8b KStG nur für Aktien gilt, für Investmentanteile dagegen die "
    "Teilfreistellung nach § 20 InvStG maßgeblich ist."
)

HINWEIS_ANLEGEN = (
    "Für die folgenden Sachverhalte sieht der Standardkontenrahmen kein Konto "
    "vor. Diese Konten sind einmalig im Mandanten anzulegen und mit dem "
    "jeweiligen Kontenzweck zu versehen (DATEV-Dokument 1004273 für die "
    "Kontenzwecke des Investmentsteuergesetzes, Dokument 1037312 zum Anlegen "
    "und Zuordnen von Konten). Die Nummern sind Vorschläge aus freien "
    "Nummernkreisen und können durch kanzleieigene ersetzt werden."
)

HINWEIS_MARKER = (
    "Buchungstexte können Marker als Präfix tragen. Sie kennzeichnen "
    "Sachverhalte, die Wertstapel bewusst nicht selbst entscheidet:"
)

MARKER_ERKLAERUNG = [
    ("#TF80# #TF60# #TF40# #TF0#",
     "Investmentanteil. Der Marker nennt den für eine Körperschaft "
     "maßgeblichen Teilfreistellungssatz nach der erkannten Fondskategorie. "
     "Gebucht wird stets der ungekürzte Betrag."),
    ("#TF?#",
     "Fondskategorie nicht ermittelbar. Buchung auf dem Sammelkonto "
     "„Kategorie unbestimmt“. Bei Interactive Brokers der Regelfall, weil "
     "dort keine Teilfreistellung ausgewiesen wird."),
    ("#DIV#",
     "Dividende. Ob Streubesitz nach § 8b Abs. 4 KStG oder Schachtel"
     "beteiligung vorliegt, geht aus den Bankdaten nicht hervor."),
    ("#ADR#",
     "American Depositary Receipt. Gebucht wie eine Aktie unter § 8b KStG; "
     "höchstrichterlich nicht entschieden."),
    ("#AK-PRÜFEN#",
     "Anschaffungskosten nicht oder nur teilweise ableitbar, etwa bei "
     "Altbeständen aus der Zeit vor dem Exportzeitraum."),
    ("#VORABP#",
     "Auf diese ISIN wurde im Zeitraum Vorabpauschale versteuert."),
    ("#CHECK#",
     "Seltener Sachverhalt, der nicht automatisch gebucht wird: "
     "Einlagenrückgewähr nach § 27 KStG, Split, Spin-off, Fusion."),
    ("#KLASSE#",
     "Instrumentenklasse nicht sicher erkannt."),
]

# Zwecke für die Übersicht "so wird gebucht"
UEBERSICHT = [
    ("Verrechnungskonto des Depots", "bank", None),
    ("Aktien — Bestand", "bestand", "aktie"),
    ("Aktien — Veräußerungserlös bei Gewinn", ("aktie", "erloes_gewinn"), None),
    ("Aktien — Buchwertabgang bei Gewinn", ("aktie", "buchwert_gewinn"), None),
    ("Aktien — Veräußerungserlös bei Verlust", ("aktie", "erloes_verlust"), None),
    ("Aktien — Buchwertabgang bei Verlust", ("aktie", "buchwert_verlust"), None),
    ("Aktien — Veräußerungskosten bei Gewinn", ("aktie", "kosten_gewinn"), None),
    ("Aktien — Veräußerungskosten bei Verlust", ("aktie", "kosten_verlust"), None),
    ("Aktien — Dividende", ("aktie", "dividende"), None),
    ("Investmentanteile — Bestand", "bestand", "fonds"),
    ("Anleihen — Bestand", "bestand", "anleihe"),
    ("Anleihen — Abgangsergebnis Gewinn", ("anleihe", "abgang_gewinn"), None),
    ("Anleihen — Abgangsergebnis Verlust", ("anleihe", "abgang_verlust"), None),
    ("Anleihen — Zinsertrag und erhaltene Stückzinsen", ("anleihe", "zinsertrag"), None),
    ("Anleihen — gezahlte Stückzinsen (antizipativ)", ("anleihe", "stueckzinsen_aktiv"), None),
    ("Verbriefte Derivate — Bestand", "bestand", "derivat_verbrieft"),
    ("Anrechenbare Kapitalertragsteuer", "gemeinsam", "kapest"),
    ("Anrechenbarer Solidaritätszuschlag", "gemeinsam", "solz"),
    ("Anrechenbare ausländische Quellensteuer", "gemeinsam", "quellensteuer_anrechenbar"),
    ("Verwahrentgelt", "gemeinsam", "verwahrentgelt"),
    ("Depot- und Kontoführungsgebühren", "gemeinsam", "nebenkosten_geldverkehr"),
    ("Sonstige Zinserträge", "gemeinsam", "zinsertrag_sonstige"),
    ("Zinsaufwendungen", "gemeinsam", "zinsaufwand"),
]


def _uebersicht_zeilen(matrix: Kontenmatrix, ctx: KontenKontext,
                       klassen: List[str]) -> List[tuple]:
    zeilen = []
    for label, zweck, arg in UEBERSICHT:
        try:
            if zweck == "bank":
                nr = matrix.bank(ctx)
            elif zweck == "bestand":
                if arg not in klassen:
                    continue
                nr = matrix.bestand(arg, ctx)
            elif zweck == "gemeinsam":
                nr = matrix.gemeinsam(arg, ctx)
            else:
                klasse, z = zweck
                if klasse not in klassen:
                    continue
                nr = matrix.erfolg(klasse, z, ctx)
        except (KontoNichtDefiniert, KeyError):
            continue
        zeilen.append((nr, label))

    if "fonds" in klassen:
        for zw, txt in (("ausschuettung", "Ausschüttung"),
                        ("abgang_gewinn", "Abgangsergebnis Gewinn"),
                        ("abgang_verlust", "Abgangsergebnis Verlust")):
            for kat, katname in (("aktienfonds", "Aktienfonds"),
                                 ("mischfonds", "Mischfonds"),
                                 ("immobilienfonds", "Immobilienfonds"),
                                 ("rentenfonds_sonstige", "Renten-/sonstige Fonds"),
                                 ("unbestimmt", "Kategorie unbestimmt")):
                try:
                    nr = matrix.fonds(zw, kat, ctx)
                except (KontoNichtDefiniert, KeyError):
                    continue
                zeilen.append((nr, f"Investmentanteile — {txt}, {katname}"))
        for zw, txt in (("veraeusserungskosten", "Veräußerungskosten"),
                        ("vorabpauschale_ertrag", "Ertrag Vorabpauschale (Steuerstapel)"),
                        ("ausgleichsposten_aktiv", "Aktiver Ausgleichsposten InvStG"),
                        ("ausgleichsposten_aufloesung_verlust", "Auflösung Ausgleichsposten")):
            try:
                nr = matrix.fonds(zw, None, ctx)
            except (KontoNichtDefiniert, KeyError):
                continue
            zeilen.append((nr, f"Investmentanteile — {txt}"))

    if "derivat_verbrieft" in klassen:
        for zw, txt in (("ertrag", "Ertrag § 15 Abs. 4 S. 3 EStG"),
                        ("verlust", "Verlust § 15 Abs. 4 S. 3 EStG")):
            try:
                zeilen.append((matrix.erfolg("derivat_verbrieft", zw, ctx),
                               f"Verbriefte Derivate — {txt}"))
            except (KontoNichtDefiniert, KeyError):
                continue

    return sorted(zeilen, key=lambda z: z[0])


def schreibe_csv(pfad: Path, matrix: Kontenmatrix, ctx: KontenKontext,
                 klassen: List[str], depots: int = 1) -> int:
    konten = matrix.anzulegende_konten(ctx, klassen, depots)
    with open(pfad, "w", encoding="utf-8-sig", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow([TITEL])
        w.writerow([f"{ctx.kontenrahmen}, "
                    f"{'Umlaufvermögen' if ctx.vermoegensart == 'UV' else 'Anlagevermögen'}"])
        w.writerow([])
        w.writerow(["Anzulegen", "Verwendung"])
        for k in konten:
            w.writerow([k.nummer, k.bezeichnung])
        w.writerow([])
        w.writerow(["Verwendetes Standardkonto", "Sachverhalt"])
        for nr, label in _uebersicht_zeilen(matrix, ctx, klassen):
            w.writerow([nr, label])
    return len(konten)


def schreibe_pdf(pfad: Path, matrix: Kontenmatrix, ctx: KontenKontext,
                 klassen: List[str], mandant: str = "",
                 verrechnungskonto: Optional[str] = None,
                 depots: int = 1) -> int:
    """Rückgabe: Anzahl anzulegender Konten. Bei fehlendem reportlab wird
    stattdessen eine CSV mit gleichem Stamm geschrieben."""
    try:
        from reportlab.lib import colors
        from reportlab.lib.pagesizes import A4
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.lib.units import mm
        from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer,
                                        Table, TableStyle)
    except ImportError:
        return schreibe_csv(pfad.with_suffix(".csv"), matrix, ctx, klassen, depots)

    konten = matrix.anzulegende_konten(ctx, klassen, depots)
    st = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=st["BodyText"], fontSize=9,
                          leading=12.5, spaceAfter=6)
    h1 = ParagraphStyle("h1", parent=st["Heading1"], fontSize=16,
                        textColor=colors.HexColor("#1F3864"), spaceAfter=2)
    h2 = ParagraphStyle("h2", parent=st["Heading2"], fontSize=11.5,
                        textColor=colors.HexColor("#1F3864"),
                        spaceBefore=14, spaceAfter=6)
    klein = ParagraphStyle("klein", parent=body, fontSize=8, leading=10.5)

    doc = SimpleDocTemplate(str(pfad), pagesize=A4,
                            leftMargin=20 * mm, rightMargin=20 * mm,
                            topMargin=18 * mm, bottomMargin=18 * mm,
                            title=TITEL, author="Wertstapel")
    f = []
    f.append(Paragraph(TITEL, h1))
    kopf = (f"{ctx.kontenrahmen} · "
            f"{'Umlaufvermögen' if ctx.vermoegensart == 'UV' else 'Anlagevermögen'} · "
            f"Stand {date.today().strftime('%d.%m.%Y')}")
    if mandant:
        kopf = f"Mandant {mandant} · " + kopf
    f.append(Paragraph(kopf, klein))
    f.append(Spacer(1, 8))
    f.append(Paragraph(EINLEITUNG, body))

    if verrechnungskonto:
        f.append(Paragraph(
            f"Das Verrechnungskonto des Depots ist auf <b>{verrechnungskonto}</b> "
            f"gebucht. Es ist ein eigenes Bankkonto neben dem laufenden "
            f"Geschäftskonto und sollte im Kontenplan getrennt geführt werden.",
            body))

    def tabelle(daten, breiten):
        t = Table(daten, colWidths=breiten, repeatRows=1)
        t.setStyle(TableStyle([
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 8.5),
            ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#E8ECF2")),
            ("VALIGN", (0, 0), (-1, -1), "TOP"),
            ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#B8C0CC")),
            ("LEFTPADDING", (0, 0), (-1, -1), 5),
            ("RIGHTPADDING", (0, 0), (-1, -1), 5),
            ("TOPPADDING", (0, 0), (-1, -1), 3),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1),
             [colors.white, colors.HexColor("#F6F8FA")]),
        ]))
        return t

    f.append(Paragraph("Einmalig anzulegende Konten", h2))
    if konten:
        f.append(Paragraph(HINWEIS_ANLEGEN, body))
        daten = [["Konto", "Verwendung"]] + [
            [k.nummer, Paragraph(k.bezeichnung, klein)] for k in konten]
        f.append(tabelle(daten, [22 * mm, 148 * mm]))
    else:
        f.append(Paragraph(
            "Für die im Export vorkommenden Sachverhalte sind keine "
            "zusätzlichen Konten erforderlich.", body))

    f.append(Paragraph("Verwendete Standardkonten", h2))
    f.append(Paragraph(
        "Diese Konten sind im Kontenrahmen belegt und müssen nicht angelegt "
        "werden. Die Übersicht zeigt, welcher Sachverhalt auf welchem Konto "
        "landet.", body))
    zeilen = _uebersicht_zeilen(matrix, ctx, klassen)
    daten = [["Konto", "Sachverhalt"]] + [
        [nr, Paragraph(label, klein)] for nr, label in zeilen]
    f.append(tabelle(daten, [22 * mm, 148 * mm]))

    f.append(Paragraph("Marker in den Buchungstexten", h2))
    f.append(Paragraph(HINWEIS_MARKER, body))
    daten = [["Marker", "Bedeutung"]] + [
        [Paragraph(f"<b>{m}</b>", klein), Paragraph(t, klein)]
        for m, t in MARKER_ERKLAERUNG]
    f.append(tabelle(daten, [42 * mm, 128 * mm]))

    f.append(Spacer(1, 10))
    f.append(Paragraph(
        "Erzeugt von Wertstapel, wertstapel.de — Betreiber: Spark Innovation "
        "GmbH, Düsseldorf. Die Kontenvorschläge sind mit einer Steuerberaterin "
        "abgestimmt, ersetzen aber keine Prüfung im Einzelfall.", klein))

    doc.build(f)
    return len(konten)
