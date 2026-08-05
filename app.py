import streamlit as st
import pandas as pd
from datetime import datetime
import pypdf
import io

st.set_page_config(page_title="FantaManager & Scouting Hub 10 Squadre", page_icon="⚽", layout="wide")

# --- LISTA DELLE 10 SQUADRE UFFICIALI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

# --- INIZIALIZZAZIONE SICURA DELLO STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state or not isinstance(st.session_state.squadre, dict):
    st.session_state.squadre = {}

for sq in NOMI_SQUADRE:
    if sq not in st.session_state.squadre:
        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}

if 'storico_mercato' not in st.session_state:
    st.session_state.storico_mercato = []

if 'watchlist' not in st.session_state:
    st.session_state.watchlist = []

# Rosa precaricata di esempio per PECU (se vuota)
if len(st.session_state.squadre["PECU"]["rosa"]) == 0:
    st.session_state.squadre["PECU"]["rosa"] = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "Costo_Acquisto": 14, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Paleari", "Ruolo": "P", "Squadra_SerieA": "Torino", "Quotazione": 8, "FantaMedia": 5.0, "Costo_Acquisto": 8, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 6, "FantaMedia": 6.1, "Costo_Acquisto": 6, "Scadenza_Contratto": "Giugno 2027"},
        {"Nome": "Lucumì", "Ruolo": "D", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 6, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 10, "FantaMedia": 6.6, "Costo_Acquisto": 10, "Scadenza_Contratto": "Giugno 2030"},
        {"Nome": "Biraghi", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 1, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Ranieri L.", "Ruolo": "D", "Squadra_SerieA": "Fiorentina", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 6, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Maripan", "Ruolo": "D", "Squadra_SerieA": "Torino", "Quotazione": 9, "FantaMedia": 6.2, "Costo_Acquisto": 9, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Mina", "Ruolo": "D", "Squadra_SerieA": "Cagliari", "Quotazione": 7, "FantaMedia": 6.1, "Costo_Acquisto": 7, "Scadenza_Contratto": "Giugno 2027"},
        {"Nome": "Juan Jesus", "Ruolo": "D", "Squadra_SerieA": "Napoli", "Quotazione": 6, "FantaMedia": 5.9, "Costo_Acquisto": 4, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Gila", "Ruolo": "D", "Squadra_SerieA": "Lazio", "Quotazione": 9, "FantaMedia": 6.3, "Costo_Acquisto": 9, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Aebischer", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 7, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Cristante", "Ruolo": "C", "Squadra_SerieA": "Roma", "Quotazione": 12, "FantaMedia": 6.5, "Costo_Acquisto": 13, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Freuler", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 8, "FantaMedia": 6.3, "Costo_Acquisto": 6, "Scadenza_Contratto": "Giugno 2027"},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 15, "FantaMedia": 7.5, "Costo_Acquisto": 13, "Scadenza_Contratto": "Giugno 2030"},
        {"Nome": "Jashari", "Ruolo": "C", "Squadra_SerieA": "Bologna", "Quotazione": 6, "FantaMedia": 6.0, "Costo_Acquisto": 5, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "De Roon", "Ruolo": "C", "Squadra_SerieA": "Atalanta", "Quotazione": 10, "FantaMedia": 6.4, "Costo_Acquisto": 9, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Loftus-Cheek", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 14, "FantaMedia": 6.7, "Costo_Acquisto": 13, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Mandragora", "Ruolo": "C", "Squadra_SerieA": "Fiorentina", "Quotazione": 11, "FantaMedia": 6.3, "Costo_Acquisto": 18, "Scadenza_Contratto": "Giugno 2027"},
        {"Nome": "McKennie", "Ruolo": "C", "Squadra_SerieA": "Juventus", "Quotazione": 15, "FantaMedia": 6.9, "Costo_Acquisto": 18, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Buksa", "Ruolo": "A", "Squadra_SerieA": "Udinese", "Quotazione": 9, "FantaMedia": 6.5, "Costo_Acquisto": 7, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Dallinga", "Ruolo": "A", "Squadra_SerieA": "Bologna", "Quotazione": 12, "FantaMedia": 6.6, "Costo_Acquisto": 7, "Scadenza_Contratto": "Giugno 2029"},
        {"Nome": "Boga", "Ruolo": "A", "Squadra_SerieA": "Atalanta", "Quotazione": 13, "FantaMedia": 6.8, "Costo_Acquisto": 11, "Scadenza_Contratto": "Giugno 2028"},
        {"Nome": "Douvikas", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 25, "FantaMedia": 7.8, "Costo_Acquisto": 27, "Scadenza_Contratto": "Giugno 2030"},
        {"Nome": "Camarda", "Ruolo": "A", "Squadra_SerieA": "Milan", "Quotazione": 8, "FantaMedia": 6.2, "Costo_Acquisto": 3, "Scadenza_Contratto": "Giugno 2031"},
        {"Nome": "Meister", "Ruolo": "A", "Squadra_SerieA": "Altro", "Quotazione": 7, "FantaMedia": 6.0, "Costo_Acquisto": 6, "Scadenza_Contratto": "Giugno 2027"}
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
                df_load = pd.read_csv(listone_file, encoding='utf-8', on_bad_lines='skip')
            else:
                df_load = pd.read_excel(listone_file)
            
            df_load.columns = [str(c).strip() for c in df_load.columns]
            
            col_mappa = {}
            for col in df_load.columns:
                c_low = str(col).lower()
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
                df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                
                if 'Ruolo' not in df_load.columns: df_load['Ruolo'] = 'C'
                if 'Squadra_SerieA' not in df_load.columns: df_load['Squadra_SerieA'] = 'N/D'
                if 'Quotazione' not in df_load.columns: df_load['Quotazione'] = 10
                if 'FantaMedia' not in df_load.columns: df_load['FantaMedia'] = 6.0
                
                df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                
                fm_serie = df_load['FantaMedia']
                if isinstance(fm_serie, pd.DataFrame):
                    fm_serie = fm_serie.iloc[:, 0]
                df_load['FantaMedia'] = pd.to_numeric(
                    fm_serie.astype(str).str.replace(',', '.', regex=False), 
                    errors='coerce'
                ).fillna(6.0)
                
                if 'Potenziale' not in df_load.columns: df_load['Potenziale'] = 3
                if 'Titolarita' not in df_load.columns: df_load['Titolarita'] = 3
                
                st.session_state.giocatori_db = df_load[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Potenziale', 'Titolarita']]
                st.sidebar.success("Listone importato con successo!")
            else:
                st.sidebar.error("Impossibile trovare la colonna 'Nome' nel file.")
        except Exception as e:
            st.sidebar.error(f"Errore nella lettura: {e}")

with st.sidebar.expander("📋 Importa Rose Esistenti"):
    st.markdown("Carica un file CSV, Excel o PDF con le rose. Colonne richieste: **Squadra**, **Nome**, **Ruolo**, **Costo**, **Contratto**.")
    rose_file = st.file_uploader("File Rose (10 Squadre)", type=["csv", "xlsx", "pdf"], key="upload_rose")
    
    if rose_file is not None:
        try:
            df_rose = None
            if rose_file.name.endswith('.csv'):
                df_rose = pd.read_csv(rose_file, encoding='utf-8', on_bad_lines='skip')
            elif rose_file.name.endswith('.xlsx'):
                df_rose = pd.read_excel(rose_file)
            elif rose_file.name.endswith('.pdf'):
                reader = pypdf.PdfReader(rose_file)
                righe_pdf = []
                for page in reader.pages:
                    text = page.extract_text()
                    if text:
                        for line in text.split('\n'):
                            if line.strip():
                                righe_pdf.append({"testo_riga": line.strip()})
                df_rose = pd.DataFrame(righe_pdf)
            
            if df_rose is not None and not df_rose.empty:
                if rose_file.name.endswith('.pdf'):
                    count_importati = 0
                    sq_corrente = "BARDO"
                    for _, row in df_rose.iterrows():
                        riga = row["testo_riga"]
                        riga_upper = riga.upper()
                        
                        sq_match = next((s for s in NOMI_SQUADRE if s in riga_upper), None)
                        if sq_match and len(riga.split()) <= 3:
                            sq_corrente = sq_match
                            continue
                        
                        parti = riga.split()
                        if len(parti) >= 2:
                            g_nome = parti[0]
                            g_ruolo = "C"
                            g_costo = 1
                            g_scadenza = "Giugno 2027"
                            for p in parti:
                                if p in ["P", "D", "C", "A"]:
                                    g_ruolo = p
                                elif p.isdigit():
                                    val_num = int(p)
                                    if val_num <= 5:
                                        g_scadenza = f"Giugno {2026 + val_num}"
                                    else:
                                        g_costo = val_num
                            
                            db_g = st.session_state.giocatori_db
                            match_db = db_g[db_g['Nome'].str.lower() == g_nome.lower()]
                            
                            squadra_sa = "N/D"
                            quot = 10
                            fm = 6.0
                            if not match_db.empty:
                                squadra_sa = match_db.iloc[0]['Squadra_SerieA']
                                quot = int(match_db.iloc[0]['Quotazione'])
                                fm = float(match_db.iloc[0]['FantaMedia'])
                                g_ruolo = str(match_db.iloc[0]['Ruolo'])

                            if not any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_corrente]["rosa"]):
                                st.session_state.squadre[sq_corrente]["rosa"].append({
                                    "Nome": g_nome,
                                    "Ruolo": g_ruolo,
                                    "Squadra_SerieA": squadra_sa,
                                    "Quotazione": quot,
                                    "FantaMedia": fm,
                                    "Costo_Acquisto": g_costo,
                                    "Scadenza_Contratto": g_scadenza
                                })
                                count_importati += 1
                    st.sidebar.success(f"Importati {count_importati} giocatori dal PDF con successo!")
                
                else:
                    df_rose.columns = [str(c).strip().lower() for c in df_rose.columns]
                    col_squadra = next((c for c in df_rose.columns if 'squadra' in c or 'fantateam' in c or 'proprietario' in c), None)
                    col_nome = next((c for c in df_rose.columns if 'nome' in c or 'giocatore' in c), None)
                    col_ruolo = next((c for c in df_rose.columns if 'ruolo' in c or 'r' == c), None)
                    col_costo = next((c for c in df_rose.columns if 'costo' in c or 'prezzo' in c or 'pagato' in c or 'quot' in c), None)
                    col_contratto = next((c for c in df_rose.columns if 'contratto' in c or 'anni' in c or 'scadenza' in c), None)
                    
                    if col_squadra and col_nome:
                        count_importati = 0
                        for _, row in df_rose.iterrows():
                            sq_nome = str(row[col_squadra]).strip().upper()
                            sq_match = next((s for s in NOMI_SQUADRE if s.upper() in sq_nome or sq_nome in s.upper()), None)
                            
                            if sq_match:
                                g_nome = str(row[col_nome]).strip()
                                g_ruolo = str(row[col_ruolo]).strip().upper() if col_ruolo and pd.notna(row[col_ruolo]) else "C"
                                
                                raw_costo = row[col_costo] if col_costo and pd.notna(row[col_costo]) else 1
                                try:
                                    g_costo = int(pd.to_numeric(raw_costo, errors='coerce'))
                                    if pd.isna(g_costo): g_costo = 1
                                except:
                                    g_costo = 1

                                raw_contratto = row[col_contratto] if col_contratto and pd.notna(row[col_contratto]) else 1
                                try:
                                    val_c = int(pd.to_numeric(raw_contratto, errors='coerce'))
                                    if pd.isna(val_c):
                                        g_scadenza = str(row[col_contratto]).strip()
                                    else:
                                        g_scadenza = f"Giugno {2026 + val_c}"
                                except:
                                    g_scadenza = "Giugno 2027"
                                
                                db_g = st.session_state.giocatori_db
                                match_db = db_g[db_g['Nome'].str.lower() == g_nome.lower()]
                                
                                squadra_sa = "N/D"
                                quot = 10
                                fm = 6.0
                                if not match_db.empty:
                                    squadra_sa = match_db.iloc[0]['Squadra_SerieA']
                                    quot = int(match_db.iloc[0]['Quotazione'])
                                    fm = float(match_db.iloc[0]['FantaMedia'])
                                    g_ruolo = str(match_db.iloc[0]['Ruolo'])

                                if not any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_match]["rosa"]):
                                    st.session_state.squadre[sq_match]["rosa"].append({
                                        "Nome": g_nome,
                                        "Ruolo": g_ruolo,
                                        "Squadra_SerieA": squadra_sa,
                                        "Quotazione": quot,
                                        "FantaMedia": fm,
                                        "Costo_Acquisto": g_costo,
                                        "Scadenza_Contratto": g_scadenza
                                    })
                                    count_importati += 1
                        st.sidebar.success(f"Importati {count_importati} giocatori nelle rose con successo!")
                    else:
                        st.sidebar.error("Colonne essenziali mancanti ('Squadra' o 'Nome').")
            else:
                st.sidebar.error("Il file caricato è vuoto o non leggibile.")
        except Exception as e:
            st.sidebar.error(f"Errore caricamento rose: {e}")

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
    st.header("🔍 Hub Scouting, Quotazioni & FantaMedie Avanzate")
    df = st.session_state.giocatori_db.copy()

    df["Indice_Affare"] = round(df["FantaMedia"] / df["Quotazione"].replace(0, 1), 2)

    giocatori_assegnati = {}
    for sq, dati in st.session_state.squadre.items():
        for g in dati["rosa"]:
            giocatori_assegnati[g["Nome"].lower()] = sq
            
    df["Proprietario"] = df["Nome"].apply(lambda x: giocatori_assegnati.get(x.lower(), "Svincolato 🟢"))

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        ruoli_disponibili = df["Ruolo"].unique() if "Ruolo" in df.columns else ["P", "D", "C", "A"]
        filtro_ruolo = st.multiselect("Filtra per Ruolo", options=ruoli_disponibili, default=ruoli_disponibili)
    with col2:
        min_fm = st.slider("FantaMedia Minima", 4.0, 10.0, 5.0, 0.1)
    with col3:
        solo_svincolati = st.checkbox("Mostra solo Svincolati", value=False)
    with col4:
        search_nome = st.text_input("Cerca per Nome Giocatore")

    df_filtrato = df[(df["Ruolo"].isin(filtro_ruolo)) & (df["FantaMedia"] >= min_fm)]
    if solo_svincolati:
        df_filtrato = df_filtrato[df_filtrato["Proprietario"] == "Svincolato 🟢"]
    if search_nome:
        df_filtrato = df_filtrato[df_filtrato["Nome"].str.contains(search_nome, case=False, na=False)]

    df_filtrato = df_filtrato.sort_values(by="Indice_Affare", ascending=False)

    st.subheader(f"Risultati Scouting ({len(df_filtrato)} giocatori trovati)")
    st.dataframe(df_filtrato, use_container_width=True)

    st.markdown("---")
    st.subheader("⭐ Watchlist (Lista dei Desideri Personale)")
    g_watchlist = st.selectbox("Aggiungi giocatore alla Watchlist", df["Nome"].values, key="sel_watchlist")
    if st.button("Aggiungi alla Watchlist"):
        if g_watchlist not in st.session_state.watchlist:
            st.session_state.watchlist.append(g_watchlist)
            st.success(f"{g_watchlist} aggiunto alla tua Watchlist!")
            st.rerun()
        else:
            st.warning("Il giocatore è già nella tua Watchlist.")

    if len(st.session_state.watchlist) > 0:
        df_watch = df[df["Nome"].isin(st.session_state.watchlist)]
        st.dataframe(df_watch[["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Indice_Affare", "Proprietario"]], use_container_width=True)
        if st.button("Svuota Watchlist"):
            st.session_state.watchlist = []
            st.rerun()
    else:
        st.info("La tua watchlist è vuota. Aggiungi i tuoi obiettivi preferiti.")

