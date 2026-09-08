"""
flatex_jahr.py — Koordinator für den Flatex-Jahresmodus.

Der Jahresmodus verarbeitet eine Dokumentenkombination statt einer
Einzeldatei:

    Erträgnisaufstellung (PDF)  →  Verkäufe (mit korrektem A-Wert),
                                   Dividenden, Ausschüttungen, Stornos
    Kontoumsätze (CSV, 1..n)    →  Käufe, Verwahrentgelt, Zinsen,
                                   Vorabpauschale-Steuer, Depot-Zuordnung

Reihenfolge ist zwingend: erst die CSVs (sie bauen Registry und TA-Index
auf), dann das PDF (es braucht beides für Depot-Zuordnung und die Trennung
von Anschaffungs- und Veräußerungskosten).

Aufruf aus run.py:

    from flatex_jahr import verarbeite_jahresmodus
    ergebnis = verarbeite_jahresmodus(pdf_pfad, csv_pfade)
"""

from dataclasses import dataclass, field
from decimal import Decimal
from typing import List, Optional, Dict
from collections import Counter

from flatex_jahr_types import Beleg, UngebuchterBeleg, IgnoredPage
from depot_registry import DepotRegistry, SPLIT_BESTANDSKONTO
import parser_flatex_kontoumsaetze as pk
import parser_flatex_ertraegnis as pe


@dataclass
class JahresErgebnis:
    belege: List[Beleg] = field(default_factory=list)
    ungebucht: List[UngebuchterBeleg] = field(default_factory=list)
    ignoriert: List[IgnoredPage] = field(default_factory=list)
    registry: Optional[DepotRegistry] = None
    warnungen: List[str] = field(default_factory=list)
    vorabpauschalen: List = field(default_factory=list)

    def protokoll(self) -> str:
        z = []
        if self.registry:
            z.append(self.registry.protokoll())
        z.append("")
        typen = Counter(b.typ for b in self.belege)
        z.append(f"Belege gesamt: {len(self.belege)}")
        for t, n in sorted(typen.items()):
            z.append(f"  {t:24} {n:4}")

        quellen = Counter(b.depot_quelle for b in self.belege)
        z.append("")
        z.append("Depot-Zuordnung nach Quelle:")
        for q, n in sorted(quellen.items(), key=lambda x: -x[1]):
            z.append(f"  {q:24} {n:4}")

        if self.registry and self.registry.ist_multidepot:
            je_depot = Counter(b.depot or "— unbestimmt —" for b in self.belege)
            z.append("")
            z.append("Belege je Depot:")
            for d, n in sorted(je_depot.items()):
                z.append(f"  {d:24} {n:4}")

        offen = [b for b in self.belege if b.depot_quelle == "unbestimmt"]
        if offen:
            z.append("")
            z.append(f"ACHTUNG — {len(offen)} Beleg(e) ohne eindeutiges Depot "
                     "(#DEPOT-PRÜFEN#):")
            for b in offen:
                z.append(f"  TA {b.auftragsnummer}  {b.isin}  {b.wertpapierbezeichnung[:40]}")

        ak = [b for b in self.belege if b.ak_unvollstaendig]
        if ak:
            z.append("")
            z.append(f"ACHTUNG — {len(ak)} Verkauf/Verkäufe mit ungetrennten "
                     "Kosten (#AK-PRÜFEN#):")
            for b in ak:
                z.append(f"  TA {b.auftragsnummer}  {b.isin}")

        if self.ungebucht:
            z.append("")
            z.append(f"Nicht automatisch gebucht: {len(self.ungebucht)}")
            for u in self.ungebucht:
                z.append(f"  [{u.typ}] {u.isin or '—'} {u.bezeichnung[:34]:34} {u.grund[:50]}")

        if self.ignoriert:
            z.append("")
            z.append(f"Übersprungene Seiten/Bereiche: {len(self.ignoriert)}")
            for i in self.ignoriert:
                z.append(f"  Seite {i.seite}: [{i.typ}] {i.grund}")

        if self.vorabpauschalen:
            z.append("")
            z.append("Vorabpauschalen — NICHT gebucht, für die "
                     "Steuererklärung (§ 17 InvStG):")
            je_isin: Dict[str, list] = {}
            for v in self.vorabpauschalen:
                je_isin.setdefault(v.isin, []).append(v)
            summe_ertrag = summe_steuer = Decimal("0")
            for isin in sorted(je_isin):
                gruppe = je_isin[isin]
                ertrag = sum(v.betrag for v in gruppe)
                steuer = sum(v.steuer for v in gruppe)
                summe_ertrag += ertrag
                summe_steuer += steuer
                bez = gruppe[0].bezeichnung[:26]
                depots = {v.depot for v in gruppe if v.depot}
                dep = f"  [{', '.join(sorted(depots))}]" if depots else ""
                z.append(f"  {isin}  {bez:26} fiktiver Ertrag {ertrag:>9} EUR"
                         f"   Steuer {steuer:>7} EUR{dep}")
            z.append(f"  {'SUMME':<14}{'':26} {' '*16}{summe_ertrag:>9} EUR"
                     f"   {' '*7}{summe_steuer:>7} EUR")
            betroffen = [b for b in self.belege if "#VORABP#" in b.wertpapierbezeichnung]
            if betroffen:
                z.append(f"  → {len(betroffen)} Verkauf/Verkäufe mit Marker "
                         "#VORABP# gekennzeichnet.")
            z.append("  → Die gezahlte Steuer ist als Abfluss auf 1780 gebucht. "
                     "Der fiktive Ertrag ist NICHT gebucht (§ 255 HGB).")
            z.append("  → OFFEN: jahresübergreifende Kumulierung — Verkäufe in "
                     "Folgejahren benötigen die Vorabpauschalen der Vorjahre, "
                     "die in diesem Dokument nicht enthalten sind.")

        for w in self.warnungen:
            z.append(f"WARNUNG: {w}")
        return "\n".join(z)


