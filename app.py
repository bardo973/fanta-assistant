import json
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT SICURO
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
            return pd.Series(["Top", 2029])
        elif quot >= 15:
            return pd.Series(["Semitop", 2029])
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

# Inizializzazione rapida vettorizzata al primo avvio (Contratto iniziale di default o 4 anni)
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
                "Valore_Attuale": int(r["Quotazione"]),
                "Scadenza": int(r["Scadenza_Contratto"]),
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
# 3. SIDEBAR: PANNELLO DI CONTROLLO & CARICAMENTO DATI
# ---------------------------------------------------------
st.sidebar.title("🏆 FantaLega Dashboard")
fanta_allenatore_attivo = st.sidebar.selectbox(
    "Chi sta acquistando ora:", PARTECIPANTI_LEGA, key="allenatore_attivo_sb"
)

budget_input = st.sidebar.number_input(
    "Budget Iniziale Crediti (Tutti)",
    value=st.session_state.get("budget_iniziale", 500),
    step=10,
)
if budget_input != st.session_state.budget_iniziale:
    st.session_state.budget_iniziale = budget_input

rose_lega_dict = st.session_state.get(
    "rose_lega", {p: [] for p in PARTECIPANTI_LEGA}
)
extra_budget_dict = st.session_state.get(
    "extra_budget", {p: 0 for p in PARTECIPANTI_LEGA}
)

