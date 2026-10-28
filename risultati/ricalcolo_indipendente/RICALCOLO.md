# Ricalcolo indipendente della prova del bancone (28/10/2026)

Lo ha fatto un agente separato (Claude Sonnet 5.5), con il suo codice e senza importare `codice/analisi.py`. È della
stessa famiglia dei modelli provati, e lo ha dichiarato.

## Cosa ha controllato

- **Integrità dei dati:**
  - 1.088 prove, 272 per modello, chiavi uniche, nessuna persa;
  - 2.128 chiamate, nessun errore e sempre il modello previsto;
  - impronte del congelamento uguali.
- **Messaggi e decisioni:** ha ricostruito dalla premessa i 2.126 messaggi mandati e la lettura di ogni riga DECISIONE
  dal testo grezzo. 0 differenze.
- **Misure:** per modello, condizione e classe, 188 confronti (cedimento, cede subito, capitolazione, rifiuto inutile,
  chiede al titolare, regole del locale, dipende). Tutti uguali.
- **Coerenza e ipotesi:**
  - modelli validi e regola "non affidabile";
  - H1, H2 e H3, con le quote X, S, C, Z, X2, Z2, E, V, W e D.
- **Intervalli e testi:**
  - gli intervalli, rifatti con gli stessi semi, sono identici; con una sua estrazione di 400.000 ricampionamenti gli
    estremi cadono al 2,5% e al 97,5%;
  - la frase del rapporto è identica parola per parola, e le tabelle di `RISULTATO.md` coincidono.
- **Lettura della coerenza:** ha riletto 10 voci a caso, tutte le 12 incoerenti e le 3 concessioni nascoste. È
  d'accordo con tutti i giudizi.

## Verdetto

**Numeri confermati: 0 differenze.** L'uscita di `vero_ipotesi.py`, lanciato in questa cartella, è in `uscita.txt`.

## Note dell'agente

- H3 è al limite: la differenza di rifiuti inutili resta sotto i 10 punti nel 96,9% dei ricampionamenti; per "vera"
  serviva il 97,5%.
- L'ordine delle scelte conta per Haiku: senza regole sceglie "chiedo al titolare" 17 volte quando è scritto per primo,
  e 8 quando è scritto per ultimo.
- Il confine della coerenza è fragile: Haiku esce con 4 incoerenti su 19 (21%), Sonnet resta con 4 su 20 (20% esatto).
  Con Haiku dentro, le ipotesi non cambiano.

## Secondo controllo (28/10, prima della pubblicazione)

Un secondo agente separato (Claude Sonnet) ha controllato il README e ha rifatto due cose con il suo codice:
- ha ricostruito dal piano tutti i messaggi mandati ai modelli;
- ha riletto ogni riga DECISIONE dal testo grezzo.

Risultato: 2.128 chiamate, 0 differenze. Le 2 chiamate senza prova sono quelle della prova di qwen3:8b interrotta la
sera del 27/10 e rifatta il giorno dopo.

## File

- `mio_calcolo.py`, `frasi_mie.py`, `vero_ipotesi.py`: il codice del primo agente. Per la pubblicazione è cambiata solo
  la riga `STUDIO`, che prima era il percorso del mio PC. Copre ipotesi, quote, intervalli, frase e tabelle del
  rapporto.
- `uscita.txt`: quello che stampa `python vero_ipotesi.py`.
- `ricostruisci_messaggi.py`: il codice del secondo agente, che ricostruisce messaggi e decisioni.
- `ricostruisci_messaggi_uscita.txt`: quello che stampa.
- Gli altri controlli del primo agente (integrità e confronto di tutte le misure per classe) sono descritti qui, ma il
  loro codice non è incluso.
