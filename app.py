import streamlit as st
import pandas as pd
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

if 'giocatori_db' not in st.session_state:
    # Database dimostrativo iniziale pronto all'uso
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

# --- 3. MOTORE DI LETTURA SPECIFICO PER EXCEL .XLSX ---
def carica_excel_sicuro(file_oggetto):
    try:
        df_excel = pd.read_excel(file_oggetto, engine='openpyxl')
        if df_excel is not None:
            df_excel = df_excel.dropna(how='all')
            return df_excel
        return None
    except Exception as e:
        st.sidebar.error(f"⚠️ Impossibile leggere il file Excel (.xlsx): {e}")
        return None

# --- 4. BARRA LATERALE: STRUMENTI E IMPORTAZIONI ---
st.sidebar.title("⚽ FantaManager Pro v3")
st.sidebar.markdown("---")

with st.sidebar.expander("📁 Carica Listone / Rose .xlsx", expanded=True):
    st.markdown("**1. Importa Listone Generale**")
    file_l = st.file_uploader("Scegli Listone Excel (.xlsx)", type=["xlsx"], key="upl_l")
    if file_l:
        df = carica_excel_sicuro(file_l)
        if df is not None and not df.empty:
            try:
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
                    if 'Ruolo' not in df.columns: df['Ruolo'] = 'C'
                    if 'Squadra_SerieA' not in df.columns: df['Squadra_SerieA'] = 'N/D'
                    if 'Quotazione' not in df.columns: df['Quotazione'] = 1
                    if 'FantaMedia' not in df.columns: df['FantaMedia'] = 6.0
                    
                    df = df.dropna(subset=['Nome'])
                    df['Nome'] = df['Nome'].astype(str).str.strip()
                    df['Ruolo'] = df['Ruolo'].astype(str).str.upper().str.strip().apply(lambda x: x if len(x) > 0 else 'C')
                    df['Squadra_SerieA'] = df['Squadra_SerieA'].astype(str).str.strip()
                    df['Quotazione'] = pd.to_numeric(df['Quotazione'], errors='coerce').fillna(1).astype(int)
                    df['FantaMedia'] = pd.to_numeric(df['FantaMedia'], errors='coerce').fillna(6.0).astype(float)
                    
                    df = df.drop_duplicates(subset=['Nome'])
                    st.session_state.giocatori_db = df[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia']].copy()
                    st.sidebar.success(f"📊 Listone caricato! Importati {len(df)} calciatori.")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Errore intestazione: Colonna del nome del giocatore non identificata.")
            except Exception as e:
                st.sidebar.error(f"Errore elaborazione dati Excel: {e}")

    st.markdown("**2. Importa Rose Attuali**")
    file_r = st.file_uploader("Scegli Rose Excel (.xlsx)", type=["xlsx"], key="upl_r")
    if file_r:
        df_r = carica_excel_sicuro(file_r)
        if df_r is not None and not df_r.empty:
            try:
                df_r.columns = [str(c).strip().lower() for c in df_r.columns]
                f_sq, cost, name = None, None, None
                for c in df_r.columns:
                    if any(x in c for x in ['fantasquadra', 'squadra_fanta', 'team', 'proprietario', 'utente']): f_sq = c
                    elif any(x in c for x in ['costo', 'spesa', 'prezzo', 'crediti', 'pagato']): cost = c
                    elif any(x in c for x in ['nome', 'giocatore', 'calciatore']): name = c
                
                if f_sq and cost and name:
                    for sq in NOMI_SQUADRE: 
                        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
                    
                    for _, row in df_r.iterrows():
                        if pd.isna(row[name]) or pd.isna(row[f_sq]):
                            continue
                            
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
                    st.sidebar.success("✅ Rose Excel caricate e sincronizzate!")
                    st.rerun()
                else:
                    st.sidebar.error("❌ Intestazioni file rose non riconosciute.")
            except Exception as e:
                st.sidebar.error(f"Errore caricamento rose Excel: {e}")

st.sidebar.markdown("### 🗺️ Navigazione App")
menu = st.sidebar.radio("Scegli la sezione:", ["🔨 Martello Asta", "🔍 Scouting Diviso per Ruolo", "🤝 Scambi & Prestiti Annuali", "📊 Situazione Rose & Scadenze", "📜 Storico Operazioni"])

# --- 5. SEZIONE: MARTELLO ASTA ---
if menu == "🔨 Martello Asta":
    st.title("🔨 Pannello di Assegnazione e Martello Asta")
    col_sx, col_dx = st.columns(2)
    
    with col_sx:
        st.subheader("📋 Seleziona Calciatore")
        lista_nomi = sorted(st.session_state.giocatori_db['Nome'].unique()) if not st.session_state.giocatori_db.empty else []
        if lista_nomi:
            giocatore_scelto = st.selectbox("Cerca Calciatore nel Listone", lista_nomi)
            riga_g = st.session_state.giocatori_db[st.session_state.giocatori_db['Nome'] == giocatore_scelto]
            if not riga_g.empty:
                info_g = riga_g.iloc[0]
                st.info(f"Dettagli Calciatore:\n* **Ruolo**: {info_g['Ruolo']}\n* **Squadra Serie A**: {info_g['Squadra_SerieA']}\n* **FantaMedia**: {info_g['FantaMedia']}\n* **Quotazione**: {info_g['Quotazione']}")
        else:
            st.warning("Nessun calciatore nel database. Carica un listone .xlsx di fianco.")

    with col_dx:
        st.subheader("✍️ Registra Contratto e Assegna")
        if lista_nomi and not riga_g.empty:
            squadra_acq = st.selectbox("Assegna alla FantaSquadra", NOMI_SQUADRE)
            prezzo_acq = st.number_input("Prezzo Finale d'Acquisto (Crediti)", min_value=1, max_value=500, value=int(info_g['Quotazione']))
            
            scadenza_contratto = ANNO_ATTUALE + DURATA_CONTRATTO_ANNI
            st.markdown(f"📅 *Scadenza contratto automatica: Settembre **{scadenza_contratto}** (Durata: 4 anni).*")
            
            if st.button("Conferma Acquisto Calciatore", type="primary"):
                dati_sq = st.session_state.squadre[squadra_acq]
                conteggio_ruoli = pd.DataFrame(dati_sq["rosa"])['Ruolo'].value_counts().to_dict() if dati_sq["rosa"] else {}
                
                if dati_sq["crediti"] < prezzo_acq:
