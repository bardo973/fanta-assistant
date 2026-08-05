import streamlit as st
import pandas as pd
import numpy as np

st.set_page_config(page_title="FantaManager & Scouting Hub", page_icon="⚽", layout="wide")

# --- INIZIALIZZAZIONE DELLO STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state:
    st.session_state.squadre = {
        "Squadra A": {"crediti": 500, "rosa": []},
        "Squadra B": {"crediti": 500, "rosa": []},
        "Squadra C": {"crediti": 500, "rosa": []}
    }

if 'giocatori_db' not in st.session_state:
    # Database iniziale di scouting
    data_iniziale = [
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Como", "Quotazione": 27, "FantaMedia": 7.8, "Potenziale": 4, "Titolarita": 5},
        {"Nome": "Vardy", "Ruolo": "A", "Squadra_SerieA": "Cremonese", "Quotazione": 16, "FantaMedia": 7.2, "Potenziale": 3, "Titolarita": 4},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Juventus", "Quotazione": 11, "FantaMedia": 6.8, "Potenziale": 4, "Titolarita": 3},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 13, "FantaMedia": 7.5, "Potenziale": 4, "Titolarita": 5},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 18, "FantaMedia": 6.9, "Potenziale": 3, "Titolarita": 4},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 13, "FantaMedia": 6.7, "Potenziale": 4, "Titolarita": 4},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Potenziale": 5, "Titolarita": 5},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Potenziale": 3, "Titolarita": 4},
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Potenziale": 3, "Titolarita": 5},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Potenziale": 2, "Titolarita": 3}
    ]
    st.session_state.giocatori_db = pd.DataFrame(data_iniziale)

# Assegnazione di esempio iniziale se le rose sono vuote (per test rapido)
if len(st.session_state.squadre["Squadra A"]["rosa"]) == 0:
    st.session_state.squadre["Squadra A"]["rosa"].append({"Nome": "Douvikas", "Ruolo": "A", "Costo_Acquisto": 27})
    st.session_state.squadre["Squadra B"]["rosa"].append({"Nome": "Zaccagni", "Ruolo": "C", "Costo_Acquisto": 13})

# --- BARRA LATERALE: NAVIGAZIONE ---
st.sidebar.title("⚽ Fanta Manager Hub")
menu = st.sidebar.selectbox("Navigazione", [
    "🔍 Scouting & Database", 
    "🛒 Mercato (Acquisti/Vendite)", 
    "🤝 Scambi tra Proprietà", 
    "📋 Rose e Crediti"
])

# ==========================================
# 1. SCOUTING & DATABASE
# ==========================================
if menu == "🔍 Scouting & Database":
    st.header("🔍 Hub Scouting & Parametri Giocatori")
    st.markdown("Filtra e analizza i giocatori in base a parametri avanzati di scouting (FantaMedia, Potenziale, Titolarità).")

    df = st.session_state.giocatori_db

    # Filtri di ricerca
    col1, col2, col3 = st.columns(3)
    with col1:
        filtro_ruolo = st.multiselect("Filtra per Ruolo", options=df["Ruolo"].unique(), default=df["Ruolo"].unique())
    with col2:
        min_fm = st.slider("FantaMedia Minima", 4.0, 10.0, 5.0, 0.1)
    with col3:
        search_nome = st.text_input("Cerca per Nome Giocatore")

    # Applicazione filtri
    df_filtrato = df[
        (df["Ruolo"].isin(filtro_ruolo)) & 
        (df["FantaMedia"] >= min_fm)
    ]
    if search_nome:
        df_filtrato = df_filtrato[df_filtrato["Nome"].str.contains(search_nome, case=False, na=False)]

    st.subheader(f"Risultati Scouting ({len(df_filtrato)} giocatori trovati)")
    st.dataframe(df_filtrato, use_container_width=True)

    with st.expander("➕ Aggiungi Nuovo Giocatore al Database di Scouting"):
        with st.form("form_nuovo_giocatore"):
            c1, c2, c3 = st.columns(3)
            with c1:
                n_nome = st.text_input("Nome Giocatore")
                n_ruolo = st.selectbox("Ruolo", ["P", "D", "C", "A"])
            with c2:
                n_squadra = st.text_input("Squadra di Serie A")
                n_quot = st.number_input("Quotazione Iniziale / Valore", min_value=1, value=10)
            with c3:
                n_fm = st.number_input("FantaMedia Prevista", min_value=4.0, max_value=10.0, value=6.0, step=0.1)
                n_pot = st.slider("Potenziale (1-5)", 1, 5, 3)
                n_tit = st.slider("Titolarità (1-5)", 1, 5, 3)
            
            submit_giocatore = st.form_submit_button("Inserisci nel Database")
            if submit_giocatore and n_nome:
                nuova_riga = pd.DataFrame([{
                    "Nome": n_nome, "Ruolo": n_ruolo, "Squadra_SerieA": n_squadra,
                    "Quotazione": n_quot, "FantaMedia": n_fm, "Potenziale": n_pot, "Titolarita": n_tit
                }])
                st.session_state.giocatori_db = pd.concat([st.session_state.giocatori_db, nuova_riga], ignore_index=True)
                st.success(f"Giocatore {n_nome} aggiunto correttamente al database!")
                st.rerun()

# ==========================================
# 2. MERCATO (ACQUISTI E VENDITE)
# ==========================================
elif menu == "🛒 Mercato (Acquisti/Vendite)":
    st.header("🛒 Gestione Mercato: Acquisti e Svincoli")
    
    tab_acq, tab_vend = st.tabs(["📥 Acquista da Lista Svincolati", "📤 Vendi a Prezzo Personalizzato"])

    # --- ACQUISTI ---
    with tab_acq:
        st.subheader("Acquista un giocatore svincolato")
        squadra_selezionata = st.selectbox("Seleziona la tua Squadra", list(st.session_state.squadre.keys()), key="mercato_sq")
        crediti_disponibili = st.session_state.squadre[squadra_selezionata]["crediti"]
        st.info(f"Crediti residui per {squadra_selezionata}: **{crediti_disponibili} crediti**")

        # Trova giocatori non presenti in nessuna rosa
        giocatori_in_rosa = []
        for sq_data in st.session_state.squadre.values():
            for g in sq_data["rosa"]:
                giocatori_in_rosa.append(g["Nome"])
        
        db_g = st.session_state.giocatori_db
        svincolati = db_g[~db_g["Nome"].isin(giocatori_in_rosa)]

        if len(svincolati) > 0:
            giocatore_scelto = st.selectbox("Seleziona Giocatore Svincolato", svincolati["Nome"].values)
            info_g = svincolati[svincolati["Nome"] == giocatore_scelto].iloc[0]
            
            prezzo_consigliato = int(info_g["Quotazione"])
            st.write(f"Ruolo: **{info_g['Ruolo']}** | Squadra: **{info_g['Squadra_SerieA']}** | Quotazione di listino: **{prezzo_consigliato}**")

            prezzo_acquisto = st.number_input("Prezzo di Acquisto effettivo (crediti)", min_value=1, max_value=max(1, crediti_disponibili), value=prezzo_consigliato)

            if st.button("Conferma Acquisto"):
                if crediti_disponibili >= prezzo_acquisto:
                    st.session_state.squadre[squadra_selezionata]["crediti"] -= prezzo_acquisto
                    st.session_state.squadre[squadra_selezionata]["rosa"].append({
                        "Nome": giocatore_scelto,
                        "Ruolo": info_g["Ruolo"],
                        "Costo_Acquisto": prezzo_acquisto
                    })
                    st.success(f"Acquisto completato! {giocatore_scelto} è ora in rosa a {squadra_selezionata}.")
                    st.rerun()
                else:
                    st.error("Crediti insufficienti per completare l'acquisto!")
        else:
            st.warning("Non ci sono giocatori svincolati disponibili.")

    # --- VENDITE / SVINCOLI ---
    with tab_vend:
        st.subheader("Vendi o Svincola un giocatore della tua rosa")
        sq_vendi = st.selectbox("Seleziona la tua Squadra", list(st.session_state.squadre.keys()), key="vendi_sq")
        rosa_sq = st.session_state.squadre[sq_vendi]["rosa"]

        if len(rosa_sq) > 0:
            nomi_rosa = [g["Nome"] for g in rosa_sq]
            giocatore_da_vendere = st.selectbox("Seleziona il giocatore da cedere", nomi_rosa)
            
            # Trova costo iniziale o precedente
            g_obj = next(item for item in rosa_sq if item["Nome"] == giocatore_da_vendere)
            prezzo_base = g_obj.get("Costo_Acquisto", 10)

            prezzo_vendita = st.number_input("Prezzo di vendita / rimborso scelto (crediti)", min_value=0, value=prezzo_base)

            if st.button("Conferma Vendita / Svincolo"):
                # Rimuovi dalla rosa
                st.session_state.squadre[sq_vendi]["rosa"] = [g for g in rosa_sq if g["Nome"] != giocatore_da_vendere]
                # Aggiungi crediti
                st.session_state.squadre[sq_vendi]["crediti"] += prezzo_vendita
                st.success(f"Cessione avvenuta con successo! Incassati {prezzo_vendita} crediti.")
                st.rerun()
        else:
            st.info("La rosa selezionata è vuota.")

# ==========================================
# 3. SCAMBI TRA PROPRIETARI
# ==========================================
elif menu == "🤝 Scambi tra Proprietà":
    st.header("🤝 Negoziazione Scambi & Prestiti")
    st.markdown("Gestisci scambi diretti di giocatori tra proprietari, con l'aggiunta opzionale di conguagli in denaro o formule di prestito.")

    c_off, c_ricev = st.columns(2)

    with c_off:
        st.subheader("Squadra 1 (Mittente)")
        sq1 = st.selectbox("Seleziona Squadra 1", list(st.session_state.squadre.keys()), key="scambio_sq1")
        rosa_sq1 = st.session_state.squadre[sq1]["rosa"]
        giocatori_sq1_scelti = st.multiselect("Giocatori ceduti da Squadra 1", [g["Nome"] for g in rosa_sq1], key="g_sq1")
        denaro_sq1 = st.number_input(f"Crediti offerti da {sq1} (Conguaglio)", min_value=0, max_value=st.session_state.squadre[sq1]["crediti"], value=0, key="d_sq1")

    with c_ricev:
        st.subheader("Squadra 2 (Ricevente)")
        # Escludi la squadra 1 dalla scelta
        altre_squadre = [s for s in st.session_state.squadre.keys() if s != sq1]
        if len(altre_squadre) > 0:
            sq2 = st.selectbox("Seleziona Squadra 2", altre_squadre, key="scambio_sq2")
            rosa_sq2 = st.session_state.squadre[sq2]["rosa"]
            giocatori_sq2_scelti = st.multiselect("Giocatori ceduti da Squadra 2", [g["Nome"] for g in rosa_sq2], key="g_sq2")
            denaro_sq2 = st.number_input(f"Crediti offerti da {sq2} (Conguaglio)", min_value=0, max_value=st.session_state.squadre[sq2]["crediti"], value=0, key="d_sq2")
        else:
            sq2 = None
            giocatori_sq2_scelti = []
            denaro_sq2 = 0

    st.markdown("---")
    tipo_operazione = st.radio("Tipo di operazione", ["Scambio Definitivo", "Prestito con Diritto/Obbligo"])

    if st.button("Finalizza Scambio / Trattativa", type="primary"):
        if not sq2:
            st.error("Seleziona una seconda squadra valida.")
        elif len(giocatori_sq1_scelti) == 0 and len(giocatori_sq2_scelti) == 0 and denaro_sq1 == 0 and denaro_sq2 == 0:
            st.warning("Seleziona almeno un giocatore o un importo in denaro per effettuare lo scambio.")
        else:
            # Verifica crediti
            if st.session_state.squadre[sq1]["crediti"] < denaro_sq1:
                st.error(f"{sq1} non ha abbastanza crediti per il conguaglio.")
            elif st.session_state.squadre[sq2]["crediti"] < denaro_sq2:
                st.error(f"{sq2} non ha abbastanza crediti per il conguaglio.")
            else:
                # Esegui movimento crediti
                st.session_state.squadre[sq1]["crediti"] -= denaro_sq1
                st.session_state.squadre[sq1]["crediti"] += denaro_sq2
                
                st.session_state.squadre[sq2]["crediti"] -= denaro_sq2
                st.session_state.squadre[sq2]["crediti"] += denaro_sq1

                # Estrai oggetti giocatori da Sq1 e sposta in Sq2
                oggetti_sq1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] in giocatori_sq1_scelti]
                st.session_state.squadre[sq1]["rosa"] = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] not in giocatori_sq1_scelti]
                
                # Estrai oggetti giocatori da Sq2 e sposta in Sq1
                oggetti_sq2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] in giocatori_sq2_scelti]
                st.session_state.squadre[sq2]["rosa"] = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] not in giocatori_sq2_scelti]

                if tipo_operazione == "Scambio Definitivo":
                    st.session_state.squadre[sq1]["rosa"].extend(oggetti_sq2)
                    st.session_state.squadre[sq2]["rosa"].extend(oggetti_sq1)
                    st.success(f"🎉 Scambio definitivo completato con successo tra {sq1} e {sq2}!")
                else:
                    # Gestione prestito (aggiunge un tag nel nome o note)
                    for g in oggetti_sq2:
                        g_prestito = g.copy()
                        g_prestito["Nome"] = f"{g_prestito['Nome']} (in prestito da {sq2})"
                        st.session_state.squadre[sq1]["rosa"].append(g_prestito)
                    for g in oggetti_sq1:
                        g_prestito = g.copy()
                        g_prestito["Nome"] = f"{g_prestito['Nome']} (in prestito da {sq1})"
                        st.session_state.squadre[sq2]["rosa"].append(g_prestito)
                    st.success(f"🤝 Prestito registrato con successo tra {sq1} e {sq2}!")
                
                st.rerun()

# ==========================================
# 4. ROSE E CREDITI
# ==========================================
elif menu == "📋 Rose e Crediti":
    st.header("📋 Riepilogo Rose e Situazione Finanziaria")

    for nome_sq, dati in st.session_state.squadre.items():
        with st.container():
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(f"🛡️ {nome_sq}")
            with col_b:
                st.metric("Crediti Residui", f"{dati['crediti']} 🪙")
            
            rosa_df = pd.DataFrame(dati["rosa"])
            if not rosa_df.empty:
                st.dataframe(rosa_df, use_container_width=True)
            else:
                st.info("La rosa è attualmente vuota.")
            st.markdown("---")