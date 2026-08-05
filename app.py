import io
import json
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT
# ---------------------------------------------------------
st.set_page_config(
    page_title="FantaLega Manager & Scouting Pro", layout="wide"
)

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500

# ---------------------------------------------------------
# 2. FUNZIONE DI SUPPORTO PER ACCENTI E CODIFICA
# ---------------------------------------------------------
def ripara_testo(testo):
    if not isinstance(testo, str):
        return str(testo)
    for enc_from, enc_to in [("latin1", "utf-8"), ("cp1252", "utf-8")]:
        try:
            return testo.encode(enc_from).decode(enc_to)
        except Exception:
            continue
    return testo

# ---------------------------------------------------------
# 3. CARICAMENTO E GENERAZIONE DATI CON PARAMETRI DI RENDIMENTO
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_raw = None
    for enc in ["utf-8", "latin1", "cp1252"]:
        try:
            df_raw = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding=enc)
            break
        except Exception:
            continue

    if df_raw is None:
        df_raw = pd.DataFrame(columns=["Calciatore", "Squadra", "Ruolo", "Quotazione"])

    df = pd.DataFrame()
    df["Nome"] = (
        df_raw["Calciatore"].astype(str).str.strip().apply(ripara_testo)
        if "Calciatore" in df_raw.columns
        else "Sconosciuto"
    )
    df["Squadra"] = (
        df_raw["Squadra"].astype(str).str.strip().apply(ripara_testo)
        if "Squadra" in df_raw.columns
        else "N/D"
    )
    df["Ruolo"] = (
        df_raw["Ruolo"].astype(str).str.strip()
        if "Ruolo" in df_raw.columns
        else "C"
    )
    df["Quotazione"] = (
        pd.to_numeric(df_raw["Quotazione"], errors="coerce").fillna(1)
        if "Quotazione" in df_raw.columns
        else 1
    )

    possibili_colonne_prop = [
        "proprietario",
        "Proprietario_Iniziale",
        "Proprietario",
        "Unnamed: 5",
        "Squadra_Fantacalcio",
    ]
    colonna_trovata = next(
        (c for c in possibili_colonne_prop if c in df_raw.columns), None
    )

    if colonna_trovata:
        df["Proprietario_Iniziale"] = (
            df_raw[colonna_trovata].astype(str).str.strip().str.upper().apply(ripara_testo)
        )
        df["Proprietario_Iniziale"] = df["Proprietario_Iniziale"].apply(
            lambda x: (
                "LIBERO"
                if x in ["NAN", "NONE", "", "SVINCOLATO", "LIBERO", "#N/D", "#RIF!", "0"]
                or x.startswith("=")
                else x
            )
        )
    else:
        df["Proprietario_Iniziale"] = "LIBERO"

    df["Stato"] = df["Proprietario_Iniziale"]

    def assign_tier(quot):
        if quot >= 25:
            return "Top"
        elif quot >= 15:
            return "Semitop"
        elif quot >= 8:
            return "Titolare"
        else:
            return "Scommessa"

    df["Tier"] = df["Quotazione"].apply(assign_tier)

    # Generazione metriche di rendimento e presenze (> 45 minuti)
    def genera_metriche_scout(row):
        quot = row["Quotazione"]
        ruolo = row["Ruolo"]
        
        # Partite giocate totali (es. su 38) e partite con almeno 45 minuti
        if quot >= 25:
            partite_tot = np.random.randint(32, 37)
            part_almeno_45 = np.random.randint(30, partite_tot + 1)
        elif quot >= 15:
            partite_tot = np.random.randint(25, 34)
            part_almeno_45 = np.random.randint(22, partite_tot + 1)
        elif quot >= 8:
            partite_tot = np.random.randint(18, 28)
            part_almeno_45 = np.random.randint(15, partite_tot + 1)
        else:
            partite_tot = np.random.randint(5, 20)
            part_almeno_45 = np.random.randint(3, partite_tot + 1)

        # xG e xA
        if ruolo == "A":
            xg = round(max(0.1, quot * 0.035), 2)
            xa = round(max(0.05, quot * 0.015), 2)
        elif ruolo == "C":
            xg = round(max(0.05, quot * 0.02), 2)
            xa = round(max(0.08, quot * 0.025), 2)
        elif ruolo == "D":
            xg = round(max(0.02, quot * 0.01), 2)
            xa = round(max(0.03, quot * 0.015), 2)
        else:
            xg, xa = 0.0, 0.0

        return pd.Series([partite_tot, part_almeno_45, xg, xa])

    df[["Partite_Giocate", "Partite_Almeno_45min", "xG_90", "xA_90"]] = df.apply(genera_metriche_scout, axis=1)

    def stima_fantamedia(row):
        q = row["Quotazione"]
        r = row["Ruolo"]
        base = 6.00
        if r == "A":
            base += 0.35 + (q * 0.04)
        elif r == "C":
            base += 0.20 + (q * 0.03)
        elif r == "D":
            base += 0.10 + (q * 0.02)
        else:
            base = 5.50 + (q * 0.01)
        return round(min(base, 9.5), 2)

    df["FantaMedia_Stimata"] = df.apply(stima_fantamedia, axis=1)
    df["Status_Piazzati"] = df["Quotazione"].apply(lambda q: "Rigorista 🎯" if q >= 28 else ("Vice-Rigorista 👟" if q >= 18 else "No"))

    return df


