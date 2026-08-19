import streamlit as st
import pandas as pd
from datetime import datetime

st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

# --- LISTA DELLE 10 SQUADRE UFFICIALI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

# --- INIZIALIZZAZIONE SICURA DELLO STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state or not isinstance(st.session_state.squadre, dict):
    st.session_state.squadre = {}

for sq in NOMI_SQUADRE:
    if sq not in st.session_state.squadre:
        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Rosa precaricata di esempio per PECU con colonna 'Scadenza'
if len(st.session_state.squadre["PECU"]["rosa"]) == 0:
    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Costo_Acquisto": 14, "Scadenza": "2026"},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Costo_Acquisto": 8, "Scadenza": "2027"},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 6, "FantaMedia": 6.1, "Costo_Acquisto": 6, "Scadenza": "2026"},
        {"Nome": "Lucumì", "Ruolo": "D", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 6, "Scadenza": "2028"},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Costo_Acquisto": 10, "Scadenza": "2027"},
        {"Nome": "Biraghi", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 1, "Scadenza": "2026"},
        {"Nome": "Ranieri L.", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 6, "Scadenza": "2026"},
        {"Nome": "Maripan", "Ruolo": "D", "Squadra_SerieA": "Torino", "Quotazione": 9, "FantaMedia": 6.2, "Costo_Acquisto": 9, "Scadenza": "2027"},
        {"Nome": "Mina", "Ruolo": "D", "Squadra_SerieA": "Cagliari", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 7, "Scadenza": "2026"},
        {"Nome": "Juan Jesus", "Ruolo": "D", "Squadra_SerieA": "Napoli", "Quotazione": 6, "FantaMedia": 5.9, "Costo_Acquisto": 4, "Scadenza": "2026"},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Costo_Acquisto": 9, "Scadenza": "2028"},
        {"Nome": "Aebischer", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 7, "Scadenza": "2027"},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 12, "FantaMedia": 6.5, "Costo_Acquisto": 13, "Scadenza": "2026"},
        {"Nome": "Freuler", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.3, "Costo_Acquisto": 6, "Scadenza": "2027"},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5, "Costo_Acquisto": 13, "Scadenza": "2028"},
        {"Nome": "Jashari", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 5, "Scadenza": "2029"},
        {"Nome": "De Roon", "Ruolo": "C", "Squadra_SerieA": "Atalanta", "Quotazione": 10, "FantaMedia": 6.4, "Costo_Acquisto": 9, "Scadenza": "2026"},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 14, "FantaMedia": 6.7, "Costo_Acquisto": 13, "Scadenza": "2027"},
        {"Nome": "Mandragora", "Ruolo": "C", "Squadra_SerieA": "Fiorentina", "Quotazione": 11, "FantaMedia": 6.3, "Costo_Acquisto": 18, "Scadenza": "2027"},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 15, "FantaMedia": 6.9, "Costo_Acquisto": 18, "Scadenza": "2028"},
        {"Nome": "Buksa", "Ruolo": "A", "Squadra_SerieA": "Udinese", "Quotazione": 9, "FantaMedia": 6.5, "Costo_Acquisto": 7, "Scadenza": "2027"},
        {"Nome": "Dallinga", "Ruolo": "A", "Squadra_SerieA": "Bologna", "Quotazione": 12, "FantaMedia": 6.6, "Costo_Acquisto": 7, "Scadenza": "2028"},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Atalanta", "Quotazione": 13, "FantaMedia": 6.8, "Costo_Acquisto": 11, "Scadenza": "2026"},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 25, "FantaMedia": 7.8, "Costo_Acquisto": 27, "Scadenza": "2027"},
        {"Nome": "Camarda", "Ruolo": "A", "Squadra_SerieA": "Milan", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 3, "Scadenza": "2029"},
        {"Nome": "Meister", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 7, "FantaMedia": 6.0, "Costo_Acquisto": 6, "Scadenza": "2027"}
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

# --- BARRA LATERALE: GESTIONE FILE E CONFIGURAZIONE ---
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
                
                df_load['FantaMedia'] = (
                    fm_serie.astype(str).str.replace(',', '.', regex=False)
                    if fm_serie.dtype == object 
                    else fm_serie
                )
                df_load['FantaMedia'] = pd.to_numeric(df_load['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                
                colonne_finali = ['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']
                df_scouting = df_load[colonne_finali].copy()
                df_scouting['Potenziale'] = 3
                df_scouting['Titolarita'] = 3
                
                st.session_state.giocatori_db = df_scouting
                st.sidebar.success(f"✅ Caricati con successo {len(df_scouting)} giocatori!")
            else:
                st.sidebar.error("❌ Errore: Colonna 'Nome' o 'Giocatore' non trovata nel file.")
        except Exception as e:
            st.sidebar.error(f"❌ Errore durante il caricamento: {e}")

# --- CORPO PRINCIPALE ---
st.title("⚽ FantaManager & Scouting Hub")
tab1, tab2, tab3, tab4 = st.tabs(["📋 Rose e Scadenze", "🔨 Mercato & Aste", "🔍 Scouting & DB", "📊 Log Mercato"])

# --- TAB 1: ROSE E SCADENZE ---
with tab1:
