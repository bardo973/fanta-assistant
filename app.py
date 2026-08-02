import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import pdfplumber

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT
# ---------------------------------------------------------
st.set_page_config(page_title="FantaLega AI Predictor & Contract Manager", layout="wide")

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500

# ---------------------------------------------------------
# 2. ESTRAZIONE TABULARE AVANZATA DA PDF (rose.pdf)
# ---------------------------------------------------------
@st.cache_data
def load_data_from_pdf():
    nome_file = "rose.pdf"
    if not os.path.exists(nome_file):
        st.error(f"⚠️ File PDF '{nome_file}' non trovato! Assicurati che sia presente nella directory principale del progetto.")
        return pd.DataFrame(columns=["Nome", "Squadra", "Ruolo", "Quotazione", "Stato", "Scadenza_Contratto"])

    data_list = []
    
    # Estrazione con pdfplumber per catturare correttamente le tabelle
    with pdfplumber.open(nome_file) as pdf:
        for page in pdf.pages:
            tables = page.extract_tables()
            for table in tables:
                for row in table:
                    # Pulizia delle celle della riga
                    cleaned_row = [str(cell).strip() for cell in row if cell is not None and str(cell).strip() != ""]
                    if len(cleaned_row) >= 3:
                        # Tentativo di estrazione intelligente dei campi
                        # Supponiamo formato standard: Nome, Squadra, Ruolo, Quotazione, ecc.
                        nome = cleaned_row[0]
                        squadra = cleaned_row[1] if len(cleaned_row) > 1 else "Svincolato"
                        ruolo = cleaned_row[2].upper() if len(cleaned_row) > 2 and cleaned_row[2].upper() in ["P", "D", "C", "A"] else "C"
                        
                        quotazione = 10
                        for cell in cleaned_row:
                            if cell.isdigit() and int(cell) > 0 and int(cell) < 500:
                                quotazione = int(cell)
                                break
                                
                        data_list.append({
                            "Nome": nome,
                            "Squadra": squadra,
                            "Ruolo": ruolo,
                            "Quotazione": quotazione,
                            "Stato": "LIBERO",
                            "Scadenza_Contratto": 2028
                        })

    # Se il PDF non ha tabelle strutturate rilevate, usiamo il fallback di sicurezza
    if len(data_list) < 5:
        giocatori_base = [
            ("Meret", "Napoli", "P", 15, "PAOLO"),
            ("Sommer", "Inter", "P", 16, "GALVA"),
            ("Di Gregorio", "Juventus", "P", 14, "GIOPPY"),
            ("Falcone", "Lecce", "P", 10, "ROBY"),
            ("Skorupski", "Bologna", "P", 11, "PECU"),
            ("Gabbia", "Milan", "D", 8, "PECU"),
            ("Hien", "Atalanta", "D", 9, "GALVA"),
            ("Akanji", "Inter", "D", 12, "GIOPPY"),
            ("Estupinan", "Milan", "D", 10, "ROBY"),
            ("Bellanova", "Atalanta", "D", 14, "PAOLO"),
            ("Cambiaso", "Juventus", "D", 18, "PECU"),
            ("Gosens", "Fiorentina", "D", 13, "PAOLO"),
            ("Pulisic", "Milan", "C", 28, "LIBERO"),
            ("Barella", "Inter", "C", 24, "LIBERO"),
            ("Koopmeiners", "Juventus", "C", 29, "LIBERO"),
            ("Calhanoglu", "Inter", "C", 30, "LIBERO"),
            ("Retegui", "Atalanta", "A", 35, "LIBERO"),
            ("Thuram", "Inter", "A", 32, "LIBERO"),
            ("Vlahovic", "Juventus", "A", 31, "LIBERO"),
            ("Lautaro Martinez", "Inter", "A", 42, "LIBERO"),
        ]
        data_list = [{"Nome": g[0], "Squadra": g[1], "Ruolo": g[2], "Quotazione": g[3], "Stato": g[4], "Scadenza_Contratto": 2028} for g in giocatori_base]

    df = pd.DataFrame(data_list)
    
    def assign_tier_and_contract(quot):
        if quot >= 28: return pd.Series(["Top", 2027])      
        elif quot >= 18: return pd.Series(["Semitop", 2028])
        elif quot >= 10: return pd.Series(["Titolare", 2029])
        else: return pd.Series(["Scommessa", 2030]) 
        
    df[["Tier", "Scadenza_Contratto"]] = df["Quotazione"].apply(assign_tier_and_contract)
    
    def genera_indici_salute(row):
        if row["Tier"] == "Top": return pd.Series([0.90, 34, 92])
        elif row["Tier"] == "Semitop": return pd.Series([0.75, 30, 85])
        elif row["Tier"] == "Titolare": return pd.Series([0.65, 28, 78])
        return pd.Series([0.45, 22, 65])
        
    df[["Percentuale_Titolarita", "Partite_Attese", "Indice_Resilienza"]] = df.apply(genera_indici_salute, axis=1)
    df["Media_Voto_Pura"] = df["Ruolo"].apply(lambda r: 6.10 if r in ["D", "C"] else 6.00)
    df["Status_Piazzati"] = df["Quotazione"].apply(lambda q: 3 if q >= 30 else (2 if q >= 20 else 0))
    
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
    df["Bonus_Per_Match"] = np.round(((df["xG_90"] * 3.0) + (df["xA_90"] * 1.0) + (df["Status_Piazzati"] * 0.4)) * df["Moltiplicatore_Team"], 2)
    df["Indice_Appetibilita"] = np.round((df["Valore_Atteso"] * 0.6) + (df["Indice_Resilienza"] * 0.2) + (df["Status_Piazzati"] * 5.0), 1)
    
    return df