if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data()

df = st.session_state.df_giocatori

lista_proprietari_csv = [p for p in df["Proprietario_Iniziale"].unique() if p not in ["LIBERO", "NAN", "NONE", ""]]
if not lista_proprietari_csv:
    lista_proprietari_csv = ["BARDO", "ROBY", "PECU", "SQUADRA_3", "SQUADRA_4"]

PARTECIPANTI_LEGA = sorted(lista_proprietari_csv)

if "rose_lega" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
if "extra_budget" not in st.session_state:
    st.session_state.extra_budget = {p: 0 for p in PARTECIPANTI_LEGA}
if "prestiti_lega" not in st.session_state:
    st.session_state.prestiti_lega = []

if "inizializzato" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
    for p in PARTECIPANTI_LEGA:
        sub_df = df[df["Proprietario_Iniziale"] == p]
        st.session_state.rose_lega[p] = [
            {
                "Nome": str(r["Nome"]),
                "Ruolo": str(r["Ruolo"]),
                "Squadra": str(r["Squadra"]),
                "Prezzo_Acquisto": int(r["Quotazione"]),
                "Scadenza": "Giugno 2030",
            }
            for _, r in sub_df.iterrows()
        ]
    st.session_state.inizializzato = True

for p in PARTECIPANTI_LEGA:
    if p not in st.session_state.rose_lega:
        st.session_state.rose_lega[p] = []
    if p not in st.session_state.extra_budget:
        st.session_state.extra_budget[p] = 0

df = st.session_state.df_giocatori

# ---------------------------------------------------------
# 4. SIDEBAR: GESTIONE ROSE, BACKUP E IMPORT FILE
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Manager")
allenatore_attivo = st.sidebar.selectbox("Gestisci per squadra:", PARTECIPANTI_LEGA, key="allenatore_sb")

budget_input = st.sidebar.number_input("Budget Iniziale Crediti", value=st.session_state.get("budget_iniziale", 500), step=10)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega.get(allenatore_attivo, [])
spesa_corrente = sum(item.get("Prezzo_Acquisto", 1) for item in rosa_corrente)
budget_rimanente = st.session_state.budget_iniziale + st.session_state.extra_budget.get(allenatore_attivo, 0) - spesa_corrente

st.sidebar.metric(f"Budget Rimanente ({allenatore_attivo})", f"{budget_rimanente} cr")

st.sidebar.divider()
st.sidebar.subheader("💾 Backup & Salvataggio")

stato_salva = {
    "budget_iniziale": st.session_state.budget_iniziale,
    "rose_lega": st.session_state.rose_lega,
    "extra_budget": st.session_state.extra_budget,
    "prestiti_lega": st.session_state.prestiti_lega,
    "stati_giocatori": df[["Nome", "Stato"]].set_index("Nome")["Stato"].to_dict()
}
st.sidebar.download_button("📥 Scarica Backup (JSON)", data=json.dumps(stato_salva, indent=4, ensure_ascii=False), file_name="fanta_backup.json", mime="application/json")

uploaded_json = st.sidebar.file_uploader("📂 Carica Backup (JSON)", type=["json"])
if uploaded_json is not None:
    try:
        loaded = json.load(uploaded_json)
        st.session_state.budget_iniziale = loaded.get("budget_iniziale", 500)
        st.session_state.rose_lega = loaded.get("rose_lega", {})
        st.session_state.extra_budget = loaded.get("extra_budget", {})
        st.session_state.prestiti_lega = loaded.get("prestiti_lega", [])
        stati_caricati = loaded.get("stati_giocatori", {})
        
        df_t = st.session_state.df_giocatori.copy()
        df_t["Stato"] = df_t["Nome"].map(stati_caricati).fillna("LIBERO")
        st.session_state.df_giocatori = df_t
        st.sidebar.success("✅ Backup caricato!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore caricamento: {e}")

# Importazione listone Excel / CSV / TXT
st.sidebar.divider()
st.sidebar.subheader("📊 Carica Listone / Rose")
uploaded_file = st.sidebar.file_uploader("Carica file (Excel, CSV, TXT)", type=["xlsx", "xls", "csv", "txt"])
if uploaded_file is not None:
    try:
        ext = uploaded_file.name.split('.')[-1].lower()
        if ext == 'txt':
            content = uploaded_file.read().decode('utf-8', errors='ignore')
            df_file = pd.read_csv(io.StringIO(content), sep=None, engine='python', dtype=str)
        elif ext in ['xlsx', 'xls']:
            df_file = pd.read_excel(uploaded_file, dtype=str)
        else:
            df_file = pd.read_csv(uploaded_file, dtype=str)

        df_file.columns = [str(c).strip().lower() for c in df_file.columns]
        col_nome = next((c for c in df_file.columns if any(k in c for k in ["calciatore", "giocatore", "nome"])), df_file.columns[0])
        
        new_rose = {}
        df_temp = st.session_state.df_giocatori.copy()
        df_temp["Stato"] = "LIBERO"
        master_dict = {str(r["Nome"]).strip().lower(): r for _, r in df_temp.iterrows()}

        for _, row in df_file.iterrows():
            nome_g = ripara_testo(str(row[col_nome]).strip())
            if not nome_g or nome_g.lower() in ["nan", "none", ""]:
                continue
            
            prop = "LIBERO"
            for col_p in ["proprietario", "squadra_fantacalcio"]:
                if col_p in df_file.columns:
                    val_p = ripara_testo(str(row[col_p]).strip().upper())
                    if val_p and val_p not in ["NAN", "NONE", "", "LIBERO", "SVINCOLATO", "0"]:
                        prop = val_p
                        if prop not in PARTECIPANTI_LEGA:
                            PARTECIPANTI_LEGA.append(prop)

            prezzo = 1
            for col_pr in ["quotazione", "prezzo", "valore"]:
                if col_pr in df_file.columns:
                    try:
                        prezzo = int(float(str(row[col_pr]).replace(',', '.')))
                    except:
                        pass

            nome_lower = nome_g.lower()
            if nome_lower in master_dict:
                info = master_dict[nome_lower]
                ruolo, squadra = info["Ruolo"], info["Squadra"]
            else:
                ruolo = "C"
                squadra = "N/D"

            if prop != "LIBERO":
                if prop not in new_rose:
                    new_rose[prop] = []
                new_rose[prop].append({
                    "Nome": nome_g, "Ruolo": ruolo, "Squadra": squadra, "Prezzo_Acquisto": prezzo, "Scadenza": "Giugno 2030"
                })
                idx_m = df_temp[df_temp["Nome"].str.strip().str.lower() == nome_lower].index
                if not idx_m.empty:
                    df_temp.at[idx_m[0], "Stato"] = prop

        st.session_state.rose_lega = new_rose
        st.session_state.df_giocatori = df_temp
        st.sidebar.success("✅ Listone caricato con successo!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore lettura file: {e}")

