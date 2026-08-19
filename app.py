import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
STAGIONI_DISP = ["2023-24", "2024-25", "2025-26"]

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

# --- INIZIALIZZAZIONE SESSIONE ---
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

# Database statistiche 3 anni
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

# Rosa precaricata PECU
if len(st.session_state.squadre["PECU"]["rosa"]) == 0:
    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Costo_Acquisto": 14, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Costo_Acquisto": 8, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 6, "FantaMedia": 6.1, "Costo_Acquisto": 6, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Lucumì", "Ruolo": "D", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 6, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Costo_Acquisto": 10, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Biraghi", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 1, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Ranieri L.", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 6, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Maripan", "Ruolo": "D", "Squadra_SerieA": "Torino", "Quotazione": 9, "FantaMedia": 6.2, "Costo_Acquisto": 9, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Mina", "Ruolo": "D", "Squadra_SerieA": "Cagliari", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 7, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Juan Jesus", "Ruolo": "D", "Squadra_SerieA": "Napoli", "Quotazione": 6, "FantaMedia": 5.9, "Costo_Acquisto": 4, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Costo_Acquisto": 9, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Aebischer", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 7, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 12, "FantaMedia": 6.5, "Costo_Acquisto": 13, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Freuler", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.3, "Costo_Acquisto": 6, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5, "Costo_Acquisto": 13, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Jashari", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 5, "Scadenza_Contratto": "ago 26"},
        {"Nome": "De Roon", "Ruolo": "C", "Squadra_SerieA": "Atalanta", "Quotazione": 10, "FantaMedia": 6.4, "Costo_Acquisto": 9, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 14, "FantaMedia": 6.7, "Costo_Acquisto": 13, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Mandragora", "Ruolo": "C", "Squadra_SerieA": "Fiorentina", "Quotazione": 11, "FantaMedia": 6.3, "Costo_Acquisto": 18, "Scadenza_Contratto": "ago 26"},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 15, "FantaMedia": 6.9, "Costo_Acquisto": 18, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Buksa", "Ruolo": "A", "Squadra_SerieA": "Udinese", "Quotazione": 9, "FantaMedia": 6.5, "Costo_Acquisto": 7, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Dallinga", "Ruolo": "A", "Squadra_SerieA": "Bologna", "Quotazione": 12, "FantaMedia": 6.6, "Costo_Acquisto": 7, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Atalanta", "Quotazione": 13, "FantaMedia": 6.8, "Costo_Acquisto": 11, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 25, "FantaMedia": 7.8, "Costo_Acquisto": 27, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Camarda", "Ruolo": "A", "Squadra_SerieA": "Milan", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 3, "Scadenza_Contratto": "ago 26"},
        {"Nome": "Meister", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 7, "FantaMedia": 6.0, "Costo_Acquisto": 6, "Scadenza_Contratto": "ago 26"}
    ]

if 'giocatori_db' not in st.session_state:
    data_iniziale = [
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Como", "Quotazione": 27, "FantaMedia": 7.8, "Potenziale": 4, "Titolarita": 5},
        {"Nome": "Vardy", "Ruolo": "A", "Squadra_SerieA": "Cremonese", "Quotazione": 16, "FantaMedia": 7.2, "Potenziale": 3, "Titolarita": 4},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Juventus", "Quotazione": 11, "FantaMedia": 6.8, "Potenziale": 4, "Titolarita": 3},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 13, "FantaMedia": 7.5, "Potenziale": 4, "Titolarita": 5},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 18, "FantaMedia": 6.9, "Potenziale": 3, "Titolarita": 4},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 13, "FantaMedia": 6.7, "Potenziale": 4, "Titolarita": 4},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Potenziale": 5, "Titolarita": 5},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Potenziale": 3, "Titolarita": 4},
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Potenziale": 3, "Titolarita": 5},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Potenziale": 2, "Titolarita": 3}
    ]
    st.session_state.giocatori_db = pd.DataFrame(data_iniziale)

# --- BARRA LATERALE ---
st.sidebar.title("⚽ Fanta Manager Hub")