if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data_from_pdf()

df = st.session_state.df_giocatori

if df.empty:
    st.stop()

df["Stato"] = df["Stato"].astype(str).str.strip().str.upper()
df["Nome"] = df["Nome"].astype(str).str.strip()

lista_proprietari_csv = [p for p in df["Stato"].unique() if p not in ["LIBERO", "NAN", "NONE", ""]]
if not lista_proprietari_csv:
    lista_proprietari_csv = ["BARDO", "ROBY", "PAOLO", "GALVA", "GIOPPY"]

PARTECIPANTI_LEGA = sorted(lista_proprietari_csv)

if "rose_lega" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}

if "extra_budget" not in st.session_state:
    st.session_state.extra_budget = {p: 0 for p in PARTECIPANTI_LEGA}

# Inizializzazione sicura delle rose una sola volta
if "inizializzato" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
    for idx, row in df.iterrows():
        prop = str(row["Stato"]).strip().upper()
        if prop in st.session_state.rose_lega:
            st.session_state.rose_lega[prop].append({
                "Nome": row["Nome"], 
                "Ruolo": row["Ruolo"],
                "Squadra": row["Squadra"], 
                "Prezzo_Acquisto": int(row["Quotazione"]),
                "Valore_Attuale": int(row["Quotazione"]),
                "Scadenza": int(row["Scadenza_Contratto"])
            })
        else:
            df.loc[idx, "Stato"] = "LIBERO"
    st.session_state.inizializzato = True

for p in PARTECIPANTI_LEGA:
    if p not in st.session_state.rose_lega:
        st.session_state.rose_lega[p] = []
    if p not in st.session_state.extra_budget:
        st.session_state.extra_budget[p] = 0

# ---------------------------------------------------------
# 3. SIDEBAR: PANNELLO DI CONTROLLO & MONITOR OFFERTE
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Dashboard")
fanta_allenatore_attivo = st.sidebar.selectbox("Chi sta acquistando ora:", PARTECIPANTI_LEGA, key="select_allenatore_attivo")

budget_input = st.sidebar.number_input("Budget Iniziale Crediti (Tutti)", value=st.session_state.budget_iniziale, step=10, key="input_budget_iniziale")
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega[fanta_allenatore_attivo]
spesa_corrente = sum(item.get('Prezzo_Acquisto', 1) for item in rosa_corrente)
budget_rimanente_corrente = st.session_state.budget_iniziale + st.session_state.extra_budget[fanta_allenatore_attivo] - spesa_corrente

slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
slot_presi = {r: sum(1 for g in rosa_corrente if g["Ruolo"] == r) for r in slot_target}
slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
totale_slot_liberi = sum(slot_liberi.values())