# ---------------------------------------------------------
# 5. CORPO PRINCIPALE: TABS DI GESTIONE
# ---------------------------------------------------------
tab_asta, tab_scout, tab_scambi, tab_prestiti, tab_rose = st.tabs([
    "🎯 Asta & Prezzi Consigliati",
    "🔍 Scouting & Rendimento",
    "🔄 Gestione Scambi",
    "🤝 Gestione Prestiti",
    "📋 Visualizza Rose"
])

# --- TAB 1: ASTA & PREZZI CONSIGLIATI ---
with tab_asta:
    st.header("🎯 Assistente Asta & Prezzi Consigliati")
    st.write("Seleziona un giocatore libero per visualizzare il **prezzo consigliato di acquisto** calcolato in base al budget residuo, ai posti liberi e al valore tattico.")

    giocatori_liberi = df[df["Stato"] == "LIBERO"]["Nome"].tolist()
    if giocatori_liberi:
        gioc_sel = st.selectbox("Seleziona Giocatore in Asta:", giocatori_liberi)
        g_info = df[df["Nome"] == gioc_sel].iloc[0]

        # Calcolo prezzo consigliato
        slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
        rosa_att = st.session_state.rose_lega.get(allenatore_attivo, [])
        slot_presi = {r: sum(1 for g in rosa_att if g["Ruolo"] == r) for r in slot_target}
        slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
        totale_liberi = sum(slot_liberi.values())

        riserva_minima = max(0, totale_liberi - 1)
        spendibile = max(0, budget_rimanente - riserva_minima)

        moltiplicatori_tier = {"Top": 0.45, "Semitop": 0.22, "Titolare": 0.08, "Scommessa": 0.03}
        prezzo_base = int(spendibile * moltiplicatori_tier.get(g_info["Tier"], 0.05))
        if g_info["Status_Piazzati"].startswith("Rigorista"):
            prezzo_base += 5
        if g_info["FantaMedia_Stimata"] >= 7.0:
            prezzo_base += 3

        prezzo_consigliato = max(1, prezzo_base)
        if slot_liberi.get(g_info["Ruolo"], 0) <= 0:
            prezzo_consigliato = 0 # Slot esauriti per quel ruolo

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Ruolo & Squadra", f"{g_info['Ruolo']} - {g_info['Squadra']}", f"Tier: {g_info['Tier']}")
        c2.metric("FantaMedia Stimata", f"{g_info['FantaMedia_Stimata']} FM")
        c3.metric("Rigorista", f"{g_info['Status_Piazzati']}")
        c4.metric("💰 Prezzo Consigliato", f"{prezzo_consigliato} cr")

        with st.form("form_acquisto_asta"):
            st.subheader("Registra Assegnazione")
            col_fa, col_fb = st.columns(2)
            with col_fa:
                prezzo_pagato = st.number_input("Prezzo di chiusura effettivo (crediti):", min_value=1, value=int(prezzo_consigliato))
            with col_fb:
                vincitore = st.selectbox("Assegna alla squadra:", PARTECIPANTI_LEGA, index=PARTECIPANTI_LEGA.index(allenatore_attivo) if allenatore_attivo in PARTECIPANTI_LEGA else 0)
            
            submit_acq = st.form_submit_button("Conferma Acquisto")
            if submit_acq:
                if vincitore not in st.session_state.rose_lega:
                    st.session_state.rose_lega[vincitore] = []
                st.session_state.rose_lega[vincitore].append({
                    "Nome": str(g_info["Nome"]),
                    "Ruolo": str(g_info["Ruolo"]),
                    "Squadra": str(g_info["Squadra"]),
                    "Prezzo_Acquisto": int(prezzo_pagato),
                    "Scadenza": "Giugno 2030"
                })
                idx_g = df[df["Nome"] == gioc_sel].index[0]
                st.session_state.df_giocatori.at[idx_g, "Stato"] = vincitore
                st.success(f"✅ {gioc_sel} assegnato a **{vincitore}** per {prezzo_pagato} crediti!")
                st.rerun()
    else:
        st.info("Tutti i giocatori sono stati assegnati!")

