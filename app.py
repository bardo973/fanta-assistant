import streamlit as st
import pandas as pd
from datetime import datetime
import re

# Configurazione iniziale della pagina
st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
STAGIONI = ["2023-24", "2024-25", "2025-26"]

# ─── HELPERS SCADENZA ───
MESI_ITA = {
    'gen': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'mag': 5, 'giu': 6,
    'lug': 7, 'ago': 8, 'sett': 9, 'set': 9, 'ott': 10, 'nov': 11, 'dic': 12
}
MESI_ITA_REV = {v: k for k, v in MESI_ITA.items()}

def parse_scadenza(s):
    if not s or pd.isna(s) or str(s).strip().lower() in ('n/d', 'nd', ''):
        return None
    parts = str(s).strip().lower().split()
    if len(parts) != 2:
        return None
    mese_str, anno_str = parts
    mese = MESI_ITA.get(mese_str)
    if not mese:
        return None
    anno = int('20' + anno_str) if len(anno_str) == 2 else int(anno_str)
    return datetime(anno, mese, 1)

def is_in_scadenza(scadenza_str):
    data = parse_scadenza(scadenza_str)
    if not data:
        return False
    oggi = datetime.now()
    if data < oggi:
        return False
    return (data - oggi).days <= 180

def normalizza_scadenza(val):
    if pd.isna(val) or str(val).strip().lower() in ('n/d', 'nd', ''):
        return "N/D"
    s = str(val).strip().lower()
    parts = s.split()
    if len(parts) == 2 and parts[0] in MESI_ITA:
        return f"{parts[0]} {parts[1]}"
    try:
        dt = pd.to_datetime(val)
        return f"{MESI_ITA_REV[dt.month]} {str(dt.year)[2:]}"
    except:
        return str(val)

def scadenza_da_acquisto():
    oggi = datetime.now()
    anno = oggi.year + 4
    mese = oggi.month
    return f"{MESI_ITA_REV[mese]} {str(anno)[2:]}"

# ─── HELPER SQUADRA SERIE A ───
def get_squadra_sa_da_listone(nome_giocatore):
    db = st.session_state.get('giocatori_db', pd.DataFrame())
    if db.empty or 'Nome' not in db.columns:
        return None
    match = db[db['Nome'].str.lower() == nome_giocatore.lower()]
    if not match.empty and 'Squadra_SerieA' in match.columns:
        return str(match.iloc[0]['Squadra_SerieA'])
    return None

def aggiorna_sa_rosa(rosa_list):
    """Sovrascrive Squadra_SerieA in ogni dizionario della rosa prendendo dal listone se esiste."""
    for g in rosa_list:
        sa_listone = get_squadra_sa_da_listone(g.get('Nome', ''))
        if sa_listone:
            g['Squadra_SerieA'] = sa_listone
    return rosa_list

# ─── HELPER STATISTICHE ───
def calcola_media_stats(nome, campo):
    db = st.session_state.get('statistiche_db', {})
    if nome not in db:
        return None
    vals = [db[nome][s][campo] for s in db[nome] if campo in db[nome][s]]
    return sum(vals) / len(vals) if vals else None

def ha_stats(nome):
    return nome in st.session_state.get('statistiche_db', {})

def indice_affidabilita(nome):
    """Presenze medie / 38 * 100"""
    db = st.session_state.get('statistiche_db', {})
    if nome not in db:
        return None
    pres = [db[nome][s]['Presenze'] for s in db[nome] if 'Presenze' in db[nome][s]]
    if not pres:
        return None
    return round((sum(pres) / len(pres)) / 38 * 100, 1)

# ─── INIT SESSION STATE ───
if 'squadre' not in st.session_state or not isinstance(st.session_state.squadre, dict):
    st.session_state.squadre = {}