def verarbeite_jahresmodus(
    pdf_pfad: Optional[str],
    csv_pfade: Optional[List[str]] = None,
    konten_overrides: Optional[Dict[str, Dict[str, int]]] = None,
    split_bestandskonto: Optional[bool] = None,
) -> JahresErgebnis:
    """
    konten_overrides:     {auftraggeberkonto: {"bank": 1801, "bestand": 1510}}
                          für Mandanten mit belegten Standardkonten.
    split_bestandskonto:  None = Modulvorgabe aus depot_registry verwenden
                          (Standard: eigenes Bestandskonto je Depot).
    """
    csv_pfade = csv_pfade or []
    if split_bestandskonto is None:
        split_bestandskonto = SPLIT_BESTANDSKONTO
    erg = JahresErgebnis()

    registry = DepotRegistry(
        overrides=konten_overrides,
        split_bestand=split_bestandskonto,
    )

    # ── Schritt 1: CSVs ─────────────────────────────────────────
    ta_index: Dict[int, dict] = {}
    if csv_pfade:
        belege, ungebucht, registry, ta_index = pk.parse_csvs(csv_pfade, registry)
        erg.belege.extend(belege)
        erg.ungebucht.extend(ungebucht)
    else:
        erg.warnungen.append(
            "Keine Kontoumsätze-CSV übergeben — Käufe fehlen vollständig, "
            "Anschaffungs-/Veräußerungskosten nicht trennbar, "
            "Depot-Zuordnung nicht möglich.")

    # ── Schritt 2: PDF ──────────────────────────────────────────
    if pdf_pfad:
        p_belege, p_ungebucht, ignoriert, isin_namen, vorabp = pe.parse_pdf(
            pdf_pfad, ta_index=ta_index, registry=registry)
        erg.vorabpauschalen = vorabp
        erg.belege.extend(p_belege)
        erg.ungebucht.extend(p_ungebucht)
        erg.ignoriert.extend(ignoriert)
        # WP-Namen in die CSV-Belege (Käufe) nachtragen
        pk.namen_aus_ertraegnis_nachtragen(erg.belege, isin_namen)
    else:
        erg.warnungen.append(
            "Keine Erträgnisaufstellung übergeben — Verkäufe und Erträge fehlen.")

    registry.finalisieren()
    erg.registry = registry

    # ── Plausibilität ───────────────────────────────────────────
    if registry.ist_multidepot and not csv_pfade:
        erg.warnungen.append("Mehrere Depots erkannt, aber keine CSVs vorhanden.")
    ohne_beleg = [b for b in erg.belege
                  if b.depot_quelle == "einzeldepot-ohne-beleg"]
    if ohne_beleg:
        erg.warnungen.append(
            f"{len(ohne_beleg)} Vorgang/Vorgänge aus der Erträgnisaufstellung "
            f"tauchen in den hochgeladenen Kontoumsätzen nicht auf. Es ist nur "
            f"ein Depot bekannt — wahrscheinlich fehlt der Kontoumsätze-Export "
            f"eines weiteren Unterdepots. Diese Belege sind mit #DEPOT-PRÜFEN# "
            f"markiert.")
    if registry.anzahl > len(csv_pfade) and csv_pfade:
        erg.warnungen.append(
            f"{registry.anzahl} Depots erkannt, aber nur {len(csv_pfade)} CSV(s) "
            "hochgeladen — möglicherweise fehlt ein Unterdepot-Export.")

    erg.belege.sort(key=lambda b: (b.schlusstag, b.auftragsnummer))
    return erg