# --- TAB 2: SCOUTING & RENDIMENTO (>45 MIN) ---
with tab_scout:
    st.header("🔍 Scouting Giocatori Liberi")
    st.write("Filtra i giocatori liberi in base alle **partite giocate con almeno 45 minuti** e agli indicatori di rendimento (FantaMedia, xG, xA).")

    f_col1, f_col2, f_col3 = st.columns(3)
    with f_col1:
        ruolo_scout = st.selectbox("Ruolo:", ["Tutti", "P", "D", "C", "A"], key="scout_ruolo")
    with f_col2:
        min_part_45 = st.slider("Minimo partite con almeno 45 min:", 0, 38, 15, key="scout_min_45")
    with f_col3:
        solo_rig = st.checkbox("Solo rigoristi designati 🎯", key="scout_rig")

    df_sc = df[df["Stato"] == "LIBERO"].copy()
    if ruolo_scout != "Tutti":
        df_sc = df_sc[df_sc["Ruolo"] == ruolo_scout]
    df_sc = df_sc[df_sc["Partite_Almeno_45min"] >= min_part_45]
    if solo_rig:
        df_sc = df_sc[df_sc["Status_Piazzati"].str.startswith("Rigorista")]

    df_sc = df_sc.sort_values(by="FantaMedia_Stimata", ascending=False)

    st.dataframe(
        df_sc[[
            "Nome", "Squadra", "Ruolo", "Quotazione", "FantaMedia_Stimata", 
            "Partite_Giocate", "Partite_Almeno_45min", "xG_90", "xA_90", "Status_Piazzati"
        ]],
        use_container_width=True,
        hide_index=True
    )

