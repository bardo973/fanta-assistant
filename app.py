import io
import json
import base64
import numpy as np
import pandas as pd
import streamlit as st

# ---------------------------------------------------------
# 1. CONFIGURAZIONE PAGINA E STATE MANAGEMENT SICURO
# ---------------------------------------------------------
st.set_page_config(
    page_title="FantaLega AI Advanced Predictor & Manager", layout="wide"
)

def set_custom_background():
    bg_url_or_file = "https://images.unsplash.com/photo-1508098682722-e99c43a406b2?q=80&w=1920&auto=format&fit=crop"
    
    css_code = f"""
    <style>
    [data-testid="stAppViewContainer"] {{
        background-image: linear-gradient(rgba(10, 14, 23, 0.85), rgba(10, 14, 23, 0.90)), url("{bg_url_or_file}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    [data-testid="stSidebar"] {{
        background-color: rgba(15, 20, 30, 0.95);
    }}
    </style>
    """
    st.markdown(css_code, unsafe_allow_html=True)

set_custom_background()

if "budget_iniziale" not in st.session_state:
    st.session_state.budget_iniziale = 500

# ---------------------------------------------------------
# 2. FUNZIONI DI SUPPORTO (Encoding, Scadenze e Safe Get)
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

def formatta_scadenza_csv(val_scad):
    if not isinstance(val_scad, str) or not val_scad.strip() or val_scad.strip().lower() in ["nan", "none", "", "n/d"]:
        return "Giugno 2030"
    
    v = val_scad.strip().lower()
    mesi_mappa = {
        "gen": "Gennaio", "feb": "Febbraio", "mar": "Marzo", "apr": "Aprile",
        "mag": "Maggio", "giu": "Giugno", "lug": "Luglio", "ago": "Agosto",
        "set": "Settembre", "ott": "Ottobre", "nov": "Novembre", "dic": "Dicembre"
    }
    
    for m_abbr, m_nome in mesi_mappa.items():
        if m_abbr in v:
            parti = v.replace("-", " ").replace("/", " ").split()
            anno_str = next((p for p in parti if len(p) >= 2 and p.isdigit()), "30")
            if len(anno_str) == 2:
                anno_str = "20" + anno_str
            return f"{m_nome} {anno_str}"
            
    return val_scad.strip().capitalize()

def safe_get(data, keys, default="N/D"):
    if data is None:
        return default
    if isinstance(keys, str):
        keys = [keys]
    for k in keys:
        if hasattr(data, "index") and k in data.index:
            val = data[k]
        elif isinstance(data, dict) and k in data:
            val = data[k]
        else:
            continue
        try:
            if pd.isna(val):
                continue
        except Exception:
            pass
        return val
    return default

