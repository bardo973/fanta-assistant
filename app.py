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
    df["Nome"] = df_raw["Calciatore"]
    df["Squadra"] = df_raw["Squadra"]
    df["Ruolo"] = df_raw["Ruolo"]
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
                "Nome": row["Nome"],
                "Ruolo": row["Ruolo"],
                "Squadra": row["Squadra"],
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
    "Chi sta acquistando ora:", PARTECIPANTI_LEGA
)

budget_input = st.sidebar.number_input(
    "Budget Iniziale Crediti (Tutti)",
    value=st.session_state.budget_iniziale,
    step=10,
)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rosa_corrente = st.session_state.rose_lega[fanta_allenatore_attivo]
spesa_corrente = sum(item.get("Prezzo_Acquisto", 1) for item in rosa_corrente)
budget_rimanente_corrente = (
    st.session_state.budget_iniziale
    + st.session_state.extra_budget[fanta_allenatore_attivo]
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

# --- CARICAMENTO NUOVO LISTONE UFFICIALE ---
st.sidebar.divider()
st.sidebar.subheader("📄 Carica Nuovo Listone Ufficiale")
nuovo_listone_file = st.sidebar.file_uploader(
    "Carica CSV nuovo listone", type=["csv"], key="listone_generale"
)

if nuovo_listone_file is not None:
    try:
        df_nuovo = pd.read_csv(nuovo_listone_file, encoding="latin1")
        df_new_processed = pd.DataFrame()
        df_new_processed["Nome"] = df_nuovo["Calciatore"]
        df_new_processed["Squadra"] = df_nuovo["Squadra"]
        df_new_processed["Ruolo"] = df_nuovo["Ruolo"]
        df_new_processed["Quotazione"] = pd.to_numeric(
            df_nuovo["Quotazione"], errors="coerce"
        ).fillna(1)
        df_new_processed["Stato"] = "LIBERO"

        rose_attuali = st.session_state.rose_lega
        for idx, row in df_new_processed.iterrows():
            nome_giocatore = row["Nome"]
            for allenatore, rosa in rose_attuali.items():
                if any(
                    g["Nome"].strip().lower() == nome_giocatore.strip().lower()
                    for g in rosa
                ):
                    df_new_processed.at[idx, "Stato"] = allenatore
                    break

        df_new_processed[["Tier", "Scadenza_Contratto"]] = df_new_processed[
            "Quotazione"
        ].apply(lambda q: pd.Series(["Top", 2027] if q >= 25 else (["Semitop", 2028] if q >= 15 else (["Titolare", 2029] if q >= 8 else ["Scommessa", 2030]))))
        df_new_processed["Percentuale_Titolarita"] = 0.8
        df_new_processed["Partite_Attese"] = 30
        df_new_processed["Indice_Continuita"] = 7.0
        df_new_processed["Rischio_Infortunio"] = "Medio"
        df_new_processed["FantaMedia_Stimata"] = 6.5
        df_new_processed["Status_Piazzati"] = df_new_processed[
            "Quotazione"
        ].apply(
            lambda q: (
                "Rigorista 🎯"
                if q >= 28
                else ("Vice-Rigorista 👟" if q >= 18 else "No")
            )
        )
        df_new_processed["Valore_Atteso"] = 10.0
        df_new_processed["Indice_VfM"] = 1.0

        st.session_state.df_giocatori = df_new_processed
        st.sidebar.success(
            "✅ Nuovo listone caricato e rose sincronizzate con successo!"
        )
    except Exception as e:
        st.sidebar.error(f"Errore nel caricamento: {e}")

# --- CARICAMENTO GLOBALE DELLE ROSE DI TUTTI ---
st.sidebar.divider()
st.sidebar.subheader("📁 Carica Rose di Tutti")
file_rose_tutti = st.sidebar.file_uploader(
    "Carica file unificato rose (CSV/Excel)",
    type=["csv", "xlsx"],
    key="uploader_tutti",
)

if file_rose_tutti is not None:
    try:
        if file_rose_tutti.name.endswith(".csv"):
            df_tutti = pd.read_csv(file_rose_tutti, encoding="latin1")
        else:
            df_tutti = pd.read_excel(file_rose_tutti)

        possibili_col_nomi = ["Calciatore", "Nome", "Giocatore", "Player"]
        possibili_col_prop = [
            "Proprietario",
            "Squadra_Fantacalcio",
            "Allenatore",
            "Proprietario_Iniziale",
        ]

        col_nome_tutti = next(
            (c for c in possibili_col_nomi if c in df_tutti.columns), None
        )
        col_prop_tutti = next(
            (c for c in possibili_col_prop if c in df_tutti.columns), None
        )

        if col_nome_tutti and col_prop_tutti:
            nuove_rose = {p: [] for p in PARTECIPANTI_LEGA}
            df_corrente = st.session_state.df_giocatori
            df_corrente["Stato"] = "LIBERO"

            for _, row_t in df_tutti.iterrows():
                nome_giocatore = str(row_t[col_nome_tutti]).strip()
                proprietario = str(row_t[col_prop_tutti]).strip().upper()

                if proprietario in nuove_rose:
                    match_generale = df_corrente[
                        df_corrente["Nome"].str.strip().str.lower()
                        == nome_giocatore.lower()
                    ]

                    if not match_generale.empty:
                        g_info = match_generale.iloc[0]
                        idx_gen = match_generale.index[0]
                        df_corrente.at[idx_gen, "Stato"] = proprietario

                        prezzo_acq = (
                            int(row_t["Prezzo"])
                            if "Prezzo" in df_tutti.columns
                            and pd.notna(row_t["Prezzo"])
                            else int(g_info["Quotazione"])
                        )

                        nuove_rose[proprietario].append({
                            "Nome": g_info["Nome"],
                            "Ruolo": g_info["Ruolo"],
                            "Squadra": g_info["Squadra"],
                            "Prezzo_Acquisto": prezzo_acq,
                            "Valore_Attuale": int(g_info["Quotazione"]),
                            "Scadenza": int(g_info["Scadenza_Contratto"]),
                        })

            st.session_state.rose_lega = nuove_rose
            st.session_state.df_giocatori = df_corrente
            st.sidebar.success("✅ Rose di tutti caricate e sincronizzate!")
        else:
            st.sidebar.error(
                "❌ Colonne mancanti nel file. Controlla i nomi delle colonne (es. 'Calciatore' e 'Proprietario')."
            )
    except Exception as e:
        st.sidebar.error(f"Errore caricamento rose: {e}")

st.sidebar.divider()
st.sidebar.subheader("💰 Massime Offerte (Tutti)")
slot_totale_lega = sum(slot_target.values())
for p in PARTECIPANTI_LEGA:
    r_p = st.session_state.rose_lega[p]
    spesa_p = sum(item.get("Prezzo_Acquisto", 1) for item in r_p)
    bud_rim_p = (
        st.session_state.budget_iniziale
        + st.session_state.extra_budget[p]
        - spesa_p
    )
    slot_presi_p = sum(1 for g in r_p if g["Ruolo"] in slot_target)
    slot_liberi_p = max(0, slot_totale_lega - slot_presi_p)
    riserva_minima_p = max(0, slot_liberi_p - 1)
    max_offerta_p = max(0, bud_rim_p - riserva_minima_p)
    st.sidebar.text(f"{p}: Max {max_offerta_p} cr (Rim. {bud_rim_p} cr)")

# Salvataggio e Caricamento Stato
st.sidebar.divider()
st.sidebar.subheader("💾 Salvataggio & Caricamento")
stato_salva = {
    "budget_iniziale": st.session_state.budget_iniziale,
    "rose_lega": st.session_state.rose_lega,
    "extra_budget": st.session_state.extra_budget,
    "stati_giocatori": df[["Nome", "Stato"]].set_index("Nome")["Stato"].to_dict(),
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
            nome_giocatore = row["Nome"]
            if nome_giocatore in stati_caricati:
                df.at[idx, "Stato"] = stati_caricati[nome_giocatore]
        st.sidebar.success("✅ Stato caricato con successo!")
    except Exception as e:
        st.sidebar.error(f"Errore: {e}")

st.sidebar.divider()
st.sidebar.subheader("📋 Esplora Rose & Valori")
squadra_da_esplorare = st.sidebar.selectbox(
    "Seleziona rosa da visualizzare:", PARTECIPANTI_LEGA, key="esplora_sidebar"
)
rosa_selezionata_sidebar = st.session_state.rose_lega[squadra_da_esplorare]
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
        "Seleziona il giocatore chiamato in asta:", giocatori_liberi
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

    st.info(
        f"💡 **Parametri Avanzati:** Continuità: **{g_data['Indice_Continuita']}/10** | Rischio Infortunio: **{g_data['Rischio_Infortunio']}** | Contratto Scadenza: **{int(g_data['Scadenza_Contratto'])}**"
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
            )
        submit_asta = st.form_submit_button("Conferma Acquisto Giocatore")

        if submit_asta:
            st.session_state.rose_lega[vincitore_asta].append({
                "Nome": g_data["Nome"],
                "Ruolo": g_data["Ruolo"],
                "Squadra": g_data["Squadra"],
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
        "Filtra per Ruolo:", ["Tutti", "P", "D", "C", "A"]
    )
with col_f2:
    filtro_tier = st.selectbox(
        "Filtra per Tier:", ["Tutti", "Top", "Semitop", "Titolare", "Scommessa"]
    )
with col_f3:
    solo_rigoristi_checkbox = st.checkbox("Solo Rigoristi Designati 🎯")

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
# 6. SEZIONE SVINCOLI E GESTIONE ROSA
# ---------------------------------------------------------
st.divider()
st.subheader("🔄 Gestione Rosa & Svincoli")

allenatore_svincolo = st.selectbox(
    "Seleziona allenatore che intende svincolare:",
    PARTECIPANTI_LEGA,
    key="select_svincolo",
)
rosa_allenatore_attuale = st.session_state.rose_lega[allenatore_svincolo]

if rosa_allenatore_attuale:
    nomi_giocatori_in_rosa = [g["Nome"] for g in rosa_allenatore_attuale]
    with st.form("form_svincolo"):
        giocatore_da_svincolare = st.selectbox(
            "Seleziona il giocatore da svincolare:", nomi_giocatori_in_rosa
        )
        submit_svincolo = st.form_submit_button("Conferma Svincolo")
        if submit_svincolo:
            # Rimuove il giocatore dalla rosa usando un controllo flessibile sui nomi
            st.session_state.rose_lega[allenatore_svincolo] = [
                g
                for g in rosa_allenatore_attuale
                if g["Nome"].strip().lower()
                != giocatore_da_svincolare.strip().lower()
            ]

            # Riporta lo stato del giocatore a LIBERO nel dataframe principale
            match_df = df[
                df["Nome"].str.strip().str.lower()
                == giocatore_da_svincolare.strip().lower()
            ]
            if not match_df.empty:
                idx_df = match_df.index[0]
                st.session_state.df_giocatori.at[idx_df, "Stato"] = "LIBERO"

            st.success(
                f"🗑️ **{giocatore_da_svincolare}** svincolato e tornato **LIBERO**!"
            )
            st.rerun()
else:
    st.info(f"La rosa di {allenatore_svincolo} è vuota.")