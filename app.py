import json
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT
# ---------------------------------------------------------
st.set_page_config(
    page_title="FantaLega AI Advanced Predictor & Manager", layout="wide"
)

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500

# ---------------------------------------------------------
# 2. CARICAMENTO E GENERAZIONE DATI CON PARAMETRI AVANZATI
# ---------------------------------------------------------


@st.cache_data
def load_data():
    df_raw = pd.read_csv("ROSE FANTAroby-quotazioni02022026.csv", encoding="latin1")

    df = pd.DataFrame()
    df["Nome"] = df_raw["Calciatore"].astype(str).str.strip()
    df["Squadra"] = df_raw["Squadra"].astype(str).str.strip()
    df["Ruolo"] = df_raw["Ruolo"].astype(str).str.strip()
    df["Quotazione"] = pd.to_numeric(
        df_raw["Quotazione"], errors="coerce"
    ).fillna(1)

    possibili_colonne_prop = [
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
            df_raw[colonna_trovata].astype(str).str.strip().str.upper()
        )
        df["Proprietario_Iniziale"] = df["Proprietario_Iniziale"].apply(
            lambda x: (
                "LIBERO" if x in ["NAN", "NONE", "", "SVINCOLATO", "LIBERO"] else x
            )
        )
    else:
        df["Proprietario_Iniziale"] = "LIBERO"

    df["Stato"] = df["Proprietario_Iniziale"]

    def assign_tier_and_contract(quot):
        if quot >= 25:
            return pd.Series(["Top", 2027])
        elif quot >= 15:
            return pd.Series(["Semitop", 2028])
        elif quot >= 8:
            return pd.Series(["Titolare", 2029])
        else:
            return pd.Series(["Scommessa", 2030])

    df[["Tier", "Scadenza_Contratto"]] = df["Quotazione"].apply(
        assign_tier_and_contract
    )

    def genera_parametri_avanzati(row):
        quot = row["Quotazione"]
        if quot >= 25:
            return pd.Series([0.92, 35, 8.5, "Basso (Affidabile)"])
        elif quot >= 15:
            return pd.Series([0.80, 31, 7.5, "Medio-Basso"])
        elif quot >= 8:
            return pd.Series([0.65, 27, 6.5, "Medio"])
        return pd.Series([0.40, 20, 5.5, "Variabile / Rischio"])

    df[
        [
            "Percentuale_Titolarita",
            "Partite_Attese",
            "Indice_Continuita",
            "Rischio_Infortunio",
        ]
    ] = df.apply(genera_parametri_avanzati, axis=1)

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

    df["Status_Piazzati"] = df["Quotazione"].apply(
        lambda q: (
            "Rigorista 🎯"
            if q >= 28
            else ("Vice-Rigorista 👟" if q >= 18 else "No")
        )
    )

    def assegna_metriche_ruolo(ruolo):
        if ruolo == "A":
            return pd.Series([0.35, 0.12])
        elif ruolo == "C":
            return pd.Series([0.15, 0.18])
        elif ruolo == "D":
            return pd.Series([0.05, 0.08])
        return pd.Series([0.00, 0.00])

    df[["xG_90", "xA_90"]] = df["Ruolo"].apply(assegna_metriche_ruolo)

    hype_squadra = {
        "Inter": 1.25,
        "Atalanta": 1.25,
        "Milan": 1.15,
        "Juventus": 1.15,
    }
    df["Moltiplicatore_Team"] = df["Squadra"].map(hype_squadra).fillna(0.95)

    df["Valore_Atteso"] = np.round(
        ((df["xG_90"] * 3.0) + (df["xA_90"] * 1.0))
        * df["Partite_Attese"]
        * df["Moltiplicatore_Team"],
        1,
    )
    df["Indice_VfM"] = np.round(df["Valore_Atteso"] / df["Quotazione"], 2)

    return df


