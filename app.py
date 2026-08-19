import streamlit as st
import pandas as pd
import time
from datetime import datetime, timedelta

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
                st.sidebar.error("⚠️ Errore openpyxl: Per i file Excel installa 'openpyxl' nel terminale. Nel frattempo, converti il file in .csv per caricarlo istantaneamente.")
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
            df.columns = [str(c).strip().lower() for c in df.columns]
            mappa = {c: 'Nome' for c in df.columns if 'nome' in c or 'giocatore' in c}
            for c in df.columns:
                if c in ['r', 'ruolo']: mappa[c] = 'Ruolo'
                elif 'squadra' in c or 'team' in c: mappa[c] = 'Squadra_SerieA'
                elif 'quot' in c or 'valore' in c: mappa[c] = 'Quotazione'
                elif 'fm' in c or 'media' in c: mappa[c] = 'FantaMedia'
            df = df.rename(columns=mappa)
            if 'Nome' in df.columns and 'Ruolo' in df.columns:
                df['Quotazione'] = pd.to_numeric(df['Quotazione'], errors='coerce').fillna(1).astype(int)
                df['FantaMedia'] = pd.to_numeric(df['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                df['Ruolo'] = df['Ruolo'].str.upper().str.strip()
                st.session_state.giocatori_db = df[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']].copy()
                st.sidebar.success(f"Listone aggiornato ({len(df)} righe).")
                st.rerun()

    st.markdown("**2. Importa Rose Attuali**")
    file_r = st.file_uploader("File Rose (.csv / .xlsx)", type=["csv", "xlsx"], key="upl_r")
    if file_r:
        df_r = carica_file_sicuro(file_r)
        if df_r is not None:
            df_r.columns = [str(c).strip().lower() for c in df_r.columns]
            f_sq, cost, name = None, None, None
            for c in df_r.columns:
                if 'fantasquadra' in c or 'squadra_fanta' in c or 'team' in c: f_sq = c
                elif 'costo' in c or 'spesa' in c or 'prezzo' in c: cost = c
                elif 'nome' in c or 'giocatore' in c: name = c
            if f_sq and cost and name:
                for sq in NOMI_SQUADRE: st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
                for _, row in df_r.iterrows():
                    team = str(row[f_sq]).upper().strip()
                    g_name = str(row[name]).strip()
                    g_cost = int(pd.to_numeric(row[cost], errors='coerce') or 1)
                    if team in NOMI_SQUADRE:
                        match = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'].str.lower() == g_name.lower()]
                        r, s_a, qt, fm = (match.iloc['Ruolo'], match.iloc['Squadra_SerieA'], match.iloc['Quotazione'], match.iloc['FantaMedia']) if not match.empty else ("C", "N/D", 1, 6.0)
                        st.session_state.squadre[team]["rosa"].append({
                            "Nome": g_name, "Ruolo": r, "Squadra_SerieA": s_a, "Quotazione": qt, "FantaMedia": fm, "Costo_Acquisto": g_cost,
                            "Tipo_Contratto": "Proprietà", "Scadenza": ANNO_ATTUALE + DURATA_CONTRATTO_ANNI
                        })
                        st.session_state.squadre[team]["crediti"] -= g_cost
                st.sidebar.success("Rose sincronizzate con scadenze a 4 anni!")
                st.rerun()

st.sidebar.markdown("### 🗺️ Navigazione App")
menu = st.sidebar.radio("Scegli la sezione:", ["⏱️ Chiamata & Martello Asta", "🔍 Scouting Diviso per Ruolo", "🤝 Scambi & Prestiti Annuali", "📊 Situazione Rose & Scadenze", "📜 Storico Operazioni"])

# --- 5. SEZIONE: TIMING CHIAMATA & MARTELLO ASTA ---
if menu == "⏱️ Chiamata & Martello Asta":
    st.title("⏱️ Sistema di Chiamata Calciatore & Chiusura Mercato")
    
    col_timer, col_assegna = st.columns(2)
    
    with col_timer:
        st.subheader("📢 Lancia un Calciatore all'Asta")
        lista_nomi = sorted(st.session_state.giocatori_db['Nome'].unique())
        calciatore_selezionato = st.selectbox("Seleziona Calciatore da lanciare", lista_nomi)
        tempo_attesa = st.slider("Tempo di attesa (secondi)", min_value=10, max_value=120, value=30, step=5)
        
        if st.button("Avvia Timer Chiamata", type="primary"):
            st.session_state.chiamata_asta = {
                "calciatore": calciatore_selezionato,
                "scadenza_timer": time.time() + tempo_attesa
            }
            st.rerun()
            
        # Gestione Grafica del Timer di Attesa
        if st.session_state.chiamata_asta["calciatore"]:
            tempo_rimasto = int(st.session_state.chiamata_asta["scadenza_timer"] - time.time())
            if tempo_rimasto > 0:
                st.warning(f"⏳ IN ATTESA DI OFFERTE: **{st.session_state.chiamata_asta['calciatore']}**")
                st.metric(label="Tempo Rimasto prima della scadenza", value=f"{tempo_rimasto} secondi")
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"🚨 TEMPO SCADUTO per {st.session_state.chiamata_asta['calciatore']}! Assegna il giocatore a destra o chiama un nuovo profilo.")

    with col_assegna:
        st.subheader("🔨 Registrazione e Assegnazione Contratto")
        g_asta = st.session_state.chiamata_asta["calciatore"] or lista_nomi[0]
        st.markdown(f"Calciatore in lavorazione: **{g_asta}**")
        
        riga_g = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'] == g_asta]
        if not riga_g.empty:
            info_g = riga_g.iloc
            st.info(f"Dettagli: {info_g['Ruolo']} | {info_g['Squadra_SerieA']} | FantaMedia: {info_g['FantaMedia']}")
            
            squadra_acq = st.selectbox("Assegna alla FantaSquadra", NOMI_SQUADRE)
            prezzo_acq = st.number_input("Prezzo Finale di Asta (Crediti)", min_value=1, max_value=500, value=int(info_g['Quotazione']))
            
            scadenza_contratto = ANNO_ATTUALE + DURATA_CONTRATTO_ANNI
            st.markdown(f"📅 *Nota contrattuale: Scadenza fissata in automatico a fine Settembre **{scadenza_contratto}** (Durata: 4 anni).*")
            
            if st.button("Conferma Acquisto e Chiudi Asta"):
                dati_sq = st.session_state.squadre[squadra_acq]
                conteggio_ruoli = pd.DataFrame(dati_sq["rosa"])['Ruolo'].value_counts().to_dict() if dati_sq["rosa"] else {}
                
                if dati_sq["crediti"] < prezzo_acq:
                    st.error("Fondi insufficienti per completare l'operazione!")
                elif len(dati_sq["rosa"]) >= MAX_GIOCATORI:
                    st.error("La rosa della fanta-squadra selezionata è piena.")
                elif conteggio_ruoli.get(info_g['Ruolo'], 0) >= LIMITI_RUOLI[info_g['Ruolo']]:
                    st.error(f"Slot esauriti per il ruolo {info_g['Ruolo']}.")
                else:
                    dati_sq["rosa"].append({
                        "Nome": info_g['Nome'], "Ruolo": info_g['Ruolo'], "Squadra_SerieA": info_g['Squadra_SerieA'],
                        "Quotazione": info_g['Quotazione'], "FantaMedia": info_g['FantaMedia'], "Costo_Acquisto": prezzo_acq,