def elabora_file_caricato(uploaded_file):
    file_extension = uploaded_file.name.split('.')[-1].lower()
    df_excel = None
    
    if file_extension == 'txt':
        content_bytes = uploaded_file.read()
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
        df_excel = pd.read_excel(uploaded_file, dtype=str)
    else:
        uploaded_file.seek(0)
        for s in [',', ';', '\t', '|']:
            for enc in ['utf-8', 'latin1', 'cp1252']:
                try:
                    uploaded_file.seek(0)
                    df_test = pd.read_csv(uploaded_file, encoding=enc, sep=s, dtype=str, on_bad_lines='skip')
                    if df_test.shape[1] > 1:
                        df_excel = df_test
                        break
                except:
                    continue
            if df_excel is not None:
                break
        if df_excel is None:
            uploaded_file.seek(0)
            df_excel = pd.read_csv(uploaded_file, encoding='latin1', dtype=str, on_bad_lines='skip')

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
        elif any(k in col for k in ["proprietario", "prop", "squadra_fantacalcio", "vincolato", "titolare_cartellino", "rosa"]):
            map_colonne["proprietario"] = col
        elif any(k in col for k in ["scad", "contratto", "scadenza"]):
            map_colonne["scadenza"] = col

    if "calciatore" not in map_colonne and len(df_excel.columns) > 0:
        map_colonne["calciatore"] = df_excel.columns[0]

    return df_excel, map_colonne

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

    df_raw.columns = [str(c).strip() for c in df_raw.columns]
    df_raw_cols_lower = {str(c).strip().lower(): c for c in df_raw.columns}

    df = pd.DataFrame()
    
    col_nome = next((df_raw_cols_lower[k] for k in ["calciatore", "giocatore", "nome", "player"] if k in df_raw_cols_lower), df_raw.columns[0])
    df["Nome"] = df_raw[col_nome].astype(str).str.strip().apply(ripara_testo)

    col_sq = next((df_raw_cols_lower[k] for k in ["squadra", "team"] if k in df_raw_cols_lower), None)
    df["Squadra"] = df_raw[col_sq].astype(str).str.strip().apply(ripara_testo) if col_sq else "N/D"

    col_ruolo = next((df_raw_cols_lower[k] for k in ["ruolo"] if k in df_raw_cols_lower), None)
    df["Ruolo"] = df_raw[col_ruolo].astype(str).str.strip() if col_ruolo else "C"

    col_quot = next((df_raw_cols_lower[k] for k in ["quotazione", "prezzo", "valore"] if k in df_raw_cols_lower), None)
    df["Quotazione"] = pd.to_numeric(df_raw[col_quot], errors="coerce").fillna(1) if col_quot else 1

    possibili_colonne_prop = [
        "proprietario", "prop", "squadra_fantacalcio", "vincolato", 
        "titolare_cartellino", "rosa", "proprietario_iniziale"
    ]
    colonna_trovata = next(
        (df_raw_cols_lower[k] for k in possibili_colonne_prop if k in df_raw_cols_lower), None
    )
    
    if not colonna_trovata:
        for col_l, col_orig in df_raw_cols_lower.items():
            if any(term in col_l for term in ["prop", "vincol", "rosa", "squadra_fanta", "titolare"]):
                colonna_trovata = col_orig
                break

    if colonna_trovata:
        df["Proprietario_Iniziale"] = (
            df_raw[colonna_trovata].astype(str).str.strip().str.upper().apply(ripara_testo)
        )
        df["Proprietario_Iniziale"] = df["Proprietario_Iniziale"].apply(
            lambda x: (
                "LIBERO"
                if x in [
                    "NAN", "NONE", "", "SVINCOLATO", "LIBERO", "#N/D", "#RIF!", "0", "NAT", "INF"
                ]
                or x.startswith("=")
                else x
            )
        )
    else:
        df["Proprietario_Iniziale"] = "LIBERO"

    df["Stato"] = df["Proprietario_Iniziale"]

    possibili_colonne_scad = ["scad", "scadenza", "contratto", "scadenza_contratto"]
    col_scad_trovata = next((df_raw_cols_lower[k] for k in possibili_colonne_scad if k in df_raw_cols_lower), None)
    if not col_scad_trovata:
        for col_l, col_orig in df_raw_cols_lower.items():
            if any(term in col_l for term in ["scad", "contratt"]):
                col_scad_trovata = col_orig
                break
    
    if col_scad_trovata:
        df["Scadenza_Contratto"] = df_raw[col_scad_trovata].astype(str).apply(formatta_scadenza_csv)
    else:
        def assign_default_contract(quot):
            if quot >= 25:
                return "Giugno 2029"
            elif quot >= 15:
                return "Giugno 2029"
            elif quot >= 8:
                return "Giugno 2029"
            else:
                return "Giugno 2030"
        df["Scadenza_Contratto"] = df["Quotazione"].apply(assign_default_contract)

    df["Tier"] = df["Quotazione"].apply(
        lambda q: "Top" if q >= 25 else ("Semitop" if q >= 15 else ("Titolare" if q >= 8 else "Scommessa"))
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
            p_tit, part_att, cont, r_inf, r_turn = 0.95, 36, 8.8, "Basso (Affidabile)", "Basso"
        elif quot >= 15:
            p_tit, part_att, cont, r_inf, r_turn = 0.82, 32, 7.8, "Medio-Basso", "Medio"
        elif quot >= 8:
            p_tit, part_att, cont, r_inf, r_turn = 0.65, 27, 6.8, "Medio", "Medio"
        else:
            p_tit, part_att, cont, r_inf, r_turn = 0.40, 20, 5.8, "Variabile / Rischio", "Alto"

        partite_titolare = int(round(part_att * p_tit))
        partite_subentrato = max(0, int(part_att - partite_titolare))

        return pd.Series([p_tit, part_att, cont, r_inf, xg, xa, malus_cartellini, r_turn, partite_titolare, partite_subentrato])

    df[
        [
            "Percentuale_Titolarita",
            "Partite_Attese",
            "Indice_Continuita",
            "Rischio_Infortunio",
            "xG_90",
            "xA_90",
            "Indice_Cartellini",
            "Rischio_Turnover",
            "Partite_Titolare",
            "Partite_Subentrato"
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

if "storico_scambi" not in st.session_state:
    st.session_state.storico_scambi = []

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

for p_squadra, lista_gioc in st.session_state.rose_lega.items():
    for g_item in lista_gioc:
        nome_g_corr = str(g_item["Nome"]).strip().lower()
        idx_match = df[df["Nome"].astype(str).str.strip().str.lower() == nome_g_corr].index
        if not idx_match.empty:
            df.at[idx_match[0], "Stato"] = p_squadra

SLOT_TARGET_RUOLI = {"P": 3, "D": 9, "C": 9, "A": 7}
SLOT_TARGET_TOTALE = sum(SLOT_TARGET_RUOLI.values())

# ---------------------------------------------------------
# 4. SIDEBAR: PANNELLO DI CONTROLLO & RIEPILOGO LEGA
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

with st.sidebar.expander("📊 Riepilogo Soldi & Mancanti per Ruolo"):
    for part in PARTECIPANTI_LEGA:
        r_part = rose_lega_dict.get(part, [])
        spesa_part = sum(item.get("Prezzo_Acquisto", 1) for item in r_part)
        budget_rim_part = st.session_state.get("budget_iniziale", 500) + extra_budget_dict.get(part, 0) - spesa_part
        
        presidi_ruolo = {r: sum(1 for g in r_part if g["Ruolo"] == r) for r in SLOT_TARGET_RUOLI}
        mancanti_ruoli = {r: max(0, SLOT_TARGET_RUOLI[r] - presidi_ruolo[r]) for r in SLOT_TARGET_RUOLI}
        tot_mancanti = sum(mancanti_ruoli.values())
        
        st.markdown(f"**{part}** (Rimasti: **{budget_rim_part} cr** | Tot. Mancanti: **{tot_mancanti}**)")
        
        for r_code, r_target in SLOT_TARGET_RUOLI.items():
            current_count = presidi_ruolo[r_code]
            progress_val = min(1.0, current_count / r_target) if r_target > 0 else 1.0
            r_label = {"P": "Portieri (P)", "D": "Difensori (D)", "C": "Centrocampisti (C)", "A": "Attaccanti (A)"}[r_code]
            st.text(f"  • {r_label}: {current_count}/{r_target}")
            st.progress(progress_val)
            
        st.markdown("---")

st.sidebar.subheader("🛠️ Strumenti di Gestione")

with st.sidebar.expander("💾 Salvataggio & Caricamento JSON"):
    stato_salva = {
        "budget_iniziale": st.session_state.get("budget_iniziale", 500),
        "rose_lega": rose_lega_dict,
        "extra_budget": extra_budget_dict,
        "prestiti_lega": st.session_state.get("prestiti_lega", []),
        "storico_scambi": st.session_state.get("storico_scambi", []),
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
                st.session_state.storico_scambi = loaded_state.get("storico_scambi", [])

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

with st.sidebar.expander("📊 Importa Rose, Vincolati & Scadenze"):
    uploaded_excel = st.file_uploader(
        "Carica file rose/vincolati", type=["xlsx", "xls", "csv", "txt"], key="excel_rose_uploader"
    )

    if uploaded_excel is not None:
        excel_identifier = f"{uploaded_excel.name}_{uploaded_excel.size}"
        if st.session_state.get("last_uploaded_excel") != excel_identifier:
            try:
                df_excel, map_colonne = elabora_file_caricato(uploaded_excel)

                if "calciatore" in map_colonne:
                    new_rose = st.session_state.get("rose_lega", {p: [] for p in PARTECIPANTI_LEGA})
                    df_temp = st.session_state.df_giocatori.copy()
                    
                    master_dict = {str(row["Nome"]).strip().lower(): row for _, row in df_temp.iterrows()}
                    
                    for _, row in df_excel.iterrows():
                        nome_g = ripara_testo(str(row[map_colonne["calciatore"]]).strip())
                        if not nome_g or nome_g.lower() in ["nan", "none", "", "nat", "inf"]:
                            continue
                            
                        nome_g_lower = nome_g.lower()
                        
                        prop_val = "LIBERO"
                        if "proprietario" in map_colonne and map_colonne["proprietario"] in row:
                            p_raw = ripara_testo(str(row[map_colonne["proprietario"]]).strip().upper())
                            if p_raw and p_raw not in ["NAN", "NONE", "", "SVINCOLATO", "LIBERO", "0", "#N/D", "#RIF!", "NAT", "INF"] and not p_raw.startswith("="):
                                prop_val = p_raw
                                if prop_val not in PARTECIPANTI_LEGA:
                                    PARTECIPANTI_LEGA.append(prop_val)
                                    if prop_val not in new_rose:
                                        new_rose[prop_val] = []
                        
                        prezzo_val = 1
                        if "quotazione" in map_colonne and map_colonne["quotazione"] in row:
                            try:
                                prezzo_val = int(float(str(row[map_colonne["quotazione"]]).replace(',', '.')))
                            except:
                                pass

                        scad_val = "Giugno 2030"
                        if "scadenza" in map_colonne and map_colonne["scadenza"] in row:
                            scad_raw = str(row[map_colonne["scadenza"]]).strip()
                            scad_val = formatta_scadenza_csv(scad_raw)

                        if nome_g_lower in master_dict:
                            g_info = master_dict[nome_g_lower]
                            ruolo_g = str(g_info["Ruolo"])
                            squadra_g = ripara_testo(str(g_info["Squadra"]))
                            quot_g = int(g_info["Quotazione"])
                            if scad_val == "Giugno 2030" and "Scadenza_Contratto" in g_info:
                                scad_val = str(g_info["Scadenza_Contratto"])
                        else:
                            ruolo_g = ripara_testo(str(row[map_colonne["ruolo"]])) if "ruolo" in map_colonne and map_colonne["ruolo"] in row else "C"
                            squadra_g = ripara_testo(str(row[map_colonne["squadra"]])) if "squadra" in map_colonne and map_colonne["squadra"] in row else "N/D"
                            quot_g = prezzo_val

                        if prop_val != "LIBERO":
                            if prop_val not in new_rose:
                                new_rose[prop_val] = []
                            
                            esistente = next((g for g in new_rose[prop_val] if str(g["Nome"]).strip().lower() == nome_g_lower), None)
                            if esistente:
                                esistente["Ruolo"] = ruolo_g
                                esistente["Squadra"] = squadra_g
                                esistente["Prezzo_Acquisto"] = prezzo_val
                                esistente["Scadenza"] = scad_val
                            else:
                                new_rose[prop_val].append({
                                    "Nome": nome_g,
                                    "Ruolo": ruolo_g,
                                    "Squadra": squadra_g,
                                    "Prezzo_Acquisto": prezzo_val,
                                    "Valore_Attuale": quot_g,
                                    "Scadenza": scad_val,
                                })
                                
                            idx_match = df_temp[df_temp["Nome"].astype(str).str.strip().str.lower() == nome_g_lower].index
                            if not idx_match.empty:
                                df_temp.at[idx_match[0], "Stato"] = prop_val
                                df_temp.at[idx_match[0], "Scadenza_Contratto"] = scad_val

                    st.session_state.rose_lega = new_rose
                    st.session_state.df_giocatori = df_temp
                    st.session_state.last_uploaded_excel = excel_identifier
                    st.sidebar.success(f"Rose, vincolati e scadenze aggiornati con successo!")
                    st.rerun()
                else:
                    st.sidebar.error("Impossibile individuare la colonna del nome/giocatore nel file.")
            except Exception as e:
                st.sidebar.error(f"Errore durante l'estrazione delle rose dal file: {e}")

with st.sidebar.expander("📋 Importa Listone Quotazioni (es. 2026/2027)"):
    st.info("Carica il nuovo listone per aggiungere i nuovi giocatori o aggiornare le quotazioni senza perdere le rose esistenti.")
    uploaded_listone = st.file_uploader(
        "Carica listone (es. quotazioni_fantacalcio_2026/2027)", type=["xlsx", "xls", "csv", "txt"], key="excel_listone_uploader"
    )

    if uploaded_listone is not None:
        listone_identifier = f"{uploaded_listone.name}_{uploaded_listone.size}"
        if st.session_state.get("last_uploaded_listone") != listone_identifier:
            try:
                df_listone_raw, map_col_listone = elabora_file_caricato(uploaded_listone)

                if "calciatore" in map_col_listone:
                    df_master = st.session_state.df_giocatori.copy()
                    
                    stati_attuali_map = {}
                    for p_squadra, lista_gioc in st.session_state.rose_lega.items():
                        for g in lista_gioc:
                            stati_attuali_map[str(g["Nome"]).strip().lower()] = {
                                "proprietario": p_squadra,
                                "prezzo": g.get("Prezzo_Acquisto", 1),
                                "scadenza": g.get("Scadenza", "Giugno 2030")
                            }
                    
                    for _, row in df_master.iterrows():
                        n_low = str(row["Nome"]).strip().lower()
                        if n_low not in stati_attuali_map and row["Stato"] != "LIBERO":
                            stati_attuali_map[n_low] = {
                                "proprietario": row["Stato"],
                                "prezzo": int(row["Quotazione"]),
                                "scadenza": str(row.get("Scadenza_Contratto", "Giugno 2030"))
                            }

                    nuovi_righe_master = []
                    nuove_rose = {p: list(st.session_state.rose_lega.get(p, [])) for p in PARTECIPANTI_LEGA}
                    
                    for _, row in df_listone_raw.iterrows():
                        nome_g = ripara_testo(str(row[map_col_listone["calciatore"]]).strip())
                        if not nome_g or nome_g.lower() in ["nan", "none", "", "nat", "inf"]:
                            continue
                        
                        nome_g_lower = nome_g.lower()
                        
                        ruolo_g = ripara_testo(str(row[map_col_listone["ruolo"]])) if "ruolo" in map_col_listone and map_col_listone["ruolo"] in row else "C"
                        squadra_g = ripara_testo(str(row[map_col_listone["squadra"]])) if "squadra" in map_col_listone and map_col_listone["squadra"] in row else "N/D"
                        
                        quot_val = 1
                        if "quotazione" in map_col_listone and map_col_listone["quotazione"] in row:
                            try:
                                quot_val = int(float(str(row[map_col_listone["quotazione"]]).replace(',', '.')))
                            except:
                                pass

                        proprietario_finale = "LIBERO"
                        scadenza_finale = "Giugno 2030"
                        
                        if nome_g_lower in stati_attuali_map:
                            proprietario_finale = stati_attuali_map[nome_g_lower]["proprietario"]
                            scadenza_finale = stati_attuali_map[nome_g_lower]["scadenza"]
                        
                        tier_g = "Top" if quot_val >= 25 else ("Semitop" if quot_val >= 15 else ("Titolare" if quot_val >= 8 else "Scommessa"))
                        
                        if ruolo_g == "A":
                            xg = round(max(0.1, quot_val * 0.035), 2)
                            xa = round(max(0.05, quot_val * 0.015), 2)
                        elif ruolo_g == "C":
                            xg = round(max(0.05, quot_val * 0.02), 2)
                            xa = round(max(0.08, quot_val * 0.025), 2)
                        elif ruolo_g == "D":
                            xg = round(max(0.02, quot_val * 0.01), 2)
                            xa = round(max(0.03, quot_val * 0.015), 2)
                        else:
                            xg, xa = 0.0, 0.0

                        if quot_val >= 25:
                            p_tit, part_att = 0.95, 36
                        elif quot_val >= 15:
                            p_tit, part_att = 0.82, 32
                        elif quot_val >= 8:
                            p_tit, part_att = 0.65, 27
                        else:
                            p_tit, part_att = 0.40, 20

                        partite_titolare = int(round(part_att * p_tit))
                        partite_subentrato = max(0, int(part_att - partite_titolare))
                        
                        base_fm = 6.00
                        if ruolo_g == "A":
                            base_fm += 0.35 + (quot_val * 0.04)
                        elif ruolo_g == "C":
                            base_fm += 0.20 + (quot_val * 0.03)
                        elif ruolo_g == "D":
                            base_fm += 0.10 + (quot_val * 0.02)
                        else:
                            base_fm = 5.50 + (quot_val * 0.01)
                        fanta_media = round(min(base_fm, 9.5), 2)
                        
                        status_piaz = "Rigorista 🎯" if quot_val >= 28 else ("Vice-Rigorista 👟" if quot_val >= 18 else "No")
                        
                        hype_squadra = {"Inter": 1.25, "Atalanta": 1.25, "Milan": 1.15, "Juventus": 1.15}
                        mult_team = hype_squadra.get(squadra_g, 0.95)
                        val_atteso = round(((xg * 3.0) + (xa * 1.0)) * part_att * mult_team, 1)
                        indice_vfm = round(val_atteso / quot_val, 2) if quot_val > 0 else 0.0

                        nuovi_righe_master.append({
                            "Nome": nome_g,
                            "Squadra": squadra_g,
                            "Ruolo": ruolo_g,
                            "Quotazione": quot_val,
                            "Proprietario_Iniziale": proprietario_finale,
                            "Stato": proprietario_finale,
                            "Scadenza_Contratto": scadenza_finale,
                            "Tier": tier_g,
                            "Percentuale_Titolarita": p_tit,
                            "Partite_Attese": part_att,
                            "Indice_Continuita": 7.8 if quot_val >= 15 else 6.8,
                            "Rischio_Infortunio": "Basso" if quot_val >= 15 else "Medio",
                            "xG_90": xg,
                            "xA_90": xa,
                            "Indice_Cartellini": "Medio",
                            "Rischio_Turnover": "Basso" if quot_val >= 15 else "Medio",
                            "Partite_Titolare": partite_titolare,
                            "Partite_Subentrato": partite_subentrato,
                            "FantaMedia_Stimata": fanta_media,
                            "Status_Piazzati": status_piaz,
                            "Moltiplicatore_Team": mult_team,
                            "Valore_Atteso": val_atteso,
                            "Indice_VfM": indice_vfm
                        })

                        if proprietario_finale != "LIBERO":
                            if proprietario_finale not in nuove_rose:
                                nuove_rose[proprietario_finale] = []
                            
                            esistente_rosa = next((g for g in nuove_rose[proprietario_finale] if str(g["Nome"]).strip().lower() == nome_g_lower), None)
                            if esistente_rosa:
                                esistente_rosa["Ruolo"] = ruolo_g
                                esistente_rosa["Squadra"] = squadra_g
                                esistente_rosa["Valore_Attuale"] = quot_val
                            else:
                                prezzo_acq = stati_attuali_map[nome_g_lower]["prezzo"]
                                nuove_rose[proprietario_finale].append({
                                    "Nome": nome_g,
                                    "Ruolo": ruolo_g,
                                    "Squadra": squadra_g,
                                    "Prezzo_Acquisto": prezzo_acq,
                                    "Valore_Attuale": quot_val,
                                    "Scadenza": scadenza_finale
                                })

                    df_nuovo_master = pd.DataFrame(nuovi_righe_master)
                    st.session_state.df_giocatori = df_nuovo_master
                    st.session_state.rose_lega = nuove_rose
                    st.session_state.last_uploaded_listone = listone_identifier

                    st.sidebar.success(f"✅ Listone aggiornato con successo! Nuovi giocatori integrati e rose preservate.")
                    st.rerun()
                else:
                    st.sidebar.error("Impossibile individuare la colonna del nome/giocatore nel listone.")
            except Exception as e:
                st.sidebar.error(f"Errore durante l'importazione del listone: {e}")

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
            
            idx_m = df[df["Nome"].astype(str).str.strip().str.lower() == str(giocatore_da_aggiornare).strip().lower()].index
            if not idx_m.empty:
                st.session_state.df_giocatori.at[idx_m[0], "Scadenza_Contratto"] = scadenza_formattata

            st.success(f"✅ Contratto aggiornato a **{scadenza_formattata}**!")
            st.rerun()
    else:
        st.info("Rosa vuota.")

with st.sidebar.expander("📋 Esplora Rose, Valori & Esportazione"):
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
                "Squadra": g.get("Squadra", "N/D"),
                "Spesa": g.get("Prezzo_Acquisto", 1),
                "Scadenza": g["Scadenza"],
            }
            for g in rosa_selezionata_sidebar
        ]
        df_side_pd = pd.DataFrame(df_side_list)
        st.dataframe(
            df_side_pd, use_container_width=True, hide_index=True
        )
        
        txt_output = f"📋 **ROSA FANTA-LEGA: {squadra_da_esplorare}**\n"
        for _, row_exp in df_side_pd.iterrows():
            txt_output += f"- {row_exp['Ruolo']} | {row_exp['Nome']} ({row_exp['Squadra']}) [Spesa: {row_exp['Spesa']}cr | Scad: {row_exp['Scadenza']}]\n"
        
        st.download_button(
            label="📥 Esporta Rosa (Testo / WhatsApp)",
            data=txt_output,
            file_name=f"rosa_{squadra_da_esplorare.lower()}.txt",
            mime="text/plain",
            key=f"download_txt_rosa_{squadra_da_esplorare}"
        )
    else:
        st.info("Rosa vuota.")

# ---------------------------------------------------------
# 5. DASHBOARD PRINCIPALE: ASTA LIVE & SELEZIONE RUOLO/SQUADRA
# ---------------------------------------------------------
st.title("⚡ Live Auction Intelligent Assistant (Advanced)")

st.subheader(f"🔍 Analisi Giocatore per: {fanta_allenatore_attivo}")

df_liberi_base = df[df["Stato"] == "LIBERO"]

if not df_liberi_base.empty:
    col_filtro_a, col_filtro_b = st.columns(2)
    with col_filtro_a:
        ruoli_disponibili_asta = ["Tutti"] + sorted([str(r) for r in df_liberi_base["Ruolo"].dropna().unique().tolist()])
        ruolo_filtro_scelta = st.selectbox("Filtra per Ruolo in Asta:", ruoli_disponibili_asta, key="filtro_ruolo_asta_call")
    with col_filtro_b:
        squadre_disponibili_asta = ["Tutte"] + sorted([str(s) for s in df_liberi_base["Squadra"].dropna().unique().tolist()])
        squadra_filtro_scelta = st.selectbox("Filtra per Squadra Serie A in Asta:", squadre_disponibili_asta, key="filtro_squadra_asta_call")

    df_liberi_filtrati = df_liberi_base.copy()
    if ruolo_filtro_scelta != "Tutti":
        df_liberi_filtrati = df_liberi_filtrati[df_liberi_filtrati["Ruolo"] == ruolo_filtro_scelta]
    if squadra_filtro_scelta != "Tutte":
        df_liberi_filtrati = df_liberi_filtrati[df_liberi_filtrati["Squadra"] == squadra_filtro_scelta]

    giocatori_liberi = df_liberi_filtrati["Nome"].tolist()

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

        with st.expander("📊 Metriche Avanzate & Partite (Titolare / Subentrato)"):
            p_titolare = safe_get(g_data, ['Partite_Titolare', 'Partite Titolare', 'Titolare'], 0)
            p_subentrato = safe_get(g_data, ['Partite_Subentrato', 'Partite Subentrato', 'Subentrato'], 0)
            
            c_m1, c_m2, c_m3 = st.columns(3)
            c_m1.metric("Partite da Titolare Attese", f"{p_titolare}")
            c_m2.metric("Partite da Subentrato", f"{p_subentrato}")
            c_m3.metric("Indice di Continuità", f"{safe_get(g_data, ['Indice_Continuita', 'Continuita'], 'N/D')}")

            c_m4, c_m5, c_m6 = st.columns(3)
            c_m4.metric("xG / 90min", f"{safe_get(g_data, ['xG_90', 'xg'], 0.0)}")
            c_m5.metric("xA / 90min", f"{safe_get(g_data, ['xA_90', 'xa'], 0.0)}")
            c_m6.metric("Rischio Infortunio", f"{safe_get(g_data, ['Rischio_Infortunio'], 'Basso')}")

        st.markdown("---")
        st.subheader("🛒 Registra Acquisto in Asta")

        col_acq1, col_acq2, col_acq3 = st.columns(3)
        with col_acq1:
            prezzo_aggiudicazione = st.number_input(
                "Prezzo di Aggiudicazione (crediti):",
                min_value=1,
                max_value=max(1000, budget_rimanente_corrente + 500),
                value=max(1, quotazione_listone),
                step=1,
                key="input_prezzo_asta",
            )
        with col_acq2:
            mesi_contratto_default = ["Giugno 2029", "Giugno 2030", "Giugno 2031", "Giugno 2032"]
            scadenza_scelta = st.selectbox(
                "Scadenza Contratto:",
                mesi_contratto_default,
                index=0 if quotazione_listone >= 15 else 1,
                key="select_scadenza_asta",
            )
        with col_acq3:
            st.markdown("<br>", unsafe_allow_html=True)
            registra_acquisto_btn = st.button(
                "✅ Conferma e Assegna Giocatore",
                type="primary",
                key="btn_conferma_acquisto",
            )

        if registra_acquisto_btn:
            if prezzo_aggiudicazione > budget_rimanente_corrente:
                st.error(
                    f"❌ Crediti insufficienti! Budget rimanente per {fanta_allenatore_attivo}: {budget_rimanente_corrente} cr."
                )
            else:
                nuovo_elemento_rosa = {
                    "Nome": str(g_data["Nome"]),
                    "Ruolo": str(g_data["Ruolo"]),
                    "Squadra": str(g_data["Squadra"]),
                    "Prezzo_Acquisto": int(prezzo_aggiudicazione),
                    "Valore_Attuale": int(quotazione_listone),
                    "Scadenza": str(scadenza_scelta),
                }

                if fanta_allenatore_attivo not in st.session_state.rose_lega:
                    st.session_state.rose_lega[fanta_allenatore_attivo] = []

                st.session_state.rose_lega[fanta_allenatore_attivo].append(
                    nuovo_elemento_rosa
                )

                idx_g = df[df["Nome"] == giocatore_sel].index[0]
                df.at[idx_g, "Stato"] = fanta_allenatore_attivo
                df.at[idx_g, "Scadenza_Contratto"] = str(scadenza_scelta)
                st.session_state.df_giocatori = df

                st.success(
                    f"🎉 **{giocatore_sel}** assegnato a **{fanta_allenatore_attivo}** per **{prezzo_aggiudicazione} crediti** (Contratto: {scadenza_scelta})!"
                )
                st.rerun()
    else:
        st.info("Nessun giocatore disponibile con i filtri selezionati.")
else:
    st.info("Tutti i giocatori sono stati assegnati o il listone è vuoto.")