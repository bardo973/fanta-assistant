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
    st.session_state.chiamata_asta = {"calciatore": None, "scadenza_timer": None}

if 'giocatori_db' not in st.session_state:
    # Database dimostrativo iniziale pronto all'uso (sovrascritto al caricamento del file)
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

# --- 3. MOTORE DI LETTURA ROBUSTO (RISOLVE IL SALTO DELLE RIGHE) ---
def carica_file_sicuro(file_oggetto):
    try:
        if file_oggetto.name.endswith('.csv'):
            # Proviamo prima la codifica standard utf-8 con gestione BOM per Excel italiani
            try:
                return pd.read_csv(file_oggetto, encoding='utf-8-sig', sep=None, engine='python')
            except Exception:
                # Fallback su latin1 se ci sono caratteri o accenti speciali bloccanti
                file_oggetto.seek(0)
                return pd.read_csv(file_oggetto, encoding='latin1', sep=None, engine='python')
        else:
            try:
                return pd.read_excel(file_oggetto, engine='openpyxl')
            except ImportError:
                st.sidebar.error("⚠️ Errore openpyxl: Installa 'openpyxl' o converti il listone in formato .csv")
                return None
    except Exception as e:
        st.sidebar.error(f"⚠️ Errore critico di lettura file: {e}")
        return None

# --- 4. BARRA LATERALE: STRUMENTI E IMPORTAZIONI ---
st.sidebar.title("⚽ FantaManager Pro v3")
st.sidebar.markdown("---")

with st.sidebar.expander("📁 Carica Listone / Rose", expanded=True):
    st.markdown("**1. Importa Listone Generale**")
    file_l = st.file_uploader("File Listone (.csv / .xlsx)", type=["csv", "xlsx"], key="upl_l")
    if file_l:
        df = carica_file_sicuro(file_l)
        if df is not None and not df.empty:
            try:
                # Normalizzazione radicale delle colonne (rimozione spazi e minuscolo)
                df.columns = [str(c).strip().lower() for c in df.columns]
                
                mappa = {}
                for c in df.columns:
                    if any(x in c for x in ['nome', 'giocatore', 'calciatore', 'atleta']): mappa[c] = 'Nome'
                    elif c in ['r', 'ruolo', 'ruoli', 'pos', 'posizione']: mappa[c] = 'Ruolo'
                    elif any(x in c for x in ['squadra', 'team', 'club', 'sq']): mappa[c] = 'Squadra_SerieA'
                    elif any(x in c for x in ['quot', 'valore', 'qt', 'costo_base', 'prezzo']): mappa[c] = 'Quotazione'
                    elif any(x in c for x in ['fm', 'media', 'fantamedia', 'voto_medio']): mappa[c] = 'FantaMedia'
                
                df = df.rename(columns=mappa)
                
                if 'Nome' in df.columns:
                    # Garantiamo che le colonne essenziali esistano valorizzandole se assenti
                    if 'Ruolo' not in df.columns: df['Ruolo'] = 'C'
                    if 'Squadra_SerieA' not in df.columns: df['Squadra_SerieA'] = 'N/D'
                    if 'Quotazione' not in df.columns: df['Quotazione'] = 1
                    if 'FantaMedia' not in df.columns: df['FantaMedia'] = 6.0
                    
                    # Pulizia e forzatura dei tipi dato per evitare problemi nei calcoli matematici
                    df['Nome'] = df['Nome'].astype(str).str.strip()
                    df['Ruolo'] = df['Ruolo'].astype(str).str.upper().str.strip().str[0] # Prende solo la prima lettera (P, D, C, A)
                    df['Squadra_SerieA'] = df['Squadra_SerieA'].astype(str).str.strip()
                    df['Quotazione'] = pd.to_numeric(df['Quotazione'], errors='coerce').fillna(1).astype(int)
                    df['FantaMedia'] = pd.to_numeric(df['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                    
                    # Elimina righe completamente vuote o senza nome per non falsare i conteggi
                    df = df.dropna(subset=['Nome'])
                    df = df.drop_duplicates(subset=['Nome'])
                    
                    # Salvataggio persistente ed effettivo nello stato
                    st.session_state.giocatori_db = df[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']].copy()
                    st.sidebar.success(f"📊 Listone caricato con successo! Importati {len(df)} giocatori senza saltare righe.")
                else:
                    st.sidebar.error("❌ Impossibile mappare la colonna del Nome del Giocatore. Controlla l'intestazione della colonna nel tuo file.")
            except Exception as e:
                st.sidebar.error(f"Errore durante l'elaborazione dei dati del listone: {e}")

    st.markdown("**2. Importa Rose Attuali**")
    file_r = st.file_uploader("File Rose (.csv / .xlsx)", type=["csv", "xlsx"], key="upl_r")
    if file_r:
        df_r = carica_file_sicuro(file_r)
        if df_r is not None and not df_r.empty:
            try:
                df_r.columns = [str(c).strip().lower() for c in df_r.columns]
                f_sq, cost, name = None, None, None
                for c in df_r.columns:
                    if any(x in c for x in ['fantasquadra', 'squadra_fanta', 'team', 'proprietario', 'utente']): f_sq = c
                    elif any(x in c for x in ['costo', 'spesa', 'prezzo', 'crediti', 'pagato']): cost = c
                    elif any(x in c for x in ['nome', 'giocatore', 'calciatore']): name = c
                
                if f_sq and cost and name:
                    # Pulizia totale preventiva per l'importazione
                    for sq in NOMI_SQUADRE: 
                        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
                    
                    for _, row in df_r.iterrows():
                        team = str(row[f_sq]).upper().strip()
                        g_name = str(row[name]).strip()
                        g_cost = int(pd.to_numeric(row[cost], errors='coerce') or 1)
                        
                        if team in NOMI_SQUADRE and g_name != 'nan':
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
                    st.sidebar.success("✅ Rose dei partecipanti sincronizzate a sistema!")
                else:
                    st.sidebar.error("❌ Intestazioni del file rose non riconosciute (richiesti campi: FantaSquadra, Costo, Giocatore).")
            except Exception as e:
                st.sidebar.error(f"Errore durante l'elaborazione del file rose: {e}")

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