st.sidebar.metric(f"Budget Rimanente ({fanta_allenatore_attivo})", f"{budget_rimanente_corrente} cr")

# --- PANNELLO MASSIME OFFERTE PER TUTTI IN SIDEBAR ---
st.sidebar.divider()
st.sidebar.subheader("💰 Massime Offerte (Tutti)")

slot_totale_lega = sum(slot_target.values())
for p in PARTECIPANTI_LEGA:
    r_p = st.session_state.rose_lega[p]
    spesa_p = sum(item.get('Prezzo_Acquisto', 1) for item in r_p)
    bud_rim_p = st.session_state.budget_iniziale + st.session_state.extra_budget[p] - spesa_p
    
    slot_presi_p = sum(1 for g in r_p if g["Ruolo"] in slot_target)
    slot_liberi_p = max(0, slot_totale_lega - slot_presi_p)
    riserva_minima_p = max(0, slot_liberi_p - 1)
    max_offerta_p = max(0, bud_rim_p - riserva_minima_p)
    
    st.sidebar.text(f"{p}: Max {max_offerta_p} cr (Rim. {bud_rim_p} cr)")

# --- SALVATAGGIO E CARICAMENTO STATO LEGA ---
st.sidebar.divider()
st.sidebar.subheader("💾 Salvataggio & Caricamento")

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
    st.sidebar.dataframe(df_side[["Nome", "Ruolo", "Spesa", "Valore", "Scadenza"]], use_container_width=True, hide_index=True)
else:
    st.sidebar.info("Questa rosa è attualmente vuota.")

# ---------------------------------------------------------
# 4. DASHBOARD PRINCIPALE: VALUTAZIONE ASTA LIVE
# ---------------------------------------------------------
st.title("⚡ Live Auction Intelligent Assistant (Pdfplumber Engine)")
st.subheader(f"🔍 Analisi Giocatore per: {fanta_allenatore_attivo}")

mask_liberi = (df["Stato"] == "LIBERO") & (df["Nome"].notna()) & (df["Nome"].str.strip() != "")
giocatori_liberi = sorted([str(n) for n in df.loc[mask_liberi, "Nome"].tolist() if str(n).upper() != "NAN"])

if giocatori_liberi:
    giocatore_sel = st.selectbox("Seleziona il giocatore chiamato in asta:", giocatori_liberi, key="select_asta_giocatore")
    g_data = df[df["Nome"] == giocatore_sel].iloc[0]
    
    riserva_minima = max(0, totale_slot_liberi - 1)
    budget_spendibile = max(0, budget_rimanente_corrente - riserva_minima)
    
    percentuali_tier = {"Top": 0.45, "Semitop": 0.22, "Titolare": 0.08, "Scommessa": 0.03}
    base_offerta = int(budget_spendibile * percentuali_tier.get(g_data["Tier"], 0.04))
    
    top_rimanenti_ruolo = len(df[(df["Ruolo"] == g_data["Ruolo"]) & (df["Tier"] == g_data["Tier"]) & (df["Stato"] == "LIBERO")])
    moltiplicatore_scarsita = 1.15 if (top_rimanenti_ruolo <= 3 and g_data["Tier"] in ["Top", "Semitop"]) else 1.0
        
    moltiplicatore_personale = g_data["Percentuale_Titolarita"]
    if g_data["Status_Piazzati"] == 3: base_offerta += 5
    if g_data["Ruolo"] == "D" and g_data["Media_Voto_Pura"] >= 6.10: base_offerta += 2
    
    max_offerta_consigliata = int(base_offerta * moltiplicatore_scarsita * moltiplicatore_personale)
    max_offerta_consigliata = max(1, max_offerta_consigliata)

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ruolo & Squadra", f"{g_data['Ruolo']} - {g_data['Squadra']}", f"Tier: {g_data['Tier']}")
    col2.metric("Quotazione", f"{int(g_data['Quotazione'])} cr", f"Scad.: {int(g_data['Scadenza_Contratto'])}")
    col3.metric("Resilienza / Presenze", f"{int(g_data['Indice_Resilienza'])}% ({int(g_data['Partite_Attese'])} g.)", "Rigorista 🎯" if g_data["Status_Piazzati"] == 3 else "No")
    col4.metric("🔥 Max Offerta Consigliata", f"{max_offerta_consigliata} cr", f"Bonus/M: {g_data['Bonus_Per_Match']}")

    st.info(f"💡 **Consiglio AI:** Valore atteso: **{g_data['Valore_Atteso']}** | Indice Appetibilità: **{g_data['Indice_Appetibilita']}** | Value-for-Money: **{g_data['Indice_VfM']}**")

    valore_default_input = max(1, int(max_offerta_consigliata))

    with st.form("form_aggiudicazione"):
        st.write("### Registra Acquisto Asta")
        col_A, col_B = st.columns(2)
        with col_A:
            prezzo_aggiudicazione = st.number_input("Prezzo di chiusura asta (crediti):", min_value=1, value=valore_default_input, key="input_prezzo_asta")
        with col_B:
            vincitore_asta = st.selectbox("Assegna a fanta-allenatore:", PARTECIPANTI_LEGA, index=PARTECIPANTI_LEGA.index(fanta_allenatore_attivo), key="form_vincitore_asta")
        
        submit_asta = st.form_submit_button("Conferma Acquisto Giocatore")
        
        if submit_asta:
            st.session_state.rose_lega[vincitore_asta].append({
                "Nome": g_data["Nome"],
                "Ruolo": g_data["Ruolo"],
                "Squadra": g_data["Squadra"],
                "Prezzo_Acquisto": int(prezzo_aggiudicazione),
                "Valore_Attuale": int(g_data["Quotazione"]),
                "Scadenza": int(g_data["Scadenza_Contratto"])
            })
            df.loc[df["Nome"] == giocatore_sel, "Stato"] = str(vincitore_asta).upper()
            st.success(f"✅ {giocatore_sel} è stato assegnato a **{vincitore_asta}** per {prezzo_aggiudicazione} crediti!")
