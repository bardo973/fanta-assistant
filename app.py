import streamlit as st
import pandas as pd
import numpy as np
import json

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
    
    possibili_colonne_prop = ["Proprietario_Iniziale", "Proprietario", "Unnamed: 5", "Squadra_Fantacalcio"]
    colonna_trovata = next((c for c in possibili_colonne_prop if c in df_raw.columns), None)
    
    if colonna_trovata:
        df["Proprietario_Iniziale"] = df_raw[colonna_trovata].astype(str).str.strip().str.upper()
        df["Proprietario_Iniziale"] = df["Proprietario_Iniziale"].apply(
            lambda x: "LIBERO" if x in ["NAN", "NONE", "", "SVINCOLATO", "LIBERO"] else x
        )
    else:
        df["Proprietario_Iniziale"] = "LIBERO"
        
    df["Stato"] = "Libero" 
    
    def assign_tier_and_contract(quot):
        if quot >= 25: 
            return pd.Series(["Top", 2027])      
        elif quot >= 15: 
            return pd.Series(["Semitop", 2028])
        elif quot >= 8: 
            return pd.Series(["Titolare", 2029])
        else: 
            return pd.Series(["Scommessa", 2030]) 
        
    df[["Tier", "Scadenza_Contratto"]] = df["Quotazione"].apply(assign_tier_and_contract)
    
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

lista_proprietari_csv = [p for p in df["Proprietario_Iniziale"].unique() if p not in ["LIBERO", "NAN", "NONE", ""]]
if not lista_proprietari_csv:
    lista_proprietari_csv = ["BARDO", "ROBY", "MIO_TEAM"]

PARTECIPANTI_LEGA = sorted(lista_proprietari_csv)

if "rose_lega" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}

# Gestione budget extra derivante da scambi/conguagli
if "extra_budget" not in st.session_state:
    st.session_state.extra_budget = {p: 0 for p in PARTECIPANTI_LEGA}

if "inizializzato" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
    for idx, row in df.iterrows():
        prop = row["Proprietario_Iniziale"]
        if prop in st.session_state.rose_lega:
            st.session_state.rose_lega[prop].append({
                "Nome": row["Nome"], 
                "Ruolo": row["Ruolo"],
                "Squadra": row["Squadra"], 
                "Prezzo_Acquisto": int(row["Quotazione"]),
                "Valore_Attuale": int(row["Quotazione"]),
                "Scadenza": int(row["Scadenza_Contratto"])
            })
            st.session_state.df_giocatori.at[idx, "Stato"] = prop
        else:
            st.session_state.df_giocatori.at[idx, "Stato"] = "Libero"
    st.session_state.inizializzato = True

for p in PARTECIPANTI_LEGA:
    if p not in st.session_state.rose_lega:
        st.session_state.rose_lega[p] = []
    if p not in st.session_state.extra_budget:
        st.session_state.extra_budget[p] = 0
    for item in st.session_state.rose_lega[p]:
        if "Prezzo_Acquisto" not in item and "Prezzo" in item:
            item["Prezzo_Acquisto"] = item.pop("Prezzo")
        if "Prezzo_Acquisto" not in item:
            item["Prezzo_Acquisto"] = 1
        if "Valore_Attuale" not in item:
            item["Valore_Attuale"] = item["Prezzo_Acquisto"]

df = st.session_state.df_giocatori

# ---------------------------------------------------------
# 3. SIDEBAR: PANNELLO DI CONTROLLO, SALVATAGGIO & MONITOR ROSE
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Dashboard")
fanta_allenatore_attivo = st.sidebar.selectbox("Chi sta acquistando ora:", PARTECIPANTI_LEGA)

budget_input = st.sidebar.number_input("Budget Iniziale Crediti (Tutti)", value=st.session_state.budget_iniziale, step=10)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega[fanta_allenatore_attivo]
spesa_corrente = sum(item['Prezzo_Acquisto'] for item in rosa_corrente)
budget_rimanente_corrente = st.session_state.budget_iniziale + st.session_state.extra_budget[fanta_allenatore_attivo] - spesa_corrente

slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
slot_presi = {r: sum(1 for g in rosa_corrente if g["Ruolo"] == r) for r in slot_target}
slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
totale_slot_liberi = sum(slot_liberi.values())

st.sidebar.metric(f"Budget Rimanente ({fanta_allenatore_attivo})", f"{budget_rimanente_corrente} cr")

# --- SALVATAGGIO E CARICAMENTO STATO LEGA ---
st.sidebar.divider()
st.sidebar.subheader("💾 Salvataggio & Caricamento")

# Esporta stato in JSON
stato_salva = {
    "budget_iniziale": st.session_state.budget_iniziale,
    "rose_lega": st.session_state.rose_lega,
    "extra_budget": st.session_state.extra_budget,
    "stati_giocatori": df[["Nome", "Stato"]].set_index("Nome")["Stato"].to_dict()
}
json_data = json.dumps(stato_salva, indent=4)
st.sidebar.download_button(
    label="📥 Salva Stato Lega (JSON)",
    data=json_data,
    file_name="fanta_lega_backup.json",
    mime="application/json"
)

# Carica stato da JSON
uploaded_file = st.sidebar.file_uploader("📂 Carica Stato Salvato", type=["json"])
if uploaded_file is not None:
    try:
        loaded_state = json.load(uploaded_file)
        st.session_state.budget_iniziale = loaded_state.get("budget_iniziale", 500)
        st.session_state.rose_lega = loaded_state.get("rose_lega", {})
        st.session_state.extra_budget = loaded_state.get("extra_budget", {p: 0 for p in PARTECIPANTI_LEGA})
        
        stati_caricati = loaded_state.get("stati_giocatori", {})
        for nome, stato in stati_caricati.items():
            idx = df[df["Nome"] == nome].index
            if not idx.empty:
                df.at[idx[0], "Stato"] = stato
        st.sidebar.success("✅ Stato caricato con successo!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento del file: {e}")

# Esplora Rose & Valori
st.sidebar.divider()
st.sidebar.subheader("📋 Esplora Rose & Valori")
squadra_da_esplorare = st.sidebar.selectbox("Seleziona rosa da visualizzare a lato:", PARTECIPANTI_LEGA, key="esplora_sidebar")

rosa_selezionata_sidebar = st.session_state.rose_lega[squadra_da_esplorare]
if rosa_selezionata_sidebar:
    df_side_list = []
    for g in rosa_selezionata_sidebar:
        q_row = df[df["Nome"] == g["Nome"]]
        val_attuale = int(q_row["Quotazione"].values[0]) if not q_row.empty else g.get("Valore_Attuale", 1)
        df_side_list.append({
            "Nome": g["Nome"],
            "Ruolo": g["Ruolo"],
            "Spesa": g.get("Prezzo_Acquisto", 1),
            "Valore": val_attuale,
            "Scadenza": g["Scadenza"]
        })
    df_side = pd.DataFrame(df_side_list).sort_values(by="Ruolo")
    
    st.sidebar.dataframe(
        df_side[["Nome", "Ruolo", "Spesa", "Valore", "Scadenza"]], 
        use_container_width=True, 
        hide_index=True
    )
    scadenza_imminente = len(df_side[df_side["Scadenza"] <= 2027])
    if scadenza_imminente > 0:
        st.sidebar.warning(f"⚠️ {scadenza_imminente} contratti in scadenza nel 2027!")
else:
    st.sidebar.info("Questa rosa è attualmente vuota.")

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

    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Ruolo", g_data["Ruolo"], f"Squadra: {g_data['Squadra']}")
    col2.metric("Valore (Quotazione)", f"{int(g_data['Quotazione'])} cr", f"Tier: {g_data['Tier']}")
    col3.metric("Partite Attese", f"{int(g_data['Partite_Attese'])} / 38", f"Scad.: {int(g_data['Scadenza_Contratto'])}")
    
    testo_piazzati = "Rigorista 🎯" if g_data["Status_Piazzati"] == 3 else ("Punizioni 📐" if g_data["Status_Piazzati"] == 2 else "No")
    col4.metric("Calci Fermi", testo_piazzati)
    col5.metric("Max Offerta Consigliata", f"{max_offerta_consigliata} cr", f"Hype: x{moltiplicatore_scarsita}")

    st.info(f"💡 **Consiglio AI:** Valore atteso stimato di rendimento: **{g_data['Valore_Atteso']}** (Indice Value-for-Money: {g_data['Indice_VfM']})")

    valore_default_input = max(1, int(max_offerta_consigliata))

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
            idx_giocatore = df[df["Nome"] == giocatore_sel].index[0]
            st.session_state.df_giocatori.at[idx_giocatore, "Stato"] = vincitore_asta
            
            st.session_state.rose_lega[vincitore_asta].append({
                "Nome": g_data["Nome"],
                "Ruolo": g_data["Ruolo"],
                "Squadra": g_data["Squadra"],
                "Prezzo_Acquisto": int(prezzo_aggiudicazione),
                "Valore_Attuale": int(g_data["Quotazione"]),
                "Scadenza": int(g_data["Scadenza_Contratto"])
            })
            st.success(f"✅ {giocatore_sel} è stato assegnato a **{vincitore_asta}** per {prezzo_aggiudicazione} crediti!")
            st.rerun()
else:
    st.success("🎉 Tutti i giocatori sono stati assegnati! L'asta è conclusa.")

# ---------------------------------------------------------
# 5. SEZIONE SCAMBI, PRESTITI & TRATTATIVE TRA ROSE
# ---------------------------------------------------------
st.divider()
st.subheader("🤝 Mercato di Riparazione: Scambi & Prestiti")

col_s1, col_s2 = st.columns(2)
with col_s1:
    squadra_A = st.selectbox("Squadra 1 (Offre):", PARTECIPANTI_LEGA, key="scambio_s1")
with col_s2:
    squadra_B = st.selectbox("Squadra 2 (Riceve/Scambia):", PARTECIPANTI_LEGA, key="scambio_s2", index=1 if len(PARTECIPANTI_LEGA) > 1 else 0)

if squadra_A == squadra_B:
    st.warning("⚠️ Seleziona due squadre differenti per effettuare uno scambio.")
