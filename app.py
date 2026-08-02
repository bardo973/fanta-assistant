import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT (LEGA COMPLETA)
# ---------------------------------------------------------
st.set_page_config(page_title="FantaLega AI Predictor & Contract Manager", layout="wide")

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500

# ---------------------------------------------------------
# 2. CARICAMENTO DATI POTENZIATO CON PARAMETRI ALGORITMICI & CONTRATTI
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_raw = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")
    
    df = pd.DataFrame()
    df["Nome"] = df_raw["Calciatore"]
    df["Squadra"] = df_raw["Squadra"]
    df["Ruolo"] = df_raw["Ruolo"]
    df["Quotazione"] = pd.to_numeric(df_raw["Quotazione"], errors="coerce").fillna(1)
    
    # Pulizia radicale della colonna dei proprietari per evitare disallineamenti
    if "Unnamed: 5" in df_raw.columns:
        df["Proprietario_Iniziale"] = df_raw["Unnamed: 5"].astype(str).str.strip().str.upper()
        df["Proprietario_Iniziale"] = df["Proprietario_Iniziale"].apply(
            lambda x: "LIBERO" if x in ["NAN", "", "SVINCOLATO", "LIBERO"] else x
        )
    else:
        df["Proprietario_Iniziale"] = "LIBERO"
        
    df["Stato"] = "Libero" 
    
    # Generazione dinamica della Scadenza di Contratto basata sul Tier
    def assign_tier_and_contract(quot):
        if quot >= 25: 
            return pd.Series(["Top", 2027])      # I top rinnovano spesso a breve termine
        elif quot >= 15: 
            return pd.Series(["Semitop", 2028])
        elif quot >= 8: 
            return pd.Series(["Titolare", 2029])
        else: 
            return pd.Series(["Scommessa", 2030]) # I giovani o le scommesse hanno contratti più lunghi
        
    df[["Tier", "Scadenza_Contratto"]] = df["Quotazione"].apply(assign_tier_and_contract)
    
    # Parametri algoritmici di salute e titolarità
    def genera_indici_salute(row):
        if row["Tier"] == "Top": return pd.Series([0.90, 34])
        elif row["Tier"] == "Semitop": return pd.Series([0.75, 30])
        elif row["Tier"] == "Titolare": return pd.Series([0.65, 28])
        return pd.Series([0.45, 22])
        
    df[["Percentuale_Titolarita", "Partite_Attese"]] = df.apply(genera_indici_salute, axis=1)
    
    def stima_voto_puro(ruolo):
        if ruolo == "D": return 6.10
        elif ruolo == "C": return 6.05
        return 6.00
    df["Media_Voto_Pura"] = df["Ruolo"].apply(stima_voto_puro)
    
    df["Status_Piazzati"] = df["Quotazione"].apply(lambda q: 3 if q >= 28 else (2 if q >= 18 else 0))
    
    def assegna_metriche_ruolo(ruolo):
        if ruolo == "A": return pd.Series([0.35, 0.12])
        elif ruolo == "C": return pd.Series([0.15, 0.18])
        elif ruolo == "D": return pd.Series([0.05, 0.08])
        return pd.Series([0.00, 0.00])
        
    df[["xG_90", "xA_90"]] = df["Ruolo"].apply(assegna_metriche_ruolo)
    
    hype_squadra = {"Inter": 1.25, "Atalanta": 1.25, "Milan": 1.15, "Juventus": 1.15}
    df["Moltiplicatore_Team"] = df["Squadra"].map(hype_squadra).fillna(0.95)
    
    df["Valore_Atteso"] = np.round(((df["xG_90"] * 3.0) + (df["xA_90"] * 1.0)) * df["Partite_Attese"] * df["Moltiplicatore_Team"], 1)
    df["Indice_VfM"] = np.round(df["Valore_Atteso"] / df["Quotazione"], 2)
    
    return df

if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data()

df = st.session_state.df_giocatori

# Estrae i nomi dei partecipanti REALI direttamente dal file CSV
lista_proprietari_csv = [p for p in df["Proprietario_Iniziale"].unique() if p != "LIBERO"]
if not lista_proprietari_csv:
    lista_proprietari_csv = ["BARDO", "ROBY", "MIO_TEAM"]