else:
    st.success("🎉 Tutti i giocatori sono stati assegnati! L'asta è conclusa.")

# ---------------------------------------------------------
# 5. SEZIONE SCOUTING & VENDITA
# ---------------------------------------------------------
st.divider()
st.subheader("🎯 Scout di Rendimento: Trova i Top Player")

lista_club = sorted([str(c) for c in df["Squadra"].dropna().unique().tolist() if str(c).upper() != "NAN"])
opzioni_club = ["Tutti i club"] + lista_club

col_f1, col_f2, col_f3, col_f4, col_f5 = st.columns(5)
with col_f1:
    filtro_ruolo = st.selectbox("Filtra per Ruolo:", ["Tutti", "P", "D", "C", "A"], key="scout_ruolo")
with col_f2:
    filtro_club = st.selectbox("Filtra per Club:", opzioni_club, key="scout_club")
with col_f3:
    filtro_tier = st.selectbox("Filtra per Tier:", ["Tutti", "Top", "Semitop", "Titolare", "Scommessa"], key="scout_tier")
with col_f4:
    solo_rigoristi = st.checkbox("Solo Rigoristi", key="scout_rigoristi")
with col_f5:
    min_vfm = st.slider("Minimo VfM:", 0.0, 3.0, 0.0, 0.1, key="scout_vfm")

df_scout = df.loc[df["Stato"] == "LIBERO"].copy()

if filtro_ruolo != "Tutti":
    df_scout = df_scout[df_scout["Ruolo"] == filtro_ruolo]
if filtro_club != "Tutti i club":
    df_scout = df_scout[df_scout["Squadra"] == filtro_club]
if filtro_tier != "Tutti":
    df_scout = df_scout[df_scout["Tier"] == filtro_tier]
if solo_rigoristi:
    df_scout = df_scout[df_scout["Status_Piazzati"] == 3]
if min_vfm > 0:
    df_scout = df_scout[df_scout["Indice_VfM"] >= min_vfm]

st.dataframe(
    df_scout[["Nome", "Squadra", "Ruolo", "Quotazione", "Valore_Atteso", "Indice_Appetibilita", "Indice_VfM", "Bonus_Per_Match", "Indice_Resilienza"]],
    use_container_width=True,
    hide_index=True
)