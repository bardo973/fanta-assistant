import streamlit as st
import pandas as pd
import json
import os
from datetime import datetime

st.set_page_config(page_title="FantaManager 2026/27 - 10 Squadre", page_icon="⚽", layout="wide")

# ============================================================
# CONFIG
# ============================================================
SAVE_FILE = "fantamanager_save.json"
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
ANNO_CORRENTE = 2026
CONTRATTO_ANNI = 4

# ============================================================
# LISTONE DEFAULT 2026/2027
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Butez","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":32,"FantaMedia":5.8,"Consiglio":"top","Note":"19 clean sheet, miglior difesa"},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"Consiglio":"top","Note":"13 clean sheet, 2 rigori parati"},
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"Consiglio":"top","Note":"18 clean sheet, fantamedia 6"},
    {"Nome":"Martinez","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":29,"FantaMedia":5.7,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Genoa"},
    {"Nome":"Meret","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":30,"FantaMedia":5.8,"Consiglio":"consigliato","Note":"Titolare con Allegri"},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"Consiglio":"consigliato","Note":"Miglior fantamedia, 13 clean sheet"},
    {"Nome":"De Gea","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":24,"FantaMedia":5.6,"Consiglio":"consigliato","Note":"Stagione del riscatto"},
    {"Nome":"Falcone","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":17,"FantaMedia":5.5,"Consiglio":"scommessa","Note":"Media voto 6.41, low cost"},
    {"Nome":"Stankovic","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":13,"FantaMedia":5.3,"Consiglio":"scommessa","Note":"Torna in Serie A"},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata"},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta"},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"Consiglio":"top","Note":"Voti alti e bonus"},
    {"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":32,"FantaMedia":6.7,"Consiglio":"top","Note":"4 gol, leader difesa Gasperini"},
    {"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":28,"FantaMedia":6.6,"Consiglio":"top","Note":"5 gol, potenziale stagione alla Gosens"},
    {"Nome":"Pavlovic","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":33,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5 gol, media 6.24"},
    {"Nome":"Ostigard","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"5 gol, centrale prolifico"},
    {"Nome":"Cambiaso","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":29,"FantaMedia":6.6,"Consiglio":"consigliato","Note":"3 gol, 4 assist"},
    {"Nome":"Spinazzola","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":27,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Sottovalutato, bonus garantiti"},
    {"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":32,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"Gran gamba, qualità offensiva"},
    {"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"Ex City, rotazioni Chivu"},
    {"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"1 gol, 4 assist in 19 partite"},
    {"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"7 gol in Europa, sostituto Gila"},
    {"Nome":"Jimenez","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":21,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Torna in Serie A, jolly tattico"},
    {"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":14,"FantaMedia":5.9,"Consiglio":"scommessa","Note":"Nuovo titolare sinistra"},
    {"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":48,"FantaMedia":7.5,"Consiglio":"top","Note":"Potenziale top, alla Milinkovic-Savic"},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"Consiglio":"top","Note":"Cambio ruolo, più appetibile"},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti"},
    {"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":52,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"8 gol, 3 assist, rigorista"},
    {"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":48,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"5 gol, 6 assist, attaccante aggiunto"},
    {"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Rendimento garantito"},
    {"Nome":"Koné","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":40,"FantaMedia":6.9,"Consiglio":"consigliato","Note":"Media 6.26, mai sotto sufficienza"},
    {"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":35,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 4 assist, voti alti"},
    {"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":38,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"Da prendere con Rowe"},
    {"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":36,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 3 assist, può crescere"},
    {"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5-6 gol potenziali"},
    {"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.6,"Consiglio":"scommessa","Note":"Talentino trequarti, attenzione hype"},
    {"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Sarri lo vuole, grande intuizione"},
    {"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Fiducia Chivu, sostituto Calhanoglu"},
    {"Nome":"Calò","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"10 gol, 14 assist in Serie B"},
    {"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Solo Yamal più assist in Liga"},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist"},
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"Consiglio":"top","Note":"14 gol in mezzo campionato, vice-cannonieri"},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"Consiglio":"top","Note":"13 gol, 6 assist"},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol"},
    {"Nome":"Goncalo Ramos","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Colpo da 70M, titolare Amorim"},
    {"Nome":"Kolo Muani","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":76,"FantaMedia":7.9,"Consiglio":"top","Note":"Tornato alla Juve, Spalletti lo vuole"},
    {"Nome":"Kean","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":65,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Doppia cifra garantita"},
    {"Nome":"Yildiz","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":70,"FantaMedia":7.7,"Consiglio":"consigliato","Note":"10 gol, 6 assist, centro progetto"},
    {"Nome":"Douvikas","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":65,"FantaMedia":7.8,"Consiglio":"consigliato","Note":"14 gol, sorpresa 2024-25"},
    {"Nome":"Dybala","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":58,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"Sempre utile, momento della differenza"},
    {"Nome":"Davis","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":61,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"10 gol, rigorista"},
    {"Nome":"Scamacca","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":55,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Attenzione infortuni"},
    {"Nome":"Simeone","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"11 gol, conferma"},
    {"Nome":"Dovbyk","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":48,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Doppia cifra a Bologna"},
    {"Nome":"Colombo","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":35,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"7 gol, obiettivo doppia cifra"},
    {"Nome":"Alajbegovic K.","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.7,"Consiglio":"scommessa","Note":"Colpo di mercato, trequarti"},
    {"Nome":"Ekhator","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Low cost, potenziale"},
    {"Nome":"Mendy","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":15,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"2 gol in 8 partite, 2007"},
    {"Nome":"Camarda","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Vice Ramos, a 1 credito ci sta"},
    {"Nome":"Ratkov","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Gattuso lo rilancia"},
]

# ============================================================
# PERSISTENZA
# ============================================================
def save_state():
    data = {
        "squadre": st.session_state.squadre,
        "storico_mercato": st.session_state.storico_mercato,
        "watchlist": st.session_state.watchlist,
        "prestiti": st.session_state.prestiti,
        "contratti": st.session_state.contratti,
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records")
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
            st.session_state.squadre = data.get("squadre", {})
            st.session_state.storico_mercato = data.get("storico_mercato", [])
            st.session_state.watchlist = data.get("watchlist", [])
            st.session_state.prestiti = data.get("prestiti", [])
            st.session_state.contratti = data.get("contratti", {})
            db = data.get("giocatori_db", [])
            st.session_state.giocatori_db = pd.DataFrame(db) if db else pd.DataFrame(LISTONE_DEFAULT)
            # Assicura che tutte le squadre esistano
            for sq in NOMI_SQUADRE:
                if sq not in st.session_state.squadre:
                    st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
            return True
        except Exception:
            pass
    return False

# ============================================================
# INIZIALIZZAZIONE
# ============================================================
if "initialized" not in st.session_state:
    st.session_state.squadre = {}
    st.session_state.storico_mercato = []
    st.session_state.watchlist = []
    st.session_state.prestiti = []
    st.session_state.contratti = {}
    st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)

    # Prova a caricare dati salvati
    if not load_state():
        for sq in NOMI_SQUADRE:
            st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}

    st.session_state.initialized = True

# ============================================================
# SIDEBAR
# ============================================================
st.sidebar.title("⚽ FantaManager 2026/27")

st.sidebar.markdown("---")
st.sidebar.subheader("💾 Salva / Carica Stato")
c1, c2 = st.sidebar.columns(2)
with c1:
    if st.button("💾 Salva", use_container_width=True):
        save_state()
        st.sidebar.success("Salvato!")
with c2:
    if st.button("📂 Carica", use_container_width=True):
        if load_state():
            st.sidebar.success("Caricato!")
            st.rerun()
        else:
            st.sidebar.warning("Nessun salvataggio trovato.")

st.sidebar.markdown("---")

# --- IMPORTA LISTONE ---
with st.sidebar.expander("📁 Importa Listone (CSV/Excel)"):
    st.markdown("Carica il listone aggiornato. Colonne: Nome, Ruolo, Squadra, Quotazione, FantaMedia.")
    up_listone = st.file_uploader("File Listone", type=["csv","xlsx"], key="ul")
    if up_listone is not None:
        try:
            if up_listone.name.endswith('.csv'):
                df_load = pd.read_csv(up_listone, encoding='utf-8', on_bad_lines='skip')
            else:
                df_load = pd.read_excel(up_listone)
            df_load.columns = [str(c).strip() for c in df_load.columns]
            col_mappa = {}
            for col in df_load.columns:
                cl = str(col).lower()
                if 'nome' in cl or 'giocatore' in cl: col_mappa[col] = 'Nome'
                elif cl in ['r','ruolo']: col_mappa[col] = 'Ruolo'
                elif 'squadra' in cl or 'team' in cl: col_mappa[col] = 'Squadra_SerieA'
                elif 'quot' in cl or 'valore' in cl or 'fc' in cl or 'qt' in cl: col_mappa[col] = 'Quotazione'
                elif 'fm' in cl or 'fantamedia' in cl or 'media' in cl: col_mappa[col] = 'FantaMedia'
            df_load = df_load.rename(columns=col_mappa)
            if 'Nome' in df_load.columns:
                df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                for c, d in [('Ruolo','C'),('Squadra_SerieA','N/D'),('Quotazione',10),('FantaMedia',6.0)]:
                    if c not in df_load.columns: df_load[c] = d
                df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                fm = df_load['FantaMedia']
                if isinstance(fm, pd.DataFrame): fm = fm.iloc[:,0]
                df_load['FantaMedia'] = pd.to_numeric(fm.astype(str).str.replace(',','.',regex=False), errors='coerce').fillna(6.0)
                if 'Consiglio' not in df_load.columns: df_load['Consiglio'] = 'consigliato'
                if 'Note' not in df_load.columns: df_load['Note'] = ''
                st.session_state.giocatori_db = df_load[['Nome','Ruolo','Squadra_SerieA','Quotazione','FantaMedia','Consiglio','Note']]
                save_state()
                st.sidebar.success("✅ Listone importato e salvato!")
            else:
                st.sidebar.error("Colonna 'Nome' mancante.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

# --- IMPORTA ROSE ---
with st.sidebar.expander("📋 Importa Rose Stagione Precedente"):
    st.markdown("CSV/Excel con colonne: **Squadra**, **Nome**, **Ruolo**, **Costo**.")
    up_rose = st.file_uploader("File Rose", type=["csv","xlsx"], key="ur")
    if up_rose is not None:
        try:
            if up_rose.name.endswith('.csv'):
                df_r = pd.read_csv(up_rose, encoding='utf-8', on_bad_lines='skip')
            else:
                df_r = pd.read_excel(up_rose)
            df_r.columns = [str(c).strip().lower() for c in df_r.columns]
            col_sq = next((c for c in df_r.columns if 'squadra' in c or 'fantateam' in c or 'proprietario' in c), None)
            col_nm = next((c for c in df_r.columns if 'nome' in c or 'giocatore' in c), None)
            col_rl = next((c for c in df_r.columns if 'ruolo' in c or c=='r'), None)
            col_cs = next((c for c in df_r.columns if 'costo' in c or 'prezzo' in c or 'pagato' in c or 'quot' in c), None)
            if col_sq and col_nm:
                count = 0
                for _, row in df_r.iterrows():
                    sq_nome = str(row[col_sq]).strip().upper()
                    sq_match = next((s for s in NOMI_SQUADRE if s.upper() in sq_nome or sq_nome in s.upper()), None)
                    if sq_match:
                        g_nome = str(row[col_nm]).strip()
                        g_ruolo = str(row[col_rl]).strip().upper() if col_rl and pd.notna(row[col_rl]) else "C"
                        g_costo = int(row[col_cs]) if col_cs and pd.notna(row[col_cs]) else 1
                        db_g = st.session_state.giocatori_db
                        match_db = db_g[db_g['Nome'].str.lower() == g_nome.lower()]
                        sq_sa = "N/D"; quot = 10; fm = 6.0
                        if not match_db.empty:
                            sq_sa = match_db.iloc[0]['Squadra_SerieA']
                            quot = int(match_db.iloc[0]['Quotazione'])
                            fm = float(match_db.iloc[0]['FantaMedia'])
                            g_ruolo = str(match_db.iloc[0]['Ruolo'])
                        if not any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_match]["rosa"]):
                            st.session_state.squadre[sq_match]["rosa"].append({
                                "Nome": g_nome, "Ruolo": g_ruolo, "Squadra_SerieA": sq_sa,
                                "Quotazione": quot, "FantaMedia": fm, "Costo_Acquisto": g_costo,
                                "Anno_Acquisto": ANNO_CORRENTE, "Contratto_Anni": CONTRATTO_ANNI
                            })
                            st.session_state.squadre[sq_match]["crediti"] -= g_costo
                            st.session_state.contratti[g_nome] = {"squadra": sq_match, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI}
                            count += 1
                save_state()
                st.sidebar.success(f"✅ Importati {count} giocatori!")
            else:
                st.sidebar.error("Colonne 'Squadra' o 'Nome' mancanti.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

with st.sidebar.expander("⚠️ Reset"):
    if st.button("🗑️ Resetta TUTTO", use_container_width=True):
        if os.path.exists(SAVE_FILE): os.remove(SAVE_FILE)
        for k in list(st.session_state.keys()): del st.session_state[k]
        st.sidebar.success("Resettato! Ricarica la pagina.")
        st.rerun()

st.sidebar.markdown("---")
menu = st.sidebar.selectbox("Navigazione", [
    "🔍 Scouting & Database",
    "🛒 Mercato (Acquisti/Vendite)",
    "🤝 Scambi & Prestiti",
    "📋 Rose, Crediti & Contratti"
])

# ============================================================
# 1. SCOUTING
# ============================================================
if menu == "🔍 Scouting & Database":
    st.header("🔍 Hub Scouting 2026/27")
    df = st.session_state.giocatori_db.copy()

    if df.empty:
        st.warning("Nessun giocatore nel database.")
    else:
        df["Indice_Affare"] = round(df["FantaMedia"] / df["Quotazione"].replace(0,1), 2)

        assegnati = {}
        for sq, dati in st.session_state.squadre.items():
            for g in dati["rosa"]:
                # Se è in prestito, mostra il proprietario reale
                nome_base = g["Nome"].replace(f" (PRESTITO)", "").strip()
                assegnati[nome_base.lower()] = sq
                assegnati[g["Nome"].lower()] = sq
        df["Proprietario"] = df["Nome"].apply(lambda x: assegnati.get(x.lower(), "Svincolato 🟢"))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            ruoli = sorted(df["Ruolo"].unique()) if "Ruolo" in df.columns else ["P","D","C","A"]
            filtro_ruolo = st.multiselect("Ruolo", ruoli, default=ruoli)
        with c2:
            min_fm = st.slider("FantaMedia min", 4.0, 10.0, 5.0, 0.1)
        with c3:
            solo_svinc = st.checkbox("Solo Svincolati", value=False)
        with c4:
            search = st.text_input("Cerca nome")

        consigli_fasce = st.multiselect("Fascia consiglio", ["top","consigliato","scommessa"], default=["top","consigliato","scommessa"])

        df_f = df[(df["Ruolo"].isin(filtro_ruolo)) & (df["FantaMedia"] >= min_fm) & (df["Consiglio"].isin(consigli_fasce))]
        if solo_svinc:
            df_f = df_f[df_f["Proprietario"] == "Svincolato 🟢"]
        if search:
            df_f = df_f[df_f["Nome"].str.contains(search, case=False, na=False)]
        df_f = df_f.sort_values(by="Indice_Affare", ascending=False)

        st.subheader(f"Trovati: {len(df_f)} giocatori")
        st.dataframe(df_f, use_container_width=True)

        # Watchlist
        st.markdown("---")
        st.subheader("⭐ Watchlist")
        g_sel = st.selectbox("Aggiungi giocatore", df["Nome"].values, key="wl")
        if st.button("Aggiungi"):
            if g_sel not in st.session_state.watchlist:
                st.session_state.watchlist.append(g_sel)
                save_state()
                st.success(f"{g_sel} aggiunto!")
                st.rerun()
        if st.session_state.watchlist:
            df_wl = df[df["Nome"].isin(st.session_state.watchlist)]
            st.dataframe(df_wl[["Nome","Ruolo","Squadra_SerieA","Quotazione","FantaMedia","Indice_Affare","Proprietario"]], use_container_width=True)
            if st.button("Svuota Watchlist"):
                st.session_state.watchlist = []
                save_state()
                st.rerun()

# ============================================================
# 2. MERCATO
# ============================================================
elif menu == "🛒 Mercato (Acquisti/Vendite)":
    st.header("🛒 Gestione Mercato")
    t_acq, t_vend, t_reg = st.tabs(["📥 Acquista", "📤 Vendi/Svincola", "📜 Registro"])

    with t_acq:
        st.subheader("Acquista giocatore svincolato")
        sq = st.selectbox("Squadra acquirente", NOMI_SQUADRE, key="acq_sq")
        cred = st.session_state.squadre[sq]["crediti"]
        rosa_len = len(st.session_state.squadre[sq]["rosa"])
        c1, c2 = st.columns(2)
        c1.metric("Crediti", f"{cred} 🪙")
        c2.metric("Rosa", f"{rosa_len}")

        db = st.session_state.giocatori_db
        if db.empty:
            st.warning("Importa prima un listone.")
        else:
            # Giocatori già in rosa (qualsiasi squadra)
            in_rosa = set()
            for d in st.session_state.squadre.values():
                for g in d["rosa"]:
                    in_rosa.add(g["Nome"].lower())
            svinc = db[~db["Nome"].str.lower().isin(in_rosa)]
            if len(svinc) > 0:
                g_sel = st.selectbox("Giocatore", svinc["Nome"].values)
                info = svinc[svinc["Nome"] == g_sel].iloc[0]
                st.write(f"Ruolo: **{info['Ruolo']}** | Squadra: **{info['Squadra_SerieA']}** | Quotazione: **{int(info['Quotazione'])}** | FM: **{info['FantaMedia']}** | Consiglio: **{info.get('Consiglio','')}**")
                prezzo = st.number_input("Prezzo pagato", min_value=1, max_value=max(1,cred), value=int(info["Quotazione"]), key="acq_p")
                if st.button("Conferma Acquisto"):
                    if cred >= prezzo:
                        st.session_state.squadre[sq]["crediti"] -= prezzo
                        st.session_state.squadre[sq]["rosa"].append({
                            "Nome": g_sel, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                            "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                            "Costo_Acquisto": prezzo, "Anno_Acquisto": ANNO_CORRENTE, "Contratto_Anni": CONTRATTO_ANNI
                        })
                        st.session_state.contratti[g_sel] = {"squadra": sq, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI}
                        st.session_state.storico_mercato.insert(0, {
                            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Operazione": "ACQUISTO",
                            "Dettagli": f"{sq} acquista {g_sel} ({info['Ruolo']}) per {prezzo}cr — Contratto fino al {ANNO_CORRENTE+CONTRATTO_ANNI}"
                        })
                        save_state()
                        st.success(f"✅ {g_sel} acquistato! Contratto 4 anni (fino al {ANNO_CORRENTE+CONTRATTO_ANNI}).")
                        st.rerun()
                    else:
                        st.error("Crediti insufficienti!")
            else:
                st.warning("Nessuno svincolato disponibile.")

    with t_vend:
        st.subheader("Vendi / Svincola giocatore")
        sq_v = st.selectbox("Squadra", NOMI_SQUADRE, key="vend_sq")
        rosa = st.session_state.squadre[sq_v]["rosa"]
        # Filtra solo giocatori di proprietà (non in prestito ricevuto)
        rosa_proprieta = [g for g in rosa if "(PRESTITO da" not in g.get("Nome", "")]
        if rosa_proprieta:
            nomi = [g["Nome"] for g in rosa_proprieta]
            g_v = st.selectbox("Giocatore", nomi, key="vend_g")
            g_obj = next(g for g in rosa_proprieta if g["Nome"] == g_v)
            prezzo_v = st.number_input("Prezzo rimborso", min_value=0, value=g_obj.get("Costo_Acquisto",10), key="vend_p")
            if st.button("Conferma Vendita"):
                # Rimuovi da tutte le rose (anche se in prestito, ma qui filtriamo proprietà)
                st.session_state.squadre[sq_v]["rosa"] = [g for g in rosa if g["Nome"] != g_v]
                st.session_state.squadre[sq_v]["crediti"] += prezzo_v
                if g_v in st.session_state.contratti:
                    del st.session_state.contratti[g_v]
                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "SVINCOLO",
                    "Dettagli": f"{sq_v} svincola {g_v}, incassa {prezzo_v}cr"
                })
                save_state()
                st.success(f"🗑️ {g_v} svincolato!")
                st.rerun()
        else:
            st.info("Nessun giocatore di proprietà nella rosa.")

    with t_reg:
        st.subheader("📜 Storico Operazioni")
        if st.session_state.storico_mercato:
            st.dataframe(pd.DataFrame(st.session_state.storico_mercato), use_container_width=True)
            if st.button("🗑️ Svuota registro"):
                st.session_state.storico_mercato = []
                save_state()
                st.rerun()
        else:
            st.info("Nessuna operazione.")

# ============================================================
# 3. SCAMBI & PRESTITI
# ============================================================
elif menu == "🤝 Scambi & Prestiti":
    st.header("🤝 Scambi Definitivi & Prestiti")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Squadra A")
        sq1 = st.selectbox("Squadra 1", NOMI_SQUADRE, key="sc1")
        rosa1 = [g for g in st.session_state.squadre[sq1]["rosa"] if "(PRESTITO da" not in g.get("Nome","")]
        g1 = st.multiselect("Cede giocatori", [g["Nome"] for g in rosa1], key="g1")
        d1 = st.number_input(f"Conguaglio da {sq1}", min_value=0, max_value=st.session_state.squadre[sq1]["crediti"], value=0, key="d1")
    with c2:
        st.subheader("Squadra B")
        sq2 = st.selectbox("Squadra 2", [s for s in NOMI_SQUADRE if s != sq1], key="sc2")
        rosa2 = [g for g in st.session_state.squadre[sq2]["rosa"] if "(PRESTITO da" not in g.get("Nome","")]
        g2 = st.multiselect("Cede giocatori", [g["Nome"] for g in rosa2], key="g2")
        d2 = st.number_input(f"Conguaglio da {sq2}", min_value=0, max_value=st.session_state.squadre[sq2]["crediti"], value=0, key="d2")

    tipo = st.radio("Tipo operazione", ["Scambio Definitivo", "Prestito 6 mesi", "Prestito 1 anno"], horizontal=True)

    if st.button("Finalizza", type="primary"):
        if not g1 and not g2 and d1 == 0 and d2 == 0:
            st.warning("Seleziona qualcosa.")
        elif st.session_state.squadre[sq1]["crediti"] < d1:
            st.error(f"{sq1} non ha abbastanza crediti.")
        elif st.session_state.squadre[sq2]["crediti"] < d2:
            st.error(f"{sq2} non ha abbastanza crediti.")
        else:
            # Conguaglio
            st.session_state.squadre[sq1]["crediti"] = st.session_state.squadre[sq1]["crediti"] - d1 + d2
            st.session_state.squadre[sq2]["crediti"] = st.session_state.squadre[sq2]["crediti"] - d2 + d1

            oggetti1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] in g1]
            st.session_state.squadre[sq1]["rosa"] = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] not in g1]
            oggetti2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] in g2]
            st.session_state.squadre[sq2]["rosa"] = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] not in g2]

            if tipo == "Scambio Definitivo":
                st.session_state.squadre[sq1]["rosa"].extend(oggetti2)
                st.session_state.squadre[sq2]["rosa"].extend(oggetti1)
                for g in oggetti2:
                    st.session_state.contratti[g["Nome"]] = {"squadra": sq1, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI}
                for g in oggetti1:
                    st.session_state.contratti[g["Nome"]] = {"squadra": sq2, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI}
                msg = f"Scambio definitivo: {sq1} ↔ {sq2}"
                st.success(f"🎉 {msg}")
            else:
                durata = 6 if tipo == "Prestito 6 mesi" else 12
                for g in oggetti2:
                    g_p = g.copy()
                    g_p["Nome_Originale"] = g["Nome"]
                    g_p["Nome"] = f"{g['Nome']} (PRESTITO da {sq2})"
                    g_p["Prestito_Da"] = sq2
                    g_p["Prestito_A"] = sq1
                    g_p["Prestito_Durata"] = durata
                    g_p["Prestito_Anno"] = ANNO_CORRENTE
                    st.session_state.squadre[sq1]["rosa"].append(g_p)
                    st.session_state.prestiti.append({
                        "Giocatore": g["Nome"], "Da": sq2, "A": sq1,
                        "Durata": durata, "Anno": ANNO_CORRENTE, "Denaro": d2 - d1
                    })
                for g in oggetti1:
                    g_p = g.copy()
                    g_p["Nome_Originale"] = g["Nome"]
                    g_p["Nome"] = f"{g['Nome']} (PRESTITO da {sq1})"
                    g_p["Prestito_Da"] = sq1
                    g_p["Prestito_A"] = sq2
                    g_p["Prestito_Durata"] = durata
                    g_p["Prestito_Anno"] = ANNO_CORRENTE
                    st.session_state.squadre[sq2]["rosa"].append(g_p)
                    st.session_state.prestiti.append({
                        "Giocatore": g["Nome"], "Da": sq1, "A": sq2,
                        "Durata": durata, "Anno": ANNO_CORRENTE, "Denaro": d1 - d2
                    })
                msg = f"Prestito ({durata} mesi): {sq1} ↔ {sq2}"
                st.success(f"🤝 {msg}")

            st.session_state.storico_mercato.insert(0, {
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Operazione": tipo.upper(),
                "Dettagli": msg + (f" | Conguaglio: {d1}cr vs {d2}cr" if d1 or d2 else "")
            })
            save_state()
            st.rerun()

    # Prestiti attivi
    if st.session_state.prestiti:
        st.markdown("---")
        st.subheader("📋 Prestiti Attivi")
        df_prest = pd.DataFrame(st.session_state.prestiti)
        st.dataframe(df_prest, use_container_width=True)

        st.subheader("Termina prestito")
        nomi_prestito = list(df_prest["Giocatore"].unique())
        gp = st.selectbox("Seleziona giocatore", nomi_prestito, key="term_p")
        if st.button("Termina prestito e riporta in rosa originale"):
            # Trova il prestito
            to_remove = None
            for i, p in enumerate(st.session_state.prestiti):
                if p["Giocatore"] == gp:
                    to_remove = i
                    da_sq = p["Da"]
                    a_sq = p["A"]
                    # Rimuovi dalla rosa del prestinatario
                    st.session_state.squadre[a_sq]["rosa"] = [
                        g for g in st.session_state.squadre[a_sq]["rosa"]
                        if g.get("Nome_Originale") != gp and g["Nome"] != gp
                    ]
                    # Riporta nella rosa del proprietario (se non c'è già)
                    g_orig = None
                    for g in st.session_state.squadre[da_sq]["rosa"]:
                        if g["Nome"] == gp:
                            g_orig = g
                            break
                    if not g_orig:
                        # Ricostruisci dal db
                        db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"] == gp]
                        if not db_match.empty:
                            info = db_match.iloc[0]
                            g_orig = {
                                "Nome": gp, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                                "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                                "Costo_Acquisto": 0, "Anno_Acquisto": ANNO_CORRENTE, "Contratto_Anni": CONTRATTO_ANNI
                            }
                        else:
                            g_orig = {"Nome": gp, "Ruolo": "C", "Squadra_SerieA": "N/D", "Quotazione": 1, "FantaMedia": 6.0, "Costo_Acquisto": 0}
                        st.session_state.squadre[da_sq]["rosa"].append(g_orig)
                    break
            if to_remove is not None:
                st.session_state.prestiti.pop(to_remove)
                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "FINE PRESTITO",
                    "Dettagli": f"{gp} torna a {da_sq}"
                })
                save_state()
                st.success(f"✅ {gp} rientrato da prestito!")
                st.rerun()

