import io
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
# 2. FUNZIONE DI SUPPORTO PER CORRETTO ENCODING (ACCENTI)
# ---------------------------------------------------------
def ripara_testo(testo):
    if not isinstance(testo, str):
        return str(testo)
    for enc_from, enc_to in [('latin1', 'utf-8'), ('cp1252', 'utf-8')]:
        try:
            return testo.encode(enc_from).decode(enc_to)
        except Exception:
            continue
    return testo

# ---------------------------------------------------------
# 3. CARICAMENTO E GENERAZIONE DATI CON PARAMETRI AVANZATI
# ---------------------------------------------------------
@st.cache_data
def load_data():
    df_raw = None
    for enc in ['utf-8', 'latin1', 'cp1252']:
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
                if x in [
                    "NAN",
                    "NONE",
                    "",
                    "SVINCOLATO",
                    "LIBERO",
                    "#N/D",
                    "#RIF!",
                    "0",
                ]
                or x.startswith("=")
                else x
            )
        )
    else:
        df["Proprietario_Iniziale"] = "LIBERO"

    df["Stato"] = df["Proprietario_Iniziale"]

    def assign_tier_and_contract(quot):
        if quot >= 25:
            return pd.Series(["Top", "Giugno 2029"])
        elif quot >= 15:
            return pd.Series(["Semitop", "Giugno 2029"])
        elif quot >= 8:
            return pd.Series(["Titolare", "Giugno 2029"])
        else:
            return pd.Series(["Scommessa", "Giugno 2030"])

    df[["Tier", "Scadenza_Contratto"]] = df["Quotazione"].apply(
        assign_tier_and_contract
    )

    def genera_parametri_avanzati(row):
        quot = row["Quotazione"]
        ruolo = row["Ruolo"]
        
        if ruolo == "A":
            xg = round(max(0.1, quot * 0.035), 2)
            xa = round(max(0.05, quot * 0.015), 2)
            malus_cartellini = "Medio" if quot < 20 else "Basso"
        elif ruolo == "C":
            xg = round(max(0.05, quot * 0.02), 2)
            xa = round(max(0.08, quot * 0.025), 2)
            malus_cartellini = "Medio-Alto"
        elif ruolo == "D":
            xg = round(max(0.02, quot * 0.01), 2)
            xa = round(max(0.03, quot * 0.015), 2)
            malus_cartellini = "Alto"
        else:
            xg, xa = 0.0, 0.0
            malus_cartellini = "Basso"

        if quot >= 25:
            return pd.Series([0.95, 36, 8.8, "Basso (Affidabile)", xg, xa, malus_cartellini, "Basso"])
        elif quot >= 15:
            return pd.Series([0.82, 32, 7.8, "Medio-Basso", xg, xa, malus_cartellini, "Medio"])
        elif quot >= 8:
            return pd.Series([0.65, 27, 6.8, "Medio", xg, xa, malus_cartellini, "Medio"])
        return pd.Series([0.40, 20, 5.8, "Variabile / Rischio", xg, xa, malus_cartellini, "Alto"])

    df[
        [
            "Percentuale_Titolarita",
            "Partite_Attese",
            "Indice_Continuita",
            "Rischio_Infortunio",
            "xG_90",
            "xA_90",
            "Indice_Cartellini",
            "Rischio_Turnover"
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
        "PECU",
        "SQUADRA_3",
        "SQUADRA_4",
        "SQUADRA_5",
    ]

PARTECIPANTI_LEGA = sorted(lista_proprietari_csv)
if "BARDO" not in PARTECIPANTI_LEGA:
    PARTECIPANTI_LEGA.append("BARDO")
    PARTECIPANTI_LEGA = sorted(PARTECIPANTI_LEGA)

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
                "Valore_Attuale": int(r["Quotazione"]),
                "Scadenza": str(r["Scadenza_Contratto"]),
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

# Slot target per ruolo (P: 3, D: 8, C: 8, A: 6 = 25 totali)
SLOT_TARGET_RUOLI = {"P": 3, "D": 8, "C": 8, "A": 6}
SLOT_TARGET_TOTALE = sum(SLOT_TARGET_RUOLI.values())

# ---------------------------------------------------------
# 4. SIDEBAR: PANNELLO DI CONTROLLO CON MENU A TENDINA & RIEPILOGO LEGA
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

giocatori_mancanti_corrente = max(0, SLOT_TARGET_TOTALE - len(rosa_corrente))

st.sidebar.metric(
    f"Budget Rimanente ({fanta_allenatore_attivo})",
    f"{budget_rimanente_corrente} cr",
    f"Mancanti: {giocatori_mancanti_corrente} giocatori"
)

# --- RIEPILOGO SOLDI RIMANENTI E GIOCATORI MANCANTI PER RUOLO (MENU A SINISTRA) ---
with st.sidebar.expander("📊 Riepilogo Soldi & Mancanti per Ruolo"):
    for part in PARTECIPANTI_LEGA:
        r_part = rose_lega_dict.get(part, [])
        spesa_part = sum(item.get("Prezzo_Acquisto", 1) for item in r_part)
        budget_rim_part = st.session_state.get("budget_iniziale", 500) + extra_budget_dict.get(part, 0) - spesa_part
        
        presidi_ruolo = {r: sum(1 for g in r_part if g["Ruolo"] == r) for r in SLOT_TARGET_RUOLI}
        mancanti_ruoli = {r: max(0, SLOT_TARGET_RUOLI[r] - presidi_ruolo[r]) for r in SLOT_TARGET_RUOLI}
        tot_mancanti = sum(mancanti_ruoli.values())
        
        st.markdown(f"**{part}** (Rimasti: **{budget_rim_part} cr** | Tot. Mancanti: **{tot_mancanti}**)")
        st.text(f"  • Portieri (P): {mancanti_ruoli['P']} mancanti")
        st.text(f"  • Difensori (D): {mancanti_ruoli['D']} mancanti")
        st.text(f"  • Centrocampisti (C): {mancanti_ruoli['C']} mancanti")
        st.text(f"  • Attaccanti (A): {mancanti_ruoli['A']} mancanti")
        st.markdown("---")

# --- MENU A TENDINA NELLA SIDEBAR (ORDINE E PULIZIA) ---
st.sidebar.subheader("🛠️ Strumenti di Gestione")

with st.sidebar.expander("💾 Salvataggio & Caricamento JSON"):
    stato_salva = {
        "budget_iniziale": st.session_state.get("budget_iniziale", 500),
        "rose_lega": rose_lega_dict,
        "extra_budget": extra_budget_dict,
        "prestiti_lega": st.session_state.get("prestiti_lega", []),
        "stati_giocatori": df[["Nome", "Stato"]]
        .set_index("Nome")["Stato"]
        .to_dict(),
    }
    json_data = json.dumps(stato_salva, indent=4, ensure_ascii=False)
    st.download_button(
        label="📥 Salva Stato Lega (JSON)",
        data=json_data,
        file_name="fanta_lega_backup.json",
        mime="application/json",
    )

    uploaded_file = st.file_uploader(
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
                st.session_state.prestiti_lega = loaded_state.get("prestiti_lega", [])

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

with st.sidebar.expander("📊 Importa Rose da Listone"):
    uploaded_excel = st.file_uploader(
        "Carica file listone rose", type=["xlsx", "xls", "csv", "txt"], key="excel_rose_uploader"
    )

    if uploaded_excel is not None:
        excel_identifier = f"{uploaded_excel.name}_{uploaded_excel.size}"
        if st.session_state.get("last_uploaded_excel") != excel_identifier:
            try:
                file_extension = uploaded_excel.name.split('.')[-1].lower()
                
                if file_extension == 'txt':
                    content_bytes = uploaded_excel.read()
                    text_content = None
                    for enc in ['utf-8', 'cp1252', 'latin1', 'iso-8859-1']:
                        try:
                            text_content = content_bytes.decode(enc)
                            break
                        except:
                            continue
                    if text_content is None:
                        text_content = content_bytes.decode('latin1', errors='ignore')
                    
                    text_content = ripara_testo(text_content)
                    lines = [line.strip() for line in text_content.splitlines() if line.strip()]
                    if any(',' in line or '\t' in line or ';' in line for line in lines[:3]):
                        sep_char = '\t' if '\t' in lines[0] else (';' if ';' in lines[0] else ',')
                        df_excel = pd.read_csv(io.StringIO(text_content), sep=sep_char, dtype=str)
                    else:
                        df_excel = pd.DataFrame({'Calciatore': lines})
                elif file_extension in ['xlsx', 'xls', 'ods']:
                    df_excel = pd.read_excel(uploaded_excel, dtype=str)
                else:
                    uploaded_excel.seek(0)
                    df_excel = None
                    for s in [',', ';', '\t', '|']:
                        for enc in ['utf-8', 'latin1', 'cp1252']:
                            try:
                                uploaded_excel.seek(0)
                                df_test = pd.read_csv(uploaded_excel, encoding=enc, sep=s, dtype=str, on_bad_lines='skip')
                                if df_test.shape[1] > 1:
                                    df_excel = df_test
                                    break
                            except:
                                continue
                        if df_excel is not None:
                            break
                    if df_excel is None:
                        uploaded_excel.seek(0)
                        df_excel = pd.read_csv(uploaded_excel, encoding='latin1', dtype=str, on_bad_lines='skip')

                df_excel.columns = [str(c).strip().lower() for c in df_excel.columns]
                
                map_colonne = {}
                for col in df_excel.columns:
                    if any(k in col for k in ["calciatore", "giocatore", "nome", "player"]):
                        map_colonne["calciatore"] = col
                    elif any(k in col for k in ["ruolo"]):
                        map_colonne["ruolo"] = col
                    elif any(k in col for k in ["squadra", "team"]):
                        map_colonne["squadra"] = col
                    elif any(k in col for k in ["quotazione", "prezzo", "valore"]):
                        map_colonne["quotazione"] = col
                    elif any(k in col for k in ["proprietario", "prop", "squadra_fantacalcio"]):
                        map_colonne["proprietario"] = col

                if "calciatore" not in map_colonne and len(df_excel.columns) > 0:
                    map_colonne["calciatore"] = df_excel.columns[0]

                if "calciatore" in map_colonne:
                    new_rose = {}
                    df_temp = st.session_state.df_giocatori.copy()
                    df_temp["Stato"] = "LIBERO"
                    
                    master_dict = {str(row["Nome"]).strip().lower(): row for _, row in df_temp.iterrows()}
                    
                    for _, row in df_excel.iterrows():
                        nome_g = ripara_testo(str(row[map_colonne["calciatore"]]).strip())
                        if not nome_g or nome_g.lower() in ["nan", "none", "", "nat", "inf"]:
                            continue
                            
                        nome_g_lower = nome_g.lower()
                        
                        prop_val = "LIBERO"
                        if "proprietario" in map_colonne:
                            p_raw = ripara_testo(str(row[map_colonne["proprietario"]]).strip().upper())
                            if p_raw and p_raw not in ["NAN", "NONE", "", "SVINCOLATO", "LIBERO", "0", "#N/D", "#RIF!"] and not p_raw.startswith("="):
                                prop_val = p_raw
                                if prop_val not in PARTECIPANTI_LEGA:
                                    PARTECIPANTI_LEGA.append(prop_val)
                        
                        prezzo_val = 1
                        if "quotazione" in map_colonne:
                            try:
                                prezzo_val = int(float(str(row[map_colonne["quotazione"]]).replace(',', '.')))
                            except:
                                pass

                        if nome_g_lower in master_dict:
                            g_info = master_dict[nome_g_lower]
                            ruolo_g = str(g_info["Ruolo"])
                            squadra_g = ripara_testo(str(g_info["Squadra"]))
                            quot_g = int(g_info["Quotazione"])
                        else:
                            ruolo_g = ripara_testo(str(row[map_colonne["ruolo"]])) if "ruolo" in map_colonne and map_colonne["ruolo"] in row else "C"
                            squadra_g = ripara_testo(str(row[map_colonne["squadra"]])) if "squadra" in map_colonne and map_colonne["squadra"] in row else "N/D"
                            quot_g = prezzo_val

                        if prop_val != "LIBERO":
                            if prop_val not in new_rose:
                                new_rose[prop_val] = []
                            
                            if not any(str(g["Nome"]).strip().lower() == nome_g_lower for g in new_rose[prop_val]):
                                new_rose[prop_val].append({
                                    "Nome": nome_g,
                                    "Ruolo": ruolo_g,
                                    "Squadra": squadra_g,
                                    "Prezzo_Acquisto": prezzo_val,
                                    "Valore_Attuale": quot_g,
                                    "Scadenza": "Giugno 2030",
                                })
                                
                            idx_match = df_temp[df_temp["Nome"].astype(str).str.strip().str.lower() == nome_g_lower].index
                            if not idx_match.empty:
                                df_temp.at[idx_match[0], "Stato"] = prop_val

                    st.session_state.rose_lega = new_rose
                    st.session_state.df_giocatori = df_temp
                    st.session_state.last_uploaded_excel = excel_identifier
                    st.sidebar.success(f"Rosa caricata con successo! Trovati {len(df_excel)} elementi.")
                    st.rerun()
                else:
                    st.sidebar.error("Impossibile individuare la colonna del nome/giocatore nel file.")
            except Exception as e:
                st.sidebar.error(f"Errore durante l'estrazione delle rose dal file: {e}")

with st.sidebar.expander("📅 Modifica Scadenze Contratti"):
    squadra_mod_scadenza = st.selectbox("Seleziona squadra:", PARTECIPANTI_LEGA, key="mod_scad_sq")
    rosa_mod_scadenza = st.session_state.get("rose_lega", {}).get(squadra_mod_scadenza, [])

    if rosa_mod_scadenza:
        nomi_mod_scadenza = [str(g["Nome"]) for g in rosa_mod_scadenza]
        giocatore_da_aggiornare = st.selectbox("Seleziona giocatore:", nomi_mod_scadenza, key="mod_scad_gioc")
        
        gioc_obj_corrente = next((g for g in rosa_mod_scadenza if str(g["Nome"]).strip().lower() == str(giocatore_da_aggiornare).strip().lower()), None)
        scadenza_attuale_val = str(gioc_obj_corrente.get("Scadenza", "Giugno 2030")) if gioc_obj_corrente else "Giugno 2030"
        
        col_scad1, col_scad2 = st.columns(2)
        with col_scad1:
            mesi_disponibili = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
            mese_default = next((m for m in mesi_disponibili if m.lower() in scadenza_attuale_val.lower()), "Giugno")
            idx_mese = mesi_disponibili.index(mese_default) if mese_default in mesi_disponibili else 5
            nuovo_mese = st.selectbox("Mese:", mesi_disponibili, index=idx_mese, key="select_nuovo_mese")
        
        with col_scad2:
            anni_disponibili = [2026, 2027, 2028, 2029, 2030, 2031, 2032, 2033, 2034, 2035]
            anno_default = next((a for a in anni_disponibili if str(a) in scadenza_attuale_val), 2030)
            idx_anno = anni_disponibili.index(anno_default) if anno_default in anni_disponibili else 4
            nuovo_anno = st.selectbox("Anno:", anni_disponibili, index=idx_anno, key="select_nuovo_anno")
        
        scadenza_formattata = f"{nuovo_mese} {nuovo_anno}"
        
        if st.button("💾 Aggiorna Scadenza", key="btn_aggiorna_scad"):
            for g in st.session_state.rose_lega[squadra_mod_scadenza]:
                if str(g["Nome"]).strip().lower() == str(giocatore_da_aggiornare).strip().lower():
                    g["Scadenza"] = scadenza_formattata
                    break
            st.success(f"✅ Contratto aggiornato a **{scadenza_formattata}**!")
            st.rerun()
    else:
        st.info("Rosa vuota.")

with st.sidebar.expander("📋 Esplora Rose & Valori"):
    squadra_da_esplorare = st.selectbox(
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
        st.dataframe(
            pd.DataFrame(df_side_list), use_container_width=True, hide_index=True
        )
    else:
        st.info("Rosa vuota.")

# ---------------------------------------------------------
# 5. DASHBOARD PRINCIPALE: ASTA LIVE & PARAMETRI AVANZATI
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

    quotazione_listone = int(g_data["Quotazione"])

    col1, col2, col3, col4 = st.columns(4)
    col1.metric(
        "Ruolo & Squadra",
        f"{g_data['Ruolo']} - {g_data['Squadra']}",
        f"Tier: {g_data['Tier']}",
    )
    col2.metric("FantaMedia Stimata", f"{g_data['FantaMedia_Stimata']} FM")
    col3.metric("Rigorista / Piazzati", f"{g_data['Status_Piazzati']}")
    col4.metric(
        "🏷️ Prezzo Partita (Quotazione Listone)", f"{quotazione_listone} cr"
    )

    with st.expander("📊 Metriche Avanzate & Dettagli Realistici"):
        m_col1, m_col2, m_col3, m_col4 = st.columns(4)
        m_col1.metric("xG / 90 min", f"{g_data['xG_90']}")
        m_col2.metric("xA / 90 min", f"{g_data['xA_90']}")
        m_col3.metric("Rischio Cartellini", f"{g_data['Indice_Cartellini']}")
        m_col4.metric("Rischio Infortunio", f"{g_data['Rischio_Infortunio']}")

    with st.expander("⚖️ Confronta con la tua Rosa (Consiglio per alzare la media)", expanded=True):
        rosa_allenatore_attuale = st.session_state.get("rose_lega", {}).get(fanta_allenatore_attivo, [])
        if rosa_allenatore_attuale:
            st.write(f"Confronto di **{g_data['Nome']}** ({g_data['Ruolo']} - FM: **{g_data['FantaMedia_Stimata']}**) con i tuoi giocatori in rosa dello stesso ruolo:")
            
            giocatori_stesso_ruolo = [g for g in rosa_allenatore_attuale if g["Ruolo"] == g_data["Ruolo"]]
            
            if giocatori_stesso_ruolo:
                nomi_stesso_ruolo = [str(g["Nome"]) for g in giocatori_stesso_ruolo]
                giocatore_confronto_sel = st.selectbox("Seleziona giocatore in rosa da confrontare:", nomi_stesso_ruolo, key="select_confronto_rosa")
                
                g_rosa_obj = next((g for g in giocatori_stesso_ruolo if str(g["Nome"]).strip().lower() == str(giocatore_confronto_sel).strip().lower()), None)
                if g_rosa_obj:
                    df_rosa_match = df[df["Nome"].astype(str).str.strip().str.lower() == str(giocatore_confronto_sel).strip().lower()]
                    fm_rosa = df_rosa_match["FantaMedia_Stimata"].values[0] if not df_rosa_match.empty else 6.0
                    
                    c_col1, c_col2 = st.columns(2)
                    c_col1.metric(f"Giocatore in Asta: {g_data['Nome']}", f"{g_data['FantaMedia_Stimata']} FM", f"Quot: {quotazione_listone} cr")
                    c_col2.metric(f"In Rosa: {giocatore_confronto_sel}", f"{fm_rosa} FM")
                    
                    diff_fm = round(g_data['FantaMedia_Stimata'] - fm_rosa, 2)
                    if diff_fm > 0:
                        st.success(f"📈 **Consiglio:** Acquistare **{g_data['Nome']}** e sostituirlo/alternarlo a **{giocatore_confronto_sel}** **alzerà la media** della tua rosa di **+{diff_fm} FM** in questo ruolo!")
                    elif diff_fm < 0:
                        st.warning(f"📉 **Attenzione:** **{g_data['Nome']}** ha una FantaMedia stimata inferiore rispetto a **{giocatore_confronto_sel}** ({diff_fm} FM). Prenderlo non alzerà la media in questo slot.")
                    else:
                        st.info(f"⚖️ **Neutro:** I due giocatori hanno esattamente la stessa FantaMedia stimata ({fm_rosa} FM).")
            else:
                st.info(f"Non hai ancora giocatori nel ruolo **{g_data['Ruolo']}** nella tua rosa. Acquistare questo giocatore completerà lo slot!")
        else:
            st.info("La tua rosa è attualmente vuota, questo sarà il tuo primo acquisto per il ruolo!")

    with st.form("form_aggiudicazione"):
        st.write("Registra Acquisto Asta")
        col_A, col_B = st.columns(2)
        with col_A:
            prezzo_aggiudicazione = st.number_input(
                "Prezzo di chiusura asta (crediti):",
                min_value=1,
                value=max(1, quotazione_listone),
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
            
            current_rose[vincitore_asta].append({
                "Nome": str(g_data["Nome"]),
                "Ruolo": str(g_data["Ruolo"]),
                "Squadra": str(g_data["Squadra"]),
                "Prezzo_Acquisto": int(prezzo_aggiudicazione),
                "Valore_Attuale": int(g_data["Quotazione"]),
                "Scadenza": "Giugno 2030",
            })
            st.session_state.rose_lega = current_rose
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
# 6. SEZIONE SCOUTING AVANZATO & FILTRI (CON CONSIGLI 2 PER RUOLO)
# ---------------------------------------------------------
st.divider()
st.subheader("🎯 Scout di Rendimento & Consigli Consigliati (Top 2 per Ruolo)")

st.markdown("### 🌟 Giocatori Consigliati (Liberi)")
col_cons_d, col_cons_c, col_cons_a = st.columns(3)

with col_cons_d:
    st.markdown("#### 🛡️ Difensori Top")
    df_cons_d = df[(df["Stato"] == "LIBERO") & (df["Ruolo"] == "D")].sort_values(by="FantaMedia_Stimata", ascending=False).head(2)
    if not df_cons_d.empty:
        for _, row_g in df_cons_d.iterrows():
            st.info(f"**{row_g['Nome']}** ({row_g['Squadra']})\n- FM Stimata: **{row_g['FantaMedia_Stimata']}**\n- Quotazione: {row_g['Quotazione']} cr")
    else:
        st.write("Nessun difensore libero disponibile.")

with col_cons_c:
    st.markdown("#### ⚙️ Centrocampisti Top")
    df_cons_c = df[(df["Stato"] == "LIBERO") & (df["Ruolo"] == "C")].sort_values(by="FantaMedia_Stimata", ascending=False).head(2)
    if not df_cons_c.empty:
        for _, row_g in df_cons_c.iterrows():
            st.info(f"**{row_g['Nome']}** ({row_g['Squadra']})\n- FM Stimata: **{row_g['FantaMedia_Stimata']}**\n- Quotazione: {row_g['Quotazione']} cr")
    else:
        st.write("Nessun centrocampista libero disponibile.")

with col_cons_a:
    st.markdown("#### ⚽ Attaccanti Top")
    df_cons_a = df[(df["Stato"] == "LIBERO") & (df["Ruolo"] == "A")].sort_values(by="FantaMedia_Stimata", ascending=False).head(2)
    if not df_cons_a.empty:
        for _, row_g in df_cons_a.iterrows():
            st.info(f"**{row_g['Nome']}** ({row_g['Squadra']})\n- FM Stimata: **{row_g['FantaMedia_Stimata']}**\n- Quotazione: {row_g['Quotazione']} cr")
    else:
        st.write("Nessun attaccante libero disponibile.")

st.divider()
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
        "xG_90",
        "xA_90",
        "Status_Piazzati",
        "Indice_Continuita",
        "Rischio_Infortunio",
        "Valore_Atteso",
    ]],
    use_container_width=True,
    hide_index=True,
)

# ---------------------------------------------------------
# 7. SEZIONE PRINCIPALE ORGANIZZATA CON MENU A TENDINA (EXPANDER)
# ---------------------------------------------------------
st.divider()
st.subheader("📋 Gestione Avanzata & Analisi Lega")

with st.expander("🔮 Analisi Predittiva & Consigli per Bardo"):
    punteggi_squadre = {}
    for part in PARTECIPANTI_LEGA:
        rosa_part = st.session_state.rose_lega.get(part, [])
        if rosa_part:
            nomi_rosa = [str(g["Nome"]).strip().lower() for g in rosa_part]
            sub_df = df[df["Nome"].astype(str).str.strip().str.lower().isin(nomi_rosa)]
            if not sub_df.empty:
                fm_totale = sub_df["FantaMedia_Stimata"].sum()
                val_atteso_totale = sub_df["Valore_Atteso"].sum()
                forza_complessiva = (fm_totale * 1.5) + (val_atteso_totale * 0.8)
            else:
                forza_complessiva = 0.0
        else:
            forza_complessiva = 0.0
        punteggi_squadre[part] = forza_complessiva

    squadra_piu_forte = max(punteggi_squadre, key=punteggi_squadre.get) if punteggi_squadre and max(punteggi_squadre.values()) > 0 else "Nessuna (Rose vuote)"

    col_pred1, col_pred2 = st.columns(2)

    with col_pred1:
        st.markdown("### 🏆 Previsione Squadra Più Forte")
        st.info(f"Basandosi sulle rose attuali, l'algoritmo predice che la squadra più forte della lega è: **{squadra_piu_forte}**!")
        
        df_ranking = pd.DataFrame(list(punteggi_squadre.items()), columns=["Squadra", "Indice di Forza"]).sort_values(by="Indice di Forza", ascending=False)
        df_ranking["Indice di Forza"] = df_ranking["Indice di Forza"].round(1)
        st.dataframe(df_ranking, use_container_width=True, hide_index=True)

    with col_pred2:
        st.markdown("### 🎸 Stato Rosa Bardo")
        rosa_bardo = st.session_state.rose_lega.get("BARDO", [])
        
        if rosa_bardo:
            nomi_bardo = [str(g["Nome"]).strip().lower() for g in rosa_bardo]
            df_bardo = df[df["Nome"].astype(str).str.strip().str.lower().isin(nomi_bardo)]
            
            if not df_bardo.empty:
                fm_media_bardo = df_bardo["FantaMedia_Stimata"].mean()
                st.metric("FantaMedia Media Attuale (Bardo)", f"{fm_media_bardo:.2f} FM")
                
                ruoli_bardo = df_bardo["Ruolo"].value_counts()
                st.write("Composizione Rosa di Bardo:")
                for r, count in ruoli_bardo.items():
                    st.text(f"- {r}: {count} giocatori")
            else:
                st.warning("La rosa di Bardo non contiene giocatori registrati nel listone o è vuota.")
        else:
            st.warning("La rosa di Bardo è attualmente vuota. Inizia ad acquistare giocatori!")

with st.expander("🔄 Gestione Rosa & Svincoli (Rendi Libero)"):
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

with st.expander("🤝 Scambi Diretti & Multipli tra Società (Con Soldi & Anteprima Forza)"):
    col_sc1, col_sc2 = st.columns(2)
    with col_sc1:
        societa_a = st.selectbox("Società A:", PARTECIPANTI_LEGA, key="scambio_soc_a")
    with col_sc2:
        societa_b = st.selectbox("Società B:", [p for p in PARTECIPANTI_LEGA if p != societa_a], key="scambio_soc_b")

    rosa_soc_a = st.session_state.get("rose_lega", {}).get(societa_a, [])
    rosa_soc_b = st.session_state.get("rose_lega", {}).get(societa_b, [])

    if rosa_soc_a or rosa_soc_b:
        st.markdown("#### 📋 Seleziona i giocatori oggetto dello scambio")
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            giocatori_da_a = st.multiselect(f"Giocatori ceduti da **{societa_a}**:", [g["Nome"] for g in rosa_soc_a], key="scambio_mult_a")
        with col_g2:
            giocatori_da_b = st.multiselect(f"Giocatori ceduti da **{societa_b}**:", [g["Nome"] for g in rosa_soc_b], key="scambio_mult_b")

        st.markdown("#### 💰 Aggiungi Crediti allo Scambio")
        col_soldi1, col_soldi2 = st.columns(2)
        with col_soldi1:
            soldi_da_a = st.number_input(f"Crediti aggiuntivi offerti da **{societa_a}** a {societa_b}:", min_value=0, value=0, step=1, key="soldi_da_a_input")
        with col_soldi2:
            soldi_da_b = st.number_input(f"Crediti aggiuntivi offerti da **{societa_b}** a {societa_a}:", min_value=0, value=0, step=1, key="soldi_da_b_input")

        sub_df_a = df[df["Nome"].astype(str).str.strip().str.lower().isin([str(x).strip().lower() for x in giocatori_da_a])]
        sub_df_b = df[df["Nome"].astype(str).str.strip().str.lower().isin([str(x).strip().lower() for x in giocatori_da_b])]

        tot_fm_a = sub_df_a["FantaMedia_Stimata"].sum() if not sub_df_a.empty else 0.0
        tot_fm_b = sub_df_b["FantaMedia_Stimata"].sum() if not sub_df_b.empty else 0.0

        st.markdown("---")
        st.markdown("### 📊 Anteprima Bilancio Scambio (Giocatori & Crediti)")
        prev_col1, prev_col2 = st.columns(2)
        prev_col1.metric(f"Pacchetto {societa_a}", f"{tot_fm_a:.2f} FM", f"+ {soldi_da_a} crediti offerti")
        prev_col2.metric(f"Pacchetto {societa_b}", f"{tot_fm_b:.2f} FM", f"+ {soldi_da_b} crediti offerti")

        if tot_fm_a > tot_fm_b:
            diff_scambio = round(tot_fm_a - tot_fm_b, 2)
            st.warning(f"⚠️ **Verifica:** La società **{societa_b}** riceve giocatori con FantaMedia superiore (+{diff_scambio} FM).")
        elif tot_fm_b > tot_fm_a:
            diff_scambio = round(tot_fm_b - tot_fm_a, 2)
            st.warning(f"⚠️ **Verifica:** La società **{societa_a}** riceve giocatori con FantaMedia superiore (+{diff_scambio} FM).")
        else:
            st.success("⚖️ I pacchetti giocatori si equivalgono a livello di FantaMedia!")

        st.markdown("---")
        if st.button("⚖️ Conferma ed Esegui Scambio con Crediti", key="btn_esegui_scambio_multiplo"):
            current_rose = st.session_state.get("rose_lega", {})
            current_extra = st.session_state.get("extra_budget", {})

            oggetti_a = [g for g in rosa_soc_a if str(g["Nome"]).strip().lower() in [str(x).strip().lower() for x in giocatori_da_a]]
            oggetti_b = [g for g in rosa_soc_b if str(g["Nome"]).strip().lower() in [str(x).strip().lower() for x in giocatori_da_b]]

            current_rose[societa_a] = [g for g in current_rose[societa_a] if str(g["Nome"]).strip().lower() not in [str(x).strip().lower() for x in giocatori_da_a]]
            current_rose[societa_b] = [g for g in current_rose[societa_b] if str(g["Nome"]).strip().lower() not in [str(x).strip().lower() for x in giocatori_da_b]]

            current_rose[societa_a].extend(oggetti_b)
            current_rose[societa_b].extend(oggetti_a)

            # Aggiornamento budget extra per i crediti trasferiti nello scambio
            current_extra[societa_a] = current_extra.get(societa_a, 0) - soldi_da_a + soldi_da_b
            current_extra[societa_b] = current_extra.get(societa_b, 0) - soldi_da_b + soldi_da_a

            st.session_state.rose_lega = current_rose
            st.session_state.extra_budget = current_extra

            for nome_g in giocatori_da_a:
                idx_g = df[df["Nome"].astype(str).str.strip().str.lower() == str(nome_g).strip().lower()].index
                if not idx_g.empty:
                    st.session_state.df_giocatori.at[idx_g[0], "Stato"] = societa_b

            for nome_g in giocatori_da_b:
                idx_g = df[df["Nome"].astype(str).str.strip().str.lower() == str(nome_g).strip().lower()].index
                if not idx_g.empty:
                    st.session_state.df_giocatori.at[idx_g[0], "Stato"] = societa_a

            st.success(f"✅ Scambio completato con successo tra **{societa_a}** e **{societa_b}** (inclusi i conguagli in crediti)!")
            st.rerun()
    else:
        st.info("Impossibile effettuare scambi: le rose selezionate sono vuote.")

with st.expander("🤝 Gestione Prestiti tra Squadre (Durata, Rinnovo & Interruzione)"):
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

        col_dur1, col_dur2 = st.columns(2)
        with col_dur1:
            giocatore_prestito = st.selectbox(
                "Seleziona il giocatore da dare in prestito:",
                nomi_cedente,
                key="giocatore_in_prestito_sel",
            )
        with col_dur2:
            durata_prestito = st.selectbox(
                "Durata del prestito:",
                ["6 mesi", "1 anno"],
                key="durata_prestito_sel"
            )

        if st.button("🔄 Registra Nuovo Prestito", key="btn_prestito"):
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

                st.session_state.prestiti_lega.append({
                    "Giocatore": giocatore_obj["Nome"],
                    "Cedente": squadra_cedente,
                    "Ricevente": squadra_ricevente,
                    "Durata": durata_prestito
                })

                match_idx = st.session_state.df_giocatori[
                    st.session_state.df_giocatori["Nome"].astype(str).str.strip().str.lower()
                    == str(giocatore_prestito).strip().lower()
                ].index
                if not match_idx.empty:
                    for idx_df in match_idx:
                        st.session_state.df_giocatori.at[idx_df, "Stato"] = squadra_ricevente

                st.success(f"✅ Prestito di **{giocatore_prestito}** da **{squadra_cedente}** a **{squadra_ricevente}** registrato con successo!")
                st.rerun()
    else:
        st.info("Nessun giocatore disponibile per il prestito nella squadra selezionata.")

    if st.session_state.prestiti_lega:
        st.markdown("### 📋 Prestiti Attivi in Corso")
        for i, prestito in enumerate(st.session_state.prestiti_lega):
            cols_pr = st.columns([3, 2])
            cols_pr[0].write(f"**{prestito['Giocatore']}** ({prestito['Cedente']} ➡️ {prestito['Ricevente']} | {prestito['Durata']})")
            if cols_pr[1].button("↩️ Restituisci / Interrompi", key=f"restituisci_prestito_{i}"):
                gioc_nome = prestito["Giocatore"]
                sq_ced = prestito["Cedente"]
                sq_ric = prestito["Ricevente"]
                
                current_rose = st.session_state.get("rose_lega", {})
                gioc_obj = None
                if sq_ric in current_rose:
                    current_rose[sq_ric] = [
                        g for g in current_rose[sq_ric]
                        if str(g["Nome"]).strip().lower() != str(gioc_nome).strip().lower()
                    ]
                    for g in current_rose.get(sq_ric, []):
                        if str(g["Nome"]).strip().lower() == str(gioc_nome).strip().lower():
                            gioc_obj = g
                            break
                
                if not gioc_obj:
                    match_row = st.session_state.df_giocatori[
                        st.session_state.df_giocatori["Nome"].astype(str).str.strip().str.lower() == str(gioc_nome).strip().lower()
                    ]
                    if not match_row.empty:
                        r = match_row.iloc[0]
                        gioc_obj = {
                            "Nome": str(r["Nome"]),
                            "Ruolo": str(r["Ruolo"]),
                            "Squadra": str(r["Squadra"]),
                            "Prezzo_Acquisto": int(r["Quotazione"]),
                            "Valore_Attuale": int(r["Quotazione"]),
                            "Scadenza": "Giugno 2030",
                        }

                if gioc_obj:
                    if sq_ced not in current_rose:
                        current_rose[sq_ced] = []
                    current_rose[sq_ced].append(gioc_obj)

                st.session_state.prestiti_lega.pop(i)
                st.success(f"✅ Prestito interrotto: **{gioc_nome}** è tornato a **{sq_ced}**!")
                st.rerun()