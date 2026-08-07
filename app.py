import streamlit as st
import pandas as pd

st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

# --- LISTA DELLE 10 SQUADRE UFFICIALI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

# --- FUNZIONI DI CALCOLO E PULIZIA ---
def calcola_prezzo_consigliato(row):
    quot = row.get('Quotazione', 10)
    fm = row.get('FantaMedia', 6.0)
    fm_2025 = row.get('FM_2025', fm)
    fm_2024 = row.get('FM_2024', fm)
    
    # Media storica pesata (50% anno corrente, 30% 2025, 20% 2024)
    media_storica = (fm * 0.5) + (fm_2025 * 0.3) + (fm_2024 * 0.2)
    bonus_rendimento = max(0, (media_storica - 6.0) * 5)
    
    ruolo = row.get('Ruolo', 'C')
    moltiplicatore_ruolo = {'A': 1.3, 'C': 1.1, 'D': 1.0, 'P': 0.9}.get(ruolo, 1.0)
    
    prezzo_stimato = (quot + bonus_rendimento) * moltiplicatore_ruolo
    return max(1, int(round(prezzo_stimato)))

def calcola_costanza(row):
    fm = row.get('FantaMedia', 6.0)
    if fm >= 7.0:
        return "🔥 Altissima"
    elif fm >= 6.5:
        return "🟢 Buona"
    elif fm >= 6.0:
        return "🟡 Altalenante"
    else:
        return "🔴 Rischiosa"

def calcola_trend(row):
    fm_attuale = row.get('FantaMedia', 6.0)
    fm_passata = row.get('FM_2025', fm_attuale)
    diff = fm_attuale - fm_passata
    if diff > 0.1:
        return "📈 In Crescita"
    elif diff < -0.1:
        return "📉 In Calo"
    else:
        return "➡️ Stabile"

# --- INIZIALIZZAZIONE STATO DELLA SESSIONE (DATABASE TEMPORANEO) ---
if 'listone_ufficiale' not in st.session_state:
    st.session_state.listone_ufficiale = pd.DataFrame([
        {"Id": 1, "Nome": "Lautaro Martinez", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 40, "FantaMedia": 8.5, "FM_2025": 8.2, "FM_2024": 8.8},
        {"Id": 2, "Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 22, "FantaMedia": 7.4, "FM_2025": 7.3, "FM_2024": 7.5},
        {"Id": 3, "Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 14, "FantaMedia": 6.7, "FM_2025": 6.5, "FM_2024": 6.2},
        {"Id": 4, "Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 12, "FantaMedia": 5.5, "FM_2025": 5.3, "FM_2024": 5.4}
    ])

if 'squadre' not in st.session_state:
    st.session_state.squadre = {sq: {"crediti": 500, "rosa": pd.DataFrame(columns=["Nome", "Ruolo", "Squadra_SerieA", "Costo_Acquisto", "In_Listone"])} for sq in NOMI_SQUADRE}

if 'voti_giornata' not in st.session_state:
    st.session_state.voti_giornata = {}

# --- INTERFACCIA GRAFICA (TABS) ---
tab1, tab2, tab3, tab4 = st.tabs(["📋 Scouting & Listone", "🏠 Gestione 10 Rose", "📊 Grafici di Lega", "📥 Carica Listone & Dati"])

# --- TAB 1: SCOUTING & LISTONE ---
with tab1:
    st.header("🔍 Scouting Calciatori & Analisi Valore")
    
    df_visualizzazione = st.session_state.listone_ufficiale.copy()
    if not df_visualizzazione.empty:
        df_visualizzazione['Prezzo_Consigliato'] = df_visualizzazione.apply(calcola_prezzo_consigliato, axis=1)
        df_visualizzazione['Costanza'] = df_visualizzazione.apply(calcola_costanza, axis=1)
        df_visualizzazione['Trend'] = df_visualizzazione.apply(calcola_trend, axis=1)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            ricerca_nome = st.text_input("Cerca calciatore per nome:")
        with col_f2:
            ricerca_ruolo = st.multiselect("Filtra per Ruolo:", options=["P", "D", "C", "A"], default=["P", "D", "C", "A"])
            
        if ricerca_nome:
            df_visualizzazione = df_visualizzazione[df_visualizzazione['Nome'].str.contains(ricerca_nome, case=False, na=False)]
        df_visualizzazione = df_visualizzazione[df_visualizzazione['Ruolo'].isin(ricerca_ruolo)]
        
        st.dataframe(df_visualizzazione[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Prezzo_Consigliato", "Costanza", "Trend"]], use_container_width=True)
        
        st.subheader("⚡ Assegna Giocatore del Listone a una Squadra")
        col_as1, col_as2, col_as3, col_as4 = st.columns(4)
        with col_as1:
            p_selezionato = st.selectbox("Seleziona Calciatore:", options=df_visualizzazione['Nome'].tolist())
        with col_as2:
            squadra_dest = st.selectbox("Assegna a:", options=NOMI_SQUADRE, key="dest_listone")
        with col_as3:
            prezzo_asta = st.number_input("Prezzo d'acquisto (Crediti):", min_value=1, max_value=500, value=1)
        with col_as4:
            if st.button("Conferma Acquisto da Listone"):
                giocatore_dati = df_visualizzazione[df_visualizzazione['Nome'] == p_selezionato].iloc[0]
                nuovo_player = pd.DataFrame([{
                    "Nome": giocatore_dati['Nome'], "Ruolo": giocatore_dati['Ruolo'], 
                    "Squadra_SerieA": giocatore_dati['Squadra_SerieA'], "Costo_Acquisto": prezzo_asta, "In_Listone": "✅ Attivo"
                }])
                st.session_state.squadre[squadra_dest]["rosa"] = pd.concat([st.session_state.squadre[squadra_dest]["rosa"], nuovo_player], ignore_index=True)
                st.session_state.squadre[squadra_dest]["crediti"] -= prezzo_asta
                st.success(f"{p_selezionato} assegnato correttamente a {squadra_dest}!")
                st.rerun()

# --- TAB 2: GESTIONE 10 ROSE ---
with tab2:
    st.header("🏠 Gestione Rose e Inserimento Manuale")
    squadra_sel = st.selectbox("Seleziona la Fanta-Squadra da visualizzare/modificare:", options=NOMI_SQUADRE)
    
    col_r1, col_r2 = st.columns(2)
    
    with col_r1:
        st.subheader(f"Rosa attuale di: {squadra_sel}")
        rosa_attuale = st.session_state.squadre[squadra_sel]["rosa"]
        crediti_rimasti = st.session_state.squadre[squadra_sel]["crediti"]
        st.metric(label="Budget Residuo (su 500 iniziali)", value=f"{crediti_rimasti} / 500 Crediti")
        
        if not rosa_attuale.empty:
            nomi_listone = st.session_state.listone_ufficiale['Nome'].tolist()
            rosa_attuale['In_Listone'] = rosa_attuale['Nome'].apply(lambda x: "✅ Attivo" if x in nomi_listone else "❌ NON IN LISTONE")
            
            st.dataframe(rosa_attuale, use_container_width=True)
            
            player_da_svincolare = st.selectbox("Seleziona un giocatore da svincolare:", options=rosa_attuale['Nome'].tolist())
            if st.button("Svincola Giocatore"):
                costo = rosa_attuale[rosa_attuale['Nome'] == player_da_svincolare]['Costo_Acquisto'].values[0]
                st.session_state.squadre[squadra_sel]["rosa"] = rosa_attuale[rosa_attuale['Nome'] != player_da_svincolare].reset_index(drop=True)
                st.session_state.squadre[squadra_sel]["crediti"] += costo
                st.success(f"{player_da_svincolare} svincolato. Crediti restituiti: {costo}")
                st.rerun()
        else:
            st.info("Questa rosa è attualmente vuota.")
            
    with col_r2:
        st.subheader("➕ Inserimento Manuale Diretto")
        with st.form("form_manuale"):
            m_nome = st.text_input("Nome Calciatore:")
            m_ruolo = st.selectbox("Ruolo:", ["P", "D", "C", "A"])
            m_squadra = st.text_input("Squadra Serie A:")
            m_prezzo = st.number_input("Prezzo di Acquisto:", min_value=1, value=1)
            submit_m = st.form_submit_button("Aggiungi alla Rosa")
            
            if submit_m and m_nome:
                nuovo_p_man = pd.DataFrame([{
                    "Nome": m_nome, "Ruolo": m_ruolo, "Squadra_SerieA": m_squadra, "Costo_Acquisto": m_prezzo, "In_Listone": "✅ Attivo"
                }])
                st.session_state.squadre[squadra_sel]["rosa"] = pd.concat([st.session_state.squadre[squadra_sel]["rosa"], nuovo_p_man], ignore_index=True)
                st.session_state.squadre[squadra_sel]["crediti"] -= m_prezzo
                st.success(f"{m_nome} inserito manualmente in {squadra_sel}!")
                st.rerun()

# --- TAB 3: GRAFICI DI LEGA ---
with tab3:
    st.header("📊 Analisi e Confronto della Lega")
    if any(not st.session_state.squadre[sq]["rosa"].empty for sq in NOMI_SQUADRE):
        dati_grafico = []
        for sq in NOMI_SQUADRE:
            crediti_restanti = st.session_state.squadre[sq]["crediti"]
            dati_grafico.append({"FantaSquadra": sq, "Crediti Residui": crediti_restanti})
        
        df_grafico = pd.DataFrame(dati_grafico)
        st.subheader("💰 Crediti Rimanenti per Squadra")
        st.bar_chart(data=df_grafico, x="FantaSquadra", y="Crediti Residui")
    else:
        st.info("Dati insufficienti per generare i grafici. Inserisci prima dei giocatori nelle rose.")

# --- TAB 4: CARICA LISTONE ---
with tab4:
    st.header("📥 Caricamento File Listone (Excel o CSV)")
    st.write("Carica il file delle quotazioni ufficiale. Il sistema aggiornerà i dati senza cancellare le vecchie statistiche.")
    
    file_caricato = st.file_uploader("Scegli un file Excel o CSV", type=["xlsx", "csv"])
    
    if file_caricato is not None:
        try:
            if file_caricato.name.endswith('.csv'):
                nuovo_df = pd.read_csv(file_caricato)
            else:
                nuovo_df = pd.read_excel(file_caricato)
                
            st.success("File caricato con successo! Mappa le colonne del tuo file:")
            
            col_m1, col_m2, col_m3, col_m4 = st.columns(4)
            all_cols = nuovo_df.columns.tolist()
            
            with col_m1: 
                c_nome = st.selectbox("Colonna Nome:", all_cols, index=0)
            with col_m2: 
                c_ruolo = st.selectbox("Colonna Ruolo:", all_cols, index=1 if len(all_cols)>1 else 0)
            with col_m3: 
                c_squadra = st.selectbox("Colonna Squadra:", all_cols, index=2 if len(all_cols)>2 else 0)
            with col_m4: 