PARTECIPANTI_LEGA = sorted(lista_proprietari_csv)

# Inizializza il dizionario delle rose in session_state
if "rose_lega" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}

if "inizializzato" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
    for idx, row in df.iterrows():
        prop = row["Proprietario_Iniziale"]
        if prop in st.session_state.rose_lega:
            st.session_state.rose_lega[prop].append({
                "Nome": row["Nome"], "Ruolo": row["Ruolo"],
                "Squadra": row["Squadra"], "Prezzo": int(row["Quotazione"]),
                "Scadenza": int(row["Scadenza_Contratto"])
            })
            st.session_state.df_giocatori.at[idx, "Stato"] = prop
        else:
            st.session_state.df_giocatori.at[idx, "Stato"] = "Libero"
    st.session_state.inizializzato = True

df = st.session_state.df_giocatori

# ---------------------------------------------------------
# 3. SIDEBAR: PANNELLO DI CONTROLLO & MONITOR ROSE
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Dashboard")
fanta_allenatore_attivo = st.sidebar.selectbox("Chi sta acquistando ora:", PARTECIPANTI_LEGA)

budget_input = st.sidebar.number_input("Budget Iniziale Crediti (Tutti)", value=st.session_state.budget_iniziale, step=10)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega[fanta_allenatore_attivo]
spesa_corrente = sum(item['Prezzo'] for item in rosa_corrente)
budget_rimanente_corrente = st.session_state.budget_iniziale - spesa_corrente

slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
slot_presi = {r: sum(1 for g in rosa_corrente if g["Ruolo"] == r) for r in slot_target}
slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
totale_slot_liberi = sum(slot_liberi.values())

st.sidebar.metric(f"Budget Rimanente ({fanta_allenatore_attivo})", f"{budget_rimanente_corrente} cr")

# Esplora Rose & Scadenze Contrattuali Dinamiche
st.sidebar.divider()
st.sidebar.subheader("📋 Esplora Rose & Scadenze")
squadra_da_esplorare = st.sidebar.selectbox("Seleziona rosa da visualizzare a lato:", PARTECIPANTI_LEGA, key="esplora_sidebar")

rosa_selezionata_sidebar = st.session_state.rose_lega[squadra_da_esplorare]
if rosa_selezionata_sidebar:
    df_side = pd.DataFrame(rosa_selezionata_sidebar)
    df_side = df_side.sort_values(by="Ruolo")
    st.sidebar.dataframe(
        df_side[["Nome", "Ruolo", "Scadenza"]], 
        use_container_width=True, 
        hide_index=True
    )
    scadenza_imminente = len(df_side[df_side["Scadenza"] <= 2027])
    if scadenza_imminente > 0:
        st.sidebar.warning(f"⚠️ {scadenza_imminente} contratti in scadenza nel 2027!")
else:
    st.sidebar.info("Questa rosa è attualmente vuota.")

st.sidebar.divider()
st.sidebar.subheader("🔥 Offerte Max Altri Allenatori")
massimi_rilanci = {}
for p in PARTECIPANTI_LEGA:
    if p != fanta_allenatore_attivo:
        rosa_avv = st.session_state.rose_lega[p]
        spesa_avv = sum(item['Prezzo'] for item in rosa_avv)
        budget_avv = st.session_state.budget_iniziale - spesa_avv
        slot_liberi_avv = sum(slot_target[r] - sum(1 for g in rosa_avv if g["Ruolo"] == r) for r in slot_target)
        
        max_rilancio_singolo = max(0, budget_avv - max(0, slot_liberi_avv - 1))
        massimi_rilanci[p] = max_rilancio_singolo
        st.sidebar.text(f"🔴 {p}: Max Rilancio {max_rilancio_singolo} cr")

pericolo_max_crediti = max(massimi_rilanci.values()) if massimi_rilanci else 0

# ---------------------------------------------------------
# 4. DASHBOARD PRINCIPALE: VALUTAZIONE PRECOGNITIVA ASTA LIVE
# ---------------------------------------------------------
st.title("⚡ Live Auction Intelligent Assistant")

st.subheader(f"🔍 Analisi Giocatore per: {fanta_allenatore_attivo}")
giocatori_liberi = df[df["Stato"] == "Libero"]["Nome"].tolist()

