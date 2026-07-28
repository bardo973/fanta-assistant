import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT
# ---------------------------------------------------------
st.set_page_config(page_title="FantaAsta Assistant", layout="wide")

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500
if "budget_rimanente" not in st.session_state:
    st.session_state.budget_rimanente = 500
if "rosa" not in st.session_state:
    st.session_state.rosa = []

# ---------------------------------------------------------
# 2. CARICAMENTO DATI DAL TUO CSV REALE
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_raw = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")
    
    df = pd.DataFrame()
    df["Nome"] = df_raw["Calciatore"]
    df["Squadra"] = df_raw["Squadra"]
    df["Ruolo"] = df_raw["Ruolo"]
    df["Quotazione"] = pd.to_numeric(df_raw["Quotazione"], errors="coerce").fillna(1)
    
    df["Stato"] = df_raw["SVINCOLATO"].apply(lambda x: "Libero" if str(x).strip().upper() == "SI" else "Preso")
    
    def assign_tier(quot):
        if quot >= 25: return "Top"
        elif quot >= 15: return "Semitop"
        elif quot >= 8: return "Titolare"
        else: return "Scommessa"
        
    df["Tier"] = df["Quotazione"].apply(assign_tier)
    
    df["xG_90"] = 0.20
    df["xA_90"] = 0.15
    df["Rigorista"] = "No"
    df["Valore_Atteso"] = np.round((df["xG_90"] * 1.5 + df["xA_90"] * 1.0) * 100, 1)
    
    return df

if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data()

df = st.session_state.df_giocatori

if not st.session_state.rosa:
    df_raw_init = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")
    bardo_init = df_raw_init[df_raw_init["Unnamed: 5"] == "BARDO"]
    for _, row in bardo_init.iterrows():
        st.session_state.rosa.append({
            "Nome": row["Calciatore"],
            "Ruolo": row["Ruolo"],
            "Squadra": row["Squadra"],
            "Prezzo": int(row["Quotazione"]) if pd.notna(row["Quotazione"]) else 1
        })
    spesa_iniziale = sum(item['Prezzo'] for item in st.session_state.rosa)
    st.session_state.budget_rimanente = st.session_state.budget_iniziale - spesa_iniziale

# ---------------------------------------------------------
# 3. SIDEBAR: PANNELLO DI CONTROLLO & BUDGET
# ---------------------------------------------------------
st.sidebar.title("⚽ FantaAsta Control Panel")

budget_input = st.sidebar.number_input("Budget Iniziale Crediti", value=st.session_state.budget_iniziale, step=10)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input
    spesa_attuale = sum(item['Prezzo'] for item in st.session_state.rosa)
    st.session_state.budget_rimanente = budget_input - spesa_attuale

slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
slot_presi = {r: sum(1 for g in st.session_state.rosa if g["Ruolo"] == r) for r in slot_target}
slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
totale_slot_liberi = sum(slot_liberi.values())

st.sidebar.metric("Budget Rimanente", f"{st.session_state.budget_rimanente} / {st.session_state.budget_iniziale} cr")

st.sidebar.subheader("Slot Rimanenti")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.write(f"🧤 Portieri: **{slot_liberi['P']}**")
col_s1.write(f"🛡️ Difensori: **{slot_liberi['D']}**")
col_s2.write(f"⚙️ Centrocampisti: **{slot_liberi['C']}**")
col_s2.write(f"⚽ Attaccanti: **{slot_liberi['A']}**")

# ---------------------------------------------------------
# 4. DASHBOARD PRINCIPALE
# ---------------------------------------------------------
st.title("⚡ Live Auction Assistant")

st.subheader("🔍 Valutazione Giocatore In Asta")
giocatori_liberi = df[df["Stato"] == "Libero"]["Nome"].tolist()

