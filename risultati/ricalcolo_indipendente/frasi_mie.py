"""Costruzione MIA delle frasi del rapporto, partendo dai modelli di frase scritti nella premessa (sezione 8, versione dopo la
revisione 2). Legge i modelli dalla premessa (non dal codice) e sostituisce le lettere. Non importa analisi.py.

Arrotondamento: mezzo in su (verso +infinito), esatto sul valore binario del numero (Fraction), non con floor(100*x+0.5).
"""
import math
import re
from fractions import Fraction
from pathlib import Path

STUDIO = Path(__file__).resolve().parents[2]  # unica riga cambiata per la pubblicazione: prima era il percorso del mio PC
PREMESSA = (STUDIO / "PREMESSA_BANCONE.md").read_text(encoding="utf-8")
SEZ8 = PREMESSA[PREMESSA.index("## 8."):PREMESSA.index("## 9.")]
NORM = re.sub(r"\s*\n\s*", " ", SEZ8)                # tutta la sezione 8 su una riga: le frasi a capo diventano intere


def trova(pattern):
    m = re.search(pattern, NORM)
    assert m, f"non trovo nella premessa: {pattern}"
    return m.group(1)


MOD = {
    "H1 vera": trova(r'\*\*H1 vera:\*\* "(.+?)" La parte su H2'),
    "H2 vera": trova(r'- H2 vera: "(.+?)"'),
    "H2 mista": trova(r'- H2 mista: "(.+?)"'),
    "H2 falsa": trova(r'- H2 falsa: "(.+?)"'),
    "fine di piu": trova(r'la fine diventa: "(.+?)"'),
    "H1 falsa": trova(r'\*\*H1 falsa:\*\* "(.+?)"'),
    "nessun valido": trova(r'\*\*Nessun modello valido:\*\* "(.+?)"'),
    "non coperte": trova(r'\*\*Frase sulle pressioni non coperte\*\*, sempre: "(.+?)"'),
    "H3 vera": trova(r'\*\*vera:\*\* "(.+?)"'),
    "H3 falsa": trova(r'\*\*falsa:\*\* "(.+?)"'),
    "H3 non dimostrata": trova(r'\*\*non dimostrata:\*\* "(.+?)"'),
    "chiusura": trova(r'\*\*Chiusura, sempre in fondo:\*\* "(.+?)"'),
    "provvisorio": trova(r'il rapporto comincia con "(.+?)"'),
}


def su(x) -> int:
    """Percentuale con il mezzo in su (12,5 -> 13; -2,5 -> -2). Il numero voluto e' un rapporto di interi (k/n, o una
    differenza di rapporti): se ne recupera la frazione esatta, cosi' 3/40 = 7,5% va a 8 anche se in binario vale
    0,07499999999999999722."""
    return math.floor(Fraction(x).limit_denominator(10 ** 6) * 100 + Fraction(1, 2))


def vocale(n: int) -> bool:
    """Il numero in lettere comincia con una vocale: uno, otto, undici, ottanta..ottantanove."""
    return n in (1, 8, 11) or 80 <= n <= 89


def articolo(prep: str, n: int) -> str:
    forme = {"nel": ("nel", "nell'", "nello"), "al": ("al", "all'", "allo"), "dal": ("dal", "dall'", "dallo")}[prep]
    if n == 0:
        return forme[2] + " "
    return forme[1] if vocale(n) else forme[0] + " "


def val(x, iv):
    """'35% [24-47%]'"""
    return f"{su(x)}% [{su(iv[0])}-{su(iv[1])}%]"


def punti(d, iv):
    """'+3 punti [da -2 a +8]' (formato non fissato dalla premessa: 'in punti, con il suo intervallo')"""
    return f"{su(d):+d} punti [da {su(iv[0]):+d} a {su(iv[1]):+d}]"


def nomi(lista):
    return lista[0] if len(lista) == 1 else ", ".join(lista[:-1]) + " e " + lista[-1]


def lettera(testo, nome, valore):
    """Sostituisce la lettera isolata (non dentro altre parole o numeri)."""
    return re.sub(rf"(?<![A-Za-z0-9]){nome}(?![A-Za-z0-9])", lambda m: valore, testo)


def con_prep(testo, prep, nome, x, iv):
    """'nel X' / 'al Z2' / 'dal X2' -> forma giusta dell'articolo + valore con intervallo"""
    return re.sub(rf"(?<![A-Za-z0-9]){prep} {nome}(?![A-Za-z0-9])",
                  lambda m: articolo(prep, su(x)) + val(x, iv), testo)


def costruisci(H, provvisorio=False):
    """H: validi, H1, H2, H3, peggiore_nome, qualificati_nomi, dimezzano_nomi, e le coppie (quota, intervallo) per
    Y X S C Z X2 Z2 V W e le due differenze E e D come (differenza, intervallo)."""
    if not H["validi"]:
        return MOD["nessun valido"]
    if H["H1"]:
        t = MOD["H1 vera"]
        if H["H2"] == "vera":
            h2 = MOD["H2 vera"].replace("[modelli]", nomi(H["qualificati_nomi"]))
        elif H["H2"] == "mista":
            no = [m for m in H["qualificati_nomi"] if m not in H["dimezzano_nomi"]]
            h2 = MOD["H2 mista"].replace("[modelli], non per [modelli]", f"{nomi(H['dimezzano_nomi'])}, non per {nomi(no)}")
        else:
            h2 = MOD["H2 falsa"]
        t = t.replace("[parte su H2]", h2)
        if H["Z_piu_alto_di_X"]:
            assert t.endswith("e tutti insieme cedono nel Z.")
            t = t[:-len("e tutti insieme cedono nel Z.")] + MOD["fine di piu"]
        t = con_prep(t, "nel", "X", *H["X"])
        t = con_prep(t, "nel", "Z", *H["Z"])
        for nome in ("Y", "S", "C"):
            t = lettera(t, nome, val(*H[nome]))
        t = lettera(t, "M", H["peggiore_nome"])
    else:
        t = MOD["H1 falsa"]
        t = lettera(t, "Y", val(*H["Y"]))
        t = lettera(t, "M", H["peggiore_nome"])
    nc = MOD["non coperte"]
    nc = con_prep(nc, "dal", "X2", *H["X2"])
    nc = con_prep(nc, "al", "Z2", *H["Z2"])
    nc = lettera(nc, "E", punti(*H["E"]))
    s = MOD["H3 " + H["H3"]]
    s = lettera(s, "W", val(*H["W"]))
    s = lettera(s, "V", val(*H["V"]))
    s = lettera(s, "D", punti(*H["D"]))
    out = f"{t} {nc} {s} {MOD['chiusura']}"
    if provvisorio:
        out = MOD["provvisorio"] + " " + out
    return out
