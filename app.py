                # --- CONTINUAZIONE IMPORTAZIONE LISTONE ---
                df_load['FantaMedia'] = pd.to_numeric(fm_serie, errors='coerce').fillna(6.0).astype(float)
                
                if 'Potenziale' not in df_load.columns: df_load['Potenziale'] = 3
                if 'Titolarita' not in df_load.columns: df_load['Titolarita'] = 3
                
                campi_finali = ['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Potenziale', 'Titolarita']
                st.session_state.giocatori_db = df_load[campi_finali].drop_duplicates(subset=['Nome']).reset_index(drop=True)
                st.sidebar.success(f"✅ Caricati {len(st.session_state.giocatori_db)} giocatori!")
            else:
                st.sidebar.error("❌ Colonna 'Nome' o 'Giocatore' non trovata nel file.")
        except Exception as e:
            st.sidebar.error(f"❌ Errore nel caricamento: {e}")

# Navigazione principale
menu = st.sidebar.radio("🧭 Seleziona Menu", ["🔍 Scouting Hub", "🔨 Mercato & Asta", "📋 Gestione Rose", "📈 Tabellone Generale"])

# --- FUNZIONI DI UTILITÀ ---
def calcola_spazi_ruolo(rosa, ruolo, limite):
    """Calcola quanti slot liberi ci sono per un determinato ruolo."""
    conteggio = sum(1 for j in rosa if j['Ruolo'] == ruolo)
    return max(0, limite - conteggio)

# --- 1. SCOUTING HUB ---
if menu == "🔍 Scouting Hub":
    st.title("🔍 Scouting Hub & Analisi Giocatori")
    
    # Filtri di ricerca
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        cerca_nome = st.text_input("Cerca Giocatore", "")
    with col2:
        filtro_ruolo = st.multiselect("Ruolo", ["P", "D", "C", "A"], default=["P", "D", "C", "A"])
    with col3:
        filtro_squadra = st.multiselect("Squadra Serie A", sorted(st.session_state.giocatori_db["Squadra_SerieA"].unique().tolist()))
    with col4:
        min_fm = st.slider("FantaMedia Minima", 4.0, 10.0, 4.0, step=0.1)

    # Filtraggio del DataFrame dello stato
    df_filtrato = st.session_state.giocatori_db.copy()
    if cerca_nome:
        df_filtrato = df_filtrato[df_filtrato['Nome'].str.contains(cerca_nome, case=False, na=False)]
    if filtro_ruolo:
        df_filtrato = df_filtrato[df_filtrato['Ruolo'].isin(filtro_ruolo)]
    if filtro_squadra:
        df_filtrato = df_filtrato[df_filtrato['Squadra_SerieA'].isin(filtro_squadra)]
    df_filtrato = df_filtrato[df_filtrato['FantaMedia'] >= min_fm]

    st.dataframe(df_filtrato, use_container_width=True, hide_index=True)

    # Watchlist personale
    st.subheader("📌 La tua Watchlist di Obiettivi")
    col_w1, col_w2 = st.columns([2, 1])
    with col_w1:
        player_to_watch = st.selectbox("Seleziona un giocatore da seguire", st.session_state.giocatori_db["Nome"].unique())
    with col_w2:
        if st.button("➕ Aggiungi a Watchlist", use_container_width=True):
            if player_to_watch not in st.session_state.watchlist:
                st.session_state.watchlist.append(player_to_watch)
                st.toast(f"{player_to_watch} aggiunto!")

    if st.session_state.watchlist:
        df_watch = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].isin(st.session_state.watchlist)]
        st.table(df_watch)
        if st.button("🗑️ Svuota Watchlist"):
            st.session_state.watchlist = []
            st.rerun()

