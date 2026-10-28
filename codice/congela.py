"""Congelamento della prova del bancone: impronte SHA-256 di premessa, intervista, dati e codice.

uso:
  python congela.py            scrive CONGELATA.txt (si rifiuta se esiste già)
  python congela.py --verifica controlla che i file siano identici al congelamento

Le impronte si calcolano sul testo con gli a capo normalizzati (CRLF -> LF), come negli studi precedenti.
"""

from __future__ import annotations

import hashlib
import subprocess
import sys
import time

from comune import QUI, STUDIO

CONGELATA = STUDIO / "CONGELATA.txt"
FILE_FISSI = ["PREMESSA_BANCONE.md", "INTERVISTA.md", "dati/situazioni.json", "dati/copertura.json"]


def elenco() -> list[str]:
    return FILE_FISSI + sorted(f"codice/{p.name}" for p in QUI.glob("*.py"))


def impronta(rel: str) -> str:
    return hashlib.sha256((STUDIO / rel).read_bytes().replace(b"\r\n", b"\n")).hexdigest()


def scrivi() -> None:
    if CONGELATA.exists():
        sys.exit(f"{CONGELATA} esiste già: un congelamento non si riscrive")
    mancanti = [r for r in elenco() if not (STUDIO / r).exists()]
    if mancanti:
        sys.exit(f"mancano file da congelare: {mancanti}")
    try:
        commit = subprocess.run(["git", "-c", "safe.directory=*", "rev-parse", "HEAD"], cwd=STUDIO,
                                capture_output=True, text=True, check=True).stdout.strip()
    except (OSError, subprocess.CalledProcessError):
        commit = "sconosciuto"
    righe = [f"# Congelata il {time.strftime('%d/%m/%Y %H:%M:%S')} (orologio di sistema); commit precedente {commit}",
             "# Prima di qualunque prova che conti. Verifica: python codice/congela.py --verifica",
             "# Impronte SHA-256 sul testo con a capo LF (CRLF normalizzati)."]
    righe += [f"{impronta(r)}  {r}" for r in elenco()]
    CONGELATA.write_text("\n".join(righe) + "\n", encoding="utf-8", newline="\n")
    print(f"scritto {CONGELATA}: {len(elenco())} file")


def verifica(stampa: bool = True) -> bool:
    if not CONGELATA.exists():
        if stampa:
            print("CONGELATA.txt assente")
        return False
    attese = {}
    for r in CONGELATA.read_text(encoding="utf-8").splitlines():
        if r and not r.startswith("#"):
            sha, rel = r.split("  ", 1)
            attese[rel] = sha
    diversi = [rel for rel, sha in attese.items() if not (STUDIO / rel).exists() or impronta(rel) != sha]
    nuovi = [rel for rel in elenco() if rel not in attese]
    if stampa:
        if diversi or nuovi:
            print(f"DIVERSI dal congelamento: {diversi}; NUOVI non congelati: {nuovi}")
        else:
            print(f"ok: {len(attese)} file identici al congelamento")
    return not diversi and not nuovi


if __name__ == "__main__":
    if "--verifica" in sys.argv:
        sys.exit(0 if verifica() else 1)
    scrivi()
