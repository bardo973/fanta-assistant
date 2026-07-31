import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT (LEGA COMPLETA)
# ---------------------------------------------------------
st.set_page_config(page_title="FantaLega Manager Pro", layout="wide")

# Lista dei partecipanti della tua lega (L'app convertirà tutto in MAIUSCOLO per evitare errori)
PARTECIPANTI_LEGA = ["BARDO", "ROBY", "MIO_TEAM", "FUTURO_CAMPIONE", "ZIO_MICK"]
PARTECIPANTI_LEGA = [p.strip().upper() for p in PARTECIPANTI_LEGA]

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500

# Gestione delle rose della lega come dizionario
if "rose_lega" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}

if "inizializzato" not in st.session_state:
    st.session_state.inizializzato = False

# ---------------------------------------------------------
# 2. CARICAMENTO DATI POTENZIATO
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_raw = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")
    
    df = pd.DataFrame()
    df["Nome"] = df_raw["Calciatore"]
    df["Squadra"] = df_raw["Squadra"]
    df["Ruolo"] = df_raw["Ruolo"]
    df["Quotazione"] = pd.to_numeric(df_raw["Quotazione"], errors="coerce").fillna(1)
    
    # 📌 FIX: Pulizia stringhe per evitare errori di corrispondenza maiuscole/minuscole
    if "Unnamed: 5" in df_raw.columns:
        df["Proprietario_Iniziale"] = df_raw["Unnamed: 5"].astype(str).str.strip().str.upper()
    else:
        df["Proprietario_Iniziale"] = "LIBERO"
        
    df["Stato"] = "Libero" 
    
    def assign_tier(quot):
        if quot >= 25: return "Top"
        elif quot >= 15: return "Semitop"
        elif quot >= 8: return "Titolare"
        else: return "Scommessa"
        
    df["Tier"] = df["Quotazione"].apply(assign_tier)
    
    def assegna_metriche_ruolo(ruolo):
        if ruolo == "A": return 0.35, 0.12
        elif ruolo == "C": return 0.15, 0.18
        elif ruolo == "D": return 0.05, 0.08
        return 0.00, 0.00
        
    metriche = df["Ruolo"].apply(assegna_metriche_ruolo)
    df["xG_90"] = [m[0] for m in metriche]
    df["xA_90"] = [m[1] for m in metriche]
    
    hype_squadra = {"Inter": 1.25, "Atalanta": 1.25, "Milan": 1.15, "Juventus": 1.15}
    df["Moltiplicatore_Team"] = df["Squadra"].map(hype_squadra).fillna(0.95)
    df["Valore_Atteso"] = np.round(((df["xG_90"] * 3.0) + (df["xA_90"] * 1.0)) * 100 * df["Moltiplicatore_Team"], 1)
    df["Indice_VfM"] = np.round(df["Valore_Atteso"] / df["Quotazione"], 2)
    df["Rigorista"] = "No"
    
    return df

if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data()

# 📌 FIX: Sincronizzazione automatica e forzata delle rose dal CSV allo stato di sessione
if not st.session_state.inizializzato:
    # Resetta per sicurezza prima dell'importazione iniziale
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
    
    df_f = st.session_state.df_giocatori
    for idx, row in df_f.iterrows():
        prop = row["Proprietario_Iniziale"]
        if prop in st.session_state.rose_lega:
            st.session_state.rose_lega[prop].append({
                "Nome": row["Nome"], 
                "Ruolo": row["Ruolo"],
                "Squadra": row["Squadra"], 
                "Prezzo": int(row["Quotazione"])
            })
            st.session_state.df_giocatori.at[idx, "Stato"] = prop
        else:
            st.session_state.df_giocatori.at[idx, "Stato"] = "Libero"
    st.session_state.inizializzato = True

df = st.session_state.df_giocatori

# ---------------------------------------------------------
# 3. SIDEBAR: PANNELLO DI CONTROLLO LEGA COMPLETA
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Dashboard")

fanta_allenatore_attivo = st.sidebar.selectbox("Seleziona chi sta acquistando:", PARTECIPANTI_LEGA)

budget_input = st.sidebar.number_input("Budget Iniziale Crediti (Valido per tutti)", value=st.session_state.budget_iniziale, step=10)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega[fanta_allenatore_attivo]
spesa_corrente = sum(item['Prezzo'] for item in rosa_corrente)
budget_rimanente_corrente = st.session_state.budget_iniziale - spesa_corrente

slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
slot_presi = {r: sum(1 for g in rosa_corrente if g["Ruolo"] == r) for r in slot_target}
slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
totale_slot_liberi = sum(slot_liberi.values())

st.sidebar.metric(f"Budget Rimanente ({fanta_allenatore_attivo})", f"{budget_rimanente_corrente} / {st.session_state.budget_iniziale} cr")

st.sidebar.subheader(f"Slot Liberi {fanta_allenatore_attivo}")
col_s1, col_s2 = st.sidebar.columns(2)
col_s1.write(f"🧤 Portieri: **{slot_liberi['P']}**")
col_s1.write(f"🛡️ Difensori: **{slot_liberi['D']}**")
col_s2.write(f"⚙️ Centrocampisti: **{slot_liberi['C']}**")
col_s2.write(f"⚽ Attaccanti: **{slot_liberi['A']}**")

# ---------------------------------------------------------
# 4. DASHBOARD PRINCIPALE: MERCATO & ASTA LIVE
# ---------------------------------------------------------
st.title("⚡ Live Auction & Market Manager")