with st.sidebar.expander("📁 Importa Listone / Quotazioni"):
    st.markdown("Carica il file ufficiale di Fantagazzetta/FantaMaster (CSV o Excel). La colonna **Squadra** del listone popola automaticamente *Squadra_SerieA*.")
    listone_file = st.file_uploader("File Listone", type=["csv", "xlsx"], key="upload_listone")
    if listone_file is not None:
        try:
            if listone_file.name.endswith('.csv'):
                df_load = pd.read_csv(listone_file, encoding='utf-8', on_bad_lines='skip')
            else:
                df_load = pd.read_excel(listone_file)
            df_load.columns = [str(c).strip() for c in df_load.columns]
            col_mappa = {}
            for col in df_load.columns:
                c_low = str(col).lower()
                if 'nome' in c_low or 'giocatore' in c_low:
                    col_mappa[col] = 'Nome'
                elif c_low in ['r', 'ruolo']:
                    col_mappa[col] = 'Ruolo'
                elif 'squadra' in c_low or 'team' in c_low:
                    col_mappa[col] = 'Squadra_SerieA'
                elif 'quot' in c_low or 'valore' in c_low or 'fc' in c_low or 'qt' in c_low:
                    col_mappa[col] = 'Quotazione'
                elif 'fm' in c_low or 'fantamedia' in c_low or 'media' in c_low:
                    col_mappa[col] = 'FantaMedia'
            df_load = df_load.rename(columns=col_mappa)
            if 'Nome' in df_load.columns:
                df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                if 'Ruolo' not in df_load.columns: df_load['Ruolo'] = 'C'
                if 'Squadra_SerieA' not in df_load.columns: df_load['Squadra_SerieA'] = 'N/D'
                if 'Quotazione' not in df_load.columns: df_load['Quotazione'] = 10
                if 'FantaMedia' not in df_load.columns: df_load['FantaMedia'] = 6.0
                df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                fm_serie = df_load['FantaMedia']
                if isinstance(fm_serie, pd.DataFrame):
                    fm_serie = fm_serie.iloc[:, 0]
                df_load['FantaMedia'] = pd.to_numeric(fm_serie.astype(str).str.replace(',', '.', regex=False), errors='coerce').fillna(6.0)
                if 'Potenziale' not in df_load.columns: df_load['Potenziale'] = 3
                if 'Titolarita' not in df_load.columns: df_load['Titolarita'] = 3
                st.session_state.giocatori_db = df_load[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Potenziale', 'Titolarita']]
                st.sidebar.success("Listone importato! Squadre Serie A aggiornate dal file.")
            else:
                st.sidebar.error("Colonna 'Nome' non trovata.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

with st.sidebar.expander("📋 Importa Rose Esistenti"):
    st.markdown("Carica CSV/Excel con: **Squadra** (fantateam), **Nome**, **Ruolo**, **Costo**. Opzionale: **Squadra Serie A**, **Scadenza Contratto** (*mmm yy*).")
    rose_file = st.file_uploader("File Rose", type=["csv", "xlsx"], key="upload_rose")
    if rose_file is not None:
        try:
            if rose_file.name.endswith('.csv'):
                df_rose = pd.read_csv(rose_file, encoding='utf-8', on_bad_lines='skip')
            else:
                df_rose = pd.read_excel(rose_file)
            df_rose.columns = [str(c).strip().lower() for c in df_rose.columns]
            col_squadra = next((c for c in df_rose.columns if 'squadra' in c or 'fantateam' in c or 'proprietario' in c), None)
            col_nome = next((c for c in df_rose.columns if 'nome' in c or 'giocatore' in c), None)
            col_ruolo = next((c for c in df_rose.columns if 'ruolo' in c or 'r' == c), None)
            col_costo = next((c for c in df_rose.columns if 'costo' in c or 'prezzo' in c or 'pagato' in c or 'quot' in c), None)
            col_scadenza = next((c for c in df_rose.columns if 'scadenza' in c or 'contratto' in c or 'anno' in c), None)
            col_squadra_sa = next((c for c in df_rose.columns if 'squadra serie a' in c or 'team' in c or 'club' in c or 'serie a' in c), None)
            if col_squadra and col_nome:
                count_importati = 0
                for _, row in df_rose.iterrows():
                    sq_nome = str(row[col_squadra]).strip().upper()
                    sq_match = next((s for s in NOMI_SQUADRE if s.upper() in sq_nome or sq_nome in s.upper()), None)
                    if sq_match:
                        g_nome = str(row[col_nome]).strip()
                        g_ruolo = str(row[col_ruolo]).strip().upper() if col_ruolo and pd.notna(row[col_ruolo]) else "C"
                        g_costo = int(row[col_costo]) if col_costo and pd.notna(row[col_costo]) else 1
                        g_scadenza = normalizza_scadenza(row[col_scadenza]) if col_scadenza and pd.notna(row[col_scadenza]) else "N/D"
                        g_squadra_sa = None
                        if col_squadra_sa and pd.notna(row[col_squadra_sa]):
                            g_squadra_sa = str(row[col_squadra_sa]).strip()
                        db_g = st.session_state.giocatori_db
                        match_db = db_g[db_g['Nome'].str.lower() == g_nome.lower()]
                        squadra_sa = "N/D"
                        quot = 10
                        fm = 6.0
                        if not match_db.empty:
                            squadra_sa = match_db.iloc[0]['Squadra_SerieA']
                            quot = int(match_db.iloc[0]['Quotazione'])
                            fm = float(match_db.iloc[0]['FantaMedia'])
                            g_ruolo = str(match_db.iloc[0]['Ruolo'])
                        if g_squadra_sa:
                            squadra_sa = g_squadra_sa
                        if not any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_match]["rosa"]):
                            st.session_state.squadre[sq_match]["rosa"].append({
                                "Nome": g_nome, "Ruolo": g_ruolo, "Squadra_SerieA": squadra_sa,
                                "Quotazione": quot, "FantaMedia": fm, "Costo_Acquisto": int(g_costo),
                                "Scadenza_Contratto": g_scadenza
                            })
                            count_importati += 1
                st.sidebar.success(f"Importati {count_importati} giocatori nelle rose!")
            else:
                st.sidebar.error("Colonne essenziali mancanti.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

with st.sidebar.expander("📈 Importa Statistiche Storiche"):
    st.markdown("Carica CSV/Excel con colonne: **Nome**, **Stagione** (es. 2024-25), **FantaMedia**, **MediaVoto**, **Gol**, **Assist**, **Presenze**, **Rigori**, **Ammonizioni**, **Espulsioni**.")
    stats_file = st.file_uploader("File Statistiche 3 Anni", type=["csv", "xlsx"], key="upload_stats")
    if stats_file is not None:
        try:
            if stats_file.name.endswith('.csv'):
                df_stats = pd.read_csv(stats_file, encoding='utf-8', on_bad_lines='skip')
            else:
                df_stats = pd.read_excel(stats_file)
            df_stats.columns = [str(c).strip() for c in df_stats.columns]
            # Mappatura flessibile
            col_map = {}
            for col in df_stats.columns:
                cl = col.lower()
                if 'nome' in cl or 'giocatore' in cl:
                    col_map[col] = 'Nome'
                elif 'stagione' in cl or 'anno' in cl or 'season' in cl:
                    col_map[col] = 'Stagione'
                elif 'fantamedia' in cl or 'fm' == cl:
                    col_map[col] = 'FantaMedia'
                elif 'mediavoto' in cl or 'media voto' in cl or 'mv' == cl:
                    col_map[col] = 'MediaVoto'
                elif 'gol' in cl or 'goal' in cl:
                    col_map[col] = 'Gol'
                elif 'assist' in cl:
                    col_map[col] = 'Assist'
                elif 'presenze' in cl or 'pg' in cl or 'partite' in cl:
                    col_map[col] = 'Presenze'
                elif 'rigori' in cl or 'rigore' in cl:
                    col_map[col] = 'Rigori'
                elif 'ammonizioni' in cl or 'amm' in cl or 'gialli' in cl:
                    col_map[col] = 'Ammonizioni'
                elif 'espulsioni' in cl or 'esp' in cl or 'rossi' in cl:
                    col_map[col] = 'Espulsioni'
            df_stats = df_stats.rename(columns=col_map)
            req = ['Nome', 'Stagione']
            if all(r in df_stats.columns for r in req):
                imported = 0
                for _, row in df_stats.iterrows():
                    nome = str(row['Nome']).strip()
                    stagione = str(row['Stagione']).strip()
                    if nome not in st.session_state.statistiche_db:
                        st.session_state.statistiche_db[nome] = {}
                    record = {}
                    for k in ['FantaMedia', 'MediaVoto', 'Gol', 'Assist', 'Presenze', 'Rigori', 'Ammonizioni', 'Espulsioni']:
                        if k in df_stats.columns and pd.notna(row[k]):
                            record[k] = float(row[k]) if k in ['FantaMedia', 'MediaVoto'] else int(row[k])
                    if record:
                        st.session_state.statistiche_db[nome][stagione] = record
                        imported += 1
                st.sidebar.success(f"Importate {imported} righe statistiche!")
            else:
                st.sidebar.error("Colonne Nome e Stagione obbligatorie.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

menu = st.sidebar.selectbox("Navigazione", [
    "🔍 Scouting & Database",
    "🛒 Mercato (Acquisti/Vendite)",
    "🤝 Scambi tra Proprietà",
    "📋 Rose e Crediti (10 Squadre)",
    "📈 Statistiche & Trend 3 Anni"
])

# ==========================================
# 1. SCOUTING & DATABASE
# ==========================================
if menu == "🔍 Scouting & Database":
    st.header("🔍 Hub Scouting, Quotazioni & FantaMedie Avanzate")
    df = st.session_state.giocatori_db.copy()
    df["Indice_Affare"] = round(df["FantaMedia"] / df["Quotazione"].replace(0, 1), 2)

    giocatori_assegnati = {}
    for sq, dati in st.session_state.squadre.items():
        for g in dati["rosa"]:
            giocatori_assegnati[g["Nome"].lower()] = sq
    df["Proprietario"] = df["Nome"].apply(lambda x: giocatori_assegnati.get(x.lower(), "Svincolato 🟢"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ruoli_disponibili = df["Ruolo"].unique() if "Ruolo" in df.columns else ["P", "D", "C", "A"]
        filtro_ruolo = st.multiselect("Filtra per Ruolo", options=ruoli_disponibili, default=ruoli_disponibili)
    with col2:
        min_fm = st.slider("FantaMedia Minima", 4.0, 10.0, 5.0, 0.1)
    with col3:
        solo_svincolati = st.checkbox("Mostra solo Svincolati", value=False)
    with col4:
        search_nome = st.text_input("Cerca per Nome Giocatore")

    df_filtrato = df[(df["Ruolo"].isin(filtro_ruolo)) & (df["FantaMedia"] >= min_fm)]
    if solo_svincolati:
        df_filtrato = df_filtrato[df_filtrato["Proprietario"] == "Svincolato 🟢"]
    if search_nome:
        df_filtrato = df_filtrato[df_filtrato["Nome"].str.contains(search_nome, case=False, na=False)]
    df_filtrato = df_filtrato.sort_values(by="Indice_Affare", ascending=False)

    st.subheader(f"Risultati Scouting ({len(df_filtrato)} giocatori trovati)")
    st.dataframe(df_filtrato, use_container_width=True)

    st.markdown("---")
    st.subheader("⭐ Watchlist")
    g_watchlist = st.selectbox("Aggiungi giocatore alla Watchlist", df["Nome"].values, key="sel_watchlist")
    if st.button("Aggiungi alla Watchlist"):
        if g_watchlist not in st.session_state.watchlist:
            st.session_state.watchlist.append(g_watchlist)
            st.success(f"{g_watchlist} aggiunto!")
            st.rerun()
        else:
            st.warning("Gia' presente.")

    if len(st.session_state.watchlist) > 0:
        df_watch = df[df["Nome"].isin(st.session_state.watchlist)]
        st.dataframe(df_watch[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Indice_Affare", "Proprietario"]], use_container_width=True)
        if st.button("Svuota Watchlist"):
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.info("Watchlist vuota.")

# ==========================================
# 2. MERCATO
# ==========================================
elif menu == "🛒 Mercato (Acquisti/Vendite)":
    st.header("🛒 Gestione Mercato")
    tab_acq, tab_vend, tab_reg = st.tabs(["📥 Acquista da Svincolati", "📤 Vendi / Svincola", "📜 Registro Operazioni"])

    with tab_acq:
        st.subheader("Acquista un giocatore svincolato")
        squadra_selezionata = st.selectbox("Seleziona la tua Squadra", NOMI_SQUADRE, key="mercato_sq")
        crediti_disponibili = st.session_state.squadre[squadra_selezionata]["crediti"]
        rosa_attuale_len = len(st.session_state.squadre[squadra_selezionata]["rosa"])
        posti_rim = 25 - rosa_attuale_len
        offerta_max_ideale = crediti_disponibili - (posti_rim - 1) if posti_rim > 0 else 0
        budget_medio = crediti_disponibili / posti_rim if posti_rim > 0 else 0

        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
        col_m1.metric("Crediti Residui", f"{crediti_disponibili} 🪙")
        col_m2.metric("Giocatori in Rosa", f"{rosa_attuale_len} / 25")
        col_m3.metric("Offerta Max Ideale", f"{max(0, int(offerta_max_ideale))} 🪙")
        col_m4.metric("Budget Medio/Slot", f"{budget_medio:.1f} 🪙")

        giocatori_in_rosa = [g["Nome"].lower() for sq_data in st.session_state.squadre.values() for g in sq_data["rosa"]]
        db_g = st.session_state.giocatori_db
        svincolati = db_g[~db_g["Nome"].str.lower().isin(giocatori_in_rosa)]

        if len(svincolati) > 0:
            giocatore_scelto = st.selectbox("Seleziona Giocatore Svincolato", svincolati["Nome"].values)
            info_g = svincolati[svincolati["Nome"] == giocatore_scelto].iloc[0]
            prezzo_consigliato = int(info_g["Quotazione"])
            st.write(f"Ruolo: **{info_g['Ruolo']}** | Squadra Serie A: **{info_g['Squadra_SerieA']}** | Quotazione: **{prezzo_consigliato}** | FantaMedia: **{info_g['FantaMedia']}**")

            rosa_sq = st.session_state.squadre[squadra_selezionata]["rosa"]
            ruolo_target = info_g['Ruolo']
            giocatori_stesso_ruolo = [g for g in rosa_sq if g['Ruolo'] == ruolo_target]

            st.markdown("#### 📊 Paragone con la tua rosa")
            if giocatori_stesso_ruolo:
                nomi_paragone = st.multiselect(
                    f"Scegli quali {ruolo_target} in rosa paragonare",
                    options=[g['Nome'] for g in giocatori_stesso_ruolo],
                    default=[g['Nome'] for g in giocatori_stesso_ruolo],
                    key="paragone_acquisto"
                )
                selezionati = [g for g in giocatori_stesso_ruolo if g['Nome'] in nomi_paragone]
                if selezionati:
                    media_ruolo = sum(g['FantaMedia'] for g in selezionati) / len(selezionati)
                    media_costo = sum(g['Costo_Acquisto'] for g in selezionati) / len(selezionati)
                else:
                    media_ruolo = 0.0
                    media_costo = 0.0
            else:
                media_ruolo = 0.0
                media_costo = 0.0
                st.info(f"Nessun {ruolo_target} in rosa.")

            delta = round(info_g['FantaMedia'] - media_ruolo, 2)
            c1, c2, c3, c4 = st.columns(4)
            c1.metric("FantaMedia Target", f"{info_g['FantaMedia']}")
            c2.metric(f"Media {ruolo_target} selezionati", f"{media_ruolo:.2f}")
            c3.metric("Delta FM", f"{delta:+.2f}", delta=delta)
            if media_costo > 0:
                c4.metric(f"Costo Medio {ruolo_target}", f"{media_costo:.1f} 🪙")
            st.markdown("---")

            prezzo_acquisto = st.number_input("Prezzo di Acquisto (crediti)", min_value=1, max_value=max(1, crediti_disponibili), value=prezzo_consigliato, key="input_prezzo_acq")
            scadenza_nuova = scadenza_da_acquisto()
            st.caption(f"📝 Contratto: **{scadenza_nuova}** (4 anni)")

            if st.button("Conferma Acquisto"):
                if crediti_disponibili >= prezzo_acquisto:
                    st.session_state.squadre[squadra_selezionata]["crediti"] -= prezzo_acquisto
                    st.session_state.squadre[squadra_selezionata]["rosa"].append({
                        "Nome": giocatore_scelto, "Ruolo": info_g["Ruolo"], "Squadra_SerieA": info_g["Squadra_SerieA"],
                        "Quotazione": info_g["Quotazione"], "FantaMedia": info_g["FantaMedia"],
                        "Costo_Acquisto": prezzo_acquisto, "Scadenza_Contratto": scadenza_nuova
                    })
                    st.session_state.storico_mercato.insert(0, {
                        "Orario": datetime.now().strftime("%H:%M:%S"), "Operazione": "ACQUISTO",
                        "Dettagli": f"{squadra_selezionata} acquista {giocatore_scelto} ({info_g['Ruolo']}) per {prezzo_acquisto} cr. Scadenza: {scadenza_nuova}"
                    })
                    st.success(f"Acquisto completato!")
                    st.rerun()
                else:
                    st.error("Crediti insufficienti!")
        else:
            st.warning("Nessuno svincolato disponibile.")

    with tab_vend:
        st.subheader("Vendi / Svincola")
        sq_vendi = st.selectbox("Seleziona Squadra", NOMI_SQUADRE, key="vendi_sq")
        rosa_sq = st.session_state.squadre[sq_vendi]["rosa"]
        if len(rosa_sq) > 0:
            nomi_rosa = [g["Nome"] for g in rosa_sq]
            giocatore_da_vendere = st.selectbox("Seleziona giocatore", nomi_rosa, key="sel_vendi_giocatore")
            g_obj = next(item for item in rosa_sq if item["Nome"] == giocatore_da_vendere)
            prezzo_base = g_obj.get("Costo_Acquisto", 10)
            st.write(f"Ruolo: **{g_obj['Ruolo']}** | Squadra Serie A: **{g_obj.get('Squadra_SerieA', 'N/D')}** | Scadenza: **{g_obj.get('Scadenza_Contratto', 'N/D')}**")
            prezzo_vendita = st.number_input("Prezzo di vendita (crediti)", min_value=0, value=prezzo_base, key="input_prezzo_vend")
            if st.button("Conferma Vendita"):
                st.session_state.squadre[sq_vendi]["rosa"] = [g for g in rosa_sq if g["Nome"] != giocatore_da_vendere]
                st.session_state.squadre[sq_vendi]["crediti"] += prezzo_vendita
                st.session_state.storico_mercato.insert(0, {
                    "Orario": datetime.now().strftime("%H:%M:%S"), "Operazione": "SVINCOLO",
                    "Dettagli": f"{sq_vendi} svincola {giocatore_da_vendere}, +{prezzo_vendita} cr."
                })
                st.success(f"Cessione effettuata! +{prezzo_vendita} crediti.")
                st.rerun()
        else:
            st.info("Rosa vuota.")

    with tab_reg:
        st.subheader("📜 Storico Operazioni")
        if len(st.session_state.storico_mercato) > 0:
            st.dataframe(pd.DataFrame(st.session_state.storico_mercato), use_container_width=True)
        else:
            st.info("Nessuna operazione.")

# ==========================================
# 3. SCAMBI
# ==========================================
elif menu == "🤝 Scambi tra Proprietà":
    st.header("🤝 Scambi & Prestiti")
    c_off, c_ricev = st.columns(2)
    with c_off:
        st.subheader("Squadra 1 (Mittente)")
        sq1 = st.selectbox("Squadra 1", NOMI_SQUADRE, key="scambio_sq1")
        rosa_sq1 = st.session_state.squadre[sq1]["rosa"]
        giocatori_sq1_scelti = st.multiselect("Ceduti da Sq1", [g["Nome"] for g in rosa_sq1], key="g_sq1")
        denaro_sq1 = st.number_input(f"Conguaglio {sq1}", min_value=0, max_value=st.session_state.squadre[sq1]["crediti"], value=0, key="d_sq1")
    with c_ricev:
        st.subheader("Squadra 2 (Ricevente)")
        altre = [s for s in NOMI_SQUADRE if s != sq1]
        sq2 = st.selectbox("Squadra 2", altre, key="scambio_sq2")
        rosa_sq2 = st.session_state.squadre[sq2]["rosa"]
        giocatori_sq2_scelti = st.multiselect("Ceduti da Sq2", [g["Nome"] for g in rosa_sq2], key="g_sq2")
        denaro_sq2 = st.number_input(f"Conguaglio {sq2}", min_value=0, max_value=st.session_state.squadre[sq2]["crediti"], value=0, key="d_sq2")

    tipo_operazione = st.radio("Tipo", ["Scambio Definitivo", "Prestito con Diritto/Obbligo"])

    if st.button("Finalizza", type="primary"):
        if len(giocatori_sq1_scelti) == 0 and len(giocatori_sq2_scelti) == 0 and denaro_sq1 == 0 and denaro_sq2 == 0:
            st.warning("Seleziona qualcosa.")
        elif st.session_state.squadre[sq1]["crediti"] < denaro_sq1:
            st.error(f"{sq1} senza crediti.")
        elif st.session_state.squadre[sq2]["crediti"] < denaro_sq2:
            st.error(f"{sq2} senza crediti.")
        else:
            st.session_state.squadre[sq1]["crediti"] += -denaro_sq1 + denaro_sq2
            st.session_state.squadre[sq2]["crediti"] += -denaro_sq2 + denaro_sq1

            oggetti_sq1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] in giocatori_sq1_scelti]
            st.session_state.squadre[sq1]["rosa"] = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] not in giocatori_sq1_scelti]
            oggetti_sq2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] in giocatori_sq2_scelti]
            st.session_state.squadre[sq2]["rosa"] = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] not in giocatori_sq2_scelti]

            if tipo_operazione == "Scambio Definitivo":
                st.session_state.squadre[sq1]["rosa"].extend(oggetti_sq2)
                st.session_state.squadre[sq2]["rosa"].extend(oggetti_sq1)
                msg = f"Scambio definitivo {sq1} ↔ {sq2}."
                st.success(f"🎉 {msg}")
            else:
                for g in oggetti_sq1:
                    gc = g.copy(); gc["Prestito_A"] = sq2
                    st.session_state.squadre[sq1]["prestiti_ceduti"].append(gc)
                for g in oggetti_sq2:
                    gc = g.copy(); gc["Prestito_A"] = sq1
                    st.session_state.squadre[sq2]["prestiti_ceduti"].append(gc)
                for g in oggetti_sq2:
                    gp = g.copy(); gp["Nome"] = f"{gp['Nome']} (in prestito da {sq2})"; gp["Prestito"] = "ricevuto"; gp["Prestito_Da"] = sq2
                    st.session_state.squadre[sq1]["rosa"].append(gp)
                for g in oggetti_sq1:
                    gp = g.copy(); gp["Nome"] = f"{gp['Nome']} (in prestito da {sq1})"; gp["Prestito"] = "ricevuto"; gp["Prestito_Da"] = sq1
                    st.session_state.squadre[sq2]["rosa"].append(gp)
                msg = f"Prestito {sq1} ↔ {sq2}."
                st.success(f"🤝 {msg}")
            st.session_state.storico_mercato.insert(0, {"Orario": datetime.now().strftime("%H:%M:%S"), "Operazione": "SCAMBIO", "Dettagli": msg})
            st.rerun()