if "df_giocatori" not in st.session_state:
    st.session_state.df_giocatori = load_data()

df = st.session_state.df_giocatori

lista_proprietari_csv = [
    p
    for p in df["Proprietario_Iniziale"].unique()
    if p not in ["LIBERO", "NAN", "NONE", ""]
]
if not lista_proprietari_csv:
    lista_proprietari_csv = [
        "BARDO",
        "ROBY",
        "SQUADRA_3",
        "SQUADRA_4",
        "SQUADRA_5",
        "SQUADRA_6",
    ]

PARTECIPANTI_LEGA = sorted(lista_proprietari_csv)

if "rose_lega" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}

if "extra_budget" not in st.session_state:
    st.session_state.extra_budget = {p: 0 for p in PARTECIPANTI_LEGA}

if "inizializzato" not in st.session_state:
    st.session_state.rose_lega = {p: [] for p in PARTECIPANTI_LEGA}
    for idx, row in df.iterrows():
        prop = row["Proprietario_Iniziale"]
        if prop in st.session_state.rose_lega:
            st.session_state.rose_lega[prop].append({
                "Nome": str(row["Nome"]),
                "Ruolo": str(row["Ruolo"]),
                "Squadra": str(row["Squadra"]),
                "Prezzo_Acquisto": int(row["Quotazione"]),
                "Valore_Attuale": int(row["Quotazione"]),
                "Scadenza": int(row["Scadenza_Contratto"]),
            })
            st.session_state.df_giocatori.at[idx, "Stato"] = prop
        else:
            st.session_state.df_giocatori.at[idx, "Stato"] = "LIBERO"
    st.session_state.inizializzato = True

for p in PARTECIPANTI_LEGA:
    if p not in st.session_state.rose_lega:
        st.session_state.rose_lega[p] = []
    if p not in st.session_state.extra_budget:
        st.session_state.extra_budget[p] = 0

df = st.session_state.df_giocatori

# ---------------------------------------------------------
# 3. SIDEBAR: PANNELLO DI CONTROLLO & CARICAMENTO DATI
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Dashboard")
fanta_allenatore_attivo = st.sidebar.selectbox(
    "Chi sta acquistando ora:", PARTECIPANTI_LEGA, key="allenatore_attivo_sb"
)

budget_input = st.sidebar.number_input(
    "Budget Iniziale Crediti (Tutti)",
    value=st.session_state.budget_iniziale,
    step=10,
)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega.get(fanta_allenatore_attivo, [])
spesa_corrente = sum(item.get("Prezzo_Acquisto", 1) for item in rosa_corrente)
budget_rimanente_corrente = (
    st.session_state.budget_iniziale
    + st.session_state.extra_budget.get(fanta_allenatore_attivo, 0)
    - spesa_corrente
)

slot_target = {"P": 3, "D": 8, "C": 8, "A": 6}
slot_presi = {
    r: sum(1 for g in rosa_corrente if g["Ruolo"] == r) for r in slot_target
}
slot_liberi = {r: slot_target[r] - slot_presi[r] for r in slot_target}
totale_slot_liberi = sum(slot_liberi.values())

st.sidebar.metric(
    f"Budget Rimanente ({fanta_allenatore_attivo})",
    f"{budget_rimanente_corrente} cr",
)

# --- CARICAMENTO STATO SALVATO (JSON) ---
st.sidebar.divider()
st.sidebar.subheader("💾 Salvataggio & Caricamento")
stato_salva = {
    "budget_iniziale": st.session_state.budget_iniziale,
    "rose_lega": st.session_state.rose_lega,
    "extra_budget": st.session_state.extra_budget,
    "stati_giocatori": df[["Nome", "Stato"]]
    .set_index("Nome")["Stato"]
    .to_dict(),
}
json_data = json.dumps(stato_salva, indent=4)
st.sidebar.download_button(
    label="📥 Salva Stato Lega (JSON)",
    data=json_data,
    file_name="fanta_lega_backup.json",
    mime="application/json",
)

uploaded_file = st.sidebar.file_uploader(
    "📂 Carica Stato Salvato", type=["json"]
)
if uploaded_file is not None:
    try:
        loaded_state = json.load(uploaded_file)
        st.session_state.budget_iniziale = loaded_state.get(
            "budget_iniziale", 500
        )
        st.session_state.rose_lega = loaded_state.get("rose_lega", {})
        st.session_state.extra_budget = loaded_state.get(
            "extra_budget", {p: 0 for p in PARTECIPANTI_LEGA}
        )

        stati_caricati = loaded_state.get("stati_giocatori", {})
        for idx, row in df.iterrows():
            nome_giq = str(row["Nome"]).strip()
            found_status = "LIBERO"
            for k, v in stati_caricati.items():
                if str(k).strip().lower() == nome_giq.lower():
                    found_status = v
                    break
            df.at[idx, "Stato"] = found_status

        st.session_state.df_giocatori = df
        st.sidebar.success("✅ Stato caricato con successo!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento dello stato: {e}")

st.sidebar.divider()
st.sidebar.subheader("📋 Esplora Rose & Valori")
squadra_da_esplorare = st.sidebar.selectbox(
    "Seleziona rosa da visualizzare:", PARTECIPANTI_LEGA, key="esplora_sidebar"
)
rosa_selezionata_sidebar = st.session_state.rose_lega.get(
    squadra_da_esplorare, []
)
if rosa_selezionata_sidebar:
    df_side_list = [
        {
            "Nome": g["Nome"],
            "Ruolo": g["Ruolo"],
            "Spesa": g.get("Prezzo_Acquisto", 1),
            "Scadenza": g["Scadenza"],
        }
        for g in rosa_selezionata_sidebar
    ]
    st.sidebar.dataframe(
        pd.DataFrame(df_side_list), use_container_width=True, hide_index=True
    )
else:
    st.sidebar.info("Rosa vuota.")

# ---------------------------------------------------------
# 4. DASHBOARD PRINCIPALE: ASTA LIVE & PARAMETRI AVANZATI
# ---------------------------------------------------------
st.title("⚡ Live Auction Intelligent Assistant (Advanced)")

st.subheader(f"🔍 Analisi Giocatore per: {fanta_allenatore_attivo}")
giocatori_liberi = df[df["Stato"] == "LIBERO"]["Nome"].tolist()