for sq in NOMI_SQUADRE:
    if sq not in st.session_state.squadre:
        st.session_state.squadre[sq] = {"crediti": 500, "rosa": [], "prestiti_ceduti": []}
    if "prestiti_ceduti" not in st.session_state.squadre[sq]:
        st.session_state.squadre[sq]["prestiti_ceduti"] = []

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []
if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Database statistiche storiche
if 'statistiche_db' not in st.session_state:
    st.session_state.statistiche_db = {
        "Douvikas": {
            "2023-24": {"FantaMedia": 7.5, "MediaVoto": 6.8, "Gol": 15, "Assist": 4, "Presenze": 32, "Rigori": 3, "Ammonizioni": 6, "Espulsioni": 1},
            "2024-25": {"FantaMedia": 7.8, "MediaVoto": 7.0, "Gol": 18, "Assist": 5, "Presenze": 34, "Rigori": 4, "Ammonizioni": 4, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 7.8, "MediaVoto": 7.1, "Gol": 12, "Assist": 6, "Presenze": 28, "Rigori": 2, "Ammonizioni": 5, "Espulsioni": 0}
        },
        "Zaccagni": {
            "2023-24": {"FantaMedia": 7.2, "MediaVoto": 6.5, "Gol": 8, "Assist": 10, "Presenze": 30, "Rigori": 1, "Ammonizioni": 7, "Espulsioni": 0},
            "2024-25": {"FantaMedia": 7.4, "MediaVoto": 6.7, "Gol": 10, "Assist": 8, "Presenze": 33, "Rigori": 2, "Ammonizioni": 5, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 7.5, "MediaVoto": 6.8, "Gol": 9, "Assist": 9, "Presenze": 31, "Rigori": 1, "Ammonizioni": 6, "Espulsioni": 0}
        },
        "McKennie": {
            "2023-24": {"FantaMedia": 6.5, "MediaVoto": 6.0, "Gol": 3, "Assist": 5, "Presenze": 28, "Rigori": 0, "Ammonizioni": 8, "Espulsioni": 0},
            "2024-25": {"FantaMedia": 6.7, "MediaVoto": 6.2, "Gol": 4, "Assist": 6, "Presenze": 30, "Rigori": 0, "Ammonizioni": 6, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 6.9, "MediaVoto": 6.3, "Gol": 5, "Assist": 7, "Presenze": 32, "Rigori": 0, "Ammonizioni": 5, "Espulsioni": 0}
        },
        "Cambiaso": {
            "2023-24": {"FantaMedia": 6.2, "MediaVoto": 6.0, "Gol": 2, "Assist": 4, "Presenze": 25, "Rigori": 0, "Ammonizioni": 4, "Espulsioni": 0},
            "2024-25": {"FantaMedia": 6.4, "MediaVoto": 6.1, "Gol": 3, "Assist": 5, "Presenze": 29, "Rigori": 0, "Ammonizioni": 3, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 6.6, "MediaVoto": 6.3, "Gol": 4, "Assist": 6, "Presenze": 31, "Rigori": 0, "Ammonizioni": 4, "Espulsioni": 0}
        },
        "Skorupski": {
            "2023-24": {"FantaMedia": 5.0, "MediaVoto": 6.0, "Gol": 0, "Assist": 0, "Presenze": 35, "Rigori": 0, "Ammonizioni": 1, "Espulsioni": 0},
            "2024-25": {"FantaMedia": 5.1, "MediaVoto": 6.1, "Gol": 0, "Assist": 1, "Presenze": 36, "Rigori": 0, "Ammonizioni": 2, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 5.2, "MediaVoto": 6.2, "Gol": 0, "Assist": 0, "Presenze": 34, "Rigori": 0, "Ammonizioni": 1, "Espulsioni": 0}
        },
        "Cristante": {
            "2023-24": {"FantaMedia": 6.3, "MediaVoto": 6.1, "Gol": 2, "Assist": 3, "Presenze": 33, "Rigori": 0, "Ammonizioni": 9, "Espulsioni": 1},
            "2024-25": {"FantaMedia": 6.4, "MediaVoto": 6.2, "Gol": 3, "Assist": 4, "Presenze": 34, "Rigori": 0, "Ammonizioni": 7, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 6.5, "MediaVoto": 6.2, "Gol": 2, "Assist": 5, "Presenze": 32, "Rigori": 0, "Ammonizioni": 8, "Espulsioni": 0}
        },
        "Boga": {
            "2023-24": {"FantaMedia": 6.5, "MediaVoto": 6.0, "Gol": 5, "Assist": 3, "Presenze": 22, "Rigori": 0, "Ammonizioni": 3, "Espulsioni": 0},
            "2024-25": {"FantaMedia": 6.6, "MediaVoto": 6.1, "Gol": 6, "Assist": 4, "Presenze": 26, "Rigori": 0, "Ammonizioni": 4, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 6.8, "MediaVoto": 6.2, "Gol": 7, "Assist": 5, "Presenze": 28, "Rigori": 0, "Ammonizioni": 3, "Espulsioni": 0}
        },
        "Dallinga": {
            "2023-24": {"FantaMedia": 6.2, "MediaVoto": 5.9, "Gol": 8, "Assist": 2, "Presenze": 24, "Rigori": 1, "Ammonizioni": 4, "Espulsioni": 0},
            "2024-25": {"FantaMedia": 6.4, "MediaVoto": 6.0, "Gol": 10, "Assist": 3, "Presenze": 28, "Rigori": 2, "Ammonizioni": 3, "Espulsioni": 0},
            "2025-26": {"FantaMedia": 6.6, "MediaVoto": 6.1, "Gol": 9, "Assist": 4, "Presenze": 30, "Rigori": 1, "Ammonizioni": 5, "Espulsioni": 0}
        }
    }

# Database Listone Generale (mockup per auto-completamento Squadra Serie A e controlli esistenza)
if 'giocatori_db' not in st.session_state:
    st.session_state.giocatori_db = pd.DataFrame([
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 18},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 16},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 15},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 28},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Nizza", "Quotazione": 20},
        {"Nome": "Dallinga", "Ruolo": "A", "Squadra_SerieA": "Bologna", "Quotazione": 22},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Celta Vigo", "Quotazione": 26}
    ])

# Precaricamento Rosa PECU
if len(st.session_state.squadre["PECU"]["rosa"]) == 0:
    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Costo_Acquisto": 14, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Costo_Acquisto": 8, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 18, "FantaMedia": 6.6, "Costo_Acquisto": 15, "Scadenza_Contratto": "giu 27"},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 16, "FantaMedia": 6.9, "Costo_Acquisto": 12, "Scadenza_Contratto": "giu 27"},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 15, "FantaMedia": 6.5, "Costo_Acquisto": 14, "Scadenza_Contratto": "giu 26"},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 28, "FantaMedia": 7.5, "Costo_Acquisto": 25, "Scadenza_Contratto": "giu 28"},