rosa_corrente = rose_lega_dict.get(fanta_allenatore_attivo, [])
spesa_corrente = sum(item.get("Prezzo_Acquisto", 1) for item in rosa_corrente)
budget_rimanente_corrente = (
    st.session_state.get("budget_iniziale", 500)
    + extra_budget_dict.get(fanta_allenatore_attivo, 0)
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

# --- SALVATAGGIO & CARICAMENTO JSON ---
st.sidebar.divider()
st.sidebar.subheader("💾 Salvataggio & Caricamento")

stato_salva = {
    "budget_iniziale": st.session_state.get("budget_iniziale", 500),
    "rose_lega": rose_lega_dict,
    "extra_budget": extra_budget_dict,
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
    "📂 Carica Stato Salvato (JSON)", type=["json"], key="json_backup_uploader"
)

if uploaded_file is not None:
    file_identifier = f"{uploaded_file.name}_{uploaded_file.size}"
    if st.session_state.get("last_uploaded_file") != file_identifier:
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
            stati_map_lower = {
                str(k).strip().lower(): str(v)
                for k, v in stati_caricati.items()
            }

            df_temp = st.session_state.df_giocatori.copy()
            df_temp["_nome_key"] = (
                df_temp["Nome"].astype(str).str.strip().str.lower()
            )
            df_temp["Stato"] = (
                df_temp["_nome_key"].map(stati_map_lower).fillna("LIBERO")
            )
            df_temp.drop(columns=["_nome_key"], inplace=True)

            st.session_state.df_giocatori = df_temp
            st.session_state.last_uploaded_file = file_identifier

            st.sidebar.success("✅ Backup caricato con successo!")
            st.rerun()
        except Exception as e:
            st.sidebar.error(f"Errore durante il caricamento del backup: {e}")

# --- IMPORTAZIONE EXCEL "ROSE FANTA" (Contratto a 4 anni = 2030) ---
st.sidebar.divider()
st.sidebar.subheader("📊 Importa Rose da Excel")
uploaded_excel = st.sidebar.file_uploader(
    "Carica file Excel (es. rose fanta)", type=["xlsx", "xls"], key="excel_rose_uploader"
)

if uploaded_excel is not None:
    excel_identifier = f"{uploaded_excel.name}_{uploaded_excel.size}"
    if st.session_state.get("last_uploaded_excel") != excel_identifier:
        try:
            df_excel = pd.read_excel(uploaded_excel)
            
            col_nome = next((c for c in ["Calciatore", "Nome", "Giocatore"] if c in df_excel.columns), df_excel.columns[0])
            col_prop = next((c for c in ["Proprietario", "Squadra_Fantacalcio", "Allenatore", "Team"] if c in df_excel.columns), None)
            col_prezzo = next((c for c in ["Prezzo", "Costo", "Quotazione", "Pagato"] if c in df_excel.columns), None)
            col_scadenza = next((c for c in ["Scadenza", "Contratto", "Anno"] if c in df_excel.columns), None)

            if col_prop:
                new_rose = {p: [] for p in PARTECIPANTI_LEGA}
                df_temp = st.session_state.df_giocatori.copy()
                df_temp["Stato"] = "LIBERO"
                
                master_dict = {
                    str(row["Nome"]).strip().lower(): row 
                    for _, row in df_temp.iterrows()
                }

                for _, row in df_excel.iterrows():
                    nome_giocatore = str(row[col_nome]).strip()
                    proprietario = str(row[col_prop]).strip().upper()
                    
                    if proprietario in ["NAN", "NONE", "", "SVINCOLATO", "LIBERO"]:
                        continue
                        
                    if proprietario not in PARTECIPANTI_LEGA:
                        PARTECIPANTI_LEGA.append(proprietario)
                        if proprietario not in new_rose:
                            new_rose[proprietario] = []

                    nome_key = nome_giocatore.lower()
                    prezzo_val = int(row[col_prezzo]) if col_prop and col_prezzo and pd.notna(row[col_prezzo]) else 1
                    
                    # Se non è specificata la scadenza nell'excel, imposta 4 anni di default (2030)
                    scadenza_val = int(row[col_scadenza]) if col_scadenza and pd.notna(row[col_scadenza]) else 2030

                    if nome_key in master_dict:
                        g_info = master_dict[nome_key]
                        ruolo_g = g_info["Ruolo"]
                        squadra_g = g_info["Squadra"]
                        quot_g = int(g_info["Quotazione"])
                        
                        if not col_prezzo:
                            prezzo_val = quot_g

                        new_rose[proprietario].append({
                            "Nome": g_info["Nome"],
                            "Ruolo": ruolo_g,
                            "Squadra": squadra_g,
                            "Prezzo_Acquisto": prezzo_val,
                            "Valore_Attuale": quot_g,
                            "Scadenza": scadenza_val,
                        })
                        
                        idx_match = df_temp[df_temp["Nome"].astype(str).str.strip().str.lower() == nome_key].index
                        if not idx_match.empty:
                            df_temp.at[idx_match[0], "Stato"] = proprietario

                st.session_state.rose_lega = new_rose
                st.session_state.df_giocatori = df_temp
                st.session_state.last_uploaded_excel = excel_identifier
                st.sidebar.success("✅ Rose importate con successo dall'Excel!")
                st.rerun()
            else:
                st.sidebar.error("Impossibile trovare la colonna del Proprietario/Squadra nel file Excel.")
        except Exception as e:
            st.sidebar.error(f"Errore nella lettura del file Excel: {e}")

# --- NUOVA SEZIONE SIDEBAR: MODIFICA SCADENZE CONTRATTI ---
st.sidebar.divider()
st.sidebar.subheader("📅 Modifica Scadenze Contratti")
squadra_mod_scadenza = st.sidebar.selectbox("Seleziona squadra per contratti:", PARTECIPANTI_LEGA, key="mod_scad_sq")
rosa_mod_scadenza = st.session_state.get("rose_lega", {}).get(squadra_mod_scadenza, [])

if rosa_mod_scadenza:
    nomi_mod_scadenza = [str(g["Nome"]) for g in rosa_mod_scadenza]
    giocatore_da_aggiornare = st.sidebar.selectbox("Seleziona giocatore:", nomi_mod_scadenza, key="mod_scad_gioc")
    
    # Trova la scadenza attuale del giocatore selezionato
    gioc_obj_corrente = next((g for g in rosa_mod_scadenza if str(g["Nome"]).strip().lower() == str(giocatore_da_aggiornare).strip().lower()), None)
    scadenza_attuale_val = gioc_obj_corrente.get("Scadenza", 2030) if gioc_obj_corrente else 2030
    
    nuova_scadenza = st.sidebar.number_input("Nuovo Anno Scadenza:", min_value=2026, max_value=2035, value=int(scadenza_attuale_val), step=1, key="input_nuova_scad")
    
    if st.sidebar.button("💾 Aggiorna Scadenza", key="btn_aggiorna_scad"):
        for g in st.session_state.rose_lega[squadra_mod_scadenza]:
            if str(g["Nome"]).strip().lower() == str(giocatore_da_aggiornare).strip().lower():
                g["Scadenza"] = int(nuova_scadenza)
                break
        st.sidebar.success(f"✅ Contratto di **{giocatore_da_aggiornare}** aggiornato al **{nuova_scadenza}**!")
        st.rerun()
else:
    st.sidebar.info("Rosa vuota.")

st.sidebar.divider()
st.sidebar.subheader("📋 Esplora Rose & Valori")
squadra_da_esplorare = st.sidebar.selectbox(
    "Seleziona rosa da visualizzare:", PARTECIPANTI_LEGA, key="esplora_sidebar"
)

rosa_selezionata_sidebar = st.session_state.get("rose_lega", {}).get(
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
                index=PARTECIPANTI_LEGA.index(fanta_allenatore_attivo) if fanta_allenatore_attivo in PARTECIPANTI_LEGA else 0,
                key="vincitore_asta_form",
            )
        submit_asta = st.form_submit_button("Conferma Acquisto Giocatore")

        if submit_asta:
            current_rose = st.session_state.get("rose_lega", {})
            if vincitore_asta not in current_rose:
                current_rose[vincitore_asta] = []
            
            # Assegnazione automatica del contratto a 4 anni (2026 + 4 = 2030)
            current_rose[vincitore_asta].append({
                "Nome": str(g_data["Nome"]),
                "Ruolo": str(g_data["Ruolo"]),
                "Squadra": str(g_data["Squadra"]),
                "Prezzo_Acquisto": int(prezzo_aggiudicazione),
                "Valore_Attuale": int(g_data["Quotazione"]),
                "Scadenza": 2030,  # Contratto di 4 anni per i nuovi acquisti
            })
            st.session_state.rose_lega = current_rose
            idx_giocatore = df[df["Nome"] == giocatore_sel].index[0]
            st.session_state.df_giocatori.at[idx_giocatore, "Stato"] = (
                vincitore_asta
            )
            st.success(
                f"✅ {giocatore_sel} assegnato a **{vincitore_asta}** per {prezzo_aggiudicazione} crediti con contratto quadriennale (Scad. 2030)!"
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
# 6. SEZIONE SVINCOLI E GESTIONE ROSA
# ---------------------------------------------------------
st.divider()
st.subheader("🔄 Gestione Rosa & Svincoli (Rendi Libero)")

allenatore_svincolo = st.selectbox(
    "Seleziona allenatore che intende svincolare:",
    PARTECIPANTI_LEGA,
    key="select_svincolo_allenatore",
)
rosa_allenatore_attuale = st.session_state.get("rose_lega", {}).get(
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
        current_rose = st.session_state.get("rose_lega", {})
        current_rose[allenatore_svincolo] = [
            g
            for g in rosa_allenatore_attuale
            if str(g["Nome"]).strip().lower()
            != str(giocatore_da_svincolare).strip().lower()
        ]
        st.session_state.rose_lega = current_rose

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

rosa_cedente = st.session_state.get("rose_lega", {}).get(squadra_cedente, [])

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
            current_rose = st.session_state.get("rose_lega", {})
            current_rose[squadra_cedente] = [
                g
                for g in rosa_cedente
                if str(g["Nome"]).strip().lower()
                != str(giocatore_prestito).strip().lower()
            ]
            if squadra_ricevente not in current_rose:
                current_rose[squadra_ricevente] = []
            current_rose[squadra_ricevente].append(giocatore_obj)
            st.session_state.rose_lega = current_rose

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