# ==========================================
# 2. MERCATO (ACQUISTI E VENDITE)
# ==========================================
elif menu == "🛒 Mercato (Acquisti/Vendite)":
    st.header("🛒 Gestione Mercato: Acquisti, Svincoli e Registro")
    
    tab_acq, tab_vend, tab_reg = st.tabs(["📥 Acquista da Svincolati", "📤 Vendi / Svincola", "📜 Registro Operazioni"])

    with tab_acq:
        st.subheader("Acquista un giocatore svincolato")
        squadra_selezionata = st.selectbox("Seleziona la tua Squadra", NOMI_SQUADRE, key="mercato_sq")
        crediti_disponibili = st.session_state.squadre[squadra_selezionata]["crediti"]
        rosa_attuale_len = len(st.session_state.squadre[squadra_selezionata]["rosa"])
        
        col_m1, col_m2 = st.columns(2)
        col_m1.metric("Crediti Residui", f"{crediti_disponibili} 🪙")
        col_m2.metric("Giocatori in Rosa", f"{rosa_attuale_len} / 25")

        giocatori_in_rosa = [g["Nome"].lower() for sq_data in st.session_state.squadre.values() for g in sq_data["rosa"]]
        db_g = st.session_state.giocatori_db
        
        svincolati = db_g[~db_g["Nome"].str.lower().isin(giocatori_in_rosa)]

        if len(svincolati) > 0:
            giocatore_scelto = st.selectbox("Seleziona Giocatore Svincolato", svincolati["Nome"].values)
            info_g = svincolati[svincolati["Nome"] == giocatore_scelto].iloc[0]
            
            prezzo_consigliato = int(info_g["Quotazione"])
            st.write(f"Ruolo: **{info_g['Ruolo']}** | Squadra Serie A: **{info_g['Squadra_SerieA']}** | Quotazione: **{prezzo_consigliato}** | FantaMedia: **{info_g['FantaMedia']}**")

            col_acq1, col_acq2 = st.columns(2)
            with col_acq1:
                prezzo_acquisto = st.number_input("Prezzo di Acquisto (crediti)", min_value=1, max_value=max(1, crediti_disponibili), value=prezzo_consigliato, key="input_prezzo_acq")
            with col_acq2:
                mesi_opzioni = ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"]
                col_scad1, col_scad2 = st.columns(2)
                with col_scad1:
                    sel_mese = st.selectbox("Mese Scadenza", mesi_opzioni, index=5, key="input_mese_acq")
                with col_scad2:
                    sel_anno = st.number_input("Anno Scadenza", min_value=2026, max_value=2035, value=2028, key="input_anno_acq")
                scadenza_contratto = f"{sel_mese} {sel_anno}"

            if st.button("Conferma Acquisto"):
                if crediti_disponibili >= prezzo_acquisto:
                    st.session_state.squadre[squadra_selezionata]["crediti"] -= prezzo_acquisto
                    st.session_state.squadre[squadra_selezionata]["rosa"].append({
                        "Nome": giocatore_scelto,
                        "Ruolo": info_g["Ruolo"],
                        "Squadra_SerieA": info_g["Squadra_SerieA"],
                        "Quotazione": info_g["Quotazione"],
                        "FantaMedia": info_g["FantaMedia"],
                        "Costo_Acquisto": prezzo_acquisto,
                        "Scadenza_Contratto": scadenza_contratto
                    })
                    st.session_state.storico_mercato.insert(0, {
                        "Orario": datetime.now().strftime("%H:%M:%S"),
                        "Operazione": "ACQUISTO",
                        "Dettagli": f"{squadra_selezionata} acquista {giocatore_scelto} ({info_g['Ruolo']}) per {prezzo_acquisto} crediti (Scadenza: {scadenza_contratto})."
                    })
                    st.success(f"Acquisto completato! {giocatore_scelto} è ora in rosa a {squadra_selezionata}.")
                    st.rerun()
                else:
                    st.error("Crediti insufficienti per completare l'acquisto!")
        else:
            st.warning("Non ci sono giocatori svincolati disponibili nel database.")

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
                st.session_state.storico_mercato.insert(0, {
                    "Orario": datetime.now().strftime("%H:%M:%S"),
                    "Operazione": "SVINCOLO/CESSIONE",
                    "Dettagli": f"{sq_vendi} svincola {giocatore_da_vendere}, incassando {prezzo_vendita} crediti."
                })
                st.success(f"Cessione avvenuta con successo! Incassati {prezzo_vendita} crediti.")
                st.rerun()
        else:
            st.info("La rosa selezionata è vuota.")

    with tab_reg:
        st.subheader("📜 Storico Ufficiale Operazioni di Mercato")
        if len(st.session_state.storico_mercato) > 0:
            df_storico = pd.DataFrame(st.session_state.storico_mercato)
            st.dataframe(df_storico, use_container_width=True)
        else:
            st.info("Nessuna operazione registrata in questa sessione.")

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
                    msg_log = f"Scambio definitivo tra {sq1} e {sq2}."
                    st.success(f"🎉 {msg_log}")
                else:
                    for g in oggetti_sq2:
                        g_prestito = g.copy()
                        g_prestito["Nome"] = f"{g_prestito['Nome']} (in prestito da {sq2})"
                        st.session_state.squadre[sq1]["rosa"].append(g_prestito)
                    for g in oggetti_sq1:
                        g_prestito = g.copy()
                        g_prestito["Nome"] = f"{g_prestito['Nome']} (in prestito da {sq1})"
                        st.session_state.squadre[sq2]["rosa"].append(g_prestito)
                    msg_log = f"Prestito registrato tra {sq1} e {sq2}."
                    st.success(f"🤝 {msg_log}")
                
                st.session_state.storico_mercato.insert(0, {
                    "Orario": datetime.now().strftime("%H:%M:%S"),
                    "Operazione": "SCAMBIO",
                    "Dettagli": msg_log
                })
                st.rerun()

