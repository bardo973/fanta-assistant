import streamlit as st
import pandas as pd
import time
from datetime import datetime

# --- CONFIGURAZIONE INTERFACCIA ---
st.set_page_config(
    page_title="FantaManager Ultimate Hub", 
    page_icon="⚽", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 1. PARAMETRI E COSTANTI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
LIMITI_RUOLI = {"P": 3, "D": 8, "C": 8, "A": 6}
MAX_GIOCATORI = sum(LIMITI_RUOLI.values()) # 25 giocatori
DURATA_CONTRATTO_ANNI = 4
ANNO_ATTUALE = datetime.now().year

# --- 2. INIZIALIZZAZIONE SICURA DELLA SESSIONE ---
if 'squadre' not in st.session_state:
    st.session_state.squadre = {sq: {"crediti": 500, "rosa": []} for sq in NOMI_SQUADRE}

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []

if 'chiamata_asta' not in st.session_state:
    st.session_state.chiamata_asta = {"calciatore": None, "scadenza_timer": None, "base_asta": 1}

if 'giocatori_db' not in st.session_state:
    # Dataset dimostrativo iniziale pronto all'uso
    st.session_state.giocatori_db = pd.DataFrame([
        {"Nome": "Lautaro Martinez", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 38, "FantaMedia": 8.5},
        {"Nome": "Vlahovic", "Ruolo": "A", "Squadra_SerieA": "Juventus", "Quotazione": 34, "FantaMedia": 8.1},
        {"Nome": "Pulisic", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 22, "FantaMedia": 7.9},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 18, "FantaMedia": 7.5},
        {"Nome": "Dimarco", "Ruolo": "D", "Squadra_SerieA": "Inter", "Quotazione": 15, "FantaMedia": 7.1},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 12, "FantaMedia": 6.8},
        {"Nome": "Sommer", "Ruolo": "P", "Squadra_SerieA": "Inter", "Quotazione": 18, "FantaMedia": 5.6},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Como", "Quotazione": 8, "FantaMedia": 7.3}
    ])

# --- 3. MOTORE PARSING FILE (CSV & EXCEL FALLBACK) ---
def carica_file_sicuro(file_oggetto):
    try:
        if file_oggetto.name.endswith('.csv'):
            return pd.read_csv(file_oggetto, encoding='utf-8', on_bad_lines='skip')
        else:
            try:
                return pd.read_excel(file_oggetto, engine='openpyxl')
            except ImportError:
                st.sidebar.error("⚠️ Errore openpyxl: Installa 'openpyxl' nel terminale o converti in .csv")
                return None
    except Exception as e:
        st.sidebar.error(f"⚠️ Errore file: {e}")
        return None

# --- 4. BARRA LATERALE: STRUMENTI E IMPORTAZIONI ---
st.sidebar.title("⚽ FantaManager Pro v3")
st.sidebar.markdown("---")

