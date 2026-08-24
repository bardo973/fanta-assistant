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
    {"Nome":"Butez","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":32,"FantaMedia":5.8,"Consiglio":"top","Note":"19 clean sheet, miglior difesa", "Quotazione_2025_26":32},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"Consiglio":"top","Note":"13 clean sheet, 2 rigori parati", "Quotazione_2025_26":29},
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"Consiglio":"top","Note":"18 clean sheet, fantamedia 6", "Quotazione_2025_26":35},
    {"Nome":"Martinez","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":29,"FantaMedia":5.7,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Genoa", "Quotazione_2025_26":23},
    {"Nome":"Meret","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":30,"FantaMedia":5.8,"Consiglio":"consigliato","Note":"Titolare con Allegri", "Quotazione_2025_26":31},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"Consiglio":"consigliato","Note":"Miglior fantamedia, 13 clean sheet", "Quotazione_2025_26":34},
    {"Nome":"De Gea","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":24,"FantaMedia":5.6,"Consiglio":"consigliato","Note":"Stagione del riscatto", "Quotazione_2025_26":26},
    {"Nome":"Falcone","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":17,"FantaMedia":5.5,"Consiglio":"scommessa","Note":"Media voto 6.41, low cost", "Quotazione_2025_26":5},
    {"Nome":"Stankovic","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":13,"FantaMedia":5.3,"Consiglio":"scommessa","Note":"Torna in Serie A", "Quotazione_2025_26":6},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata", "Quotazione_2025_26":39},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta", "Quotazione_2025_26":34},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"Consiglio":"top","Note":"Voti alti e bonus", "Quotazione_2025_26":34},
    {"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":32,"FantaMedia":6.7,"Consiglio":"top","Note":"4 gol, leader difesa Gasperini", "Quotazione_2025_26":27},
    {"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":28,"FantaMedia":6.6,"Consiglio":"top","Note":"5 gol, potenziale stagione alla Gosens", "Quotazione_2025_26":25},
    {"Nome":"Pavlovic","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":33,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5 gol, media 6.24", "Quotazione_2025_26":33},
    {"Nome":"Ostigard","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"5 gol, centrale prolifico", "Quotazione_2025_26":26},
    {"Nome":"Cambiaso","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":29,"FantaMedia":6.6,"Consiglio":"consigliato","Note":"3 gol, 4 assist", "Quotazione_2025_26":23},
    {"Nome":"Spinazzola","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":27,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Sottovalutato, bonus garantiti", "Quotazione_2025_26":26},
    {"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":32,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"Gran gamba, qualità offensiva", "Quotazione_2025_26":34},
    {"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"Ex City, rotazioni Chivu", "Quotazione_2025_26":21},
    {"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"1 gol, 4 assist in 19 partite", "Quotazione_2025_26":11},
    {"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"7 gol in Europa, sostituto Gila", "Quotazione_2025_26":12},
    {"Nome":"Jimenez","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":21,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Torna in Serie A, jolly tattico", "Quotazione_2025_26":8},
    {"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":14,"FantaMedia":5.9,"Consiglio":"scommessa","Note":"Nuovo titolare sinistra", "Quotazione_2025_26":4},
    {"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":48,"FantaMedia":7.5,"Consiglio":"top","Note":"Potenziale top, alla Milinkovic-Savic", "Quotazione_2025_26":52},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"Consiglio":"top","Note":"Cambio ruolo, più appetibile", "Quotazione_2025_26":53},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti", "Quotazione_2025_26":46},
    {"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":52,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"8 gol, 3 assist, rigorista", "Quotazione_2025_26":39},
    {"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":48,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"5 gol, 6 assist, attaccante aggiunto", "Quotazione_2025_26":52},
    {"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Rendimento garantito", "Quotazione_2025_26":42},
    {"Nome":"Koné","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":40,"FantaMedia":6.9,"Consiglio":"consigliato","Note":"Media 6.26, mai sotto sufficienza", "Quotazione_2025_26":43},
    {"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":35,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 4 assist, voti alti", "Quotazione_2025_26":36},
    {"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":38,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"Da prendere con Rowe", "Quotazione_2025_26":36},
    {"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":36,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 3 assist, può crescere", "Quotazione_2025_26":41},
    {"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5-6 gol potenziali", "Quotazione_2025_26":26},
    {"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.6,"Consiglio":"scommessa","Note":"Talentino trequarti, attenzione hype", "Quotazione_2025_26":16},
    {"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Sarri lo vuole, grande intuizione", "Quotazione_2025_26":12},
    {"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Fiducia Chivu, sostituto Calhanoglu", "Quotazione_2025_26":10},
    {"Nome":"Calò","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"10 gol, 14 assist in Serie B", "Quotazione_2025_26":14},
    {"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Solo Yamal più assist in Liga", "Quotazione_2025_26":10},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist", "Quotazione_2025_26":90},
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"Consiglio":"top","Note":"14 gol in mezzo campionato, vice-cannonieri", "Quotazione_2025_26":72},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"Consiglio":"top","Note":"13 gol, 6 assist", "Quotazione_2025_26":67},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol", "Quotazione_2025_26":72},
    {"Nome":"Goncalo Ramos","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Colpo da 70M, titolare Amorim", "Quotazione_2025_26":68},
    {"Nome":"Kolo Muani","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":76,"FantaMedia":7.9,"Consiglio":"top","Note":"Tornato alla Juve, Spalletti lo vuole", "Quotazione_2025_26":69},
    {"Nome":"Kean","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":65,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Doppia cifra garantita", "Quotazione_2025_26":48},
    {"Nome":"Yildiz","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":70,"FantaMedia":7.7,"Consiglio":"consigliato","Note":"10 gol, 6 assist, centro progetto", "Quotazione_2025_26":58},
    {"Nome":"Douvikas","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":65,"FantaMedia":7.8,"Consiglio":"consigliato","Note":"14 gol, sorpresa 2024-25", "Quotazione_2025_26":64},
    {"Nome":"Dybala","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":58,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"Sempre utile, momento della differenza", "Quotazione_2025_26":50},
    {"Nome":"Davis","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":61,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"10 gol, rigorista", "Quotazione_2025_26":53},
    {"Nome":"Scamacca","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":55,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Attenzione infortuni", "Quotazione_2025_26":44},
    {"Nome":"Simeone","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"11 gol, conferma", "Quotazione_2025_26":41},
    {"Nome":"Dovbyk","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":48,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Doppia cifra a Bologna", "Quotazione_2025_26":54},
    {"Nome":"Colombo","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":35,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"7 gol, obiettivo doppia cifra", "Quotazione_2025_26":35},
    {"Nome":"Alajbegovic K.","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.7,"Consiglio":"scommessa","Note":"Colpo di mercato, trequarti", "Quotazione_2025_26":17},
    {"Nome":"Ekhator","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Low cost, potenziale", "Quotazione_2025_26":7},
    {"Nome":"Mendy","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":15,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"2 gol in 8 partite, 2007", "Quotazione_2025_26":9},
    {"Nome":"Camarda","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Vice Ramos, a 1 credito ci sta", "Quotazione_2025_26":4},
    {"Nome":"Ratkov","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Gattuso lo rilancia", "Quotazione_2025_26":8},
]

# ============================================================
# AGGIUNTA COLONNA PREZZO CONSIGLIATO (retrocompatibilità)
# ============================================================
for g in LISTONE_DEFAULT:
    g.setdefault("Prezzo_Consigliato", None)

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
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
        "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if hasattr(st.session_state.stats_storiche, 'to_dict') else [],
        "quotazioni_2025_26": st.session_state.quotazioni_2025_26.to_dict(orient="records") if hasattr(st.session_state.quotazioni_2025_26, 'to_dict') else []
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
            if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
                st.session_state.giocatori_db["Prezzo_Consigliato"] = None
            else:
                st.session_state.giocatori_db["Prezzo_Consigliato"] = pd.to_numeric(
                    st.session_state.giocatori_db["Prezzo_Consigliato"], errors="coerce"
                )
            stats = data.get("stats_storiche", [])
            st.session_state.stats_storiche = pd.DataFrame(stats) if stats else pd.DataFrame()
            q25 = data.get("quotazioni_2025_26", [])
            st.session_state.quotazioni_2025_26 = pd.DataFrame(q25) if q25 else pd.DataFrame()
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
    if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
        st.session_state.giocatori_db["Prezzo_Consigliato"] = None
    st.session_state.stats_storiche = pd.DataFrame()
    st.session_state.quotazioni_2025_26 = pd.DataFrame()  # DataFrame: Nome, Quotazione_2025_26

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

# --- ESPORTA LISTONE ---
st.sidebar.subheader("📤 Esporta Listone")
exp_fmt = st.sidebar.radio("Formato", ["CSV", "Excel"], horizontal=True, key="exp_fmt")
if st.sidebar.button("📥 Scarica Listone", use_container_width=True):
    df_exp = st.session_state.giocatori_db.copy()
    if "Prezzo_Consigliato" not in df_exp.columns:
        df_exp["Prezzo_Consigliato"] = None
    # Riordina colonne
    cols_exp = [c for c in ["Nome","Ruolo","Squadra_SerieA","Quotazione","Prezzo_Consigliato","FantaMedia","Consiglio","Note","Quotazione_2025_26"] if c in df_exp.columns]
    df_exp = df_exp[cols_exp]
    if exp_fmt == "CSV":
        csv = df_exp.to_csv(index=False, encoding="utf-8-sig")
        st.sidebar.download_button(
            label="⬇️ Scarica CSV",
            data=csv,
            file_name="listone_fantamanager_2026_27.csv",
            mime="text/csv",
            use_container_width=True
        )
    else:
        import io
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
            df_exp.to_excel(writer, index=False, sheet_name="Listone")
        st.sidebar.download_button(
            label="⬇️ Scarica Excel",
            data=buffer.getvalue(),
            file_name="listone_fantamanager_2026_27.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

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
                elif 'quot' in cl or 'valore' in cl or 'fc' in cl or 'qt' in cl:
                    if '2025' in cl or 'prec' in cl or 'old' in cl or 'last' in cl or 'precedente' in cl:
                        col_mappa[col] = 'Quotazione_2025_26'
                    else:
                        col_mappa[col] = 'Quotazione'
                elif 'fm' in cl or 'fantamedia' in cl or 'media' in cl: col_mappa[col] = 'FantaMedia'
                elif 'prezzo' in cl or 'consigliato' in cl or 'suggerito' in cl or 'acquisto' in cl or 'buy' in cl: col_mappa[col] = 'Prezzo_Consigliato'
            df_load = df_load.rename(columns=col_mappa)
            if 'Nome' in df_load.columns:
                df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                for c, d in [('Ruolo','C'),('Squadra_SerieA','N/D'),('Quotazione',10),('FantaMedia',6.0),('Quotazione_2025_26',None)]:
                    if c not in df_load.columns: df_load[c] = d
                if 'Quotazione_2025_26' in df_load.columns:
                    df_load['Quotazione_2025_26'] = pd.to_numeric(df_load['Quotazione_2025_26'], errors='coerce')
                df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                fm = df_load['FantaMedia']
                if isinstance(fm, pd.DataFrame): fm = fm.iloc[:,0]
                df_load['FantaMedia'] = pd.to_numeric(fm.astype(str).str.replace(',','.',regex=False), errors='coerce').fillna(6.0)
                if 'Consiglio' not in df_load.columns: df_load['Consiglio'] = 'consigliato'
                if 'Note' not in df_load.columns: df_load['Note'] = ''
                if 'Prezzo_Consigliato' not in df_load.columns: df_load['Prezzo_Consigliato'] = None
                else:
                    df_load['Prezzo_Consigliato'] = pd.to_numeric(df_load['Prezzo_Consigliato'], errors='coerce')
                cols_final = ['Nome','Ruolo','Squadra_SerieA','Quotazione','FantaMedia','Consiglio','Note','Prezzo_Consigliato']
                if 'Quotazione_2025_26' in df_load.columns: cols_final.append('Quotazione_2025_26')
                st.session_state.giocatori_db = df_load[cols_final]
                save_state()
                st.sidebar.success(f"✅ Listone importato! {len(df_load)} giocatori.")
            else:
                st.sidebar.error("Colonna 'Nome' mancante.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

# --- IMPORTA ROSE CON ANTEPRIMA E SCADENZE ---
with st.sidebar.expander("📋 Importa Rose (con anteprima)"):
    st.markdown("""
    **Colonne attese:** Squadra, Nome, Ruolo, Costo

    **Opzionali per scadenze:** Scadenza_Anno, Scadenza_Mese (es. 2028, 6)
    Se mancano, il contratto parte da 2026 per 4 anni.
    """)

    up_rose = st.file_uploader("File Rose", type=["csv","xlsx"], key="ur")

    if up_rose is not None:
        try:
            if up_rose.name.endswith('.csv'):
                df_r = pd.read_csv(up_rose, encoding='utf-8', on_bad_lines='skip')
            else:
                xl = pd.ExcelFile(up_rose)
                sheets = xl.sheet_names
                if len(sheets) > 1:
                    sheet_sel = st.selectbox("Seleziona sheet", sheets, key="sheet_sel")
                    df_r = pd.read_excel(up_rose, sheet_name=sheet_sel)
                else:
                    df_r = pd.read_excel(up_rose)

            df_r.columns = [str(c).strip() for c in df_r.columns]
            st.write(f"**File letto:** {len(df_r)} righe, colonne: {', '.join(df_r.columns)}")

            def find_best_match(options, keywords):
                for kw in keywords:
                    for opt in options:
                        if kw in str(opt).lower():
                            return opt
                return None

            cols = [""] + list(df_r.columns)
            col_sq = st.selectbox("Colonna SQUADRA", cols, 
                                   index=cols.index(find_best_match(cols, ['squadra','team','proprietario','fantateam'])) if find_best_match(cols, ['squadra','team','proprietario','fantateam']) in cols else 0,
                                   key="map_sq")
            col_nm = st.selectbox("Colonna NOME", cols,
                                   index=cols.index(find_best_match(cols, ['nome','giocatore','player'])) if find_best_match(cols, ['nome','giocatore','player']) in cols else 0,
                                   key="map_nm")
            col_rl = st.selectbox("Colonna RUOLO (opzionale)", cols,
                                   index=cols.index(find_best_match(cols, ['ruolo','r ','role'])) if find_best_match(cols, ['ruolo','r ','role']) in cols else 0,
                                   key="map_rl")
            col_cs = st.selectbox("Colonna COSTO (opzionale)", cols,
                                   index=cols.index(find_best_match(cols, ['costo','prezzo','pagato','quotazione','quot','valore'])) if find_best_match(cols, ['costo','prezzo','pagato','quotazione','quot','valore']) in cols else 0,
                                   key="map_cs")
            col_scad_a = st.selectbox("Colonna SCADENZA ANNO (opzionale)", cols,
                                   index=cols.index(find_best_match(cols, ['scadenza anno','scadenza_anno','scad_anno','anno_scadenza','fine','fine_contratto'])) if find_best_match(cols, ['scadenza anno','scadenza_anno','scad_anno','anno_scadenza','fine','fine_contratto']) in cols else 0,
                                   key="map_scad_a")
            col_scad_m = st.selectbox("Colonna SCADENZA MESE (opzionale)", cols,
                                   index=cols.index(find_best_match(cols, ['scadenza mese','scadenza_mese','scad_mese','mese_scadenza','mese_fine'])) if find_best_match(cols, ['scadenza mese','scadenza_mese','scad_mese','mese_scadenza','mese_fine']) in cols else 0,
                                   key="map_scad_m")

            if col_sq and col_nm and col_sq != "" and col_nm != "":
                st.subheader("👁️ Anteprima dati")
                preview_cols = [col_sq, col_nm]
                if col_rl and col_rl != "": preview_cols.append(col_rl)
                if col_cs and col_cs != "": preview_cols.append(col_cs)
                if col_scad_a and col_scad_a != "": preview_cols.append(col_scad_a)
                if col_scad_m and col_scad_m != "": preview_cols.append(col_scad_m)
                st.dataframe(df_r[preview_cols].head(10), use_container_width=True)

                if st.button("✅ IMPORTA ROSE", type="primary", use_container_width=True):
                    count = 0
                    skipped = 0
                    errors = []

                    for idx, row in df_r.iterrows():
                        try:
                            sq_nome = str(row[col_sq]).strip().upper() if pd.notna(row[col_sq]) else ""
                            if not sq_nome: continue

                            sq_match = None
                            for s in NOMI_SQUADRE:
                                if s.upper() == sq_nome or s.upper() in sq_nome or sq_nome in s.upper():
                                    sq_match = s
                                    break
                            if not sq_match:
                                skipped += 1
                                continue

                            g_nome = str(row[col_nm]).strip() if pd.notna(row[col_nm]) else ""
                            if not g_nome or g_nome.lower() in ['nan', 'none', 'null', '']:
                                continue

                            g_ruolo = str(row[col_rl]).strip().upper() if col_rl and col_rl != "" and pd.notna(row[col_rl]) else "C"
                            if len(g_ruolo) > 1 and g_ruolo[0] in "PDCA":
                                g_ruolo = g_ruolo[0]
                            elif g_ruolo not in ["P","D","C","A"]:
                                g_ruolo = "C"

                            g_costo = 1
                            if col_cs and col_cs != "" and pd.notna(row[col_cs]):
                                try:
                                    g_costo = int(float(str(row[col_cs]).replace(',','.')))
                                except:
                                    g_costo = 1

                            # === SCADENZA CONTRATTO DAL FILE ===
                            scad_anno = None
                            scad_mese = None
                            if col_scad_a and col_scad_a != "" and pd.notna(row[col_scad_a]):
                                try:
                                    val = row[col_scad_a]
                                    # Se è già una data (Timestamp/datetime), estrai anno/mese
                                    if hasattr(val, 'year'):
                                        scad_anno = int(val.year)
                                        scad_mese = int(val.month)
                                    else:
                                        # Prova a convertire come numero (anno diretto o seriale Excel)
                                        num = float(str(val).replace(',','.'))
                                        if num > 40000:  # Numero seriale Excel
                                            dt = pd.to_datetime(int(num), unit='D', origin='1899-12-30')
                                            scad_anno = int(dt.year)
                                            scad_mese = int(dt.month)
                                        else:
                                            scad_anno = int(num)
                                except Exception:
                                    scad_anno = None
                                    scad_mese = None
                            if col_scad_m and col_scad_m != "" and pd.notna(row[col_scad_m]) and scad_mese is None:
                                try:
                                    val = row[col_scad_m]
                                    if hasattr(val, 'month'):
                                        scad_mese = int(val.month)
                                    else:
                                        scad_mese = int(float(str(val).replace(',','.')))
                                except Exception:
                                    scad_mese = None

                            # Cerca info nel listone
                            db_g = st.session_state.giocatori_db
                            match_db = db_g[db_g['Nome'].str.lower() == g_nome.lower()]
                            sq_sa = "N/D"
                            quot = 10
                            fm = 6.0
                            if not match_db.empty:
                                sq_sa = match_db.iloc[0]['Squadra_SerieA']
                                quot = int(match_db.iloc[0]['Quotazione'])
                                fm = float(match_db.iloc[0]['FantaMedia'])
                                g_ruolo = str(match_db.iloc[0]['Ruolo'])

                            if any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_match]["rosa"]):
                                skipped += 1
                                continue

                            if st.session_state.squadre[sq_match]["crediti"] < g_costo:
                                errors.append(f"{sq_match}: crediti insufficienti per {g_nome} ({g_costo}cr)")
                                continue

                            # === CONTRATTO: Scadenza_Anno è la fonte di verità ===
                            if not scad_anno:
                                # Nessuna scadenza fornita → nuovo acquisto default
                                scad_anno = ANNO_CORRENTE + CONTRATTO_ANNI

                            st.session_state.squadre[sq_match]["crediti"] -= g_costo
                            entry = {
                                "Nome": g_nome,
                                "Ruolo": g_ruolo,
                                "Squadra_SerieA": sq_sa,
                                "Quotazione": quot,
                                "FantaMedia": fm,
                                "Costo_Acquisto": g_costo,
                                "Scadenza_Anno": scad_anno,
                            }
                            if scad_mese:
                                entry["Scadenza_Mese"] = scad_mese

                            st.session_state.squadre[sq_match]["rosa"].append(entry)
                            st.session_state.contratti[g_nome] = {
                                "squadra": sq_match,
                                "scadenza_anno": scad_anno,
                                "scadenza_mese": scad_mese
                            }
                            count += 1

                        except Exception as e:
                            errors.append(f"Riga {idx}: {e}")

                    save_state()
                    st.sidebar.success(f"✅ Importati {count} giocatori! ({skipped} saltati)")
                    if errors:
                        with st.sidebar.expander("⚠️ Errori/Avvisi"):
                            for e in errors[:20]:
                                st.write(f"- {e}")
                            if len(errors) > 20:
                                st.write(f"... e altri {len(errors)-20} errori")
                    st.rerun()
            else:
                st.warning("Seleziona almeno le colonne Squadra e Nome.")

        except Exception as e:
            st.sidebar.error(f"Errore lettura file: {e}")

# --- IMPORTA QUOTAZIONI 2025/26 ---
with st.sidebar.expander("📊 Importa Quotazioni 2025/26"):
    st.markdown("""
    Carica un file con le quotazioni dell'ultima giornata 2025/2026.

    **Colonne attese:** Nome, Quotazione (o Quotazione_2025_26)

    Queste quotazioni verranno usate come **prezzo di rimborso** quando un giocatore
    non viene trovato nel listone attuale 2026/27.
    """)
    up_q25 = st.file_uploader("File Quotazioni 2025/26", type=["csv","xlsx"], key="uq25")
    if up_q25 is not None:
        try:
            if up_q25.name.endswith('.csv'):
                df_q = pd.read_csv(up_q25, encoding='utf-8', on_bad_lines='skip')
            else:
                df_q = pd.read_excel(up_q25)
            df_q.columns = [str(c).strip() for c in df_q.columns]

            # Mappa colonne
            col_map_q = {}
            for col in df_q.columns:
                cl = str(col).lower()
                if 'nome' in cl or 'giocatore' in cl or 'player' in cl:
                    col_map_q[col] = 'Nome'
                elif 'quot' in cl or 'valore' in cl or 'prezzo' in cl or 'fc' in cl:
                    col_map_q[col] = 'Quotazione_2025_26'
            df_q = df_q.rename(columns=col_map_q)

            if 'Nome' not in df_q.columns:
                st.sidebar.error("Colonna 'Nome' mancante nel file.")
            else:
                if 'Quotazione_2025_26' not in df_q.columns:
                    # Prova a usare la seconda colonna numerica
                    for col in df_q.columns:
                        if col != 'Nome' and pd.api.types.is_numeric_dtype(df_q[col]):
                            df_q['Quotazione_2025_26'] = pd.to_numeric(df_q[col], errors='coerce')
                            break

                df_q['Quotazione_2025_26'] = pd.to_numeric(df_q['Quotazione_2025_26'], errors='coerce').fillna(1).astype(int)
                df_q = df_q[['Nome', 'Quotazione_2025_26']].dropna()
                st.session_state.quotazioni_2025_26 = df_q
                save_state()
                st.sidebar.success(f"✅ Caricate {len(df_q)} quotazioni 2025/26!")

                # Mostra anteprima
                with st.sidebar.expander("👁️ Anteprima"):
                    st.dataframe(df_q.head(10), use_container_width=True)
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

    if not st.session_state.quotazioni_2025_26.empty:
        st.sidebar.caption(f"📊 {len(st.session_state.quotazioni_2025_26)} quotazioni 2025/26 caricate")
        if st.button("🗑️ Cancella quotazioni 2025/26", use_container_width=True):
            st.session_state.quotazioni_2025_26 = pd.DataFrame()
            save_state()
            st.sidebar.success("Cancellate!")
            st.rerun()

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
    "📋 Rose, Crediti & Contratti",
    "📈 Statistiche Storiche"
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
        if "Quotazione_2025_26" in df.columns:
            df["Variazione_%"] = round((df["Quotazione"] - df["Quotazione_2025_26"]) / df["Quotazione_2025_26"].replace(0,1) * 100, 1)
        else:
            df["Variazione_%"] = None

        assegnati = {}
        for sq, dati in st.session_state.squadre.items():
            for g in dati["rosa"]:
                nome_base = g["Nome"].replace("(PRESTITO da", "").strip()
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
        display_cols = [c for c in ["Nome","Ruolo","Squadra_SerieA","Quotazione","Prezzo_Consigliato","Quotazione_2025_26","Variazione_%","FantaMedia","Indice_Affare","Proprietario","Consiglio","Note"] if c in df_f.columns]
        st.dataframe(df_f[display_cols], use_container_width=True)

        st.markdown("---")
        st.subheader("✏️ Modifica Prezzi Consigliati")
        st.caption("Modifica il prezzo consigliato per l'acquisto direttamente nella tabella sottostante.")
        editor_cols = [c for c in ["Nome","Ruolo","Squadra_SerieA","Quotazione","FantaMedia","Prezzo_Consigliato","Consiglio","Note"] if c in df.columns]
        df_edit = df[editor_cols].copy()
        df_edited = st.data_editor(
            df_edit,
            column_config={
                "Prezzo_Consigliato": st.column_config.NumberColumn(
                    "Prezzo Consigliato",
                    help="Prezzo ideale per acquistare il giocatore all'asta",
                    min_value=0,
                    max_value=500,
                    step=1,
                    format="%d cr"
                ),
                "Nome": st.column_config.TextColumn("Nome", disabled=True),
                "Ruolo": st.column_config.TextColumn("Ruolo", disabled=True),
                "Squadra_SerieA": st.column_config.TextColumn("Squadra Serie A", disabled=True),
                "Quotazione": st.column_config.NumberColumn("Quotazione", disabled=True),
                "FantaMedia": st.column_config.NumberColumn("FantaMedia", disabled=True),
                "Consiglio": st.column_config.TextColumn("Consiglio", disabled=True),
                "Note": st.column_config.TextColumn("Note", disabled=True),
            },
            use_container_width=True,
            num_rows="fixed",
            key="editor_prezzi"
        )
        if st.button("💾 Salva Prezzi Consigliati", type="primary"):
            # Aggiorna solo la colonna Prezzo_Consigliato
            if "Prezzo_Consigliato" in df_edited.columns:
                st.session_state.giocatori_db = st.session_state.giocatori_db.drop(columns=["Prezzo_Consigliato"], errors="ignore")
                st.session_state.giocatori_db = st.session_state.giocatori_db.merge(
                    df_edited[["Nome", "Prezzo_Consigliato"]], on="Nome", how="left"
                )
                save_state()
                st.success("✅ Prezzi consigliati salvati!")
                st.rerun()

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
            wl_cols = ["Nome","Ruolo","Squadra_SerieA","Quotazione","Prezzo_Consigliato","FantaMedia","Indice_Affare","Proprietario"]
            if "Quotazione_2025_26" in df_wl.columns: wl_cols.insert(5, "Quotazione_2025_26")
            if "Variazione_%" in df_wl.columns: wl_cols.insert(6, "Variazione_%")
            st.dataframe(df_wl[wl_cols], use_container_width=True)
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
            in_rosa = set()
            for d in st.session_state.squadre.values():
                for g in d["rosa"]:
                    in_rosa.add(g["Nome"].lower())
            svinc = db[~db["Nome"].str.lower().isin(in_rosa)]
            if len(svinc) > 0:
                g_sel = st.selectbox("Giocatore", svinc["Nome"].values)
                info = svinc[svinc["Nome"] == g_sel].iloc[0]
                pc = info.get('Prezzo_Consigliato')
                pc_txt = f" | 💡 Prezzo Consigliato: **{int(pc)}cr**" if pd.notna(pc) else ""
                st.write(f"Ruolo: **{info['Ruolo']}** | Squadra: **{info['Squadra_SerieA']}** | Quotazione: **{int(info['Quotazione'])}** | FM: **{info['FantaMedia']}** | Consiglio: **{info.get('Consiglio','')}**{pc_txt}")
                default_price = int(pc) if pd.notna(pc) else int(info["Quotazione"])
                prezzo = st.number_input("Prezzo pagato", min_value=1, max_value=max(1,cred), value=default_price, key="acq_p")
                if st.button("Conferma Acquisto"):
                    if cred >= prezzo:
                        st.session_state.squadre[sq]["crediti"] -= prezzo
                        scad_acq = ANNO_CORRENTE + CONTRATTO_ANNI
                        st.session_state.squadre[sq]["rosa"].append({
                            "Nome": g_sel, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                            "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                            "Costo_Acquisto": prezzo, "Scadenza_Anno": scad_acq
                        })
                        st.session_state.contratti[g_sel] = {"squadra": sq, "scadenza_anno": scad_acq}
                        st.session_state.storico_mercato.insert(0, {
                            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Operazione": "ACQUISTO",
                            "Dettagli": f"{sq} acquista {g_sel} ({info['Ruolo']}) per {prezzo}cr — Contratto fino al {scad_acq}"
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
        rosa_proprieta = [g for g in rosa if "(PRESTITO da" not in g.get("Nome", "")]
        if rosa_proprieta:
            nomi = [g["Nome"] for g in rosa_proprieta]
            g_v = st.selectbox("Giocatore", nomi, key="vend_g")
            g_obj = next(g for g in rosa_proprieta if g["Nome"] == g_v)

            # PREZZO DI SVINCOLO: listone 2026/27 → quotazioni 2025/26 caricate → costo acquisto
            db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].str.lower() == g_v.lower()]
            if not db_match.empty:
                prezzo_listone = int(db_match.iloc[0]["Quotazione"])
                st.info(f"💡 Quotazione attuale listone 2026/27: **{prezzo_listone}cr** (valore di rimborso)")
            else:
                # Fallback 1: quotazioni 2025/26 caricate
                q25_match = None
                if not st.session_state.quotazioni_2025_26.empty and "Nome" in st.session_state.quotazioni_2025_26.columns:
                    q25_match = st.session_state.quotazioni_2025_26[
                        st.session_state.quotazioni_2025_26["Nome"].str.lower() == g_v.lower()
                    ]
                if q25_match is not None and not q25_match.empty:
                    prezzo_listone = int(q25_match.iloc[0]["Quotazione_2025_26"])
                    st.info(f"💡 Giocatore non nel listone 2026/27. Rimborso da quotazioni 2025/26: **{prezzo_listone}cr**")
                else:
                    # Fallback 2: costo d'acquisto
                    prezzo_listone = g_obj.get("Costo_Acquisto", 10)
                    st.info(f"💡 Giocatore non trovato né nel listone né nelle quotazioni 2025/26. Rimborso al costo d'acquisto: **{prezzo_listone}cr**")

            prezzo_v = st.number_input("Prezzo rimborso (modificabile)", min_value=0, value=prezzo_listone, key="vend_p")

            if st.button("Conferma Vendita"):
                st.session_state.squadre[sq_v]["rosa"] = [g for g in rosa if g["Nome"] != g_v]
                st.session_state.squadre[sq_v]["crediti"] += prezzo_v
                if g_v in st.session_state.contratti:
                    del st.session_state.contratti[g_v]
                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "SVINCOLO",
                    "Dettagli": f"{sq_v} svincola {g_v}, incassa {prezzo_v}cr (quotazione listone)"
                })
                save_state()
                st.success(f"🗑️ {g_v} svincolato! Incassati {prezzo_v}cr.")
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

    if st.session_state.prestiti:
        st.markdown("---")
        st.subheader("📋 Prestiti Attivi")
        df_prest = pd.DataFrame(st.session_state.prestiti)
        st.dataframe(df_prest, use_container_width=True)

        st.subheader("Termina prestito")
        nomi_prestito = list(df_prest["Giocatore"].unique())
        gp = st.selectbox("Seleziona giocatore", nomi_prestito, key="term_p")
        if st.button("Termina prestito e riporta in rosa originale"):
            to_remove = None
            for i, p in enumerate(st.session_state.prestiti):
                if p["Giocatore"] == gp:
                    to_remove = i
                    da_sq = p["Da"]
                    a_sq = p["A"]
                    st.session_state.squadre[a_sq]["rosa"] = [
                        g for g in st.session_state.squadre[a_sq]["rosa"]
                        if g.get("Nome_Originale") != gp and g["Nome"] != gp
                    ]
                    g_orig = None
                    for g in st.session_state.squadre[da_sq]["rosa"]:
                        if g["Nome"] == gp:
                            g_orig = g
                            break
                    if not g_orig:
                        db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"] == gp]
                        if not db_match.empty:
                            info = db_match.iloc[0]
                            g_orig = {
                                "Nome": gp, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                                "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                                "Costo_Acquisto": 0, "Scadenza_Anno": ANNO_CORRENTE + CONTRATTO_ANNI
                            }
                        else:
                            g_orig = {"Nome": gp, "Ruolo": "C", "Squadra_SerieA": "N/D", "Quotazione": 1, "FantaMedia": 6.0, "Costo_Acquisto": 0, "Scadenza_Anno": ANNO_CORRENTE + CONTRATTO_ANNI}
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
                    display = rosa_df.copy()

                    # === EVIDENZIAZIONE SCADENZA ===
                    # Assicurati che Scadenza_Anno esista sempre
                    if "Scadenza_Anno" not in display.columns:
                        display["Scadenza_Anno"] = ANNO_CORRENTE + CONTRATTO_ANNI
                    display["Scadenza_Anno"] = pd.to_numeric(display["Scadenza_Anno"], errors="coerce").fillna(ANNO_CORRENTE + CONTRATTO_ANNI).astype(int)

                    def stato_scadenza(row):
                        sa = int(row["Scadenza_Anno"])
                        sm = int(row["Scadenza_Mese"]) if "Scadenza_Mese" in row and pd.notna(row["Scadenza_Mese"]) else None
                        # Testo = dato grezzo della colonna D (Scadenza_Anno), con mese se presente
                        if sm:
                            testo = f"{sm}/{sa}"
                        else:
                            testo = str(sa)
                        # Emoji colore in base all'anno
                        if sa < ANNO_CORRENTE:
                            return f"🔴 {testo}"
                        elif sa == ANNO_CORRENTE:
                            return f"🟠 {testo}"
                        elif sa == ANNO_CORRENTE + 1:
                            return f"🟡 {testo}"
                        else:
                            return f"🟢 {testo}"

                    display["Stato_Contratto"] = display.apply(stato_scadenza, axis=1)

                    # Colonna scadenza leggibile (sempre presente)
                    display["Scadenza"] = display["Scadenza_Anno"].astype(str)
                    if "Scadenza_Mese" in display.columns:
                        display["Scadenza"] = display["Scadenza_Mese"].astype(str) + "/" + display["Scadenza_Anno"].astype(str)

                    # Aggiungi confronto quotazione 2025/26 se presente nel listone
                    if "Quotazione_2025_26" in st.session_state.giocatori_db.columns:
                        db_q = st.session_state.giocatori_db[["Nome","Quotazione_2025_26"]].copy()
                        display = display.merge(db_q, on="Nome", how="left")
                        display["Variazione_%"] = round((display["Quotazione"] - display["Quotazione_2025_26"]) / display["Quotazione_2025_26"].replace(0,1) * 100, 1)

                    # Rimuovi colonne tecniche non utili alla visualizzazione
                    hide_cols = ["Anno_Acquisto", "Contratto_Anni"]
                    display = display.drop(columns=[c for c in hide_cols if c in display.columns])

                    # Riordina colonne per leggibilità (solo colonne che esistono)
                    first_cols = [c for c in ["Nome", "Ruolo", "Stato_Contratto", "Scadenza"] if c in display.columns]
                    other_cols = [c for c in display.columns if c not in first_cols]
                    display = display[first_cols + other_cols]

                    st.dataframe(display, use_container_width=True)

                    # Alert se ci sono giocatori in scadenza
                    in_scadenza = display[display["Stato_Contratto"].str.contains("🟠|🔴")]
                    if not in_scadenza.empty:
                        st.warning(f"⚠️ {len(in_scadenza)} giocatori in scadenza: " + ", ".join(in_scadenza["Nome"].tolist()))
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
        st.subheader(f"📄 Contratti — Scadenze")
        if st.session_state.contratti:
            rows = []
            for nome, c in st.session_state.contratti.items():
                scad = ""
                if c.get("scadenza_mese") and c.get("scadenza_anno"):
                    scad = f"{c['scadenza_mese']}/{c['scadenza_anno']}"
                elif c.get("scadenza_anno"):
                    scad = str(c["scadenza_anno"])
                else:
                    scad = "N/D"
                rows.append({"Giocatore":nome, "Squadra":c["squadra"], "Scadenza":scad})
            df_contr = pd.DataFrame(rows)
            # Ordina per scadenza
            df_contr = df_contr.sort_values("Scadenza")
            st.dataframe(df_contr, use_container_width=True)
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

# ============================================================
# 5. STATISTICHE STORICHE
# ============================================================
elif menu == "📈 Statistiche Storiche":
    st.header("📈 Statistiche Storiche — Ultimi 3 Anni")

    st.markdown("""
    Carica un file CSV/Excel con le statistiche storiche dei giocatori.

    **Colonne attese:** Nome, Stagione, Gol, Assist, FantaMedia, Partite, Rigori, Ammonizioni, Espulsioni
    (puoi aggiungere altre colonne, verranno mostrate automaticamente)
    """)

    up_stats = st.file_uploader("File Statistiche Storiche", type=["csv","xlsx"], key="us")
    if up_stats is not None:
        try:
            if up_stats.name.endswith('.csv'):
                df_s = pd.read_csv(up_stats, encoding='utf-8', on_bad_lines='skip')
            else:
                df_s = pd.read_excel(up_stats)
            df_s.columns = [str(c).strip() for c in df_s.columns]
            # Mappa colonne base
            col_map = {}
            for col in df_s.columns:
                cl = str(col).lower()
                if 'nome' in cl or 'giocatore' in cl: col_map[col] = 'Nome'
                elif 'stagione' in cl or 'anno' in cl or 'season' in cl: col_map[col] = 'Stagione'
                elif 'gol' in cl or 'goal' in cl: col_map[col] = 'Gol'
                elif 'assist' in cl: col_map[col] = 'Assist'
                elif 'fm' in cl or 'fantamedia' in cl or 'media' in cl: col_map[col] = 'FantaMedia'
                elif 'partite' in cl or 'presenze' in cl or 'pg' in cl: col_map[col] = 'Partite'
                elif 'rigor' in cl: col_map[col] = 'Rigori'
                elif 'amm' in cl or 'yellow' in cl: col_map[col] = 'Ammonizioni'
                elif 'esp' in cl or 'red' in cl: col_map[col] = 'Espulsioni'
            df_s = df_s.rename(columns=col_map)
            st.session_state.stats_storiche = df_s
            save_state()
            st.success(f"✅ Caricate statistiche per {len(df_s)} righe!")
        except Exception as e:
            st.error(f"Errore: {e}")

    if not st.session_state.stats_storiche.empty:
        df_stats = st.session_state.stats_storiche.copy()

        st.subheader("🔍 Visualizza per giocatore")
        giocatori_stats = df_stats["Nome"].unique() if "Nome" in df_stats.columns else []
        if len(giocatori_stats) > 0:
            g_sel = st.selectbox("Seleziona giocatore", sorted(giocatori_stats), key="stats_sel")
            df_g = df_stats[df_stats["Nome"] == g_sel]

            st.markdown(f"**{g_sel}** — {len(df_g)} stagioni trovate")
            st.dataframe(df_g, use_container_width=True)

            # Grafici se ci sono dati numerici
            numeric_cols = df_g.select_dtypes(include=['number']).columns.tolist()
            numeric_cols = [c for c in numeric_cols if c not in ['Stagione'] and 'Stagione' not in c]
            if numeric_cols and "Stagione" in df_g.columns:
                st.subheader("📊 Andamento")
                chart_data = df_g.set_index("Stagione")[numeric_cols]
                st.line_chart(chart_data)

            # Confronto con listone attuale
            db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].str.lower() == g_sel.lower()]
            if not db_match.empty:
                st.info(f"💡 Quotazione attuale listone: **{int(db_match.iloc[0]['Quotazione'])}cr** | FantaMedia: **{db_match.iloc[0]['FantaMedia']}** | Squadra: **{db_match.iloc[0]['Squadra_SerieA']}**")

        st.markdown("---")
        st.subheader("📋 Tabella completa")
        st.dataframe(df_stats, use_container_width=True)

        if st.button("🗑️ Cancella statistiche storiche"):
            st.session_state.stats_storiche = pd.DataFrame()
            save_state()
            st.rerun()
    else:
        st.info("Nessuna statistica storica caricata. Usa l'uploader sopra.")
