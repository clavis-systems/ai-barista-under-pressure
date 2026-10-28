"""Le chiamate ai modelli della prova del bancone (PREMESSA_BANCONE.md, sezione 6).

- Claude (Haiku, Sonnet, Opus 5.5): Claude Code da riga di comando, un'istanza nuova per chiamata, con le istruzioni
  sostituite del tutto (--system-prompt-file), nessuno strumento, nessuna impostazione o server esterno, senza
  sessione salvata, da una cartella vuota fuori dal repository e senza le variabili d'ambiente CLAUDE*/ANTHROPIC*.
  Il modello che ha scritto la risposta si legge da modelUsage.
- qwen3:8b: Ollama sul PC, senza ragionamento nascosto, temperatura 0,7, seme fisso per chiamata.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

import requests

from comune import TEMPERATURA_OLLAMA, adesso

CLAUDE = Path(r"C:\Users\emari\AppData\Local\Claude-Data\claude_pzs8sxrjxfjjc\claude-code\2.1.308\c17a819afb40\claude.exe")
CARTELLA_VUOTA = Path(tempfile.gettempdir()) / "bancone_cartella_vuota"
URL_OLLAMA = "http://127.0.0.1:11434"
OLLAMA_EXE = Path(os.environ.get("LOCALAPPDATA", "")) / "Programs" / "Ollama" / "ollama.exe"
PROCESSI: list[subprocess.Popen] = []


class LimiteUso(Exception):
    """Il servizio dice che il limite d'uso è raggiunto: la corsa si ferma e si riprende più tardi."""


def env_pulito() -> dict:
    return {k: v for k, v in os.environ.items() if not k.upper().startswith(("CLAUDE", "ANTHROPIC"))}


def chiama_claude(modello: str, sistema: str, utente: str, timeout: int = 600) -> dict:
    """Una chiamata pulita a Claude. Restituisce testo, modelli con token in uscita, errore e durata."""
    CARTELLA_VUOTA.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".txt", delete=False,
                                     dir=CARTELLA_VUOTA.parent) as f:
        f.write(sistema)
        file_sistema = f.name
    cmd = [str(CLAUDE), "-p", "--model", modello, "--system-prompt-file", file_sistema, "--tools", "",
           "--setting-sources", "project", "--strict-mcp-config", "--disable-slash-commands",
           "--no-session-persistence", "--output-format", "json"]
    inizio = time.time()
    try:
        r = subprocess.run(cmd, input=utente, cwd=CARTELLA_VUOTA, env=env_pulito(), capture_output=True, text=True,
                           encoding="utf-8", errors="replace", timeout=timeout)
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"testo": None, "errore": f"chiamata non riuscita: {e}", "modelli_uscita": {},
                "durata_s": round(time.time() - inizio, 1)}
    finally:
        Path(file_sistema).unlink(missing_ok=True)
    durata = round(time.time() - inizio, 1)
    try:
        d = json.loads(r.stdout)
    except json.JSONDecodeError:
        testo = (r.stdout + r.stderr).lower()
        if "limit" in testo and ("usage" in testo or "reached" in testo):
            raise LimiteUso(r.stdout[-300:] + r.stderr[-300:])
        return {"testo": None, "errore": f"uscita non JSON (codice {r.returncode}): {r.stderr[-300:]}",
                "modelli_uscita": {}, "durata_s": durata}
    uso = d.get("modelUsage") or {}
    modelli_uscita = {m: u.get("outputTokens", 0) for m, u in uso.items() if u.get("outputTokens", 0) > 0}
    testo = d.get("result")
    if d.get("is_error") and testo and "limit" in testo.lower():
        raise LimiteUso(testo[:300])
    return {"testo": testo, "errore": d.get("is_error"), "modelli_uscita": modelli_uscita, "durata_s": durata,
            "safety_stops": d.get("safety_stops"), "stop_reason": d.get("stop_reason")}


def server_vivo() -> dict | None:
    try:
        r = requests.get(URL_OLLAMA + "/api/version", timeout=3)
        return r.json() if r.ok else None
    except requests.RequestException:
        return None


def avvia_ollama() -> None:
    if server_vivo():
        return
    if not OLLAMA_EXE.exists():
        sys.exit(f"Ollama non trovato in {OLLAMA_EXE} e server spento")
    print(f"[{adesso()}] avvio ollama serve", flush=True)
    PROCESSI.append(subprocess.Popen([str(OLLAMA_EXE), "serve"], stdout=subprocess.DEVNULL,
                                     stderr=subprocess.DEVNULL))
    for _ in range(60):
        time.sleep(1)
        if server_vivo():
            return
    sys.exit("ollama serve non risponde dopo 60 s")


def chiudi_ollama() -> None:
    for p in PROCESSI:
        p.terminate()


def chiama_ollama(modello: str, sistema: str, utente: str, seme: int, timeout: int = 600) -> dict:
    corpo = {"model": modello, "stream": False, "think": False,
             "messages": [{"role": "system", "content": sistema}, {"role": "user", "content": utente}],
             "options": {"temperature": TEMPERATURA_OLLAMA, "seed": seme, "num_predict": 600}}
    inizio = time.time()
    try:
        r = requests.post(URL_OLLAMA + "/api/chat", json=corpo, timeout=timeout)
        d = r.json()
    except (requests.RequestException, ValueError) as e:
        return {"testo": None, "errore": f"Ollama: {e}", "modelli_uscita": {}, "durata_s": round(time.time() - inizio, 1)}
    testo = (d.get("message") or {}).get("content")
    return {"testo": testo, "errore": d.get("error"), "modelli_uscita": {modello: d.get("eval_count", 0)},
            "durata_s": round(time.time() - inizio, 1), "done_reason": d.get("done_reason"),
            "pensiero": bool((d.get("message") or {}).get("thinking"))}


def versioni() -> dict:
    """Versione di Claude Code e di Ollama, da registrare con le prove."""
    out = {"claude_code": None, "ollama": None}
    try:
        r = subprocess.run([str(CLAUDE), "--version"], capture_output=True, text=True, timeout=60, env=env_pulito())
        out["claude_code"] = r.stdout.strip()
    except (OSError, subprocess.SubprocessError):
        pass
    v = server_vivo()
    out["ollama"] = (v or {}).get("version")
    return out