# --- 2. MERCATO & ASTA ---
elif menu == "🔨 Mercato & Asta":
    st.title("🔨 Pannello Gestione Asta dal Vivo")
    
    col_a, col_b = st.columns([1, 2])
    
    with col_a:
        st.subheader("Registra Acquisto")
        acquirente = st.selectbox("Squadra Acquirente", NOMI_SQUADRE)
        giocatore_scelto = st.selectbox("Giocatore", st.session_state.giocatori_db["Nome"].unique())
        prezzo_acquisto = st.number_input("Prezzo d'Asta (Crediti)", min_value=1, max_value=500, value=1)
        
        # Recupero info giocatore scelto
        info_g = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"] == giocatore_scelto].iloc[0]
        
        # Limiti standard rosa: P:3, D:8, C:8, A:6
        limiti = {"P": 3, "D": 8, "C": 8, "A": 6}
        slot_liberi = calcola_spazi_ruolo(st.session_state.squadre[acquirente]["rosa"], info_g["Ruolo"], limiti[info_g["Ruolo"]])
        crediti_attuali = st.session_state.squadre[acquirente]["crediti"]

        if st.button("🔨 Conferma Assegnazione", use_container_width=True):
            if crediti_attuali < prezzo_acquisto:
                st.error(f"❌ {acquirente} non ha abbastanza crediti ({crediti_attuali} rimasti).")
            elif slot_liberi <= 0:
                st.error(f"❌ Spazio esaurito per il ruolo {info_g['Ruolo']} nella rosa di {acquirente}.")
            else:
                # Modifica dati interni di sessione
                st.session_state.squadre[acquirente]["crediti"] -= prezzo_acquisto
                nuovo_membro = {
                    "Nome": info_g["Nome"],
                    "Ruolo": info_g["Ruolo"],
                    "Squadra_SerieA": info_g["Squadra_SerieA"],
                    "Quotazione": info_g["Quotazione"],
                    "FantaMedia": info_g["FantaMedia"],
                    "Costo_Acquisto": prezzo_acquisto
                }
                st.session_state.squadre[acquirente]["rosa"].append(nuovo_membro)
                
                # Log storico mercati
                st.session_state.storico_mercato.insert(0, {
                    "Ora": datetime.now().strftime("%H:%M:%S"),
                    "Squadra Fanta": acquirente,
                    "Giocatore": info_g["Nome"],
                    "Ruolo": info_g["Ruolo"],
                    "Costo": prezzo_acquisto
                })
                st.success(f"⚽ {info_g['Nome']} assegnato a {acquirente} per {prezzo_acquisto} crediti!")
                st.rerun()

    with col_b:
        st.subheader("📋 Storico Recente dell'Asta")
        if st.session_state.storico_mercato:
            st.dataframe(pd.DataFrame(st.session_state.storico_mercato), use_container_width=True, hide_index=True)
        else:
            st.info("Nessun giocatore acquistato in questa sessione.")

# --- 3. GESTIONE ROSE ---
elif menu == "📋 Gestione Rose":
    st.title("📋 Gestione Rose e Svincoli")
    
    squadra_sel = st.selectbox("Seleziona la Squadra da visualizzare/modificare", NOMI_SQUADRE)
    dati_sq = st.session_state.squadre[squadra_sel]
    
    col_info1, col_info2 = st.columns(2)
    col_info1.metric("💰 Crediti Rimanenti", f"{dati_sq['crediti']} / 500")
    col_info2.metric("🏃 Numero Giocatori in Rosa", f"{len(dati_sq['rosa'])} / 25")
    
    if dati_sq["rosa"]:
        df_rosa = pd.DataFrame(dati_sq["rosa"])
        st.dataframe(df_rosa, use_container_width=True, hide_index=True)
        
        # Pannello svincoli
        st.subheader("❌ Svincola un Giocatore")
        giocatore_da_svincolare = st.selectbox("Seleziona giocatore da eliminare", [g["Nome"] for g in dati_sq["rosa"]])
        recupero_crediti = st.radio("Politica di recupero crediti:", ["Intero (Prezzo d'acquisto)", "Metà (Arrotondato per difetto)", "Fisso (1 Credito)"])
        
        if st.button("⚠️ Conferma Svincolo", type="primary"):
            g_target = next(item for item in dati_sq["rosa"] if item["Nome"] == giocatore_da_svincolare)
            
            # Calcolo rimborso crediti
            if recupero_crediti == "Intero (Prezzo d'acquisto)":
                rimborso = g_target["Costo_Acquisto"]
            elif recupero_crediti == "Metà (Arrotondato per difetto)":
                rimborso = g_target["Costo_Acquisto"] // 2
            else:
                rimborso = 1
                
            dati_sq["crediti"] += rimborso
            dati_sq["rosa"].remove(g_target)
            st.success(f"Svincolato {giocatore_da_svincolare}. Recuperati {rimborso} crediti.")
            st.rerun()
    else:
        st.warning("Nessun giocatore presente in questa rosa.")

# --- 4. TABELLONE GENERALE ---
elif menu == "📈 Tabellone Generale":
    st.title("📈 Riepilogo Generale della Lega")
    
    dati_tabellone = []
    for sq, info in st.session_state.squadre.items():
        rosa = info["rosa"]
        dati_tabellone.append({
            "Fanta Squadra": sq,
            "Crediti Residui": info["crediti"],
            "Tot Giocatori": len(rosa),
            "P": sum(1 for j in rosa if j['Ruolo'] == 'P'),
            "D": sum(1 for j in rosa if j['Ruolo'] == 'D'),
            "C": sum(1 for j in rosa if j['Ruolo'] == 'C'),
            "A": sum(1 for j in rosa if j['Ruolo'] == 'A')
        })
        
    df_tabellone = pd.DataFrame(dati_tabellone)
    st.dataframe(df_tabellone, use_container_width=True, hide_index=True)
    
    st.info("💡 Questo tabellone ti permette di tenere d'occhio le necessità dei tuoi avversari durante l'asta (es. chi ha bisogno urgente di attaccanti).")
