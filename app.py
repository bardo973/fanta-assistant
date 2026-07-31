import streamlit as st
import pandas as pd
import numpy as np

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT
# ---------------------------------------------------------
st.set_page_config(page_title="FantaAsta Pro Assistant", layout="wide")

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500
if "budget_rimanente" not in st.session_state:
    st.session_state.budget_rimanente = 500
if "rosa" not in st.session_state:
    st.session_state.rosa = []
if "inizializzato" not in st.session_state:
    st.session_state.inizializzato = False

# ---------------------------------------------------------
# 2. CARICAMENTO DATI POTENZIATO (LOGICA LOW-COST)
# ---------------------------------------------------------
@st.cache_data
def load_data():
    # Caricamento del file CSV reale
    df_raw = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")
    
    df = pd.DataFrame()
    df["Nome"] = df_raw["Calciatore"]
    df["Squadra"] = df_raw["Squadra"]
    df["Ruolo"] = df_raw["Ruolo"]
    df["Quotazione"] = pd.to_numeric(df_raw["Quotazione"], errors="coerce").fillna(1)
    
    # Stato di disponibilità del calciatore
    df["Stato"] = df_raw["SVINCOLATO"].apply(lambda x: "Libero" if str(x).strip().upper() == "SI" else "Preso")
    
    # Definizione dinamica dei Tier basata sulla quotazione di mercato
    def assign_tier(quot):
        if quot >= 25: return "Top"
        elif quot >= 15: return "Semitop"
        elif quot >= 8: return "Titolare"
        else: return "Scommessa"
        
    df["Tier"] = df["Quotazione"].apply(assign_tier)
    
    # 📌 NOVITÀ: Stima statistica differenziata per ruolo (in attesa di dati reali)
    def assegna_metriche_ruolo(ruolo):
        if ruolo == "A": return 0.35, 0.12  # Alta incidenza di gol attesi
        elif ruolo == "C": return 0.15, 0.18 # Più propensi agli assist
        elif ruolo == "D": return 0.05, 0.08 # Bonus prevalentemente da piazzati/cross
        return 0.00, 0.00                    # Portieri
        
    metriche = df["Ruolo"].apply(assegna_metriche_ruolo)
    df["xG_90"] = [m[0] for m in metriche]
    df["xA_90"] = [m[1] for m in metriche]
    
    # 📌 NOVITÀ: Moltiplicatore di forza offensiva della squadra (Fattore Sorpresa)
    # Aggiungi o modifica le squadre per dare una spinta ai giocatori delle big o delle sorprese
    hype_squadra = {
        "Inter": 1.25, "Atalanta": 1.25, "Milan": 1.15, "Juventus": 1.15, 
        "Napoli": 1.15, "Roma": 1.10, "Lazio": 1.10, "Bologna": 1.05
    }
    df["Moltiplicatore_Team"] = df["Squadra"].map(hype_squadra).fillna(0.95)
    
    # Calcolo del Potenziale Offensivo Pesato (Punti Bonus Attesi)
    # Gol = +3 punti, Assist = +1 punto
    df["Valore_Atteso"] = np.round(((df["xG_90"] * 3.0) + (df["xA_90"] * 1.0)) * 100 * df["Moltiplicatore_Team"], 1)
    
    # 📌 NOVITÀ: Indice Costo/Efficienza (Value for Money)
    # Più l'indice è alto, più il giocatore produce potenziale bonus in rapporto a quanto costa
    df["Indice_VfM"] = np.round(df["Valore_Atteso"] / df["Quotazione"], 2)
    
    # Placeholder Rigorista (Puoi mapparlo manualmente per scovare rigoristi low cost)
    df["Rigorista"] = "No"
    
    return df

if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data()

df = st.session_state.df_giocatori

# Inizializzazione automatica della rosa pre-esistente (BARDO)
if not st.session_state.inizializzato:
    df_raw_init = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")
    if "Unnamed: 5" in df_raw_init.columns:
        bardo_init = df_raw_init[df_raw_init["Unnamed: 5"] == "BARDO"]
        for _, row in bardo_init.iterrows():
            st.session_state.rosa.append({
                "Nome": row["Calciatore"],
                "Ruolo": row["Ruolo"],
                "Squadra": row["Squadra"],
                "Prezzo": int(row["Quotazione"]) if pd.notna(row["Quotazione"]) else 1
            })
            st.session_state.df_giocatori.loc[st.session_state.df_giocatori["Nome"] == row["Calciatore"], "Stato"] = "Preso"
            
    spesa_iniziale = sum(item['Prezzo'] for item in st.session_state.rosa)
    st.session_state.budget_rimanente = st.session_state.budget_iniziale - spesa_iniziale
    st.session_state.inizializzato = True

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
st.title("⚡ Live Auction Assistant Pro")

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
    col2.metric("Indice Costo/Efficienza (VfM)", f"{g_data['Indice_VfM']} pt/cr")
    col3.metric("Potenziale Teorico", f"{g_data['Valore_Atteso']} Pti")
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
# 5. SEZIONE: CONSIGLIATI E OCCASIONI LOW-COST
# ---------------------------------------------------------
st.subheader("⭐ Consigli per gli Acquisti (Liberi per Ruolo)")
tab_p, tab_d, tab_c, tab_a, tab_affari = st.tabs([
    "🧤 Portieri", "🛡️ Difensori", "⚙️ Centrocampisti", "⚽ Attaccanti", "💎 Occasioni Low Cost"
])

df_liberi = df[df["Stato"] == "Libero"]

with tab_p:
    top_p = df_liberi[df_liberi["Ruolo"] == "P"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_p[["Nome", "Squadra", "Tier", "Quotazione", "Indice_VfM"]], use_container_width=True, hide_index=True)

with tab_d:
    top_d = df_liberi[df_liberi["Ruolo"] == "D"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_d[["Nome", "Squadra", "Tier", "Quotazione", "Indice_VfM"]], use_container_width=True, hide_index=True)

with tab_c:
    top_c = df_liberi[df_liberi["Ruolo"] == "C"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_c[["Nome", "Squadra", "Tier", "Quotazione", "Indice_VfM"]], use_container_width=True, hide_index=True)

with tab_a:
    top_a = df_liberi[df_liberi["Ruolo"] == "A"].sort_values(by="Quotazione", ascending=False).head(5)
    st.dataframe(top_a[["Nome", "Squadra", "Tier", "Quotazione", "Indice_VfM"]], use_container_width=True, hide_index=True)

# 📌 NOVITÀ: Tab dedicata per scovare le scommesse matematiche a basso costo
with tab_affari:
    st.markdown("#### 🚀 Giocatori con Quotazione ≤ 12 cr ordinati per Efficienza Potenziale (VfM)")
    # Filtra per costo accessibile ed esclude i portieri dalla metrica offensiva