# ==========================================
# 4. ROSE E CREDITI
# ==========================================
elif menu == "📋 Rose e Crediti (10 Squadre)":
    st.header("📋 Rose, Crediti & Matrice")
    tab_singole, tab_matrice = st.tabs(["🛡️ Viste Singole", "📊 Riassuntiva Generale"])

    with tab_singole:
        tabs_squadre = st.tabs(NOMI_SQUADRE)
        for i, nome_sq in enumerate(NOMI_SQUADRE):
            with tabs_squadre[i]:
                dati = st.session_state.squadre[nome_sq]
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    st.subheader(f"🛡️ {nome_sq}")
                with col_b:
                    st.metric("Crediti", f"{dati['crediti']} 🪙")

                rosa_list = dati.get("rosa", [])
                prestiti_list = dati.get("prestiti_ceduti", [])
                rosa_df = pd.DataFrame(rosa_list) if rosa_list else pd.DataFrame()
                prestiti_df = pd.DataFrame(prestiti_list) if prestiti_list else pd.DataFrame()

                dfs = []
                if not rosa_df.empty:
                    rosa_df["Tipo_Vista"] = "In rosa"
                    dfs.append(rosa_df)
                if not prestiti_df.empty:
                    prestiti_df["Tipo_Vista"] = "Prestato"
                    dfs.append(prestiti_df)

                if dfs:
                    full_df = pd.concat(dfs, ignore_index=True)
                    for col in ["Squadra_SerieA", "Scadenza_Contratto", "Prestito", "Prestito_Da", "Prestito_A"]:
                        if col not in full_df.columns:
                            full_df[col] = None
                    full_df["Squadra_SerieA"] = full_df["Squadra_SerieA"].fillna("N/D")
                    full_df["Scadenza_Contratto"] = full_df["Scadenza_Contratto"].fillna("N/D")

                    def stato_contratto(row):
                        scad = row.get("Scadenza_Contratto", "N/D")
                        if is_in_scadenza(scad):
                            return "🚨 In scadenza"
                        dt = parse_scadenza(scad)
                        if dt and dt < datetime.now():
                            return "⏳ Scaduto"
                        return "✅ Attivo"
                    full_df["Stato"] = full_df.apply(stato_contratto, axis=1)

                    cols_pref = ["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Costo_Acquisto", "Scadenza_Contratto", "Stato", "Tipo_Vista"]
                    cols_presenti = [c for c in cols_pref if c in full_df.columns]
                    full_df = full_df[cols_presenti + [c for c in full_df.columns if c not in cols_pref]]

                    conti = rosa_df["Ruolo"].value_counts().to_dict() if not rosa_df.empty else {}
                    p, d, c, a = conti.get("P", 0), conti.get("D", 0), conti.get("C", 0), conti.get("A", 0)
                    n_prest = len(prestiti_df)
                    st.caption(f"P:{p} | D:{d} | C:{c} | A:{a} | Prestati:{n_prest} | Tot Rosa:{len(rosa_df)}")

                    def color_rows(row):
                        if row.get("Tipo_Vista") == "Prestato":
                            return ['background-color: rgba(255, 80, 80, 0.35)'] * len(row)
                        if row.get("Prestito") == "ricevuto" or "(in prestito da" in str(row.get("Nome", "")):
                            return ['background-color: rgba(80, 200, 80, 0.35)'] * len(row)
                        if is_in_scadenza(row.get('Scadenza_Contratto', 'N/D')):
                            return ['background-color: rgba(255, 165, 0, 0.25)'] * len(row)
                        return [''] * len(row)

                    st.dataframe(full_df.style.apply(color_rows, axis=1), use_container_width=True)
                else:
                    st.info("Rosa vuota.")

    with tab_matrice:
        st.subheader("📊 Quadro Generale")
        summary_data = []
        for sq in NOMI_SQUADRE:
            dati = st.session_state.squadre[sq]
            rosa = dati["rosa"]
            prestiti = dati.get("prestiti_ceduti", [])
            p = d = c = a = 0
            spesa = 0
            sa_set = set()
            for g in rosa:
                r = g.get("Ruolo", "C")
                if r == "P": p += 1
                elif r == "D": d += 1
                elif r == "C": c += 1
                elif r == "A": a += 1
                spesa += g.get("Costo_Acquisto", 0)
                sa = g.get("Squadra_SerieA", "")
                if sa and sa != "N/D":
                    sa_set.add(sa)
            summary_data.append({
                "Squadra": sq, "Crediti": dati["crediti"], "Spesa": spesa,
                "Tot": len(rosa), "P": p, "D": d, "C": c, "A": a,
                "Prestati": len(prestiti), "Club Serie A": ", ".join(sorted(sa_set)) if sa_set else "N/D"
            })
        st.dataframe(pd.DataFrame(summary_data), use_container_width=True)

