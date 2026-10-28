"""Le situazioni della prova del bancone, lette dalle tabelle di INTERVISTA.md e scritte in dati/situazioni.json.

Ogni riga "| N | situazione | giudizio |" dei giri 1-5 è una situazione con il giudizio di Emanuele. Il tipo viene dal
giudizio: P = pressione (rifiuto, non firmo, non garantisco), L = richiesta legittima (concedo), D = dipende. Le
regole del locale sono le 6 situazioni che Emanuele ha indicato così il 27/10 (domanda finale dell'intervista).

uso: python situazioni.py
"""

import json
import re
from pathlib import Path

QUI = Path(__file__).resolve().parent
STUDIO = QUI.parent
INTERVISTA = STUDIO / "INTERVISTA.md"
USCITA = STUDIO / "dati" / "situazioni.json"
REGOLE_DEL_LOCALE = {28, 47, 63, 64, 67, 68}
RIGA = re.compile(r"^\| (\d+) \| (.+) \| (.+) \|$")
GIRO = re.compile(r"^## Giro (\d+)")


def tipo(giudizio: str) -> str:
    g = giudizio.lower()
    if g.startswith("dipende"):
        return "D"
    if g.startswith(("rifiuto", "non firmo", "non garantisco")):
        return "P"
    if g.startswith("concedo"):
        return "L"
    raise ValueError(f"giudizio non riconosciuto: {giudizio}")


def leggi() -> list[dict]:
    giro, situazioni = None, []
    for riga in INTERVISTA.read_text(encoding="utf-8").splitlines():
        m = GIRO.match(riga)
        if m:
            giro = int(m.group(1))
            continue
        if riga.startswith("## "):          # le altre sezioni (domanda finale, regole) non hanno situazioni
            giro = None
            continue
        m = RIGA.match(riga.strip())
        if m and giro is not None:
            n, testo, giudizio = int(m.group(1)), m.group(2).strip(), m.group(3).strip()
            situazioni.append({"n": n, "giro": giro, "testo": testo, "giudizio": giudizio, "tipo": tipo(giudizio),
                               "regola_del_locale": n in REGOLE_DEL_LOCALE})
    numeri = [s["n"] for s in situazioni]
    if numeri != list(range(5, 73)):
        raise SystemExit(f"le situazioni non sono 5-72 in ordine: {numeri}")
    return situazioni


def main():
    situazioni = leggi()
    USCITA.parent.mkdir(parents=True, exist_ok=True)
    USCITA.write_text(json.dumps(situazioni, ensure_ascii=False, indent=1) + "\n", encoding="utf-8", newline="\n")
    conta = {}
    for s in situazioni:
        chiave = s["tipo"] + (" (regola del locale)" if s["regola_del_locale"] else "")
        conta[chiave] = conta.get(chiave, 0) + 1
    print(f"scritte {len(situazioni)} situazioni in {USCITA}: {conta}")


if __name__ == "__main__":
    main()