if giocatori_liberi:
    giocatore_sel = st.selectbox(
        "Seleziona il giocatore chiamato in asta:",
        giocatori_liberi,
        key="seleziona_giocatore_asta",
    )
    g_data = df[df["Nome"] == giocatore_sel].iloc[0]

    riserva_minima = max(0, totale_slot_liberi - 1)
    budget_spendibile = max(0, budget_rimanente_corrente - riserva_minima)

    percentuali_tier = {
        "Top": 0.45,
        "Semitop": 0.22,
        "Titolare": 0.08,
        "Scommessa": 0.03,
    }
    base_offerta = int(
        budget_spendibile * percentuali_tier.get(g_data["Tier"], 0.04)
    )

    if g_data["Status_Piazzati"].startswith("Rigorista"):
        base_offerta += 5
    if g_data["FantaMedia_Stimata"] >= 7.0:
        base_offerta += 3

    max_offerta_consigliata = max(1, base_offerta)
    max_offerta_consigliata = (
        max_offerta_consigliata if slot_liberi[g_data["Ruolo"]] > 0 else 0
    )

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Ruolo & Squadra",
        f"{g_data['Ruolo']} - {g_data['Squadra']}",
        f"Tier: {g_data['Tier']}",
    )
    col2.metric("FantaMedia Stimata", f"{g_data['FantaMedia_Stimata']} FM")
    col3.metric("Rigorista / Piazzati", f"{g_data['Status_Piazzati']}")
    col4.metric(
        "🔥 Max Offerta Consigliata", f"{max_offerta_consigliata} cr"
    )

    with st.form("form_aggiudicazione"):
        st.write("### Registra Acquisto Asta")
        col_A, col_B = st.columns(2)
        with col_A:
            prezzo_aggiudicazione = st.number_input(
                "Prezzo di chiusura asta (crediti):",
                min_value=1,
                value=max(1, int(max_offerta_consigliata)),
            )
        with col_B:
            vincitore_asta = st.selectbox(
                "Assegna a fanta-allenatore:",
                PARTECIPANTI_LEGA,
                index=PARTECIPANTI_LEGA.index(fanta_allenatore_attivo),
                key="vincitore_asta_form",
            )
        submit_asta = st.form_submit_button("Conferma Acquisto Giocatore")

        if submit_asta:
            if vincitore_asta not in st.session_state.rose_lega:
                st.session_state.rose_lega[vincitore_asta] = []
            st.session_state.rose_lega[vincitore_asta].append({
                "Nome": str(g_data["Nome"]),
                "Ruolo": str(g_data["Ruolo"]),
                "Squadra": str(g_data["Squadra"]),
                "Prezzo_Acquisto": int(prezzo_aggiudicazione),
                "Valore_Attuale": int(g_data["Quotazione"]),
                "Scadenza": int(g_data["Scadenza_Contratto"]),
            })
            idx_giocatore = df[df["Nome"] == giocatore_sel].index[0]
            st.session_state.df_giocatori.at[idx_giocatore, "Stato"] = (
                vincitore_asta
            )
            st.success(
                f"✅ {giocatore_sel} assegnato a **{vincitore_asta}** per {prezzo_aggiudicazione} crediti!"
            )
            st.rerun()
else:
    st.success("🎉 Tutti i giocatori sono stati assegnati!")

# ---------------------------------------------------------
# 5. SEZIONE SCOUTING AVANZATO & FILTRI
# ---------------------------------------------------------
st.divider()
st.subheader("🎯 Scout di Rendimento & Parametri Avanzati")

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    filtro_ruolo = st.selectbox(
        "Filtra per Ruolo:", ["Tutti", "P", "D", "C", "A"], key="filtro_ruolo_scout"
    )
with col_f2:
    filtro_tier = st.selectbox(
        "Filtra per Tier:",
        ["Tutti", "Top", "Semitop", "Titolare", "Scommessa"],
        key="filtro_tier_scout",
    )
with col_f3:
    solo_rigoristi_checkbox = st.checkbox(
        "Solo Rigoristi Designati 🎯", key="filtro_rigoristi_scout"
    )

df_scout = df[df["Stato"] == "LIBERO"].copy()
if filtro_ruolo != "Tutti":
    df_scout = df_scout[df_scout["Ruolo"] == filtro_ruolo]
if filtro_tier != "Tutti":
    df_scout = df_scout[df_scout["Tier"] == filtro_tier]
if solo_rigoristi_checkbox:
    df_scout = df_scout[
        df_scout["Status_Piazzati"].str.startswith("Rigorista")
    ]