st.subheader(f"🔍 Registra Acquisto per: {fanta_allenatore_attivo}")
giocatori_liberi = df[df["Stato"] == "Libero"]["Nome"].tolist()

if giocatori_liberi:
    giocatore_sel = st.selectbox("Seleziona il giocatore chiamato in asta:", giocatori_liberi)
    g_data = df[df["Nome"] == giocatore_sel].iloc[0]
    
    riserva_minima = max(0, totale_slot_liberi - 1)
    budget_spendibile = max(0, budget_rimanente_corrente - riserva_minima)
    
    percentuali_tier = {"Top": 0.50, "Semitop": 0.25, "Titolare": 0.10, "Scommessa": 0.04}
    max_offerta = max(1, int(budget_spendibile * percentuali_tier.get(g_data["Tier"], 0.05))) if slot_liberi[g_data["Ruolo"]] > 0 else 0

    col1, col2, col3 = st.columns(3)
    col1.metric("Ruolo / Tier", f"{g_data['Ruolo']} — {g_data['Tier']}")
    col2.metric("Indice Convenienza (VfM)", f"{g_data['Indice_VfM']} pt/cr")
    col3.metric("Offerta Max Consigliata", f"{max_offerta} cr", delta=f"Quotazione: {g_data['Quotazione']}")

    with st.form("compra_form", clear_on_submit=True):
        col_f1, col_f2 = st.columns([3, 1])
        valore_iniziale = max(1, min(max_offerta, max(1, budget_rimanente_corrente)))
        
        prezzo_acquisto = col_f1.number_input(
            f"Prezzo d'acquisto per {fanta_allenatore_attivo}:", 
            min_value=1, max_value=max(1, budget_rimanente_corrente), value=valore_iniziale
        )
        submit_acquisto = col_f2.form_submit_button("✅ Assegna Giocatore")
        
        if submit_acquisto:
            if slot_liberi[g_data["Ruolo"]] > 0:
                st.session_state.rose_lega[fanta_allenatore_attivo].append({
                    "Nome": g_data["Nome"], "Ruolo": g_data["Ruolo"],
                    "Squadra": g_data["Squadra"], "Prezzo": prezzo_acquisto
                })
                st.session_state.df_giocatori.loc[st.session_state.df_giocatori["Nome"] == g_data["Nome"], "Stato"] = fanta_allenatore_attivo
                st.success(f"{g_data['Nome']} assegnato a {fanta_allenatore_attivo} per {prezzo_acquisto} cr!")
                st.rerun()
            else:
                st.error(f"{fanta_allenatore_attivo} non ha più slot liberi per il ruolo {g_data['Ruolo']}!")
else:
    st.info("Tutti i calciatori del database sono stati assegnati alle squadre.")

st.divider()

# ---------------------------------------------------------
# 5. SEZIONE DI INTERSCAMBIO: CESSIONI / SVINCULI & MERCATO
# ---------------------------------------------------------
st.subheader("🔁 Gestione Cessioni, Svincoli e Scambi")

giocatori_presi = df[df["Stato"] != "Libero"]

if not giocatori_presi.empty:
    col_cess1, col_cess2 = st.columns([3, 1])
    
    with col_cess1:
        giocatore_da_svincolare = st.selectbox("Seleziona un giocatore da svincolare/cedere:", giocatori_presi["Nome"].tolist())
        g_cess_data = giocatori_presi[giocatori_presi["Nome"] == giocatore_da_svincolare].iloc[0]
        proprietario_attuale = g_cess_data["Stato"]
        
        prezzo_pagato = next((item["Prezzo"] for item in st.session_state.rose_lega[proprietario_attuale] if item["Nome"] == giocatore_da_svincolare), 1)
        st.caption(f"Proprietario attuale: **{proprietario_attuale}** | Pagato: **{prezzo_pagato} cr**")
        
    with col_cess2:
        st.write("") 
        if st.button("🗑️ Svincola (Torna Libero)", use_container_width=True):
            st.session_state.rose_lega[proprietario_attuale] = [j for j in st.session_state.rose_lega[proprietario_attuale] if j["Nome"] != giocatore_da_svincolare]
            st.session_state.df_giocatori.loc[st.session_state.df_giocatori["Nome"] == giocatore_da_svincolare, "Stato"] = "Libero"
            st.success(f"{giocatore_da_svincolare} svincolato! {proprietario_attuale} recupera {prezzo_pagato} cr.")
            st.rerun()
else:
    st.info("Nessun giocatore assegnato al momento.")

st.divider()

# ---------------------------------------------------------
# 6. TABELLA RIEPILOGATIVA DI TUTTE LE ROSE DELLA LEGA
# ---------------------------------------------------------
st.subheader("📋 Tabellone Generale delle Rose della Lega")

# Creazione di tab dinamiche per visualizzare la rosa di ogni fanta-allenatore
tabs_squadre = st.tabs([f"👥 {p}" for p in PARTECIPANTI_LEGA])

for i, p in enumerate(PARTECIPANTI_LEGA):
    with tabs_squadre[i]:
        rosa_p = st.session_state.rose_lega[p]
        if rosa_p:
            df_rosa_p = pd.DataFrame(rosa_p)
            
            # Ordinamento logico dei ruoli (Portieri -> Difensori -> Centrocampisti -> Attaccanti)
