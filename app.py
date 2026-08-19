
part1 = """import streamlit as st
import pandas as pd
from datetime import datetime
import re

st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

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

st.sidebar.title("⚽ Fanta Manager Hub")

with st.sidebar.expander("📁 Importa Listone / Quotazioni"):
    st.markdown("Carica il file ufficiale di Fantagazzetta/FantaMaster (CSV o Excel).")
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
                st.sidebar.success("Listone importato con successo!")
            else:
                st.sidebar.error("Impossibile trovare la colonna 'Nome' nel file.")
        except Exception as e:
            st.sidebar.error(f"Errore nella lettura: {e}")

with st.sidebar.expander("📋 Importa Rose Esistenti"):
    st.markdown("Carica un file CSV/Excel con le rose. Colonne: **Squadra** (fantateam), **Nome**, **Ruolo**, **Costo**, opzionale: **Squadra Serie A**, **Scadenza Contratto** (formato: *mmm yy*).")
    rose_file = st.file_uploader("File Rose (10 Squadre)", type=["csv", "xlsx"], key="upload_rose")
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
                st.sidebar.success(f"Importati {count_importati} giocatori nelle rose con successo!")
            else:
                st.sidebar.error("Colonne essenziali mancanti ('Squadra' o 'Nome').")
        except Exception as e:
            st.sidebar.error(f"Errore caricamento rose: {e}")

menu = st.sidebar.selectbox("Navigazione", [
    "🔍 Scouting & Database", 
    "🛒 Mercato (Acquisti/Vendite)", 
    "🤝 Scambi tra Proprietà", 
    "📋 Rose e Crediti (10 Squadre)"
])
"""

with open('/mnt/agents/output/fanta_manager.py', 'w') as f:
    f.write(part1)
print("Part 1 scritta")