# --- TAB 3: GESTIONE SCAMBI TRA SOCIETA ---
with tab_scambi:
    st.header("🔄 Gestione Scambi tra Società")
    st.write("Effettua scambi di giocatori tra due rose differenti, con eventuale conguaglio in crediti.")

    sc_col1, sc_col2 = st.columns(2)
    with sc_col1:
        squadra_1 = st.selectbox("Prima Squadra (Cede/Riceve):", PARTECIPANTI_LEGA, key="scambio_sq1")
    with sc_col2:
        squadra_2 = st.selectbox("Seconda Squadra (Cede/Riceve):", [p for p in PARTECIPANTI_LEGA if p != squadra_1], key="scambio_sq2")

    rosa_s1 = st.session_state.rose_lega.get(squadra_1, [])
    rosa_s2 = st.session_state.rose_lega.get(squadra_2, [])

    if rosa_s1 and rosa_s2:
        nomi_s1 = [g["Nome"] for g in rosa_s1]
        nomi_s2 = [g["Nome"] for g in rosa_s2]

        col_g1, col_g2 = st.columns(2)
        with col_g1:
            giocatori_da_s1 = st.multiselect(f"Giocatori da dare da **{squadra_1}** a **{squadra_2}**:", nomi_s1, key="scambio_sel_s1")
        with col_g2:
            giocatori_da_s2 = st.multiselect(f"Giocatori da dare da **{squadra_2}** a **{squadra_1}**:", nomi_s2, key="scambio_sel_s2")

        conguaglio = st.number_input("Conguaglio in crediti (positivo se paga Sq1, negativo se paga Sq2):", value=0, step=1)

        if st.button("🤝 Esegui Scambio Ufficiale"):
            if not giocatori_da_s1 and not giocatori_da_s2:
                st.warning("Seleziona almeno un giocatore da scambiare.")
            else:
                # Estrai oggetti giocatore
                obj_s1 = [g for g in rosa_s1 if g["Nome"] in giocatori_da_s1]
                obj_s2 = [g for g in rosa_s2 if g["Nome"] in giocatori_da_s2]

                # Rimuovi da rose attuali e aggiungi alle nuove
                st.session_state.rose_lega[squadra_1] = [g for g in rosa_s1 if g["Nome"] not in giocatori_da_s1] + obj_s2
                st.session_state.rose_lega[squadra_2] = [g for g in rosa_s2 if g["Nome"] not in giocatori_da_s2] + obj_s1

                # Gestione conguaglio extra budget
                if conguaglio != 0:
                    st.session_state.extra_budget[squadra_1] = st.session_state.extra_budget.get(squadra_1, 0) - conguaglio
                    st.session_state.extra_budget[squadra_2] = st.session_state.extra_budget.get(squadra_2, 0) + conguaglio

                # Aggiorna dataframe globale stato
                for g in obj_s1:
                    idx = df[df["Nome"] == g["Nome"]].index
                    if not idx.empty:
                        st.session_state.df_giocatori.at[idx[0], "Stato"] = squadra_2
                for g in obj_s2:
                    idx = df[df["Nome"] == g["Nome"]].index
                    if not idx.empty:
                        st.session_state.df_giocatori.at[idx[0], "Stato"] = squadra_1

                st.success(f"✅ Scambio completato con successo tra **{squadra_1}** e **{squadra_2}**!")
                st.rerun()
    else:
        st.info("Una delle due rose selezionate è vuota, impossibile effettuare scambi.")

