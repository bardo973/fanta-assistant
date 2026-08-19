import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(
    page_title="FantaManager Pro v2 - Advanced Hub", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. CONFIGURAZIONE COSTANTI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
LIMITI_RUOLI = {"P": 3, "D": 8, "C": 8, "A": 6}
MAX_GIOCATORI = sum(LIMITI_RUOLI.values()) # 25 giocatori

# --- 2. INIZIALIZZAZIONE SICURA E POPOLAMENTO DATI DI ESEMPIO ---
if 'giocatori_db' not in st.session_state:
    # Generiamo un listone iniziale ricco per sbloccare subito lo Scouting e il Martello Asta
    st.session_state.giocatori_db = pd.DataFrame([
        {"Nome": "Lautaro Martinez", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 38, "FantaMedia": 8.5},
        {"Nome": "Vlahovic", "Ruolo": "A", "Squadra_SerieA": "Juventus", "Quotazione": 34, "FantaMedia": 8.1},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 18, "FantaMedia": 7.5},
        {"Nome": "Pulisic", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 22, "FantaMedia": 7.9},
        {"Nome": "Orsolini", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 16, "FantaMedia": 7.2},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 12, "FantaMedia": 6.8},
        {"Nome": "Dimarco", "Ruolo": "D", "Squadra_SerieA": "Inter", "Quotazione": 15, "FantaMedia": 7.1},
        {"Nome": "Buongiorno", "Ruolo": "D", "Squadra_SerieA": "Napoli", "Quotazione": 14, "FantaMedia": 6.6},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 8, "FantaMedia": 6.3},
        {"Nome": "Sommer", "Ruolo": "P", "Squadra_SerieA": "Inter", "Quotazione": 18, "FantaMedia": 5.6},
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 11, "FantaMedia": 5.2},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Como", "Quotazione": 10, "FantaMedia": 7.4} # Ottima efficienza per lo scouting
    ])

if 'squadre' not in st.session_state:
    st.session_state.squadre = {
        sq: {"crediti": 500, "rosa": []} for sq in NOMI_SQUADRE
    }
    # Pre-carichiamo qualche giocatore di esempio nelle rose per popolare subito "Rose & Tabellone" e "Scambi"
    st.session_state.squadre["BARDO"]["rosa"] = [
        {"Nome": "Lautaro Martinez", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 38, "FantaMedia": 8.5, "Costo_Acquisto": 120},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 8, "FantaMedia": 6.3, "Costo_Acquisto": 12}
    ]
    st.session_state.squadre["BARDO"]["crediti"] = 500 - 120 - 12

    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Pulisic", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 22, "FantaMedia": 7.9, "Costo_Acquisto": 65},
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 11, "FantaMedia": 5.2, "Costo_Acquisto": 15}
    ]
    st.session_state.squadre["PECU"]["crediti"] = 500 - 65 - 15

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = [
        {"Orario": "Inizio", "Squadra": "BARDO", "Giocatore": "Lautaro Martinez", "Ruolo": "A", "Costo": 120, "Tipo": "Acquisto Asta"},
        {"Orario": "Inizio", "Squadra": "PECU", "Giocatore": "Pulisic", "Ruolo": "C", "Costo": 65, "Tipo": "Acquisto Asta"}
    ]

# --- 3. FUNZIONE DI LETTURA CON PREVENZIONE CRASH EXCEL ---
def leggi_file_flessibile(file_oggetto):
    try:
        if file_oggetto.name.endswith('.csv'):
            return pd.read_csv(file_oggetto, encoding='utf-8', on_bad_lines='skip')
        else:
            try:
                return pd.read_excel(file_oggetto, engine='openpyxl')
            except ImportError:
                st.sidebar.error("⚠️ Errore openpyxl: Installa openpyxl o usa un file .csv!")
                return None
    except Exception as e:
        st.sidebar.error(f"⚠️ Impossibile leggere il file: {e}")
        return None

# --- 4. BARRA LATERALE: GESTIONE CARICAMENTI ---
st.sidebar.title("⚽ FantaManager Hub")
st.sidebar.markdown("---")

