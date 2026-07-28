from fastapi import FastAPI
from datetime import datetime
from typing import List

app = FastAPI(title="Fanta Dynasty - Sistema di Emergenza Blindato")

db_rose_reali = {
    "galva": [{"nome": "Provedel", "ruolo": "P", "scadenza": "set-28"}, {"nome": "Casale", "ruolo": "D", "scadenza": "set-26"}, {"nome": "Gatti", "ruolo": "D", "scadenza": "set-27"}, {"nome": "Kvaratskhelia", "ruolo": "A", "scadenza": "set-27"}],
    "paolo": [{"nome": "Sommer", "ruolo": "P", "scadenza": "set-27"}, {"nome": "Barella", "ruolo": "C", "scadenza": "feb-29"}, {"nome": "Lautaro Martinez", "ruolo": "A", "scadenza": "set-28"}],
    "beppe": [{"nome": "Caprile", "ruolo": "P", "scadenza": "feb-26"}, {"nome": "Svilar", "ruolo": "P", "scadenza": "feb-26"}, {"nome": "Koopmeiners", "ruolo": "C", "scadenza": "set-28"}],
    "bardo": [{"nome": "Carnesecchi", "ruolo": "P", "scadenza": "set-27"}, {"nome": "Lookman", "ruolo": "A", "scadenza": "set-27"}],
    "dodo": [{"nome": "De Gea", "ruolo": "P", "scadenza": "set-27"}, {"nome": "Gudmundsson", "ruolo": "A", "scadenza": "set-28"}],
    "nilo": [], "robba": [], "gioppy": [], "bortolo": [], "pecu": []
}

def analizza_data_scadenza(scadenza_str: str) -> dict:
    mesi_mappa = {"gen": 1, "feb": 2, "mar": 3, "apr": 4, "mag": 5, "giu": 6, "lug": 7, "ago": 8, "set": 9, "ott": 10, "nov": 11, "dic": 12}
    try:
        parti = scadenza_str.lower().strip().split("-")
        mese_scadenza = mesi_mappa.get(parti[0], 1)
        anno_scadenza = 2000 + int(parti[1])
        oggi = datetime(2026, 7, 28)
        data_scadenza = datetime(anno_scadenza, mese_scadenza, 1)
        differenza_mesi = (data_scadenza.year - oggi.year) * 12 + (data_scadenza.month - oggi.month)
        if differenza_mesi < 0: return {"stato": "❌ SCADUTO / SVINCOLATO"}
        if data_scadenza <= datetime(2026, 9, 30): return {"stato": "🚨 IN SCADENZA IMMEDIATA"}
        return {"stato": "🍏 SOTTO CONTRATTO"}
    except:
        return {"stato": "❌ SCADUTO / SVINCOLATO"}

@app.get("/rose/{fanta_allenatore}")
def ottieni_rosa(fanta_allenatore: str):
    giocatori = db_rose_reali.get(fanta_allenatore.strip().lower(), [])
    risultato = []
    for g in giocatori:
        analisi = analizza_data_scadenza(g["scadenza"])
        risultato.append({"nome": g["nome"], "ruolo": g["ruolo"], "scadenza": g["scadenza"], "stato_contratto": analisi["stato"]})
    return risultato

@app.get("/consigli/{fanta_allenatore}")
def genera_consigli(fanta_allenatore: str):
    rosa = ottieni_rosa(fanta_allenatore)
    ruoli_scoperti = [g["ruolo"] for g in rosa if "🚨" in g["stato_contratto"] or "❌" in g["stato_contratto"]]
    
    # DATI REALI STATICI DEL LISTONE DI FANTACALCIO INSERITI DIRETTAMENTE
    svincolati_reali = [
        {"nome": "Retegui", "ruolo": "A", "squadra": "Atalanta", "fm": 8.1, "gol": 14, "assist": 2, "q": 32},
        {"nome": "Zaccagni", "ruolo": "C", "squadra": "Lazio", "fm": 7.4, "gol": 7, "assist": 5, "q": 26},
        {"nome": "Nico Paz", "ruolo": "C", "squadra": "Como", "fm": 7.2, "gol": 5, "assist": 5, "q": 18},
        {"nome": "Dimarco", "ruolo": "D", "squadra": "Inter", "fm": 7.3, "gol": 4, "assist": 7, "q": 22},
        {"nome": "Pulisic", "ruolo": "C", "squadra": "Milan", "fm": 7.8, "gol": 12, "assist": 8, "q": 30},
        {"nome": "Thuram M.", "ruolo": "A", "squadra": "Inter", "fm": 7.9, "gol": 13, "assist": 6, "q": 34}
    ]
    
    raccomandati = []
    for s in svincolati_reali:
        punteggio = (s["fm"] * 5.0) + (s["gol"] * 3.5) + (s["assist"] * 1.5)
        punteggio_finale = round(min(punteggio, 100.0), 1)
        raccomandati.append({
            "nome": s["nome"],
            "ruolo": s["ruolo"],
            "squadra": f"Quotazione: {s['q']} crediti | FM: {s['fm']}",
            "indice": punteggio_finale,
            "prioritario": s["ruolo"] in ruoli_scoperti
        })
        
    raccomandati.sort(key=lambda x: (x["prioritario"], x["indice"]), reverse=True)
    return {"ruoli_critici": list(set(ruoli_scoperti)) if ruoli_scoperti else ["Nessuno, rosa protetta!"], "consigli": raccomandati}