# ============================================================
# 4. ROSE, CREDITI & CONTRATTI
# ============================================================
elif menu == "📋 Rose, Crediti & Contratti":
    st.header("📋 Riepilogo Rose, Crediti & Contratti")

    tab_singole, tab_matrice, tab_contratti, tab_consigli = st.tabs(["🛡️ Squadre", "📊 Matrice", "📄 Contratti", "💡 Consigli 2026/27"])

    with tab_singole:
        tabs = st.tabs(NOMI_SQUADRE)
        for i, sq in enumerate(NOMI_SQUADRE):
            with tabs[i]:
                dati = st.session_state.squadre[sq]
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.subheader(f"🛡️ {sq}")
                with c2:
                    st.metric("Crediti", f"{dati['crediti']} 🪙")

                rosa_df = pd.DataFrame(dati["rosa"])
                if not rosa_df.empty:
                    conti = rosa_df["Ruolo"].value_counts().to_dict()
                    st.caption(f"P: {conti.get('P',0)} | D: {conti.get('D',0)} | C: {conti.get('C',0)} | A: {conti.get('A',0)} | Tot: {len(rosa_df)}")
                    # Mostra anche scadenza contratto
                    display = rosa_df.copy()
                    if "Anno_Acquisto" in display.columns and "Contratto_Anni" in display.columns:
                        display["Scadenza"] = display["Anno_Acquisto"] + display["Contratto_Anni"]
                    st.dataframe(display, use_container_width=True)
                else:
                    st.info("Rosa vuota.")

    with tab_matrice:
        st.subheader("📊 Quadro Generale")
        summary = []
        for sq in NOMI_SQUADRE:
            dati = st.session_state.squadre[sq]
            rosa = dati["rosa"]
            p=d=c=a=spesa=0
            for g in rosa:
                r = g.get("Ruolo","C")
                if r=="P": p+=1
                elif r=="D": d+=1
                elif r=="C": c+=1
                elif r=="A": a+=1
                spesa += g.get("Costo_Acquisto",0)
            summary.append({"Squadra":sq, "Crediti":dati["crediti"], "Spesa":spesa, "Tot":len(rosa), "P":p, "D":d, "C":c, "A":a})
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

    with tab_contratti:
        st.subheader(f"📄 Contratti 4 anni ({ANNO_CORRENTE}-{ANNO_CORRENTE+CONTRATTO_ANNI})")
        if st.session_state.contratti:
            rows = []
            for nome, c in st.session_state.contratti.items():
                rows.append({"Giocatore":nome, "Squadra":c["squadra"], "Anno":c["anno"], "Scadenza":c["anno"]+c["durata"], "Durata":c["durata"]})
            st.dataframe(pd.DataFrame(rows), use_container_width=True)
        else:
            st.info("Nessun contratto registrato.")

    with tab_consigli:
        st.subheader("💡 Consigli Fantacalcio 2026/27")
        consigli = {
            "Portieri": {
                "top": ["Butez (Como) - 19 clean sheet", "Svilar (Roma) - 18 clean sheet", "Maignan (Milan) - 13 clean sheet"],
                "consigliati": ["Martinez (Inter)", "Meret (Napoli)", "Carnesecchi (Atalanta)", "De Gea (Fiorentina)"],
                "scommesse": ["Falcone (Lecce)", "Stankovic (Venezia)"]
            },
            "Difensori": {
                "top": ["Dimarco (Inter) - top assoluto", "Bremer (Juve)", "Bisseck (Inter)", "Mancini (Roma)", "Wesley (Roma)"],
                "consigliati": ["Pavlovic (Milan)", "Ostigard (Napoli)", "Cambiaso (Juve)", "Spinazzola (Roma)", "Zappacosta (Atalanta)"],
                "scommesse": ["Rensch (Roma)", "Doekhi (Lazio)", "Jimenez (Fiorentina)", "Kaiki (Como)"]
            },
            "Centrocampisti": {
                "top": ["Frattesi (Lazio)", "Pulisic (Milan)", "Orsolini (Bologna)"],
                "consigliati": ["Vlasic (Torino) - rigorista", "Zaniolo (Udinese)", "Modric (Inter)", "Koné (Juve)", "Perrone (Como)"],
                "scommesse": ["Alajbegovic (Juve)", "Gaetano (Atalanta)", "Stankovic A. (Inter)", "Calò (Frosinone)", "Milla (Como)"]
            },
            "Attaccanti": {
                "top": ["Lautaro (Inter) - 17 gol", "Malen (Roma) - 14 gol", "Thuram (Inter)", "Hojlund (Napoli)", "Goncalo Ramos (Milan)", "Kolo Muani (Juve)"],
                "consigliati": ["Kean (Fiorentina)", "Yildiz (Juve)", "Douvikas (Como)", "Dybala (Roma)", "Davis (Udinese)", "Simeone (Napoli)"],
                "scommesse": ["Alajbegovic K. (Juve)", "Ekhator (Juve)", "Mendy (Cagliari)", "Camarda (Milan)", "Ratkov (Lazio)"]
            }
        }
        for ruolo, dati in consigli.items():
            with st.expander(ruolo):
                st.markdown("**⭐ Top:** " + " • ".join(dati["top"]))
                st.markdown("**👍 Consigliati:** " + " • ".join(dati["consigliati"]))
                st.markdown("**🎲 Scommesse:** " + " • ".join(dati["scommesse"]))