with st.sidebar.expander("📁 Carica Listone / Rose", expanded=False):
    st.markdown("**1. Importa Listone Generale**")
    file_l = st.file_uploader("File Listone (.csv / .xlsx)", type=["csv", "xlsx"], key="upl_l")
    if file_l:
        df = carica_file_sicuro(file_l)
        if df is not None:
            try:
                # Pulizia colonne
                df.columns = [str(c).strip().lower() for c in df.columns]
                mappa = {}
                for c in df.columns:
                    if 'nome' in c or 'giocatore' in c or 'calciatore' in c: mappa[c] = 'Nome'
                    elif c in ['r', 'ruolo', 'ruoli']: mappa[c] = 'Ruolo'
                    elif 'squadra' in c or 'team' in c or 'club' in c: mappa[c] = 'Squadra_SerieA'
                    elif 'quot' in c or 'valore' in c or 'qt' in c or 'costo' in c: mappa[c] = 'Quotazione'
                    elif 'fm' in c or 'media' in c or 'fantamedia' in c: mappa[c] = 'FantaMedia'
                
                df = df.rename(columns=mappa)
                
                # RISOLTO: Controllo e Fallback di sicurezza per prevenire KeyError
                if 'Nome' not in df.columns:
                    st.sidebar.error("❌ Colonna 'Nome' o 'Giocatore' non trovata nel file.")
                else:
                    if 'Ruolo' not in df.columns: df['Ruolo'] = 'C'
                    if 'Squadra_SerieA' not in df.columns: df['Squadra_SerieA'] = 'N/D'
                    if 'Quotazione' not in df.columns: df['Quotazione'] = 1
                    if 'FantaMedia' not in df.columns: df['FantaMedia'] = 6.0
                    
                    df['Quotazione'] = pd.to_numeric(df['Quotazione'], errors='coerce').fillna(1).astype(int)
                    df['FantaMedia'] = pd.to_numeric(df['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                    df['Ruolo'] = df['Ruolo'].str.upper().str.strip()
                    
                    st.session_state.giocatori_db = df[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']].copy()
                    st.sidebar.success(f"Listone aggiornato ({len(df)} righe).")
                    st.rerun()
            except Exception as e:
                st.sidebar.error(f"Errore elaborazione listone: {e}")

    st.markdown("**2. Importa Rose Attuali**")
    file_r = st.file_uploader("File Rose (.csv / .xlsx)", type=["csv", "xlsx"], key="upl_r")
    if file_r:
        df_r = carica_file_sicuro(file_r)
        if df_r is not None:
            try:
                df_r.columns = [str(c).strip().lower() for c in df_r.columns]
                f_sq, cost, name = None, None, None
                for c in df_r.columns:
                    if 'fantasquadra' in c or 'squadra_fanta' in c or 'team' in c or 'proprietario' in c: f_sq = c
                    elif 'costo' in c or 'spesa' in c or 'prezzo' in c or 'crediti' in c: cost = c
                    elif 'nome' in c or 'giocatore' in c or 'calciatore' in c: name = c
                
                if f_sq and cost and name:
                    # Reset rose prima dell'importazione
                    for sq in NOMI_SQUADRE: st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
                    
                    for _, row in df_r.iterrows():
                        team = str(row[f_sq]).upper().strip()
                        g_name = str(row[name]).strip()
                        g_cost = int(pd.to_numeric(row[cost], errors='coerce') or 1)
                        if team in NOMI_SQUADRE:
                            match = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'].str.lower() == g_name.lower()]
                            if not match.empty:
                                r = match.iloc[0]['Ruolo']
                                s_a = match.iloc[0]['Squadra_SerieA']
                                qt = match.iloc[0]['Quotazione']
                                fm = match.iloc[0]['FantaMedia']
                            else:
                                r, s_a, qt, fm = "C", "N/D", 1, 6.0
                            
                            st.session_state.squadre[team]["rosa"].append({
                                "Nome": g_name, "Ruolo": r, "Squadra_SerieA": s_a, "Quotazione": qt, "FantaMedia": fm, "Costo_Acquisto": g_cost,
                                "Tipo_Contratto": "Proprietà", "Scadenza": ANNO_ATTUALE + DURATA_CONTRATTO_ANNI
                            })
                            st.session_state.squadre[team]["crediti"] -= g_cost
                    st.sidebar.success("Rose sincronizzate con scadenze a 4 anni!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Colonne richieste (FantaSquadra, Costo, Giocatore) non identificate.")
            except Exception as e:
                st.sidebar.error(f"Errore elaborazione rose: {e}")

st.sidebar.markdown("### 🗺️ Navigazione App")
menu = st.sidebar.radio("Scegli la sezione:", ["⏱️ Chiamata & Martello Asta", "🔍 Scouting Diviso per Ruolo", "🤝 Scambi & Prestiti Annuali", "📊 Situazione Rose & Scadenze", "📜 Storico Operazioni"])

# --- 5. SEZIONE: TIMING CHIAMATA & MARTELLO ASTA ---
if menu == "⏱️ Chiamata & Martello Asta":
    st.title("⏱️ Sistema di Chiamata Calciatore & Chiusura Mercato")
    
    col_timer, col_assegna = st.columns(2)
    
    with col_timer:
        st.subheader("📢 Lancia un Calciatore all'Asta")
        lista_nomi = sorted(st.session_state.giocatori_db['Nome'].unique()) if not st.session_state.giocatori_db.empty else []
        if lista_nomi:
            calciatore_selezionato = st.selectbox("Seleziona Calciatore da lanciare", lista_nomi)
            tempo_attesa = st.slider("Tempo di attesa (secondi)", min_value=10, max_value=120, value=30, step=5)
            
            if st.button("Avvia Timer Chiamata", type="primary"):
                st.session_state.chiamata_asta = {
                    "calciatore": calciatore_selezionato,
                    "scadenza_timer": time.time() + tempo_attesa
                }
                st.rerun()
        else:
            st.warning("Carica un listone per scegliere i calciatori.")
            
        if st.session_state.chiamata_asta["calciatore"]:
            tempo_rimasto = int(st.session_state.chiamata_asta["scadenza_timer"] - time.time())
            if tempo_rimasto > 0:
                st.warning(f"⏳ IN ATTESA DI OFFERTE: **{st.session_state.chiamata_asta['calciatore']}**")
                st.metric(label="Tempo Rimasto prima della scadenza", value=f"{tempo_rimasto} secondi")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"🚨 TEMPO SCADUTO per {st.session_state.chiamata_asta['calciatore']}!")

    with col_assegna:
        st.subheader("🔨 Registrazione e Assegnazione Contratto")
        g_asta = st.session_state.chiamata_asta["calciatore"] if st.session_state.chiamata_asta["calciatore"] else (lista_nomi[0] if lista_nomi else None)
        
        if g_asta:
            st.markdown(f"Calciatore in lavorazione: **{g_asta}**")