# Importazione Listone Generale
with st.sidebar.expander("📁 Importa Listone Generale", expanded=False):
    listone_file = st.file_uploader("Scegli file listone", type=["csv", "xlsx"], key="load_listone_main")
    if listone_file is not None:
        df_l = leggi_file_flessibile(listone_file)
        if df_l is not None:
            try:
                df_l.columns = [str(c).strip().lower() for c in df_l.columns]
                col_mappa = {}
                for col in df_l.columns:
                    if 'nome' in col or 'giocatore' in col: col_mappa[col] = 'Nome'
                    elif col in ['r', 'ruolo']: col_mappa[col] = 'Ruolo'
                    elif 'squadra' in col or 'team' in col: col_mappa[col] = 'Squadra_SerieA'
                    elif 'quot' in col or 'valore' in col or 'qt' in col: col_mappa[col] = 'Quotazione'
                    elif 'fm' in col or 'fantamedia' in col or 'media' in col: col_mappa[col] = 'FantaMedia'
                
                df_l = df_l.rename(columns=col_mappa)
                if 'Nome' in df_l.columns and 'Ruolo' in df_l.columns:
                    df_l = df_l.loc[:, ~df_l.columns.duplicated()]
                    if 'Squadra_SerieA' not in df_l.columns: df_l['Squadra_SerieA'] = 'N/D'
                    if 'Quotazione' not in df_l.columns: df_l['Quotazione'] = 1
                    if 'FantaMedia' not in df_l.columns: df_l['FantaMedia'] = 6.0
                    
                    df_l['Quotazione'] = pd.to_numeric(df_l['Quotazione'], errors='coerce').fillna(1).astype(int)
                    df_l['FantaMedia'] = pd.to_numeric(df_l['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                    df_l['Ruolo'] = df_l['Ruolo'].str.upper().str.strip()
                    
                    st.session_state.giocatori_db = df_l[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']].copy()
                    st.sidebar.success(f"✅ Listone aggiornato: {len(df_l)} giocatori.")
                    st.rerun()
                else:
                    st.sidebar.error("Intestazioni 'Nome' e 'Ruolo' non trovate nel file.")
            except Exception as e:
                st.sidebar.error(f"Errore elaborazione dati listone: {e}")

# Importazione Rose Complete da File
with st.sidebar.expander("📁 Importa Rose da File", expanded=False):
    st.markdown("Colonne richieste: **Giocatore** (o Nome), **Costo**, **FantaSquadra**.")
    rose_file = st.file_uploader("Scegli file rose", type=["csv", "xlsx"], key="load_rose_file")
    if rose_file is not None:
        df_r = leggi_file_flessibile(rose_file)
        if df_r is not None:
            try:
                df_r.columns = [str(c).strip().lower() for c in df_r.columns]
                f_sq_col, cost_col, name_col = None, None, None
                for col in df_r.columns:
                    if 'fantasquadra' in col or 'squadra_fanta' in col or 'proprietario' in col or 'team' in col: f_sq_col = col
                    elif 'costo' in col or 'spesa' in col or 'prezzo' in col or 'acquistato' in col: cost_col = col
                    elif 'nome' in col or 'giocatore' in col or 'calciatore' in col: name_col = col
                
                if f_sq_col and cost_col and name_col:
                    for sq in NOMI_SQUADRE:
                        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
                    
                    for _, row in df_r.iterrows():
                        f_team = str(row[f_sq_col]).upper().strip()
                        g_name = str(row[name_col]).strip()
                        g_cost = pd.to_numeric(row[cost_col], errors='coerce')
                        g_cost = int(g_cost) if not pd.isna(g_cost) else 1
                        
                        if f_team in NOMI_SQUADRE:
                            match_db = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'].str.lower() == g_name.lower()]
                            if not match_db.empty:
                                ruolo = match_db.iloc[0]['Ruolo']
                                team_a = match_db.iloc[0]['Squadra_SerieA']
                                quot = match_db.iloc[0]['Quotazione']
                                fm = match_db.iloc[0]['FantaMedia']
                            else:
                                ruolo, team_a, quot, fm = "C", "N/D", 1, 6.0
                            
                            nuovo_c = {"Nome": g_name, "Ruolo": ruolo, "Squadra_SerieA": team_a, "Quotazione": quot, "FantaMedia": fm, "Costo_Acquisto": g_cost}
                            st.session_state.squadre[f_team]["rosa"].append(nuovo_c)
                            st.session_state.squadre[f_team]["crediti"] -= g_cost
                    
                    st.sidebar.success("✅ Rose caricate correttamente!")
                    st.rerun()
                else:
                    st.sidebar.error("Colonne richieste non identificate nel file.")
            except Exception as e:
                st.sidebar.error(f"Errore caricamento rose: {e}")

st.sidebar.markdown("### 🗺️ Navigazione")
scelta_menu = st.sidebar.radio("Vai alla sezione:", ["🔨 Martello Asta", "🔍 Scouting & Algoritmi", "🤝 Scambi & Prestiti", "📊 Rose & Tabellone", "📜 Registro Mercato"])

# --- 5. SEZIONE: MARTELLO ASTA ---
if scelta_menu == "🔨 Martello Asta":
    st.title("🔨 Pannello di Assegnazione Calciatori")
    col_sx, col_dx = st.columns(2)
    
    with col_sx:
        st.subheader("Registra un Acquisto")
        if not st.session_state.giocatori_db.empty:
            lista_nomi = sorted(st.session_state.giocatori_db['Nome'].unique())