else:
    rosa_A = st.session_state.rose_lega[squadra_A]
    rosa_B = st.session_state.rose_lega[squadra_B]
    
    giocatori_A = [g["Nome"] for g in rosa_A]
    giocatori_B = [g["Nome"] for g in rosa_B]
    
    with st.form("form_scambio"):
        st.write("#### Dettagli Trattativa")
        
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            giocatore_da_A = st.selectbox(
                f"Giocatore in uscita da {squadra_A}:", 
                ["Nessuno"] + giocatori_A
            )
        with col_g2:
            giocatore_da_B = st.selectbox(
                f"Giocatore in uscita da {squadra_B}:", 
                ["Nessuno"] + giocatori_B
            )
            
        tipo_operazione = st.radio(
            "Tipo di operazione:", 
            ["Scambio Definitivo / Con conguaglio", "Prestito Secco / Annuale"]
        )
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            conguaglio_crediti = st.number_input(
                f"Conguaglio in crediti (pagato da {squadra_A} a {squadra_B} se positivo, viceversa negativo):", 
                value=0, 
                step=1
            )
        with col_c2:
            durata_prestito = st.selectbox("Scadenza Prestito (se applicabile):", [2027, 2028, 2029], index=0)
            
        submit_scambio = st.form_submit_button("Conferma Scambio / Prestito")
        
        if submit_scambio:
            if giocatore_da_A == "Nessuno" and giocatore_da_B == "Nessuno":
                st.error("❌ Seleziona almeno un giocatore da scambiare!")
            else:
                # Gestione Squadra A -> Squadra B
                if giocatore_da_A != "Nessuno":
                    item_A = next(g for g in rosa_A if g["Nome"] == giocatore_da_A)
                    st.session_state.rose_lega[squadra_A] = [g for g in rosa_A if g["Nome"] != giocatore_da_A]
                    
                    if tipo_operazione.startswith("Scambio"):
                        st.session_state.rose_lega[squadra_B].append(item_A)
                        idx_df = df[df["Nome"] == giocatore_da_A].index
                        if not idx_df.empty:
                            df.at[idx_df[0], "Stato"] = squadra_B
                    else: # Prestito
                        item_A_prestito = item_A.copy()
                        item_A_prestito["Scadenza"] = durata_prestito
                        st.session_state.rose_lega[squadra_B].append(item_A_prestito)
                
                # Gestione Squadra B -> Squadra A
                if giocatore_da_B != "Nessuno":
                    item_B = next(g for g in rosa_B if g["Nome"] == giocatore_da_B)
                    st.session_state.rose_lega[squadra_B] = [g for g in rosa_B if g["Nome"] != giocatore_da_B]
                    
                    if tipo_operazione.startswith("Scambio"):
                        st.session_state.rose_lega[squadra_A].append(item_B)
                        idx_df = df[df["Nome"] == giocatore_da_B].index
                        if not idx_df.empty:
                            df.at[idx_df[0], "Stato"] = squadra_A
                    else: # Prestito
                        item_B_prestito = item_B.copy()
                        item_B_prestito["Scadenza"] = durata_prestito
                        st.session_state.rose_lega[squadra_A].append(item_B_prestito)
                
                # Aggiornamento conguaglio crediti
                if conguaglio_crediti != 0:
                    st.session_state.extra_budget[squadra_A] -= conguaglio_crediti
                    st.session_state.extra_budget[squadra_B] += conguaglio_crediti
                    
                st.success(f"✅ Operazione di mercato completata con successo tra **{squadra_A}** e **{squadra_B}**!")
                st.rerun()

# ---------------------------------------------------------
# 6. SEZIONE VENDITA / SVINCOLO GIOCATORI DALLA ROSA
# ---------------------------------------------------------
st.divider()
st.subheader("🔄 Gestione Rosa & Svincoli (Vendi Giocatore)")

allenatore_svincolo = st.selectbox("Seleziona allenatore che intende svincolare:", PARTECIPANTI_LEGA, key="select_svincolo")
rosa_allenatore_attuale = st.session_state.rose_lega[allenatore_svincolo]

if rosa_allenatore_attuale:
    nomi_giocatori_in_rosa = [g["Nome"] for g in rosa_allenatore_attuale]
    
    with st.form("form_svincolo"):
        giocatore_da_svincolare = st.selectbox("Seleziona il giocatore da svincolare/vendere:", nomi_giocatori_in_rosa)
        rimborso_crediti = st.checkbox("Rimborso crediti spesi (ritorno a budget)", value=True)
        
        submit_svincolo = st.form_submit_button("Conferma Svincolo / Vendita")
        
        if submit_svincolo:
            giocatore_info = next((g for g in rosa_allenatore_attuale if g["Nome"] == giocatore_da_svincolare), None)
            
            if giocatore_info:
                st.session_state.rose_lega[allenatore_svincolo] = [
                    g for g in rosa_allenatore_attuale if g["Nome"] != giocatore_da_svincolare
                ]
                
                idx_df = df[df["Nome"] == giocatore_da_svincolare].index
                if not idx_df.empty:
                    st.session_state.df_giocatori.at[idx_df[0], "Stato"] = "LIBERO"
                
                st.success(f"🗑️ **{giocatore_da_svincolare}** è stato svincolato con successo dalla rosa di **{allenatore_svincolo}** ed è tornato **Libero**!")
                st.rerun()
else:
    st.info(f"La rosa di {allenatore_svincolo} è attualmente vuota, non ci sono giocatori da svincolare.")