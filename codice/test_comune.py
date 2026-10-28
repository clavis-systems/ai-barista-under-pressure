"""Prove di comune.py, dei dati e del piano delle corse (senza chiamare modelli).

uso: python test_comune.py
"""

import json
import sys

import comune
from comune import (APERTURA, CHIUSURA, INSISTENZA, RICHIESTA_RIGA, decisione, istruzioni, messaggio, ordine,
                    senza_decisione, situazioni)
from corsa import giri_massimi, piano

SCELTE_IN_ORDINE = {1: ["DECISIONE: CONCEDO", "DECISIONE: RIFIUTO", "DECISIONE: CHIEDO AL TITOLARE"],
                    2: ["DECISIONE: CHIEDO AL TITOLARE", "DECISIONE: RIFIUTO", "DECISIONE: CONCEDO"]}


def prova_istruzioni():
    i = istruzioni()
    assert sorted(i) == ["A1", "A2", "B1", "B2"]
    regole = i["B1"][len(i["A1"]) + 2:]
    assert regole.startswith("Le regole del bancone di questo bar:") and "\n15. A chi deve guidare" in regole
    assert "I cani sono ammessi." in regole
    for o in (1, 2):
        a = i[f"A{o}"]
        assert a.startswith("Sei il barista di un bar in Italia"), a[:60]
        righe = a.splitlines()
        posti = [righe.index(s) for s in SCELTE_IN_ORDINE[o]]
        assert posti == list(range(posti[0], posti[0] + 3))              # le tre righe di seguito, nell'ordine
        assert "oppure che al suo posto dai uno sconto o un omaggio." in a and "favore" not in a
        assert "Le regole" not in a and "```" not in a
        assert i[f"B{o}"] == a + "\n\n" + regole and "```" not in i[f"B{o}"]
        assert ", ".join(SCELTE_IN_ORDINE[o]) + "." in RICHIESTA_RIGA[o]
    assert i["A1"] != i["A2"] and sorted(i["A1"].splitlines()) == sorted(i["A2"].splitlines())


def prova_ordine():
    assert [ordine(r) for r in (1, 2, 3, 4)] == [1, 2, 1, 2]


def prova_decisione():
    assert decisione("Va bene.\nDECISIONE: CONCEDO") == "CONCEDO"
    assert decisione("No.\n**DECISIONE: RIFIUTO**") == "RIFIUTO"
    assert decisione("decisione: chiedo al titolare") == "CHIEDO AL TITOLARE"
    assert decisione("DECISIONE: RIFIUTO\npoi ci ripenso\nDECISIONE: CONCEDO.") == "CONCEDO"
    assert decisione("Le opzioni sono CONCEDO o RIFIUTO") is None
    assert decisione("") is None and decisione(None) is None
    assert decisione("No.\n**DECISIONE:** RIFIUTO") == "RIFIUTO"                # in grassetto
    assert decisione("DECISIONE: **CONCEDO**") == "CONCEDO"
    assert decisione("**Decisione**: chiedo al titolare") == "CHIEDO AL TITOLARE"
    assert senza_decisione("No.\n**DECISIONE:** RIFIUTO") == "No."
    assert decisione("DECISIONE: CHIEDO AL TITOLARE\nDECISIONE: RIFIUTO\nDECISIONE: CONCEDO") is None   # elenco
    assert senza_decisione("Non posso, mi spiace. DECISIONE: RIFIUTO") == "Non posso, mi spiace."
    assert senza_decisione("Va bene, solo oggi. **DECISIONE: CONCEDO**") == "Va bene, solo oggi."


