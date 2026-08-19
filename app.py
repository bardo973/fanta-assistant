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

# --- 2. INIZIALIZZAZIONE STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state:
    st.session_state.squadre = {
        sq: {"crediti": 500, "rosa": []} for sq in NOMI_SQUADRE
    }

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []

if 'giocatori_db' not in st.session_state:
    # Database di esempio iniziale se non viene caricato il listone
    st.session_state.giocatori_db = pd.DataFrame([
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6},
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Como", "Quotazione": 25, "FantaMedia": 7.8},
        {"Nome": "Vardy", "Ruolo": "A", "Squadra_SerieA": "Cremonese", "Quotazione": 16, "FantaMedia": 7.2},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3}
    ])

# --- 3. BARRA LATERALE: IMPORTAZIONI ---
st.sidebar.title("⚽ FantaManager Hub")
st.sidebar.markdown("---")

# FUNZIONE DI SUPPORTO PER LETTURA FILE (EXCEL / CSV FALBACK)
def leggi_file_flessibile(file_oggetto):
    if file_oggetto.name.endswith('.csv'):
        return pd.read_csv(file_oggetto, encoding='utf-8', on_bad_lines='skip')
    else:
        try:
            return pd.read_excel(file_oggetto, engine='openpyxl')
        except ImportError:
            st.sidebar.error("⚠️ Errore: 'openpyxl' non installato. Converti il file in formato .csv prima di caricarlo!")
            return None

# Expander 1: Importazione Listone Generale
with st.sidebar.expander("📁 Importa Listone Generale", expanded=False):
    listone_file = st.file_uploader("Scegli file listone", type=["csv", "xlsx"], key="load_listone_main")
    if listone_file is not None:
        df_l = leggi_file_flessibile(listone_file)
        if df_l is not None:
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
            else:
                st.sidebar.error("Colonne minime 'Nome' e 'Ruolo' non trovate.")

# Expander 2: Importazione Rose Complete da File
with st.sidebar.expander("📁 Importa Rose da File", expanded=False):
    st.markdown("Il file deve contenere le colonne: **Giocatore** (o Nome), **Costo** (o Spesa), **FantaSquadra** (corrispondente ai 10 nomi ufficiali).")
    rose_file = st.file_uploader("Scegli file rose", type=["csv", "xlsx"], key="load_rose_file")
    if rose_file is not None:
        df_r = leggi_file_flessibile(rose_file)
        if df_r is not None:
            df_r.columns = [str(c).strip().lower() for c in df_r.columns]
            
            # Mappatura colonne
            f_sq_col, cost_col, name_col = None, None, None
            for col in df_r.columns:
                if 'fantasquadra' in col or 'squadra_fanta' in col or 'proprietario' in col or 'team' in col: f_sq_col = col
                elif 'costo' in col or 'spesa' in col or 'prezzo' in col or 'acquistato' in col: cost_col = col
                elif 'nome' in col or 'giocatore' in col or 'calciatore' in col: name_col = col
            
            if f_sq_col and cost_col and name_col:
                # Reset temporaneo delle rose correnti
                for sq in NOMI_SQUADRE:
                    st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
                
                errori_assegnazione = 0
                for _, row in df_r.iterrows():
                    f_team = str(row[f_sq_col]).upper().strip()
                    g_name = str(row[name_col]).strip()
                    g_cost = pd.to_numeric(row[cost_col], errors='coerce')
                    g_cost = int(g_cost) if not pd.isna(g_cost) else 1
                    
                    if f_team in NOMI_SQUADRE:
                        # Recupera statistiche dal listone se presenti, altrimenti usa default
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
                    else:
                        errori_assegnazione += 1
                
                st.sidebar.success("✅ Rose caricate e crediti ricalcolati!")
                if errori_assegnazione > 0:
                    st.sidebar.warning(f"⚠️ {errori_assegnazione} righe scartate (nomi fanta-squadre non corrispondenti).")
            else:
                st.sidebar.error("Colonne richieste non identificate automaticamente nel file.")

st.sidebar.markdown("### 🗺️ Navigazione")
scelta_menu = st.sidebar.radio("Vai alla sezione:", ["🔨 Martello Asta", "🔍 Scouting & Algoritmi", "🤝 Scambi & Prestiti", "📊 Rose & Tabellone", "📜 Registro Mercato"])

# --- 4. SEZIONE: MARTELLO ASTA ---
if scelta_menu == "🔨 Martello Asta":
    st.title("🔨 Pannello di Assegnazione Calciatori")
    col_sx, col_dx = st.columns()
    with col_sx:
        st.subheader("Registra un Acquisto")
        lista_nomi = sorted(st.session_state.giocatori_db['Nome'].unique())
        giocatore_scelto = st.selectbox("Cerca Calciatore nel Listone", lista_nomi)
        info_g = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'] == giocatore_scelto].iloc[0]
        
        # Algoritmo Prezzo Consigliato Base (FantaMedia pesata su Quotazione)
        prezzo_consigliato = max(int(info_g['Quotazione'] * (info_g['FantaMedia'] / 6.0)), 1)
        if info_g['Ruolo'] == 'A' and info_g['FantaMedia'] >= 7.5:
            prezzo_consigliato = int(prezzo_consigliato * 1.4) # Sovrapprezzo bomber
            
        st.info(f"📋 **Dettagli**: {info_g['Ruolo']} | {info_g['Squadra_SerieA']} | Quotazione: {info_g['Quotazione']} | FantaMedia: {info_g['FantaMedia']}")
        st.markdown(f"💡 **Prezzo Consigliato di Acquisto (Algoritmo):** `{prezzo_consigliato} crediti`")
        
        squadra_acquirente = st.selectbox("Assegna alla Squadra", NOMI_SQUADRE)
        prezzo_acquisto = st.number_input("Prezzo d'acquisto (Crediti)", min_value=1, max_value=500, value=int(info_g['Quotazione']))
        
        if st.button("Conferma e Salva Acquisto", type="primary"):
            dati_squadra = st.session_state.squadre[squadra_acquirente]
            ruolo_g = info_g['Ruolo']
            conteggio_ruoli = pd.DataFrame(dati_squadra["rosa"])['Ruolo'].value_counts().to_dict() if dati_squadra["rosa"] else {}
            num_nel_ruolo = conteggio_ruoli.get(ruolo_g, 0)
            
            if dati_squadra["crediti"] < prezzo_acquisto:
                st.error(f"Fondi insufficienti per {squadra_acquirente}!")
            elif len(dati_squadra["rosa"]) >= MAX_GIOCATORI:
                st.error("Rosa già piena!")
            elif num_nel_ruolo >= LIMITI_RUOLI.get(ruolo_g, 99):
                st.error(f"Slot esauriti per il ruolo {ruolo_g}!")
            else:
                nuovo_calciatore = {"Nome": info_g['Nome'], "Ruolo": ruolo_g, "Squadra_SerieA": info_g['Squadra_SerieA'], "Quotazione": info_g['Quotazione'], "FantaMedia": info_g['FantaMedia'], "Costo_Acquisto": prezzo_acquisto}