if giocatori_liberi:
    giocatore_sel = st.selectbox("Seleziona o cerca il giocatore chiamato:", giocatori_liberi)
    g_data = df[df["Nome"] == giocatore_sel].iloc[0]
    
    riserva_minima = max(0, totale_slot_liberi - 1)
    budget_spendibile = max(0, st.session_state.budget_rimanente - riserva_minima)
    
    percentuali_tier = {"Top": 0.50, "Semitop": 0.25, "Titolare": 0.10, "Scommessa": 0.04}
    peso = percentuali_tier.get(g_data["Tier"], 0.05)
    
    max_offerta = int(budget_spendibile * peso)
    max_offerta = max(1, max_offerta) if slot_liberi[g_data["Ruolo"]] > 0 else 0

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Ruolo / Tier", f"{g_data['Ruolo']} — {g_data['Tier']}")
    col2.metric("xG / xA per 90m", f"{g_data['xG_90']} / {g_data['xA_90']}")
    col3.metric("Rigorista", g_data["Rigorista"])
    col4.metric("Offerta Max Consigliata", f"{max_offerta} cr", delta=f"Quotazione: {g_data['Quotazione']}")

    with st.form("compra_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns([3, 1])
        
        budget_disponibile = max(1, st.session_state.budget_rimanente)
        valore_iniziale = max(1, min(max_offerta, budget_disponibile))
        
        prezzo_acquisto = col_f1.number_input(
            f"Prezzo di acquisto per {g_data['Nome']}:", 
            min_value=1, 
            max_value=budget_disponibile, 
            value=valore_iniziale
        )
        submit_acquisto = col_f2.form_submit_button("✅ Aggiungi alla Rosa")
        
        if submit_acquisto:
            if slot_liberi[g_data["Ruolo"]] > 0:
                st.session_state.rosa.append({
                    "Nome": g_data["Nome"],
                    "Ruolo": g_data["Ruolo"],
                    "Squadra": g_data["Squadra"],
                    "Prezzo": prezzo_acquisto
                })
                st.session_state.budget_rimanente -= prezzo_acquisto
                st.session_state.df_giocatori.loc[st.session_state.df_giocatori["Nome"] == g_data["Nome"], "Stato"] = "Preso"
                st.success(f"{g_data['Nome']} acquistato per {prezzo_acquisto} crediti!")
                st.rerun()
            else:
                st.error(f"Hai già completato i posti per il ruolo {g_data['Ruolo']}!")
else:
    st.info("Tutti i giocatori nel database risultano già assegnati.")

st.divider()

# ---------------------------------------------------------
# 5. SEZIONE: CONSIGLIATI PER RUOLO (TOP LIBERI)
# ---------------------------------------------------------
st.subheader("⭐ Top Giocatori Consigliati (Liberi per Ruolo)")
tab_p, tab_d, tab_c, tab_a = st.tabs(["🧤 Portieri", "🛡️ Difensori", "⚙️ Centrocampisti", "⚽ Attaccanti"])

df_liberi = df[df["Stato"] == "Libero"]

with tab_p:
    top_p = df_liberi[df_liberi["Ruolo"] == "P"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_p[["Nome", "Squadra", "Tier", "Quotazione"]], use_container_width=True, hide_index=True)

with tab_d:
    top_d = df_liberi[df_liberi["Ruolo"] == "D"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_d[["Nome", "Squadra", "Tier", "Quotazione"]], use_container_width=True, hide_index=True)

with tab_c:
    top_c = df_liberi[df_liberi["Ruolo"] == "C"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_c[["Nome", "Squadra", "Tier", "Quotazione"]], use_container_width=True, hide_index=True)

with tab_a:
    top_a = df_liberi[df_liberi["Ruolo"] == "A"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_a[["Nome", "Squadra", "Tier", "Quotazione"]], use_container_width=True, hide_index=True)

st.divider()

# ---------------------------------------------------------
# 6. TABELLA GENERALE & GESTIONE ROSA
# ---------------------------------------------------------
col_left, col_right = st.columns([2, 1])

with col_left:
    st.subheader("📊 Tutti i Giocatori Disponibili")
    ruolo_filter = st.radio("Filtra Ruolo:", ["Tutti", "P", "D", "C", "A"], horizontal=True)
    
    df_disp = df[df["Stato"] == "Libero"]
    if ruolo_filter != "Tutti":
        df_disp = df_disp[df_disp["Ruolo"] == ruolo_filter]
        
    st.dataframe(
        df_disp[["Nome", "Squadra", "Ruolo", "Tier", "Quotazione"]],
        use_container_width=True,
        hide_index=True
    )

with col_right:
    st.subheader("📋 La Tua Rosa")
    if st.session_state.rosa:
        df_rosa = pd.DataFrame(st.session_state.rosa)
        st.dataframe(df_rosa[["Ruolo", "Nome", "Prezzo"]], use_container_width=True, hide_index=True)
        st.caption(f"Totale speso: **{st.session_state.budget_iniziale - st.session_state.budget_rimanente} cr**")
        
        with st.expander("⚙️ Gestisci Rosa (Rimuovi giocatore)"):
            nomi_rosa = [g["Nome"] for g in st.session_state.rosa]
            da_rimuovere = st.selectbox("Seleziona giocatore da svincolare:", nomi_rosa)
            if st.button("🗑️ Rimuovi dalla Rosa"):
                giocatore_rimosso = next((g for g in st.session_state.rosa if g["Nome"] == da_rimuovere), None)
                if giocatore_rimosso:
                    st.session_state.budget_rimanente += giocatore_rimosso["Prezzo"]
                    st.session_state.rosa = [g for g in st.session_state.rosa if g["Nome"] != da_rimuovere]
                    st.session_state.df_giocatori.loc[st.session_state.df_giocatori["Nome"] == da_rimuovere, "Stato"] = "Libero"
                    st.success(f"{da_rimuovere} rimosso e crediti rimborsati!")
                    st.rerun()
    else:
        st.write("*Nessun giocatore acquistato finora.*")