if giocatori_liberi:
    giocatore_sel = st.selectbox("Seleziona il giocatore chiamato in asta:", giocatori_liberi)
    g_data = df[df["Nome"] == giocatore_sel].iloc[0]
    
    riserva_minima = max(0, totale_slot_liberi - 1)
    budget_spendibile = max(0, budget_rimanente_corrente - riserva_minima)
    
    percentuali_tier = {"Top": 0.45, "Semitop": 0.22, "Titolare": 0.08, "Scommessa": 0.03}
    base_offerta = int(budget_spendibile * percentuali_tier.get(g_data["Tier"], 0.04))
    
    top_rimanenti_ruolo = len(df[(df["Ruolo"] == g_data["Ruolo"]) & (df["Tier"] == g_data["Tier"]) & (df["Stato"] == "Libero")])
    moltiplicatore_scarsita = 1.0
    if top_rimanenti_ruolo <= 3 and g_data["Tier"] in ["Top", "Semitop"]:
        moltiplicatore_scarsita = 1.15
        
    moltiplicatore_personale = g_data["Percentuale_Titolarita"]
    if g_data["Status_Piazzati"] == 3: base_offerta += 5
    if g_data["Ruolo"] == "D" and g_data["Media_Voto_Pura"] >= 6.10: base_offerta += 2
    
    max_offerta_consigliata = int(base_offerta * moltiplicatore_scarsita * moltiplicatore_personale)
    max_offerta_consigliata = max(1, max_offerta_consigliata) if slot_liberi[g_data["Ruolo"]] > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Partite Attese (Salute)", f"{int(g_data['Partite_Attese'])} / 38", f"Scadenza: {int(g_data['Scadenza_Contratto'])}")
    
    testo_piazzati = "Rigorista 🎯" if g_data["Status_Piazzati"] == 3 else ("Punizioni 📐" if g_data["Status_Piazzati"] == 2 else "No")
    col2.metric("Specialista Calci Fermi", testo_piazzati)
    col3.metric("Scarsità Reparto", f"{top_rimanenti_ruolo} Liberi", f"Hype: x{moltiplicatore_scarsita}")
    col4.metric("Max Offerta Consigliata", f"{max_offerta_consigliata} cr", f"Tier: {g_data['Tier']}")

    st.info(f"💡 **Consiglio AI:** Valore atteso stimato di rendimento: **{g_data['Valore_Atteso']}** (Indice Value-for-Money: {g_data['Indice_VfM']})")

    # Evitiamo che il valore di default sia inferiore a 1 per il number_input
    valore_default_input = max(1, int(max_offerta_consigliata))

    # Sezione di assegnazione effettiva del giocatore durante l'asta
    with st.form("form_aggiudicazione"):
        st.write("### Registra Acquisto Asta")
        col_A, col_B = st.columns(2)
        with col_A:
            prezzo_aggiudicazione = st.number_input(
                "Prezzo di chiusura asta (crediti):", 
                min_value=1, 
                value=valore_default_input
            )
        with col_B:
            vincitore_asta = st.selectbox(
                "Assegna a fanta-allenatore:", 
                PARTECIPANTI_LEGA, 
                index=PARTECIPANTI_LEGA.index(fanta_allenatore_attivo) if fanta_allenatore_attivo in PARTECIPANTI_LEGA else 0
            )
        
        submit_asta = st.form_submit_button("Conferma Acquisto Giocatore")
        
        if submit_asta:
            # Aggiorna stato nel dataframe
            idx_giocatore = df[df["Nome"] == giocatore_sel].index[0]
            st.session_state.df_giocatori.at[idx_giocatore, "Stato"] = vincitore_asta
            
            # Aggiunge alla rosa del vincitore
            st.session_state.rose_lega[vincitore_asta].append({
                "Nome": g_data["Nome"],
                "Ruolo": g_data["Ruolo"],
                "Squadra": g_data["Squadra"],
                "Prezzo": int(prezzo_aggiudicazione),
                "Scadenza": int(g_data["Scadenza_Contratto"])
            })
            st.success(f"✅ {giocatore_sel} è stato assegnato a **{vincitore_asta}** per {prezzo_aggiudicazione} crediti!")
            st.rerun()
else:
    st.success("🎉 Tutti i giocatori sono stati assegnati! L'asta è conclusa.")