# --- TAB 4: GESTIONE PRESTITI ---
with tab_prestiti:
    st.header("🤝 Gestione Prestiti (6 Mesi / 1 Anno, Rinnovo & Interruzione)")
    st.write("I prestiti hanno durata di 6 mesi o 1 anno. Puoi attivarli, **rinnovarli** o **interromperli** facendo rientrare il giocatore nella squadra d'origine in qualsiasi momento.")

    p_col1, p_col2 = st.columns(2)
    with p_col1:
        sq_cedente = st.selectbox("Squadra Cedente:", PARTECIPANTI_LEGA, key="prest_cedente")
    rosa_ced = st.session_state.rose_lega.get(sq_cedente, [])

    if rosa_ced:
        nomi_ced = [g["Nome"] for g in rosa_ced]
        with p_col2:
            sq_ricevente = st.selectbox("Squadra Ricevente:", [p for p in PARTECIPANTI_LEGA if p != sq_cedente], key="prest_ricevente")

        cp_1, cp_2 = st.columns(2)
        with cp_1:
            gioc_prestito = st.selectbox("Giocatore in prestito:", nomi_ced, key="gioc_prest")
        with cp_2:
            durata_p = st.selectbox("Durata prestito:", ["6 mesi", "1 anno"], key="durata_p")

        if st.button("📝 Registra Prestito"):
            g_obj = next((g for g in rosa_ced if g["Nome"] == gioc_prestito), None)
            if g_obj:
                st.session_state.rose_lega[sq_cedente] = [g for g in rosa_ced if g["Nome"] != gioc_prestito]
                if sq_ricevente not in st.session_state.rose_lega:
                    st.session_state.rose_lega[sq_ricevente] = []
                st.session_state.rose_lega[sq_ricevente].append(g_obj)

                # Aggiorna stato globale
                idx = df[df["Nome"] == gioc_prestito].index
                if not idx.empty:
                    st.session_state.df_giocatori.at[idx[0], "Stato"] = sq_ricevente

                st.session_state.prestiti_lega.append({
                    "Giocatore": gioc_prestito,
                    "Da": sq_cedente,
                    "A": sq_ricevente,
                    "Durata": durata_p,
                    "Stato": "Attivo"
                })
                st.success(f"✅ Prestito registrato ({durata_p}): **{gioc_prestito}** da {sq_cedente} a {sq_ricevente}!")
                st.rerun()
    else:
        st.info("La rosa selezionata è vuota.")

    st.subheader("📋 Registro Prestiti in Corso")
    if st.session_state.prestiti_lega:
        for idx, prestito in enumerate(st.session_state.prestiti_lega):
            r_c1, r_c2, r_c3, r_c4 = st.columns([3, 2, 2, 2])
            with r_c1:
                st.write(f"**{prestito['Giocatore']}** ({prestito['Da']} ➡️ {prestito['A']})")
                st.caption(f"Durata: {prestito['Durata']} | Stato: **{prestito['Stato']}**")
            with r_c2:
                pass
            with r_c3:
                if prestito["Stato"] in ["Attivo", "Rinnovato"]:
                    if st.button("🔄 Rinnova", key=f"rinn_{idx}"):
                        st.session_state.prestiti_lega[idx]["Stato"] = "Rinnovato"
                        st.success("Prestito rinnovato!")
                        st.rerun()
            with r_c4:
                if prestito["Stato"] in ["Attivo", "Rinnovato"]:
                    if st.button("🛑 Interrompi", key=f"interr_{idx}"):
                        g_nome = prestito["Giocatore"]
                        sq_orig = prestito["Da"]
                        sq_att = prestito["A"]
                        
                        rosa_att_prest = st.session_state.rose_lega.get(sq_att, [])
                        g_trovato = next((g for g in rosa_att_prest if g["Nome"] == g_nome), None)
                        
                        if g_trovato:
                            st.session_state.rose_lega[sq_att] = [g for g in rosa_att_prest if g["Nome"] != g_nome]
                            if sq_orig not in st.session_state.rose_lega:
                                st.session_state.rose_lega[sq_orig] = []
                            st.session_state.rose_lega[sq_orig].append(g_trovato)

                            idx_df = df[df["Nome"] == g_nome].index
                            if not idx_df.empty:
                                st.session_state.df_giocatori.at[idx_df[0], "Stato"] = sq_orig

                        st.session_state.prestiti_lega[idx]["Stato"] = "Interrotto"
                        st.success(f"Prestito interrotto. {g_nome} è rientrato a {sq_orig}.")
                        st.rerun()
    else:
        st.info("Nessun prestito registrato.")

# --- TAB 5: VISUALIZZA ROSE ---
with tab_rose:
    st.header("📋 Visualizzazione Rose e Svincoli")
    sq_vista = st.selectbox("Seleziona squadra da visualizzare:", PARTECIPANTI_LEGA, key="vista_sq")
    rosa_v = st.session_state.rose_lega.get(sq_vista, [])

    if rosa_v:
        df_r = pd.DataFrame(rosa_v)
        st.dataframe(df_r, use_container_width=True, hide_index=True)

        st.subheader("Svincola Giocatore (Rendi Libero)")
        nomi_v = [g["Nome"] for g in rosa_v]
        gioc_svin = st.selectbox("Seleziona giocatore da svincolare:", nomi_v, key="svin_sel")
        if st.button("🗑️ Conferma Svincolo"):
            st.session_state.rose_lega[sq_vista] = [g for g in rosa_v if g["Nome"] != gioc_svin]
            idx_d = df[df["Nome"] == gioc_svin].index
            if not idx_d.empty:
                st.session_state.df_giocatori.at[idx_d[0], "Stato"] = "LIBERO"
            st.success(f"✅ {gioc_svin} svincolato ed è tornato LIBERO.")
            st.rerun()
    else:
        st.info("La rosa è vuota.")