# ==========================================
# 4. ROSE E CREDITI (10 SQUADRE) + RIEPILOGO GENERALE
# ==========================================
elif menu == "📋 Rose e Crediti (10 Squadre)":
    st.header("📋 Riepilogo Rose, Contratti & Crediti delle 10 Squadre")

    tab_singole, tab_matrice = st.tabs(["🛡️ Viste Singole Squadre", "📊 Tabella Riassuntiva Generale"])

    with tab_singole:
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
                    # Uniforma o aggiunge la colonna Scadenza_Contratto se non presente o se derivata da Anni_Contratto
                    if "Scadenza_Contratto" not in rosa_df.columns:
                        if "Anni_Contratto" in rosa_df.columns:
                            rosa_df["Scadenza_Contratto"] = pd.to_numeric(rosa_df["Anni_Contratto"], errors="coerce").fillna(1).astype(int).apply(lambda x: f"Giugno {2026 + x}")
                        else:
                            rosa_df["Scadenza_Contratto"] = "Giugno 2027"

                    conti_ruoli = rosa_df["Ruolo"].value_counts().to_dict()
                    p = conti_ruoli.get("P", 0)
                    d = conti_ruoli.get("D", 0)
                    c = conti_ruoli.get("C", 0)
                    a = conti_ruoli.get("A", 0)
                    
                    st.caption(f"Composizione Rosa: 🟢 Portieri: **{p}** | 🟡 Difensori: **{d}** | 🔵 Centrocampisti: **{c}** | 🔴 Attaccanti: **{a}** (Totale: {len(rosa_df)})")
                    
                    with st.expander("⚙️ Gestisci / Modifica Scadenza Contratto Rosa"):
                        g_sel_contratto = st.selectbox("Seleziona Giocatore", rosa_df["Nome"].values, key=f"sel_c_{nome_sq}")
                        
                        col_sc1, col_sc2 = st.columns(2)
                        with col_sc1:
                            nuovo_mese = st.selectbox("Nuovo Mese", ["Gennaio", "Febbraio", "Marzo", "Aprile", "Maggio", "Giugno", "Luglio", "Agosto", "Settembre", "Ottobre", "Novembre", "Dicembre"], index=5, key=f"mese_c_{nome_sq}")
                        with col_sc2:
                            nuovo_anno = st.number_input("Nuovo Anno", min_value=2026, max_value=2035, value=2028, key=f"anno_c_{nome_sq}")
                        
                        if st.button("Aggiorna Scadenza Contratto", key=f"btn_c_{nome_sq}"):
                            nuova_scadenza = f"{nuovo_mese} {nuovo_anno}"
                            for g_item in st.session_state.squadre[nome_sq]["rosa"]:
                                if g_item["Nome"] == g_sel_contratto:
                                    g_item["Scadenza_Contratto"] = nuova_scadenza
                                    if "Anni_Contratto" in g_item:
                                        del g_item["Anni_Contratto"]
                            st.success(f"Scadenza contratto di {g_sel_contratto} aggiornata a {nuova_scadenza}!")
                            st.rerun()

                    st.dataframe(rosa_df, use_container_width=True)
                else:
                    st.info(f"La rosa di {nome_sq} è attualmente vuota.")

    with tab_matrice:
        st.subheader("📊 Panoramica Generale delle 10 Squadre")
        riepilogo_data = []
        for nome_sq in NOMI_SQUADRE:
            dati = st.session_state.squadre[nome_sq]
            r_df = pd.DataFrame(dati["rosa"])
            tot_giocatori = len(r_df)
            crediti_res = dati["crediti"]
            
            p = len(r_df[r_df["Ruolo"] == "P"]) if not r_df.empty else 0
            d = len(r_df[r_df["Ruolo"] == "D"]) if not r_df.empty else 0
            c = len(r_df[r_df["Ruolo"] == "C"]) if not r_df.empty else 0
            a = len(r_df[r_df["Ruolo"] == "A"]) if not r_df.empty else 0
            
            riepilogo_data.append({
                "Squadra": nome_sq,
                "Crediti Residui": crediti_res,
                "Tot Giocatori": tot_giocatori,
                "Portieri (P)": p,
                "Difensori (D)": d,
                "Centrocampisti (C)": c,
                "Attaccanti (A)": a
            })
            
        df_riepilogo = pd.DataFrame(riepilogo_data)
        st.dataframe(df_riepilogo, use_container_width=True)