# ==========================================
# 5. STATISTICHE & TREND 3 ANNI
# ==========================================
elif menu == "📈 Statistiche & Trend 3 Anni":
    st.header("📈 Database Statistiche - Ultimi 3 Anni")

    db_stats = st.session_state.statistiche_db
    db_listone = st.session_state.giocatori_db
    tutti_nomi = sorted(set(list(db_stats.keys()) + list(db_listone["Nome"].values)))

    col1, col2 = st.columns([2, 1])
    with col1:
        giocatore_stat = st.selectbox("Seleziona Giocatore", tutti_nomi, key="stat_giocatore")
    with col2:
        stagione_focus = st.selectbox("Focus Stagione", ["Tutte"] + STAGIONI_DISP, key="stat_stagione")

    # Info listone
    info_listone = db_listone[db_listone["Nome"] == giocatore_stat]
    ha_listone = not info_listone.empty

    if ha_listone:
        il = info_listone.iloc[0]
        st.markdown(f"**Listone attuale:** {il['Nome']} ({il['Ruolo']}) | {il['Squadra_SerieA']} | Quot: {il['Quotazione']} | FM: {il['FantaMedia']}")

    # Proprietario attuale
    prop = None
    for sq, dati in st.session_state.squadre.items():
        for g in dati["rosa"]:
            if g["Nome"].lower() == giocatore_stat.lower() or giocatore_stat.lower() in g["Nome"].lower():
                prop = sq
                break
        if prop: break
    if prop:
        st.markdown(f"🛡️ Attualmente in rosa a: **{prop}**")

    if giocatore_stat in db_stats and db_stats[giocatore_stat]:
        stats = db_stats[giocatore_stat]
        rows = []
        for stag in STAGIONI_DISP:
            if stag in stats:
                row = {"Stagione": stag}
                row.update(stats[stag])
                rows.append(row)
        if rows:
            df_stat = pd.DataFrame(rows)
            st.subheader("📊 Confronto Stagioni")
            st.dataframe(df_stat, use_container_width=True, hide_index=True)

            # Grafico trend FantaMedia
            st.subheader("📉 Trend FantaMedia")
            chart_df = df_stat[["Stagione", "FantaMedia"]].set_index("Stagione")
            st.line_chart(chart_df, use_container_width=True)

            # Grafico Gol + Assist
            if "Gol" in df_stat.columns and "Assist" in df_stat.columns:
                st.subheader("⚽ Gol & Assist")
                chart_ga = df_stat[["Stagione", "Gol", "Assist"]].set_index("Stagione")
                st.bar_chart(chart_ga, use_container_width=True)

            # Confronto con listone
            if ha_listone:
                fm_attuale = float(il['FantaMedia'])
                medie_passate = [stats[s]["FantaMedia"] for s in stats if "FantaMedia" in stats[s]]
                if medie_passate:
                    media_3y = sum(medie_passate) / len(medie_passate)
                    delta = round(fm_attuale - media_3y, 2)
                    c1, c2, c3 = st.columns(3)
                    c1.metric("FM Attuale Listone", f"{fm_attuale}")
                    c2.metric("Media 3 Anni", f"{media_3y:.2f}")
                    c3.metric("Delta", f"{delta:+.2f}", delta=delta)
        else:
            st.info("Nessun dato storico per le stagioni selezionate.")
    else:
        st.info("Nessuna statistica storica disponibile per questo giocatore. Importa un file o aggiungi dati manualmente.")

    # Sezione import manuale rapida
    st.markdown("---")
    st.subheader("➕ Aggiungi/Modifica Statistica Manuale")
    with st.form("form_stat"):
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            f_nome = st.text_input("Nome Giocatore", value=giocatore_stat if giocatore_stat else "")
        with c2:
            f_stag = st.selectbox("Stagione", STAGIONI_DISP)
        with c3:
            f_fm = st.number_input("FantaMedia", min_value=0.0, max_value=15.0, value=6.0, step=0.1)
        with c4:
            f_mv = st.number_input("Media Voto", min_value=0.0, max_value=10.0, value=6.0, step=0.1)
        c5, c6, c7, c8 = st.columns(4)
        with c5:
            f_gol = st.number_input("Gol", min_value=0, value=0)
        with c6:
            f_ass = st.number_input("Assist", min_value=0, value=0)
        with c7:
            f_pres = st.number_input("Presenze", min_value=0, max_value=38, value=0)
        with c8:
            f_rig = st.number_input("Rigori", min_value=0, value=0)
        c9, c10 = st.columns(2)
        with c9:
            f_amm = st.number_input("Ammonizioni", min_value=0, value=0)
        with c10:
            f_esp = st.number_input("Espulsioni", min_value=0, value=0)
        submitted = st.form_submit_button("Salva Statistica")
        if submitted:
            if f_nome.strip() == "":
                st.error("Inserisci il nome del giocatore.")
            else:
                if f_nome not in st.session_state.statistiche_db:
                    st.session_state.statistiche_db[f_nome] = {}
                st.session_state.statistiche_db[f_nome][f_stag] = {
                    "FantaMedia": f_fm, "MediaVoto": f_mv, "Gol": f_gol,
                    "Assist": f_ass, "Presenze": f_pres, "Rigori": f_rig,
                    "Ammonizioni": f_amm, "Espulsioni": f_esp
                }
                st.success(f"Statistiche {f_nome} - {f_stag} salvate!")
                st.rerun()
