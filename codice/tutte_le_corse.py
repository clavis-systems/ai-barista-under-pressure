"""Tutte le corse della prova del bancone, una dopo l'altra (PREMESSA_BANCONE.md, sezione 10, punto 5).

uso: python tutte_le_corse.py MODELLO [MODELLO ...]

Per ogni modello lancia corsa.py --modello:
- se restano prove rimandate la rilancia, al massimo 3 volte, a 5 minuti di distanza;
- al limite d'uso, o con il servizio che non risponde, aspetta 30 minuti e riprova, al massimo 12 volte (6 ore);
- se Claude Code o Ollama non rispondono all'avvio si ferma;
- se la corsa è finita (codice 0) o restano solo prove rimandate dopo tutti i rilanci (codice 4), lancia corsa.py
  --chiudi: le prove mai riuscite e rimandate almeno 3 volte diventano perse. Dopo un'interruzione del servizio
  (codici 3 e 5) no: le prove mancanti restano da fare, e una corsa rilanciata a mano le rifà.
Un modello che non finisce resta incompleto e si passa al successivo. Finché lavora, il PC non va in sospensione.
"""

from __future__ import annotations

import subprocess
import sys
import time

from comune import QUI, RISULTATI, adesso, prendi_lucchetto, rilascia_lucchetto

RILANCI_ERRORI = 3
ATTESA_ERRORI_S = 300
RILANCI_LIMITE = 12
ATTESA_LIMITE_S = 1800
LUCCHETTO_TUTTE = RISULTATI / ".tutte_le_corse_in_corso"


def tieni_sveglio() -> None:
    """Su Windows chiede di non andare in sospensione finché questo processo lavora. Non cambia impostazioni e finisce
    da sola quando il processo termina."""
    if sys.platform == "win32":
        import ctypes
        ctypes.windll.kernel32.SetThreadExecutionState(0x80000000 | 0x00000001)  # ES_CONTINUOUS | ES_SYSTEM_REQUIRED


def corsa(*argomenti: str) -> int:
    return subprocess.run([sys.executable, str(QUI / "corsa.py"), *argomenti], cwd=QUI).returncode


def corri(modello: str) -> int:
    """Le corse di un modello, con i rilanci; restituisce l'ultimo codice d'uscita."""
    errori = limiti = 0
    while True:
        codice = corsa("--modello", modello)
        if codice == 0:
            print(f"[{adesso()}] {modello}: corsa completa", flush=True)
            return codice
        if codice == 3 and limiti < RILANCI_LIMITE:
            limiti += 1
            print(f"[{adesso()}] {modello}: pausa, riprovo fra {ATTESA_LIMITE_S // 60} minuti "
                  f"({limiti}/{RILANCI_LIMITE})", flush=True)
            time.sleep(ATTESA_LIMITE_S)
            continue
        if codice == 4 and errori < RILANCI_ERRORI:
            errori += 1
            print(f"[{adesso()}] {modello}: prove rimandate, rilancio fra {ATTESA_ERRORI_S // 60} minuti "
                  f"({errori}/{RILANCI_ERRORI})", flush=True)
            time.sleep(ATTESA_ERRORI_S)
            continue
        print(f"[{adesso()}] {modello}: mi fermo, corsa incompleta (codice {codice})", flush=True)
        return codice


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    if len(sys.argv) < 2:
        sys.exit(__doc__)
    prendi_lucchetto("prova del bancone: tutte le corse", LUCCHETTO_TUTTE)
    try:
        tieni_sveglio()
        esiti = {}
        for m in sys.argv[1:]:
            esiti[m] = corri(m)
            if esiti[m] in (0, 4):
                corsa("--modello", m, "--chiudi")
        print(f"[{adesso()}] fine delle corse, ultimi codici: {esiti}", flush=True)
    finally:
        rilascia_lucchetto(LUCCHETTO_TUTTE)


if __name__ == "__main__":
    main()