st.dataframe(
    df_scout[[
        "Nome",
        "Squadra",
        "Ruolo",
        "Quotazione",
        "FantaMedia_Stimata",
        "Status_Piazzati",
        "Indice_Continuita",
        "Rischio_Infortunio",
        "Valore_Atteso",
    ]],
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------
# 6. SEZIONE SVINCOLI E GESTIONE ROSA (RENDI LIBERO / SVINCOLA)
# ---------------------------------------------------------
st.divider()
st.subheader("🔄 Gestione Rosa & Svincoli (Rendi Libero)")

allenatore_svincolo = st.selectbox(
    "Seleziona allenatore che intende svincolare:",
    PARTECIPANTI_LEGA,
    key="select_svincolo_allenatore",
)
rosa_allenatore_attuale = st.session_state.rose_lega.get(
    allenatore_svincolo, []
)

if rosa_allenatore_attuale:
    nomi_giocatori_in_rosa = [str(g["Nome"]) for g in rosa_allenatore_attuale]

    giocatore_da_svincolare = st.selectbox(
        "Seleziona il giocatore da svincolare (torna LIBERO):",
        nomi_giocatori_in_rosa,
        key="select_giocatore_da_svincolare",
    )

    if st.button("🗑️ Conferma Svincolo / Rendi Libero", key="btn_svincola"):
        st.session_state.rose_lega[allenatore_svincolo] = [
            g
            for g in rosa_allenatore_attuale
            if str(g["Nome"]).strip().lower()
            != str(giocatore_da_svincolare).strip().lower()
        ]

        match_idx = st.session_state.df_giocatori[
            st.session_state.df_giocatori["Nome"].astype(str).str.strip().str.lower()
            == str(giocatore_da_svincolare).strip().lower()
        ].index

        if not match_idx.empty:
            for idx_df in match_idx:
                st.session_state.df_giocatori.at[idx_df, "Stato"] = "LIBERO"

        st.success(
            f"✅ **{giocatore_da_svincolare}** è stato svincolato da {allenatore_svincolo} ed è ora nuovamente **LIBERO**!"
        )
        st.rerun()
else:
    st.info(f"La rosa di {allenatore_svincolo} è vuota.")

# ---------------------------------------------------------
# 7. SEZIONE GESTIONE PRESTITI TRA SQUADRE
# ---------------------------------------------------------
st.divider()
st.subheader("🤝 Gestione Prestiti tra Squadre")

col_p1, col_p2 = st.columns(2)
with col_p1:
    squadra_cedente = st.selectbox(
        "Squadra che cede in prestito:",
        PARTECIPANTI_LEGA,
        key="prestito_da_squadra",
    )

rosa_cedente = st.session_state.rose_lega.get(squadra_cedente, [])

if rosa_cedente:
    nomi_cedente = [str(g["Nome"]) for g in rosa_cedente]
    with col_p2:
        squadra_ricevente = st.selectbox(
            "Squadra che riceve in prestito:",
            [p for p in PARTECIPANTI_LEGA if p != squadra_cedente],
            key="prestito_a_squadra",
        )

    giocatore_prestito = st.selectbox(
        "Seleziona il giocatore da dare in prestito:",
        nomi_cedente,
        key="giocatore_in_prestito_sel",
    )

    if st.button("🔄 Conferma Trasferimento in Prestito", key="btn_prestito"):
        giocatore_obj = next(
            (
                g
                for g in rosa_cedente
                if str(g["Nome"]).strip().lower()
                == str(giocatore_prestito).strip().lower()
            ),
            None,
        )

        if giocatore_obj:
            st.session_state.rose_lega[squadra_cedente] = [
                g
                for g in rosa_cedente
                if str(g["Nome"]).strip().lower()
                != str(giocatore_prestito).strip().lower()
            ]
            if squadra_ricevente not in st.session_state.rose_lega:
                st.session_state.rose_lega[squadra_ricevente] = []
            st.session_state.rose_lega[squadra_ricevente].append(
                giocatore_obj
            )

            match_idx = st.session_state.df_giocatori[
                st.session_state.df_giocatori["Nome"].astype(str).str.strip().str.lower()
                == str(giocatore_prestito).strip().lower()
            ].index

            if not match_idx.empty:
                for idx_df in match_idx:
                    st.session_state.df_giocatori.at[
                        idx_df, "Stato"
                    ] = squadra_ricevente

            st.success(
                f"✅ Prestito completato: **{giocatore_prestito}** è passato da **{squadra_cedente}** a **{squadra_ricevente}**!"
            )
            st.rerun()
else:
    st.info(f"La rosa di {squadra_cedente} è vuota, impossibile effettuare prestiti.")