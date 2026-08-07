import streamlit as st
import pandas as pd
from datetime import datetime
import json
import os

# Configurazione della pagina
st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

# --- FILE DI SALVATAGGIO PERSISTENTE ---
DB_FILE = "fantasquadre_backup.json"
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

# --- FUNZIONI DI SALVATAGGIO E CARICAMENTO SU DISCO ---
def carica_dati_da_disco():
    """Carica i dati salvati su file per non perdere nulla al riavvio."""
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    # Se il file non esiste, crea la struttura iniziale vuota
    struttura_iniziale = {}
    for sq in NOMI_SQUADRE:
        struttura_iniziale[sq] = {"crediti": 500, "rosa": []}
    return struttura_iniziale

def salva_dati_su_disco():
    """Salva istantaneamente lo stato delle squadre su file JSON."""
    with open(DB_FILE, "w", encoding="utf-8") as f:
        json.dump(st.session_state.squadre, f, ensure_ascii=False, indent=4)

# --- INIZIALIZZAZIONE SICURA DELLO STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state:
    st.session_state.squadre = carica_dati_da_disco()

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Ripristino database giocatori iniziale se vuoto
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
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Potenziale": 2, "Titolarita": 3},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 6, "FantaMedia": 6.1, "Potenziale": 3, "Titolarita": 3},
        {"Nome": "Lucumì", "Ruolo": "D", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Potenziale": 3, "Titolarita": 4}
    ]
    st.session_state.giocatori_db = pd.DataFrame(data_iniziale)

# --- FUNZIONI DI SUPPORTO ---
def calcola_crediti_rimanenti(nome_squadra):
    budget_iniziale = 500
    speso = sum(giocatore["Costo_Acquisto"] for giocatore in st.session_state.squadre[nome_squadra]["rosa"])
    return budget_iniziale - speso

def analizza_giocatori_senza_squadra():
    lista_db_nomi = set(st.session_state.giocatori_db['Nome'].str.lower().tolist())
    esuberi = []
    for sq in NOMI_SQUADRE:
        for g in st.session_state.squadre[sq]["rosa"]:
            if g["Nome"].lower() not in lista_db_nomi:
                esuberi.append({
                    "FantaSquadra": sq, "Nome": g["Nome"], "Ruolo": g["Ruolo"],
                    "Vecchia_Squadra": g["Squadra_SerieA"], "Costo_Acquisto": g["Costo_Acquisto"]
                })
    return pd.DataFrame(esuberi)

# --- BARRA LATERALE: GESTIONE FILE E NAVIGAZIONE ---
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
                if 'nome' in c_low or 'giocatore' in c_low: col_mappa[col] = 'Nome'
                elif c_low in ['r', 'ruolo']: col_mappa[col] = 'Ruolo'
                elif 'squadra' in c_low or 'team' in c_low: col_mappa[col] = 'Squadra_SerieA'
                elif 'quot' in c_low or 'valore' in c_low or 'fc' in c_low or 'qt' in c_low: col_mappa[col] = 'Quotazione'
                elif 'fm' in c_low or 'fantamedia' in c_low or 'media' in c_low: col_mappa[col] = 'FantaMedia'
                    
            df_load = df_load.rename(columns=col_mappa)
            if 'Nome' in df_load.columns:
                df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                if 'Ruolo' not in df_load.columns: df_load['Ruolo'] = 'C'
                if 'Squadra_SerieA' not in df_load.columns: df_load['Squadra_SerieA'] = 'N/D'
                if 'Quotazione' not in df_load.columns: df_load['Quotazione'] = 10
                if 'FantaMedia' not in df_load.columns: df_load['FantaMedia'] = 6.0
                
                df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                if df_load['FantaMedia'].dtype == object:
                    df_load['FantaMedia'] = df_load['FantaMedia'].astype(str).str.replace(',', '.')
                df_load['FantaMedia'] = pd.to_numeric(df_load['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                
                vecchio_db = st.session_state.giocatori_db[['Nome', 'Potenziale', 'Titolarita']].copy() if 'Potenziale' in st.session_state.giocatori_db.columns else pd.DataFrame(columns=['Nome', 'Potenziale', 'Titolarita'])
                df_unito = pd.merge(df_load, vecchio_db, on='Nome', how='left')
                df_unito['Potenziale'] = df_unito['Potenziale'].fillna(3).astype(int)
                df_unito['Titolarita'] = df_unito['Titolarita'].fillna(3).astype(int)
                
                colonne_finali = ['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Potenziale', 'Titolarita']
                st.session_state.giocatori_db = df_unito[[c for c in colonne_finali if c in df_unito.columns]]
                st.sidebar.success("✅ Listone integrato!")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

# Pulsante di backup manuale di sicurezza
if st.sidebar.button("💾 Salva Backup Ora", use_container_width=True):
    salva_dati_su_disco()
    st.sidebar.success("Backup salvato su file!")

opzione_menu = st.sidebar.radio("Vai a:", ["📊 Dashboard & Classifiche", "🛒 Sessione Mercato", "🕵️ Scouting Hub & Listone", "📋 Rose Squadre"])

# --- VISTA 1: DASHBOARD ---
if opzione_menu == "📊 Dashboard & Classifiche":
    st.title("📊 Stato delle Leghe & Budget")
    df_esuberi_totali = analizza_giocatori_senza_squadra()
    
    dati_dashboard = []
    for sq in NOMI_SQUADRE:
        rosa = st.session_state.squadre[sq]["rosa"]
        cred_residui = calcola_crediti_rimanenti(sq)
        num_senza_squadra = len(df_esuberi_totali[df_esuberi_totali['FantaSquadra'] == sq]) if not df_esuberi_totali.empty else 0
        
        dati_dashboard.append({
            "Squadra": sq, "Crediti Residui": cred_residui, "Giocatori in Rosa": len(rosa),
            "Esuberi (Senza Squadra) ⚠️": f"⚠️ {num_senza_squadra}" if num_senza_squadra > 0 else "0",
            "Portieri": sum(1 for p in rosa if p["Ruolo"] == "P"), "Difensori": sum(1 for p in rosa if p["Ruolo"] == "D"),
            "Centrocampisti": sum(1 for p in rosa if p["Ruolo"] == "C"), "Attaccanti": sum(1 for p in rosa if p["Ruolo"] == "A")
        })
    
    df_dash = pd.DataFrame(dati_dashboard)
    col1, col2, col3 = st.columns(3)
    col1.metric("Squadra Più Ricca", df_dash.loc[df_dash['Crediti Residui'].idxmax()]['Squadra'], f"{df_dash['Crediti Residui'].max()} cr")
    col2.metric("Calciatori Senza Squadra in Lega", len(df_esuberi_totali))
    col3.metric("Totale Operazioni", len(st.session_state.storico_mercato))
    
    st.markdown("### 🏆 Tabella Riepilogativa Fanta-Squadre")
    st.dataframe(df_dash, use_container_width=True, hide_index=True)

# --- VISTA 2: MERCATO ---
elif opzione_menu == "🛒 Sessione Mercato":
    st.title("🛒 Pannello di Controllo Asta e Mercato")
    col_A, col_B = st.columns()
    
    with col_A:
        st.subheader("🔨 Registra Acquisto")
        acquirente = st.selectbox("Seleziona chi acquista:", NOMI_SQUADRE)
        cerca_giocatore = st.text_input("Cerca giocatore da inserire (Nome):")
        
        suggeriti = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'].str.contains(cerca_giocatore, case=False, na=False)] if cerca_giocatore else st.session_state.giocatori_db
            
        if not suggeriti.empty:
            player_scelto = st.selectbox("Seleziona il profilo esatto:", suggeriti['Nome'].tolist())
            p_info = suggeriti[suggeriti['Nome'] == player_scelto].iloc[0]
            