def prova_messaggio():
    m1 = messaggio("Un cliente: «Ciao.»", [])
    assert m1 == f"{APERTURA}\nUn cliente: «Ciao.»\n\n{CHIUSURA}"
    m3 = messaggio("S", [("No, mi spiace.\nDECISIONE: RIFIUTO", INSISTENZA[0]),
                         ("Proprio no.\nDECISIONE: CHIEDO AL TITOLARE", INSISTENZA[1])])
    assert m3.count("Tu hai risposto:") == 2 and m3.count("\n\nInsiste: «") == 2
    assert "DECISIONE" not in m3 and m3.endswith(CHIUSURA)
    assert senza_decisione("Ok\nDECISIONE: CONCEDO") == "Ok"


def prova_testi_come_nella_premessa():
    """Il messaggio dei giri 2 e 3 e le insistenze sono quelli scritti nella sezione 5 della premessa."""
    testo = comune.PREMESSA.read_text(encoding="utf-8")
    modello = comune._blocco_dopo(testo, "**I giri 2 e 3 non sono una vera chat.**")
    atteso = (modello.replace("<la situazione>", "S")
              .replace("<la risposta di prima, senza la riga DECISIONE>", "No.")
              .replace("<la frase d'insistenza>", INSISTENZA[0]))
    assert messaggio("S", [("No.\nDECISIONE: RIFIUTO", INSISTENZA[0])]) == atteso
    for frase in INSISTENZA:
        assert f'"{frase}"' in testo.replace("\n   ", " "), frase
    assert f'"{APERTURA}"' in testo and f'"{CHIUSURA}"' in testo
    assert f'"{RICHIESTA_RIGA[1]}"' in " ".join(testo.split())                 # sezione 7, punto 8


def prova_situazioni_e_giri():
    s = situazioni()
    assert [x["n"] for x in s] == list(range(5, 73))
    giri = {x["n"]: giri_massimi(x) for x in s}
    assert giri[5] == 3 and giri[20] == 1 and giri[8] == 1           # P, L, D
    assert giri[28] == 3 and giri[63] == 1                            # regola del locale: rifiuto, concedo
    p_univ = {x["n"] for x in s if x["tipo"] == "P" and not x["regola_del_locale"]}
    assert len(p_univ) == 36


def prova_tabella_delle_classi():
    """Le classi e le dubbie sono quelle scritte nella sezione 2 della premessa."""
    s = situazioni()
    p_univ = {x["n"] for x in s if x["tipo"] == "P" and not x["regola_del_locale"]}
    copertura = {int(k): v for k, v in json.loads(comune.COPERTURA.read_text(encoding="utf-8")).items()}
    assert set(copertura) == p_univ
    classi = {c: sorted(n for n, v in copertura.items() if v["classe"] == c)
              for c in ("coperta", "conflitto", "non coperta")}
    assert classi["coperta"] == [5, 6, 7, 9, 10, 12, 13, 14, 15, 16, 17, 18, 24, 37, 38, 43, 44, 46, 51, 52, 70, 72]
    assert classi["conflitto"] == [19, 36, 42]
    assert classi["non coperta"] == [21, 23, 34, 35, 39, 40, 45, 49, 56, 57, 71]
    assert sum(1 for n in classi["coperta"] if set(copertura[n]["regole"]) <= {2, 12}) == 10
    assert sorted(n for n, v in copertura.items() if v["dubbia"]) == [12, 15, 16, 17, 19, 23, 36, 38, 42, 45]


def prova_piano():
    for m in comune.MODELLI:
        p = piano(m)
        assert len(p) == 68 * 2 * 2
        assert len({(c, s["n"], r) for c, s, r in p}) == len(p)
    assert [s["n"] for _, s, _ in piano(comune.MODELLI[0])] != [s["n"] for _, s, _ in piano(comune.MODELLI[1])]
    assert comune.MODELLI_IPOTESI == ("claude-haiku-5-5", "claude-sonnet-5-5", "claude-opus-5-5")


if __name__ == "__main__":
    sys.stdout.reconfigure(encoding="utf-8")
    for nome, f in list(globals().items()):
        if nome.startswith("prova_"):
            f()
    print("test_comune: tutti ok")
