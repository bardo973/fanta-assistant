import streamlit as st
import pandas as pd
from datetime import datetime

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(
    page_title="FantaManager Pro - 10 Squadre", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. CONFIGURAZIONE COSTANTI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
LIMITI_RUOLI = {"P": 3, "D": 8, "C": 8, "A": 6}
MAX_GIOCATORI = sum(LIMITI_RUOLI.values()) # 25 giocatori

# --- 2. INIZIALIZZAZIONE STATO DELLA SESSIONE (DATI PERSISTENTI) ---
if 'squadre' not in st.session_state:
    st.session_state.squadre = {
        sq: {"crediti": 500, "rosa": []} for sq in NOMI_SQUADRE
    }

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

if 'giocatori_db' not in st.session_state:
    # Database iniziale di emergenza / dimostrativo
    st.session_state.giocatori_db = pd.DataFrame([
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6},
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Como", "Quotazione": 25, "FantaMedia": 7.8}
    ])

# --- 3. BARRA LATERALE: STRUMENTI E CARICAMENTO FILE ---
st.sidebar.title("⚽ FantaManager Hub")
st.sidebar.markdown("---")

# Sezione Caricamento Listone
with st.sidebar.expander("📁 Importa Listone Calciatori", expanded=False):
    st.markdown("Carica il file delle quotazioni (Excel o CSV).")
    listone_file = st.file_uploader("Scegli file", type=["csv", "xlsx"], key="file_picker")
    
    if listone_file is not None:
        try:
            if listone_file.name.endswith('.csv'):
                df_load = pd.read_csv(listone_file, encoding='utf-8', on_bad_lines='skip')
            else:
                try:
                    df_load = pd.read_excel(listone_file, engine='openpyxl')
                except ImportError:
                    st.error("Errore: Pacchetto 'openpyxl' mancante. Salva il file Excel in formato CSV e ricaricalo!")
                    df_load = None
            
            if df_load is not None:
                # Normalizzazione colonne
                df_load.columns = [str(c).strip().lower() for c in df_load.columns]
                col_mappa = {}
                for col in df_load.columns:
                    if 'nome' in col or 'giocatore' in col: col_mappa[col] = 'Nome'
                    elif col in ['r', 'ruolo']: col_mappa[col] = 'Ruolo'
                    elif 'squadra' in col or 'team' in col: col_mappa[col] = 'Squadra_SerieA'
                    elif 'quot' in col or 'valore' in col or 'qt' in col: col_mappa[col] = 'Quotazione'
                    elif 'fm' in col or 'fantamedia' in col or 'media' in col: col_mappa[col] = 'FantaMedia'
                
                df_load = df_load.rename(columns=col_mappa)
                
                # Validazione minima colonne obbligatorie
                if 'Nome' in df_load.columns and 'Ruolo' in df_load.columns:
                    df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                    if 'Squadra_SerieA' not in df_load.columns: df_load['Squadra_SerieA'] = 'N/D'
                    if 'Quotazione' not in df_load.columns: df_load['Quotazione'] = 1
                    if 'FantaMedia' not in df_load.columns: df_load['FantaMedia'] = 6.0
                    
                    # Pulizia formati dati
                    df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(1).astype(int)
                    df_load['FantaMedia'] = pd.to_numeric(df_load['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                    df_load['Ruolo'] = df_load['Ruolo'].str.upper().str.strip()
                    
                    st.session_state.giocatori_db = df_load[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']].copy()
                    st.success(f"Database aggiornato: {len(df_load)} calciatori pronti.")
                else:
                    st.error("Colonne 'Nome' o 'Ruolo' non identificate nel file.")
        except Exception as e:
            st.error(f"Errore caricamento: {e}")

# Menu di navigazione principale
st.sidebar.markdown("### 🗺️ Navigazione")
scelta_menu = st.sidebar.radio(
    "Vai alla sezione:",
    ["🔨 Martello Asta", "📊 Rose & Tabellone", "🔍 Scouting & Listone", "📜 Registro Mercato"]
)

# --- 4. SEZIONE: MARTELLO ASTA (INSERIMENTO GIOCATORI) ---
if scelta_menu == "🔨 Martello Asta":
    st.title("🔨 Pannello di Assegnazione Calciatori")
    
    col_sx, col_dx = st.columns([1, 1])
    
    with col_sx:
        st.subheader("Registra un Acquisto")
        
        # Selezione rapida del giocatore dal database caricato
        lista_nomi = sorted(st.session_state.giocatori_db['Nome'].unique())
        giocatore_scelto = st.selectbox("Cerca Calciatore nel Listone", lista_nomi)
        
        # Estrazione info giocatore selezionato
        info_g = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'] == giocatore_scelto].iloc[0]
        
        st.info(f"Dettagli Selezionato: **{info_g['Ruolo']}** | {info_g['Squadra_SerieA']} | Quotazione: {info_g['Quotazione']} | FantaMedia: {info_g['FantaMedia']}")
        
        # Input acquirente e costo
        squadra_acquirente = st.selectbox("Assegna alla Squadra", NOMI_SQUADRE)
        prezzo_acquisto = st.number_input("Prezzo d'acquisto (Crediti)", min_value=1, max_value=500, value=int(info_g['Quotazione']))
        
        if st.button("Conferma e Salva Acquisto", type="primary"):
            dati_squadra = st.session_state.squadre[squadra_acquirente]
            ruolo_g = info_g['Ruolo']
            
            # Conteggi attuali della rosa
            conteggio_ruoli = pd.DataFrame(dati_squadra["rosa"])['Ruolo'].value_counts().to_dict() if dati_squadra["rosa"] else {}
            num_nel_ruolo = conteggio_ruoli.get(ruolo_g, 0)
            
            # Controlli di validità dell'acquisto
            if dati_squadra["crediti"] < prezzo_acquisto:
                st.error(f"Fondi insufficienti! {squadra_acquirente} ha solo {dati_squadra['crediti']} crediti disponibili.")
            elif len(dati_squadra["rosa"]) >= MAX_GIOCATORI:
                st.error(f"Rosa piena! Massimo {MAX_GIOCATORI} giocatori totali.")
            elif num_nel_ruolo >= LIMITI_RUOLI.get(ruolo_g, 99):
                st.error(f"Slot esauriti! La squadra ha già {num_nel_ruolo} giocatori nel ruolo {ruolo_g} (Max {LIMITI_RUOLI[ruolo_g]}).")
            else:
                # Esecuzione transazione
                nuovo_calciatore = {
                    "Nome": info_g['Nome'],
                    "Ruolo": ruolo_g,
                    "Squadra_SerieA": info_g['Squadra_SerieA'],
                    "Quotazione": info_g['Quotazione'],
                    "FantaMedia": info_g['FantaMedia'],
                    "Costo_Acquisto": prezzo_acquisto
                }
                dati_squadra["rosa"].append(nuovo_calciatore)
                dati_squadra["crediti"] -= prezzo_acquisto
                
                # Scrittura nel registro storico
                st.session_state.storico_mercato.append({
                    "Orario": datetime.now().strftime("%H:%M:%S"),
                    "Squadra": squadra_acquirente,
                    "Giocatore": info_g['Nome'],
                    "Ruolo": ruolo_g,
                    "Costo": prezzo_acquisto,
                    "Tipo": "Acquisto Asta"
                })
                st.success(f"🔥 {info_g['Nome']} assegnato a {squadra_acquirente} per {prezzo_acquisto} crediti!")
                st.rerun()

    with col_dx:
        st.subheader("Svincola un Calciatore")
        squadra_svincolo = st.selectbox("Seleziona Squadra per Svincolo", NOMI_SQUADRE, key="svincolo_sq")
        rosa_attuale = st.session_state.squadre[squadra_svincolo]["rosa"]
        
        if rosa_attuale:
            nomi_rosa = [g["Nome"] for g in rosa_attuale]
            giocatore_da_svincolare = st.selectbox("Seleziona Calciatore da rimuovere", nomi_rosa)
            
            recupero_crediti = st.checkbox("Recupera i crediti spesi per l'acquisto", value=True)
            
            if st.button("Rimuovi dalla Rosa", type="secondary"):
                # Trova e rimuovi il giocatore
                for i, g in enumerate(rosa_attuale):
                    if g["Nome"] == giocatore_da_svincolare:
                        if recupero_crediti:
                            st.session_state.squadre[squadra_svincolo]["crediti"] += g["Costo_Acquisto"]
                        
                        st.session_state.storico_mercato.append({
                            "Orario": datetime.now().strftime("%H:%M:%S"),
                            "Squadra": squadra_svincolo,
                            "Giocatore": g["Nome"],
                            "Ruolo": g["Ruolo"],
                            "Costo": g["Costo_Acquisto"] if recupero_crediti else 0,
                            "Tipo": "Svincolo"
                        })
                        
                        rosa_attuale.pop(i)
                        st.warning(f"Svincolato {giocatore_da_svincolare} da {squadra_svincolo}.")
                        st.rerun()
                        break
        else:
            st.info("Questa squadra non ha ancora registrato calciatori in rosa.")

# --- 5. SEZIONE: ROSE & TABELLONE COMPLETO ---
elif scelta_menu == "📊 Rose & Tabellone":
    st.title("📊 Situazione Finanziaria e Rose Ufficiali")
    
    # Vista Generale KPI Riassuntivi
    dati_riassunto = []
