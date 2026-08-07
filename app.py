import streamlit as st
import pandas as pd

# 1. CONFIGURAZIONE PAGINA
st.set_page_config(page_title="FantaManager & Scouting Hub", page_icon="⚽", layout="wide")

# 2. COSTANTI UFFICIALI
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
BUDGET_INIZIALE = 500

# 3. INIZIALIZZAZIONE STATO DELLA SESSIONE (DATABASE TEMPORANEO)
if 'squadre' not in st.session_state:
    st.session_state.squadre = {sq: {"rosa": []} for sq in NOMI_SQUADRE}

# Carichiamo la tua rosa iniziale di esempio per PECU
if len(st.session_state.squadre["PECU"]["rosa"]) == 0:
    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Costo_Acquisto": 14},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Costo_Acquisto": 8},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 6, "FantaMedia": 6.1, "Costo_Acquisto": 6},
        {"Nome": "Lucumì", "Ruolo": "D", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 6},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Costo_Acquisto": 10},
        {"Nome": "Biraghi", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 1},
        {"Nome": "Ranieri L.", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 6},
        {"Nome": "Maripan", "Ruolo": "D", "Squadra_SerieA": "Torino", "Quotazione": 9, "FantaMedia": 6.2, "Costo_Acquisto": 9},
        {"Nome": "Mina", "Ruolo": "D", "Squadra_SerieA": "Cagliari", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 7},
        {"Nome": "Juan Jesus", "Ruolo": "D", "Squadra_SerieA": "Napoli", "Quotazione": 6, "FantaMedia": 5.9, "Costo_Acquisto": 4},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Costo_Acquisto": 9},
        {"Nome": "Aebischer", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 7},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 12, "FantaMedia": 6.5, "Costo_Acquisto": 13},
        {"Nome": "Freuler", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.3, "Costo_Acquisto": 6},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5, "Costo_Acquisto": 13},
        {"Nome": "Jashari", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 5},
        {"Nome": "De Roon", "Ruolo": "C", "Squadra_SerieA": "Atalanta", "Quotazione": 10, "FantaMedia": 6.4, "Costo_Acquisto": 9},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 14, "FantaMedia": 6.7, "Costo_Acquisto": 13},
        {"Nome": "Mandragora", "Ruolo": "C", "Squadra_SerieA": "Fiorentina", "Quotazione": 11, "FantaMedia": 6.3, "Costo_Acquisto": 18},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 15, "FantaMedia": 6.9, "Costo_Acquisto": 18},
        {"Nome": "Buksa", "Ruolo": "A", "Squadra_SerieA": "Udinese", "Quotazione": 9, "FantaMedia": 6.5, "Costo_Acquisto": 7},
        {"Nome": "Dallinga", "Ruolo": "A", "Squadra_SerieA": "Bologna", "Quotazione": 12, "FantaMedia": 6.6, "Costo_Acquisto": 7},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Atalanta", "Quotazione": 13, "FantaMedia": 6.8, "Costo_Acquisto": 11},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 25, "FantaMedia": 7.8, "Costo_Acquisto": 27},
        {"Nome": "Camarda", "Ruolo": "A", "Squadra_SerieA": "Milan", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 3},
        {"Nome": "Meister", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 7, "FantaMedia": 6.0, "Costo_Acquisto": 6}
    ]

# Inizializzazione del listone base con i dati di esempio (inclusi Potenziale e Titolarità)
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

# --- FUNZIONI DI CALCOLO INTERNE ---
def calcola_crediti_residui(nome_squadra):
    operazioni = st.session_state.squadre[nome_squadra]["rosa"]
    speso = sum(giocatore["Costo_Acquisto"] for giocatore in operazioni)
    return BUDGET_INIZIALE - speso

# --- BARRA LATERALE: CARICAMENTO FILE ---
st.sidebar.title("⚽ Fanta Manager & Scouting")

with st.sidebar.expander("📁 Importa Listone Ufficiale", expanded=True):
    st.markdown("Carica il file Excel o CSV ottenuto dalle piattaforme.")
    file_caricato = st.file_uploader("Scegli file", type=["csv", "xlsx"])
    
    if file_caricato is not None:
        try:
            # Lettura flessibile del formato
            df_nuovo = pd.read_csv(file_caricato, encoding='utf-8', on_bad_lines='skip') if file_caricato.name.endswith('.csv') else pd.read_excel(file_caricato)
            
            # Normalizzazione nomi colonne
            df_nuovo.columns = [str(col).strip().lower() for col in df_nuovo.columns]
            
            # Mappatura intelligente delle intestazioni
            mappa = {}
            for col in df_nuovo.columns:
                if 'nome' in col or 'giocatore' in col: mappa[col] = 'Nome'
                elif col in ['r', 'ruolo']: mappa[col] = 'Ruolo'
                elif 'squadra' in col or 'team' in col: mappa[col] = 'Squadra_SerieA'
                elif 'quot' in col or 'valore' in col or 'qt' in col: mappa[col] = 'Quotazione'
                elif 'fm' in col or 'fantamedia' in col or 'media' in col: mappa[col] = 'FantaMedia'
            
            df_nuovo = df_nuovo.rename(columns=mappa)
            
            if 'Nome' in df_nuovo.columns:
                df_nuovo = df_nuovo.loc[:, ~df_nuovo.columns.duplicated()]
                
                # Definizione dei valori mancanti di base
                if 'Ruolo' not in df_nuovo.columns: df_nuovo['Ruolo'] = 'C'
                if 'Squadra_SerieA' not in df_nuovo.columns: df_nuovo['Squadra_SerieA'] = 'N/D'
                if 'Quotazione' not in df_nuovo.columns: df_nuovo['Quotazione'] = 10
                if 'FantaMedia' not in df_nuovo.columns: df_nuovo['FantaMedia'] = 6.0
                
                # Sanificazione dei tipi di dato
                df_nuovo['Quotazione'] = pd.to_numeric(df_nuovo['Quotazione'], errors='coerce').fillna(10).astype(int)
                if df_nuovo['FantaMedia'].dtype == object:
                    df_nuovo['FantaMedia'] = df_nuovo['FantaMedia'].astype(str).str.replace(',', '.')
                df_nuovo['FantaMedia'] = pd.to_numeric(df_nuovo['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                
                # --- INTEGRAZIONE DELLE STATISTICHE ESISTENTI (MERGE BLINDATO) ---
                # Estraiamo l'anagrafica attuale delle statistiche per non perderle mai
                statistiche_vecchie = st.session_state.giocatori_db[['Nome', 'Potenziale', 'Titolarita']].copy() if 'Potenziale' in st.session_state.giocatori_db.columns else pd.DataFrame(columns=['Nome', 'Potenziale', 'Titolarita'])
                
                # Fondiamo il nuovo listone con le vecchie colonne basandoci sul Nome esatto
                df_fuso = pd.merge(df_nuovo, statistiche_vecchie, on='Nome', how='left')
                
                # Per i nuovi acquisti inseriti nel listone compiliamo i campi vuoti senza rompere l'interfaccia
                df_fuso['Potenziale'] = df_fuso['Potenziale'].fillna(3).astype(int)
                df_fuso['Titolarita'] = df_fuso['Titolarita'].fillna(3).astype(int)
                
                # Filtriamo la struttura definitiva del database
                colonne_finali = ['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Potenziale', 'Titolarita']
                st.session_state.giocatori_db = df_fuso[[c for c in colonne_finali if c in df_fuso.columns]]
                st.sidebar.success("✅ Listone aggiornato! Statistiche integrate salvate.")
        except Exception as err:
