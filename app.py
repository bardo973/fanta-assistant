import streamlit as st
import pandas as pd

st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

# --- LISTA DELLE 10 SQUADRE UFFICIALI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

# --- INIZIALIZZAZIONE SICURA DELLO STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state or not isinstance(st.session_state.squadre, dict):
    st.session_state.squadre = {}

for sq in NOMI_SQUADRE:
    if sq not in st.session_state.squadre:
        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}

# Rosa precaricata di esempio per PECU (se vuota)
if len(st.session_state.squadre["PECU"]["rosa"]) == 0:
    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Costo_Acquisto": 14},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Costo_Acquisto": 8},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 6, "FantaMedia": 6.1, "Costo_Acquisto": 6},
        {"Nome": "Lucumì", "Ruolo": "D", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 6},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Costo_Acquisto": 10},
        {"Nome": "Biraghi", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 1},
        {"Nome": "Ranieri L.", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 6},
        {"Nome": "Maripan", "Ruolo": "D", "Squadra_SerieA": "Torino", "Quotazione": 9, "FantaMedia": 6.2, "Costo_Acquisto": 9},
        {"Nome": "Mina", "Ruolo": "D", "Squadra_SerieA": "Cagliari", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 7},
        {"Nome": "Juan Jesus", "Ruolo": "D", "Squadra_SerieA": "Napoli", "Quotazione": 6, "FantaMedia": 5.9, "Costo_Acquisto": 4},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Costo_Acquisto": 9},
        {"Nome": "Aebischer", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 7},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 12, "FantaMedia": 6.5, "Costo_Acquisto": 13},
        {"Nome": "Freuler", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.3, "Costo_Acquisto": 6},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5, "Costo_Acquisto": 13},
        {"Nome": "Jashari", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 5},
        {"Nome": "De Roon", "Ruolo": "C", "Squadra_SerieA": "Atalanta", "Quotazione": 10, "FantaMedia": 6.4, "Costo_Acquisto": 9},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 14, "FantaMedia": 6.7, "Costo_Acquisto": 13},
        {"Nome": "Mandragora", "Ruolo": "C", "Squadra_SerieA": "Fiorentina", "Quotazione": 11, "FantaMedia": 6.3, "Costo_Acquisto": 18},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 15, "FantaMedia": 6.9, "Costo_Acquisto": 18},
        {"Nome": "Buksa", "Ruolo": "A", "Squadra_SerieA": "Udinese", "Quotazione": 9, "FantaMedia": 6.5, "Costo_Acquisto": 7},
        {"Nome": "Dallinga", "Ruolo": "A", "Squadra_SerieA": "Bologna", "Quotazione": 12, "FantaMedia": 6.6, "Costo_Acquisto": 7},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Atalanta", "Quotazione": 13, "FantaMedia": 6.8, "Costo_Acquisto": 11},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 25, "FantaMedia": 7.8, "Costo_Acquisto": 27},
        {"Nome": "Camarda", "Ruolo": "A", "Squadra_SerieA": "Milan", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 3},
        {"Nome": "Meister", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 7, "FantaMedia": 6.0, "Costo_Acquisto": 6}
    ]

if 'giocatori_db' not in st.session_state:
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

# --- BARRA LATERALE: GESTIONE FILE E NAVIGAZIONE ---
st.sidebar.title("⚽ Fanta Manager Hub")

with st.sidebar.expander("📁 Importa Listone / Quotazioni"):
    st.markdown("Carica il file ufficiale di Fantagazzetta/FantaMaster (CSV o Excel).")
    listone_file = st.file_uploader("File Listone", type=["csv", "xlsx"], key="upload_listone")
    
    if listone_file is not None:
        try:
            if listone_file.name.endswith('.csv'):
                df_load = pd.read_csv(listone_file)
            else:
                df_load = pd.read_excel(listone_file)
            
            col_mappa = {}
            for col in df_load.columns:
                c_low = str(col).lower().strip()
                if 'nome' in c_low or 'giocatore' in c_low:
                    col_mappa[col] = 'Nome'
                elif c_low in ['r', 'ruolo']:
                    col_mappa[col] = 'Ruolo'
                elif 'squadra' in c_low or 'team' in c_low:
                    col_mappa[col] = 'Squadra_SerieA'
                elif 'quot' in c_low or 'valore' in c_low or 'fc' in c_low or 'qt' in c_low:
                    col_mappa[col] = 'Quotazione'
                elif 'fm' in c_low or 'fantamedia' in c_low or 'media' in c_low:
                    col_mappa[col] = 'FantaMedia'
                    
            df_load = df_load.rename(columns=col_mappa)
            
            if 'Nome' in df_load.columns:
                if 'Ruolo' not in df_load.columns: df_load['Ruolo'] = 'C'
                if 'Squadra_SerieA' not in df_load.columns: df_load['Squadra_SerieA'] = 'N/D'
                if 'Quotazione' not in df_load.columns: df_load['Quotazione'] = 10
                if 'FantaMedia' not in df_load.columns: df_load['FantaMedia'] = 6.0
                
                df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                df_load['FantaMedia'] = pd.to_numeric(df_load['FantaMedia'].astype(str).str.replace(',', '.'), errors='coerce').fillna(6.0)
                
                if 'Potenziale' not in df_load.columns: df_load['Potenziale'] = 3
                if 'Titolarita' not in df_load.columns: df_load['Titolarita'] = 3
                
                st.session_state.giocatori_db = df_load[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Potenziale', 'Titolarita']]
                st.sidebar.success("Listone importato con successo!")
            else:
                st.sidebar.error("Colonna 'Nome' non trovata nel file.")
        except Exception as e:
            st.sidebar.error(f"Errore nella lettura: {e}")

menu = st.sidebar.selectbox("Navigazione", [
    "🔍 Scouting & Database", 
    "🛒 Mercato (Acquisti/Vendite)", 
    "🤝 Scambi tra Proprietà", 
    "📋 Rose e Crediti (10 Squadre)"
])

# ==========================================
# 1. SCOUTING & DATABASE
# ==========================================
if menu == "🔍 Scouting & Database":
    st.header("🔍 Hub Scouting, Quotazioni & FantaMedie")
    df = st.session_state.giocatori_db

    col1, col2, col3 = st.columns(3)
    with col1:
        ruoli_disponibili = df["Ruolo"].unique() if "Ruolo" in df.columns else ["P", "D", "C", "A"]
        filtro_ruolo = st.multiselect("Filtra per Ruolo", options=ruoli_disponibili, default=ruoli_disponibili)
    with col2:
        min_fm = st.slider("FantaMedia Minima", 4.0, 10.0, 5.0, 0.1)
    with col3:
        search_nome = st.text_input("Cerca per Nome Giocatore")

    df_filtrato = df[
        (df["Ruolo"].isin(filtro_ruolo)) & 
        (df["FantaMedia"] >= min_fm)
    ]
    if search_nome:
        df_filtrato = df_filtrato[df_filtrato["Nome"].str.contains(search_nome, case=False, na=False)]

    st.subheader(f"Risultati Scouting ({len(df_filtrato)} giocatori trovati)")
    st.dataframe(df_filtrato, use_container_width=True)

# ==========================================
# 2. MERCATO (ACQUISTI E VENDITE)
# ==========================================
elif menu == "🛒 Mercato (Acquisti/Vendite)":
    st.header("🛒 Gestione Mercato: Acquisti e Svincoli")
    
    tab_acq, tab_vend = st.tabs(["📥 Acquista da Svincolati", "📤 Vendi / Svincola"])

    with tab_acq:
        st.subheader("Acquista un giocatore svincolato")
        squadra_selezionata = st.selectbox("Seleziona la tua Squadra", NOMI_SQUADRE, key="mercato_sq")
        crediti_disponibili = st.session_state.squadre[squadra_selezionata]["crediti"]
        st.info(f"Crediti residui per **{squadra_selezionata}**: **{crediti_disponibili} crediti**")

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
            st.write(f"Ruolo: **{info_g['Ruolo']}** | Squadra Serie A: **{info_g['Squadra_SerieA']}** | Quotazione: **{prezzo_consigliato}** | FantaMedia: **{info_g['FantaMedia']}**")

            prezzo_acquisto = st.number_input("Prezzo di Acquisto effettivo (crediti)", min_value=1, max_value=max(1, crediti_disponibili), value=prezzo_consigliato, key="input_prezzo_acq")

            if st.button("Conferma Acquisto"):
                if crediti_disponibili >= prezzo_acquisto:
                    st.session_state.squadre[squadra_selezionata]["crediti"] -= prezzo_acquisto
                    st.session_state.squadre[squadra_selezionata]["rosa"].append({
                        "Nome": giocatore_scelto,
                        "Ruolo": info_g["Ruolo"],
                        "Squadra_SerieA": info_g["Squadra_SerieA"],
                        "Quotazione": info_g["Quotazione"],
                        "FantaMedia": info_g["FantaMedia"],
                        "Costo_Acquisto": prezzo_acquisto
                    })
                    st.success(f"Acquisto completato! {giocatore_scelto} è ora in rosa a {squadra_selezionata}.")
                    st.rerun()
                else:
                    st.error("Crediti insufficienti per completare l'acquisto!")
        else:
            st.warning("Non ci sono giocatori svincolati disponibili.")

    with tab_vend:
        st.subheader("Vendi o Svincola un giocatore della tua rosa")
        sq_vendi = st.selectbox("Seleziona la tua Squadra", NOMI_SQUADRE, key="vendi_sq")
        rosa_sq = st.session_state.squadre[sq_vendi]["rosa"]

        if len(rosa_sq) > 0:
            nomi_rosa = [g["Nome"] for g in rosa_sq]
            giocatore_da_vendere = st.selectbox("Seleziona il giocatore da cedere", nomi_rosa, key="sel_vendi_giocatore")
            
            g_obj = next(item for item in rosa_sq if item["Nome"] == giocatore_da_vendere)
            prezzo_base = g_obj.get("Costo_Acquisto", 10)

            prezzo_vendita = st.number_input("Prezzo di vendita / rimborso scelto (crediti)", min_value=0, value=prezzo_base, key="input_prezzo_vend")

            if st.button("Conferma Vendita / Svincolo"):
                st.session_state.squadre[sq_vendi]["rosa"] = [g for g in rosa_sq if g["Nome"] != giocatore_da_vendere]
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
    c_off, c_ricev = st.columns(2)

    with c_off:
        st.subheader("Squadra 1 (Mittente)")
        sq1 = st.selectbox("Seleziona Squadra 1", NOMI_SQUADRE, key="scambio_sq1")
        rosa_sq1 = st.session_state.squadre[sq1]["rosa"]
        giocatori_sq1_scelti = st.multiselect("Giocatori ceduti da Squadra 1", [g["Nome"] for g in rosa_sq1], key="g_sq1")
        denaro_sq1 = st.number_input(f"Crediti offerti da {sq1} (Conguaglio)", min_value=0, max_value=st.session_state.squadre[sq1]["crediti"], value=0, key="d_sq1")

    with c_ricev:
        st.subheader("Squadra 2 (Ricevente)")
        altre_squadre = [s for s in NOMI_SQUADRE if s != sq1]
        sq2 = st.selectbox("Seleziona Squadra 2", altre_squadre, key="scambio_sq2")
        rosa_sq2 = st.session_state.squadre[sq2]["rosa"]
        giocatori_sq2_scelti = st.multiselect("Giocatori ceduti da Squadra 2", [g["Nome"] for g in rosa_sq2], key="g_sq2")
        denaro_sq2 = st.number_input(f"Crediti offerti da {sq2} (Conguaglio)", min_value=0, max_value=st.session_state.squadre[sq2]["crediti"], value=0, key="d_sq2")

    st.markdown("---")
    tipo_operazione = st.radio("Tipo di operazione", ["Scambio Definitivo", "Prestito con Diritto/Obbligo"])

    if st.button("Finalizza Scambio / Trattativa", type="primary"):
        if len(giocatori_sq1_scelti) == 0 and len(giocatori_sq2_scelti) == 0 and denaro_sq1 == 0 and denaro_sq2 == 0:
            st.warning("Seleziona almeno un giocatore o un importo in denaro.")
        else:
            if st.session_state.squadre[sq1]["crediti"] < denaro_sq1:
                st.error(f"{sq1} non ha abbastanza crediti.")
            elif st.session_state.squadre[sq2]["crediti"] < denaro_sq2:
                st.error(f"{sq2} non ha abbastanza crediti.")
            else:
                st.session_state.squadre[sq1]["crediti"] = st.session_state.squadre[sq1]["crediti"] - denaro_sq1 + denaro_sq2
                st.session_state.squadre[sq2]["crediti"] = st.session_state.squadre[sq2]["crediti"] - denaro_sq2 + denaro_sq1

                oggetti_sq1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] in giocatori_sq1_scelti]
                st.session_state.squadre[sq1]["rosa"] = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] not in giocatori_sq1_scelti]
                
                oggetti_sq2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] in giocatori_sq2_scelti]
                st.session_state.squadre[sq2]["rosa"] = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] not in giocatori_sq2_scelti]

                if tipo_operazione == "Scambio Definitivo":
                    st.session_state.squadre[sq1]["rosa"].extend(oggetti_sq2)
                    st.session_state.squadre[sq2]["rosa"].extend(oggetti_sq1)
                    st.success(f"🎉 Scambio definitivo completato con successo tra {sq1} e {sq2}!")
                else:
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
# 4. ROSE E CREDITI (10 SQUADRE)
# ==========================================
elif menu == "📋 Rose e Crediti (10 Squadre)":
    st.header("📋 Riepilogo Rose, Quotazioni, FantaMedie e Crediti")

    tabs_squadre = st.tabs(NOMI_SQUADRE)

    for i, nome_sq in enumerate(NOMI_SQUADRE):
        with tabs_squadre[i]:
            dati = st.session_state.squadre[nome_sq]
            col_a, col_b = st.columns([3, 1])
            with col_a:
                st.subheader(f"🛡️ {nome_sq}")
            with col_b:
                st.metric("Crediti Residui", f"{dati['crediti']} 🪙")
            
            rosa_df = pd.DataFrame(dati["rosa"])
            if not rosa_df.empty:
                st.dataframe(rosa_df, use_container_width=True)
                st.markdown(f"Totale giocatori in rosa: **{len(rosa_df)}**")
            else:
                st.info("La rosa è attualmente vuota.")