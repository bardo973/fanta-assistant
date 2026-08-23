import streamlit as st
import pandas as pd
import json
import os
import re
from datetime import datetime

st.set_page_config(page_title="FantaManager 2026/27 - 10 Squadre", page_icon="⚽", layout="wide")

# ============================================================
# CONFIG
# ============================================================
SAVE_FILE = "fantamanager_save.json"
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
ANNO_CORRENTE = 2026
VINCOLI_ROSA = {"P": 3, "D": 9, "C": 9, "A": 7}
CONTRATTO_ANNI = 4
MESE_DEFAULT_SCADENZA = 9

MESI_NOMI = {1:"gen", 2:"feb", 3:"mar", 4:"apr", 5:"mag", 6:"giu",
             7:"lug", 8:"ago", 9:"set", 10:"ott", 11:"nov", 12:"dic"}

MESI_NOMI_INV = {v:k for k,v in MESI_NOMI.items()}
MESI_NOMI_INV["sett"] = 9
MESI_NOMI_INV["set"] = 9

def fmt_scadenza(mese, anno):
    if mese is not None and anno is not None:
        try:
            return f"{MESI_NOMI.get(int(mese), '???')}'{str(int(anno))[-2:]}"
        except:
            return str(anno)
    elif anno is not None:
        return f"'{str(int(anno))[-2:]}"
    return "N/D"

def parse_scadenza(val):
    """Parsa vari formati di scadenza: 'set\'29', 'sett\'29', 'sett 29', '09/2029', '2029-09', 'giu\'28', ecc."""
    if pd.isna(val) or val is None:
        return None, None
    s = str(val).strip().lower()
    if not s or s in ['nan','none','null','']:
        return None, None

    # Pattern tipo "set'29" o "sett'29" o "giu'28" o "sett 29" (con spazio)
    m = re.match(r"^(gen|feb|mar|apr|mag|giu|lug|ago|set|sett|ott|nov|dic)[\'\s]*([0-9]{2,4})$", s)
    if m:
        mese_str = m.group(1)
        anno_str = m.group(2)
        mese = MESI_NOMI_INV.get(mese_str)
        anno = int(anno_str)
        if anno < 100:
            anno = 2000 + anno
        return mese, anno

    # Pattern tipo "09/2029" o "9/2029"
    m = re.match(r"^([0-9]{1,2})[/\-\.]([0-9]{4})$", s)
    if m:
        mese = int(m.group(1))
        anno = int(m.group(2))
        return mese, anno

    # Pattern tipo "2029/09" o "2029-09"
    m = re.match(r"^([0-9]{4})[/\-\.]([0-9]{1,2})$", s)
    if m:
        anno = int(m.group(1))
        mese = int(m.group(2))
        return mese, anno

    # Pattern tipo "2029" (solo anno)
    m = re.match(r"^([0-9]{4})$", s)
    if m:
        return None, int(m.group(1))

    # Pattern tipo "29" (solo anno a 2 cifre)
    m = re.match(r"^([0-9]{2})$", s)
    if m:
        return None, 2000 + int(m.group(1))

    return None, None

def prezzo_consigliato(quotazione, fantamedia):
    """Calcola un range di prezzo consigliato"""
    try:
        q = float(quotazione)
        fm = float(fantamedia)
        if fm >= 7.5:
            min_p = int(q * 0.9)
            max_p = int(q * 1.3)
        elif fm >= 6.5:
            min_p = int(q * 0.85)
            max_p = int(q * 1.15)
        else:
            min_p = int(q * 0.6)
            max_p = int(q * 1.0)
        return min_p, max_p
    except:
        return 1, int(quotazione) if quotazione else 10

def analisi_scambio(oggetti1, oggetti2, d1, d2):
    """Analizza uno scambio e restituisce un dict con i dati comparativi"""
    def somma_stats(oggetti):
        tot_quot = sum(g.get("Quotazione", 0) for g in oggetti)
        tot_costo = sum(g.get("Costo_Acquisto", 0) for g in oggetti)
        avg_fm = sum(g.get("FantaMedia", 0) for g in oggetti) / len(oggetti) if oggetti else 0
        return {"quot": tot_quot, "costo": tot_costo, "fm": round(avg_fm, 2), "n": len(oggetti)}

    s1 = somma_stats(oggetti1)
    s2 = somma_stats(oggetti2)

    # Aggiungi conguaglio come "valore" (1 credito = 1 quotazione approx)
    val1 = s1["quot"] + d1
    val2 = s2["quot"] + d2

    delta_quot = val2 - val1
    delta_fm = s2["fm"] - s1["fm"] if s1["n"] > 0 and s2["n"] > 0 else 0


# ============================================================
# NUOVE FUNZIONI (vincoli, stats, scadenze, prestiti)
# ============================================================
def get_stats_giocatore(nome):
    """Recupera le statistiche storiche di un giocatore"""
    df = st.session_state.stats_storiche
    if df.empty or "Nome" not in df.columns:
        return None
    res = df[df["Nome"].str.lower() == nome.lower()]
    if res.empty:
        return None
    return res

def is_scadenza_prossima(g):
    """True se il contratto scade entro 6 mesi (entro feb 2027)"""
    anno = g.get("Scadenza_Anno")
    mese = g.get("Scadenza_Mese")
    if not anno or not mese:
        return False
    if anno < 2027:
        return True
    if anno == 2027 and mese <= 2:
        return True
    return False

def conteggio_rosa(rosa):
    """Conta i giocatori di proprietà (esclusi prestiti in entrata) per ruolo"""
    c = {"P": 0, "D": 0, "C": 0, "A": 0}
    for g in rosa:
        if "(PRESTITO da" in g.get("Nome", ""):
            continue
        r = g.get("Ruolo", "C")
        if r in c:
            c[r] += 1
    return c

def puo_acquistare(rosa, ruolo):
    """Verifica se si può acquistare un giocatore di quel ruolo rispettando i vincoli"""
    c = conteggio_rosa(rosa)
    return c.get(ruolo, 0) < VINCOLI_ROSA.get(ruolo, 99)

def vincoli_rosa_text(rosa):
    """Restituisce una stringa riassuntiva dei vincoli rosa"""
    c = conteggio_rosa(rosa)
    parts = []
    for r in ["P", "D", "C", "A"]:
        mancano = max(0, VINCOLI_ROSA[r] - c[r])
        parts.append(f"{r}: {c[r]}/{VINCOLI_ROSA[r]} (mancano {mancano})")
    return " | ".join(parts)

def giocatori_prestati_da(squadra_nome):
    """Restituisce i giocatori che questa squadra ha prestato ad altre"""
    prestati = []
    for p in st.session_state.prestiti:
        if p["Da"] == squadra_nome:
            prestati.append(p)
    return prestati

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
    {"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":32,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"Gran gamba, qualita offensiva"},
    {"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"Ex City, rotazioni Chivu"},
    {"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"1 gol, 4 assist in 19 partite"},
    {"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"7 gol in Europa, sostituto Gila"},
    {"Nome":"Jimenez","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":21,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Torna in Serie A, jolly tattico"},
    {"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":14,"FantaMedia":5.9,"Consiglio":"scommessa","Note":"Nuovo titolare sinistra"},
    {"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":48,"FantaMedia":7.5,"Consiglio":"top","Note":"Potenziale top, alla Milinkovic-Savic"},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"Consiglio":"top","Note":"Cambio ruolo, piu appetibile"},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti"},
    {"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":52,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"8 gol, 3 assist, rigorista"},
    {"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":48,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"5 gol, 6 assist, attaccante aggiunto"},
    {"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Rendimento garantito"},
    {"Nome":"Kone","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":40,"FantaMedia":6.9,"Consiglio":"consigliato","Note":"Media 6.26, mai sotto sufficienza"},
    {"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":35,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 4 assist, voti alti"},
    {"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":38,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"Da prendere con Rowe"},
    {"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":36,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 3 assist, puo crescere"},
    {"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5-6 gol potenziali"},
    {"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.6,"Consiglio":"scommessa","Note":"Talentino trequarti, attenzione hype"},
    {"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Sarri lo vuole, grande intuizione"},
    {"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Fiducia Chivu, sostituto Calhanoglu"},
    {"Nome":"Calo","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"10 gol, 14 assist in Serie B"},
    {"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Solo Yamal piu assist in Liga"},
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
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
        "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if hasattr(st.session_state.stats_storiche, 'to_dict') else []
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
            stats = data.get("stats_storiche", [])
            st.session_state.stats_storiche = pd.DataFrame(stats) if stats else pd.DataFrame()
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
    st.session_state.stats_storiche = pd.DataFrame()

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
st.sidebar.subheader("📁 File di Backup")
# Esporta
data_export = {
    "squadre": st.session_state.squadre,
    "storico_mercato": st.session_state.storico_mercato,
    "watchlist": st.session_state.watchlist,
    "prestiti": st.session_state.prestiti,
    "contratti": st.session_state.contratti,
    "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
    "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if hasattr(st.session_state.stats_storiche, 'to_dict') else []
}
st.sidebar.download_button(
    label="📥 Scarica Backup",
    data=json.dumps(data_export, ensure_ascii=False, indent=2),
    file_name=f"fantamanager_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
    mime="application/json",
    use_container_width=True
)

up_backup = st.sidebar.file_uploader("📤 Carica Backup", type=["json"], key="up_backup")
if up_backup is not None:
    try:
        data_imp = json.load(up_backup)
        st.session_state.squadre = data_imp.get("squadre", {})
        st.session_state.storico_mercato = data_imp.get("storico_mercato", [])
        st.session_state.watchlist = data_imp.get("watchlist", [])
        st.session_state.prestiti = data_imp.get("prestiti", [])
        st.session_state.contratti = data_imp.get("contratti", {})
        db = data_imp.get("giocatori_db", [])
        st.session_state.giocatori_db = pd.DataFrame(db) if db else pd.DataFrame(LISTONE_DEFAULT)
        stats = data_imp.get("stats_storiche", [])
        st.session_state.stats_storiche = pd.DataFrame(stats) if stats else pd.DataFrame()
        for sq in NOMI_SQUADRE:
            if sq not in st.session_state.squadre:
                st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}
        save_state()
        st.sidebar.success("✅ Backup caricato!")
        st.rerun()
    except Exception as e:
        st.sidebar.error(f"Errore caricamento: {e}")

st.sidebar.markdown("---")
st.sidebar.subheader("💰 Modifica Crediti")
with st.sidebar.expander("✏️ Cambia crediti squadra"):
    sq_cred = st.selectbox("Squadra", NOMI_SQUADRE, key="cred_sq")
    cred_attuali = st.session_state.squadre[sq_cred]["crediti"]
    st.write(f"Crediti attuali: **{cred_attuali}**")
    nuovi_cred = st.number_input("Nuovi crediti", min_value=0, max_value=9999, value=cred_attuali, key="cred_val")
    if st.button("💾 Salva crediti", use_container_width=True):
        st.session_state.squadre[sq_cred]["crediti"] = int(nuovi_cred)
        save_state()
        st.sidebar.success(f"✅ {sq_cred}: {cred_attuali} → {nuovi_cred} crediti!")
        st.rerun()

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
                elif 'consiglio' in cl or 'consigliato' in cl or 'fascia' in cl: col_mappa[col] = 'Consiglio'
                elif 'note' in cl or 'commento' in cl or 'commenti' in cl or 'descrizione' in cl: col_mappa[col] = 'Note'
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
                st.sidebar.success(f"✅ Listone importato! {len(df_load)} giocatori.")
            else:
                st.sidebar.error("Colonna 'Nome' mancante.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

# --- IMPORTA QUOTAZIONI ULTIMA GIORNATA 2026 ---
with st.sidebar.expander("📊 Importa Quotazioni Ultima Giornata 2026"):
    st.markdown("""
    Carica il file con le quotazioni dell'ultima giornata della stagione 2025/26.
    Utile per giocatori non piu presenti nel listone attuale.
    """)
    up_quot = st.file_uploader("File Quotazioni Ultima Giornata", type=["csv","xlsx"], key="uq")
    if up_quot is not None:
        try:
            if up_quot.name.endswith('.csv'):
                df_q = pd.read_csv(up_quot, encoding='utf-8', on_bad_lines='skip')
            else:
                df_q = pd.read_excel(up_quot)
            df_q.columns = [str(c).strip() for c in df_q.columns]
            col_mappa_q = {}
            for col in df_q.columns:
                cl = str(col).lower()
                if 'nome' in cl or 'giocatore' in cl: col_mappa_q[col] = 'Nome'
                elif cl in ['r','ruolo']: col_mappa_q[col] = 'Ruolo'
                elif 'squadra' in cl or 'team' in cl: col_mappa_q[col] = 'Squadra_SerieA'
                elif 'quot' in cl or 'valore' in cl or 'fc' in cl or 'qt' in cl: col_mappa_q[col] = 'Quotazione'
                elif 'fm' in cl or 'fantamedia' in cl or 'media' in cl: col_mappa_q[col] = 'FantaMedia'
                elif 'consiglio' in cl or 'fascia' in cl: col_mappa_q[col] = 'Consiglio'
                elif 'note' in cl or 'commento' in cl: col_mappa_q[col] = 'Note'
            df_q = df_q.rename(columns=col_mappa_q)
            if 'Nome' in df_q.columns:
                df_q = df_q.loc[:, ~df_q.columns.duplicated()]
                for c, d in [('Ruolo','C'),('Squadra_SerieA','N/D'),('Quotazione',10),('FantaMedia',6.0),('Consiglio','consigliato'),('Note','')]:
                    if c not in df_q.columns: df_q[c] = d
                df_q['Quotazione'] = pd.to_numeric(df_q['Quotazione'], errors='coerce').fillna(10).astype(int)
                fm = df_q['FantaMedia']
                if isinstance(fm, pd.DataFrame): fm = fm.iloc[:,0]
                df_q['FantaMedia'] = pd.to_numeric(fm.astype(str).str.replace(',','.',regex=False), errors='coerce').fillna(6.0)

                db = st.session_state.giocatori_db.copy()
                aggiunti = 0
                aggiornati = 0
                for _, row in df_q.iterrows():
                    nome = str(row['Nome']).strip()
                    if not nome or nome.lower() in ['nan','none','null']:
                        continue
                    mask = db['Nome'].str.lower() == nome.lower()
                    if mask.any():
                        idx = db[mask].index[0]
                        for col in ['Ruolo','Squadra_SerieA','Quotazione','FantaMedia','Consiglio','Note']:
                            if col in df_q.columns and pd.notna(row[col]) and str(row[col]).strip() not in ['','nan','none']:
                                db.at[idx, col] = row[col]
                        aggiornati += 1
                    else:
                        new_row = {col: row.get(col, d) for col, d in [('Nome',nome),('Ruolo','C'),('Squadra_SerieA','N/D'),('Quotazione',10),('FantaMedia',6.0),('Consiglio','consigliato'),('Note','')]}
                        db = pd.concat([db, pd.DataFrame([new_row])], ignore_index=True)
                        aggiunti += 1

                st.session_state.giocatori_db = db
                save_state()
                st.sidebar.success(f"✅ Quotazioni importate! {aggiornati} aggiornati, {aggiunti} nuovi giocatori.")
            else:
                st.sidebar.error("Colonna 'Nome' mancante.")
        except Exception as e:
            st.sidebar.error(f"Errore: {e}")

# --- IMPORTA ROSE CON ANTEPRIMA E SCADENZE ---
with st.sidebar.expander("📋 Importa Rose"):
    st.markdown("""
    **File CSV/Excel con colonne:**
    - **Squadra** (fantateam)
    - **Nome** (giocatore)
    - **Ruolo** (P/D/C/A) — opzionale
    - **Scadenza Contratto** — opzionale
    - **Squadra Serie A** — opzionale

    **Formati scadenza:** `ago 26`, `sett 29`, `09/2029`, `2029`, `29`
    """)

    up_rose = st.file_uploader("File Rose", type=["csv","xlsx"], key="ur")

    if up_rose is not None:
        try:
            if up_rose.name.endswith('.csv'):
                df_r = pd.read_csv(up_rose, encoding='utf-8', on_bad_lines='skip')
            else:
                df_r = pd.read_excel(up_rose)

            df_r.columns = [str(c).strip().lower() for c in df_r.columns]

            # --- Trova colonne per nome ---
            col_sq = next((c for c in df_r.columns if 'squadra' in c or 'fantateam' in c or 'proprietario' in c), None)
            col_nm = next((c for c in df_r.columns if 'nome' in c or 'giocatore' in c), None)
            col_rl = next((c for c in df_r.columns if 'ruolo' in c or 'r' == c), None)
            col_scad = next((c for c in df_r.columns if 'scadenza' in c or 'contratto' in c or 'anno' in c), None)
            col_squadra_sa = next((c for c in df_r.columns if 'squadra serie a' in c or 'team' in c or 'club' in c or 'serie a' in c), None)

            if col_sq and col_nm:
                count = 0
                skipped = 0
                errors = []
                scad_ok = 0
                scad_default = 0

                for _, row in df_r.iterrows():
                    try:
                        sq_nome = str(row[col_sq]).strip().upper()
                        sq_match = next((s for s in NOMI_SQUADRE if s.upper() in sq_nome or sq_nome in s.upper()), None)
                        if not sq_match:
                            skipped += 1
                            continue

                        g_nome = str(row[col_nm]).strip()
                        if not g_nome or g_nome.lower() in ['nan', 'none', 'null', '']:
                            continue

                        # Ruolo
                        g_ruolo = str(row[col_rl]).strip().upper() if col_rl and pd.notna(row[col_rl]) else "C"
                        if len(g_ruolo) > 1 and g_ruolo[0] in "PDCA":
                            g_ruolo = g_ruolo[0]
                        elif g_ruolo not in ["P","D","C","A"]:
                            g_ruolo = "C"

                        # Scadenza dal file (stringa originale)
                        g_scadenza_str = "N/D"
                        if col_scad and pd.notna(row[col_scad]):
                            val = str(row[col_scad]).strip()
                            if val and val.lower() not in ['nan','none','null','']:
                                g_scadenza_str = val
                                scad_ok += 1
                            else:
                                scad_default += 1
                        else:
                            scad_default += 1

                        # Squadra Serie A dal file (priorità)
                        g_squadra_sa = None
                        if col_squadra_sa and pd.notna(row[col_squadra_sa]):
                            g_squadra_sa = str(row[col_squadra_sa]).strip()

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
                            if g_ruolo == "C":
                                g_ruolo = str(match_db.iloc[0]['Ruolo'])

                        # Se il file ha una squadra Serie A specifica, usa quella
                        if g_squadra_sa:
                            sq_sa = g_squadra_sa

                        # Evita duplicati
                        if any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_match]["rosa"]):
                            skipped += 1
                            continue

                        # Parsing scadenza per i campi numerici interni
                        scad_mese, scad_anno = parse_scadenza(g_scadenza_str)
                        if scad_anno:
                            contratto_durata = max(1, scad_anno - ANNO_CORRENTE)
                            anno_acq = ANNO_CORRENTE
                        else:
                            contratto_durata = CONTRATTO_ANNI
                            anno_acq = ANNO_CORRENTE
                            scad_anno = anno_acq + contratto_durata
                            scad_mese = MESE_DEFAULT_SCADENZA

                        g_costo = 1
                        if st.session_state.squadre[sq_match]["crediti"] < g_costo:
                            errors.append(f"{sq_match}: crediti insufficienti per {g_nome}")
                            continue

                        st.session_state.squadre[sq_match]["crediti"] -= g_costo
                        entry = {
                            "Nome": g_nome,
                            "Ruolo": g_ruolo,
                            "Squadra_SerieA": sq_sa,
                            "Quotazione": quot,
                            "FantaMedia": fm,
                            "Costo_Acquisto": g_costo,
                            "Anno_Acquisto": anno_acq,
                            "Contratto_Anni": contratto_durata,
                            "Scadenza_Anno": scad_anno,
                            "Scadenza_Mese": scad_mese,
                            "Scadenza_Contratto": g_scadenza_str,  # stringa originale dal file
                        }

                        st.session_state.squadre[sq_match]["rosa"].append(entry)
                        st.session_state.contratti[g_nome] = {
                            "squadra": sq_match,
                            "anno": anno_acq,
                            "durata": contratto_durata,
                            "scadenza_anno": scad_anno,
                            "scadenza_mese": scad_mese
                        }
                        count += 1

                    except Exception as e:
                        errors.append(f"Riga: {e}")

                save_state()
                msg = f"✅ Importati {count} giocatori! ({skipped} saltati)"
                if scad_ok > 0:
                    msg += f" | Scadenze dal file: {scad_ok}"
                if scad_default > 0:
                    msg += f" | Default: {scad_default}"
                st.sidebar.success(msg)
                if errors:
                    with st.sidebar.expander("⚠️ Errori"):
                        for e in errors[:20]:
                            st.write(f"- {e}")
                st.rerun()
            else:
                st.sidebar.error("Colonne Squadra e Nome mancanti.")

        except Exception as e:
            st.sidebar.error(f"Errore lettura file: {e}")

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

        for col in ['Consiglio','Note']:
            if col not in df_f.columns:
                df_f[col] = '' if col == 'Note' else 'consigliato'

        st.subheader(f"Trovati: {len(df_f)} giocatori")
        st.dataframe(
            df_f,
            column_config={
                "Note": st.column_config.TextColumn("Note", width="large"),
                "Consiglio": st.column_config.TextColumn("Consiglio", width="small"),
            },
            use_container_width=True
        )

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
            show_cols = ["Nome","Ruolo","Squadra_SerieA","Quotazione","FantaMedia","Indice_Affare","Proprietario"]
            if "Consiglio" in df_wl.columns: show_cols.append("Consiglio")
            if "Note" in df_wl.columns: show_cols.append("Note")
            st.dataframe(df_wl[show_cols], use_container_width=True)
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

        # --- POPUP VINCOLI ROSA ---
        with st.popover("📋 Vincoli Rosa", use_container_width=True):
            c_rosa = conteggio_rosa(st.session_state.squadre[sq]["rosa"])
            st.markdown(f"**Squadra: {sq}**")
            for r in ["P", "D", "C", "A"]:
                mancano = max(0, VINCOLI_ROSA[r] - c_rosa[r])
                colore = "🟢" if c_rosa[r] >= VINCOLI_ROSA[r] else "🟡" if c_rosa[r] >= VINCOLI_ROSA[r] - 2 else "🔴"
                st.write(f"{colore} **{r}**: {c_rosa[r]}/{VINCOLI_ROSA[r]} — mancano **{mancano}**")
            st.caption("I giocatori in prestito ENTRATA non contano per i vincoli.")

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
                ruolo_sel = info['Ruolo']

                st.write(f"Ruolo: **{ruolo_sel}** | Squadra: **{info['Squadra_SerieA']}** | Quotazione: **{int(info['Quotazione'])}** | FM: **{info['FantaMedia']}** | Consiglio: **{info.get('Consiglio','')}**")

                # Prezzo consigliato
                min_p, max_p = prezzo_consigliato(info['Quotazione'], info['FantaMedia'])
                st.info(f"💡 **Prezzo consigliato:** {min_p}-{max_p} crediti (quotazione listone: {int(info['Quotazione'])}cr)")

                # --- STATS STORICHE ---
                stats_sel = get_stats_giocatore(g_sel)
                if stats_sel is not None and not stats_sel.empty:
                    with st.expander("📊 Stats storiche 2025/26"):
                        st.dataframe(stats_sel, use_container_width=True)

                prezzo = st.number_input("Prezzo pagato", min_value=1, max_value=max(1,cred), value=int(info["Quotazione"]), key="acq_p")
                mese_scad = st.selectbox("Mese scadenza contratto", options=list(range(1,13)),
                                         format_func=lambda x: MESI_NOMI[x],
                                         index=MESE_DEFAULT_SCADENZA-1, key="acq_mese")

                # Paragone con giocatori della rosa stesso ruolo
                rosa_mia = st.session_state.squadre[sq]["rosa"]
                rosa_stesso_ruolo = [g for g in rosa_mia if g.get("Ruolo") == ruolo_sel and "(PRESTITO da" not in g.get("Nome", "")]

                if rosa_stesso_ruolo:
                    st.markdown("---")
                    st.markdown("### ⚖️ Paragone con la tua rosa")
                    nomi_paragone = [g["Nome"] for g in rosa_stesso_ruolo]
                    g_par = st.selectbox("Scegli giocatore da paragonare", nomi_paragone, key="paragone_acq")
                    g_par_obj = next(g for g in rosa_stesso_ruolo if g["Nome"] == g_par)

                    comp_data = {
                        "Metrica": ["Nome", "Ruolo", "Quotazione", "FantaMedia", "Costo Acquisto", "Indice Affare"],
                        "Da Acquistare": [
                            g_sel,
                            ruolo_sel,
                            int(info["Quotazione"]),
                            info["FantaMedia"],
                            prezzo,
                            round(info["FantaMedia"] / max(int(info["Quotazione"]), 1), 2)
                        ],
                        "In Rosa": [
                            g_par,
                            g_par_obj.get("Ruolo", ruolo_sel),
                            g_par_obj.get("Quotazione", "N/D"),
                            g_par_obj.get("FantaMedia", "N/D"),
                            g_par_obj.get("Costo_Acquisto", "N/D"),
                            round(g_par_obj.get("FantaMedia", 0) / max(g_par_obj.get("Quotazione", 1), 1), 2) if g_par_obj.get("Quotazione") else "N/D"
                        ]
                    }
                    st.dataframe(pd.DataFrame(comp_data), use_container_width=True)

                    # Stats storiche paragone
                    stats_par = get_stats_giocatore(g_par)
                    if (stats_sel is not None and not stats_sel.empty) or (stats_par is not None and not stats_par.empty):
                        with st.expander("📊 Confronto stats storiche"):
                            c_s, c_p = st.columns(2)
                            with c_s:
                                st.markdown(f"**{g_sel}**")
                                if stats_sel is not None and not stats_sel.empty:
                                    st.dataframe(stats_sel, use_container_width=True)
                                else:
                                    st.caption("Nessuna statistica storica")
                            with c_p:
                                st.markdown(f"**{g_par}**")
                                if stats_par is not None and not stats_par.empty:
                                    st.dataframe(stats_par, use_container_width=True)
                                else:
                                    st.caption("Nessuna statistica storica")

                    # Giudizio rapido
                    delta_q = int(info["Quotazione"]) - g_par_obj.get("Quotazione", 0)
                    delta_fm = info["FantaMedia"] - g_par_obj.get("FantaMedia", 0)
                    if delta_fm > 0.3 and delta_q <= 5:
                        st.success("🟢 Upgrade! FantaMedia superiore a poco prezzo.")
                    elif delta_fm < -0.3:
                        st.warning("🟡 Downgrade in FantaMedia.")
                    else:
                        st.info("⚪ Valori simili, dipende dal prezzo d'acquisto.")

                # Controllo vincoli
                puo_acq = puo_acquistare(st.session_state.squadre[sq]["rosa"], ruolo_sel)
                if not puo_acq:
                    st.error(f"🚫 Hai già raggiunto il limite di {VINCOLI_ROSA[ruolo_sel]} {ruolo_sel} di proprietà!")

                if st.button("Conferma Acquisto"):
                    if not puo_acq:
                        st.error("Acquisto bloccato: vincoli rosa non rispettati!")
                    elif cred >= prezzo:
                        scad_anno = ANNO_CORRENTE + CONTRATTO_ANNI
                        st.session_state.squadre[sq]["crediti"] -= prezzo
                        st.session_state.squadre[sq]["rosa"].append({
                            "Nome": g_sel, "Ruolo": ruolo_sel, "Squadra_SerieA": info["Squadra_SerieA"],
                            "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                            "Costo_Acquisto": prezzo, "Anno_Acquisto": ANNO_CORRENTE, "Contratto_Anni": CONTRATTO_ANNI,
                            "Scadenza_Anno": scad_anno, "Scadenza_Mese": mese_scad
                        })
                        st.session_state.contratti[g_sel] = {
                            "squadra": sq, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI,
                            "scadenza_anno": scad_anno, "scadenza_mese": mese_scad
                        }
                        st.session_state.storico_mercato.insert(0, {
                            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Operazione": "ACQUISTO",
                            "Dettagli": f"{sq} acquista {g_sel} ({ruolo_sel}) per {prezzo}cr — Contratto fino al {fmt_scadenza(mese_scad, scad_anno)}"
                        })
                        save_state()
                        st.success(f"✅ {g_sel} acquistato! Contratto fino al {fmt_scadenza(mese_scad, scad_anno)}.")
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

            db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].str.lower() == g_v.lower()]
            if not db_match.empty:
                prezzo_listone = int(db_match.iloc[0]["Quotazione"])
                st.info(f"💡 Quotazione attuale listone: **{prezzo_listone}cr** (questo e il valore di rimborso)")
            else:
                prezzo_listone = g_obj.get("Costo_Acquisto", 10)
                st.info(f"💡 Giocatore non trovato nel listone. Rimborso al costo d'acquisto: **{prezzo_listone}cr**")

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
            st.info("Nessun giocatore di proprieta nella rosa.")

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

    # --- ANALISI PRE-SCAMBIO ---
    oggetti1_sel = [g for g in rosa1 if g["Nome"] in g1]
    oggetti2_sel = [g for g in rosa2 if g["Nome"] in g2]

    if oggetti1_sel or oggetti2_sel or d1 or d2:
        try:
            st.markdown("---")
            st.subheader("📊 Analisi Scambio")

            analisi = analisi_scambio(oggetti1_sel, oggetti2_sel, d1, d2)

            col_a, col_b = st.columns(2)
            with col_a:
                st.markdown(f"**🟦 {sq1} cede:**")
                if oggetti1_sel:
                    for g in oggetti1_sel:
                        st.write(f"• {g['Nome']} ({g.get('Ruolo','')}) — Q:{g.get('Quotazione','?')} FM:{g.get('FantaMedia','?')} Costo:{g.get('Costo_Acquisto','?')}cr")
                else:
                    st.write("Nessun giocatore")
                if d1 > 0:
                    st.write(f"💰 + {d1}cr conguaglio")
                st.markdown(f"**Totale quotazione: {analisi['sq1']['quot']} | FantaMedia media: {analisi['sq1']['fm']}**")

            with col_b:
                st.markdown(f"**🟥 {sq2} cede:**")
                if oggetti2_sel:
                    for g in oggetti2_sel:
                        st.write(f"• {g['Nome']} ({g.get('Ruolo','')}) — Q:{g.get('Quotazione','?')} FM:{g.get('FantaMedia','?')} Costo:{g.get('Costo_Acquisto','?')}cr")
                else:
                    st.write("Nessun giocatore")
                if d2 > 0:
                    st.write(f"💰 + {d2}cr conguaglio")
                st.markdown(f"**Totale quotazione: {analisi['sq2']['quot']} | FantaMedia media: {analisi['sq2']['fm']}**")

            st.markdown("---")
            st.markdown("### 📊 Dati comparativi")
            st.write(f"Delta quotazione (valore): **{analisi['delta_quot']:+.0f}cr**")
            st.write(f"Delta FantaMedia media: **{analisi['delta_fm']:+.2f}**")

            # Stats storiche giocatori coinvolti
            nomi_stats = []
            for g in oggetti1_sel + oggetti2_sel:
                s = get_stats_giocatore(g["Nome"])
                if s is not None and not s.empty:
                    nomi_stats.append(g["Nome"])
            if nomi_stats:
                with st.expander("📊 Stats storiche giocatori coinvolti"):
                    for nome_s in nomi_stats:
                        st.markdown(f"**{nome_s}**")
                        st.dataframe(get_stats_giocatore(nome_s), use_container_width=True)

            if tipo != "Scambio Definitivo":
                st.info("ℹ️ Per i prestiti il giudizio si basa solo sui conguagli.")
                if d1 > d2:
                    st.write(f"{sq1} paga {d1-d2}cr a {sq2}")
                elif d2 > d1:
                    st.write(f"{sq2} paga {d2-d1}cr a {sq1}")
                else:
                    st.write("Nessun conguaglio")
        except Exception as e:
            st.error(f"Errore nell'analisi dello scambio: {e}")

    if st.button("Finalizza", type="primary"):
        if tipo == "Scambio Definitivo":
            # Validazione vincoli
            sim_rosa1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] not in g1 and "(PRESTITO da" not in g.get("Nome", "")]
            sim_rosa2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] not in g2 and "(PRESTITO da" not in g.get("Nome", "")]
            sim_rosa1.extend([g for g in oggetti2_sel if "(PRESTITO da" not in g.get("Nome", "")])
            sim_rosa2.extend([g for g in oggetti1_sel if "(PRESTITO da" not in g.get("Nome", "")])
            vincoli_ok = True
            msgs = []
            for sq_n, sim_rosa in [(sq1, sim_rosa1), (sq2, sim_rosa2)]:
                c = conteggio_rosa(sim_rosa)
                for r in ["P", "D", "C", "A"]:
                    if c[r] > VINCOLI_ROSA[r]:
                        msgs.append(f"🚫 {sq_n}: supereresti il limite di {VINCOLI_ROSA[r]} {r} (sarebbero {c[r]})")
                        vincoli_ok = False
            if not vincoli_ok:
                for m in msgs:
                    st.error(m)
                st.warning("Correggi lo scambio per rispettare i vincoli di rosa (3P, 9D, 9C, 7A).")
                st.stop()

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
                    st.session_state.contratti[g["Nome"]] = {"squadra": sq1, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI, "scadenza_anno": ANNO_CORRENTE+CONTRATTO_ANNI, "scadenza_mese": MESE_DEFAULT_SCADENZA}
                for g in oggetti1:
                    st.session_state.contratti[g["Nome"]] = {"squadra": sq2, "anno": ANNO_CORRENTE, "durata": CONTRATTO_ANNI, "scadenza_anno": ANNO_CORRENTE+CONTRATTO_ANNI, "scadenza_mese": MESE_DEFAULT_SCADENZA}
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
                                "Costo_Acquisto": 0, "Anno_Acquisto": ANNO_CORRENTE, "Contratto_Anni": CONTRATTO_ANNI,
                                "Scadenza_Anno": ANNO_CORRENTE+CONTRATTO_ANNI, "Scadenza_Mese": MESE_DEFAULT_SCADENZA
                            }
                        else:
                            g_orig = {"Nome": gp, "Ruolo": "C", "Squadra_SerieA": "N/D", "Quotazione": 1, "FantaMedia": 6.0, "Costo_Acquisto": 0, "Scadenza_Anno": ANNO_CORRENTE+CONTRATTO_ANNI, "Scadenza_Mese": MESE_DEFAULT_SCADENZA}
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
                c1, c2, c3 = st.columns([3, 1, 1])
                with c1:
                    st.subheader(f"🛡️ {sq}")
                with c2:
                    st.metric("Crediti", f"{dati['crediti']} 🪙")
                with c3:
                    with st.popover("✏️ Modifica"):
                        nuovi_cred_rosa = st.number_input("Crediti", min_value=0, max_value=9999, value=dati["crediti"], key=f"cred_pop_{sq}")
                        if st.button("Salva", key=f"btn_cred_{sq}"):
                            st.session_state.squadre[sq]["crediti"] = int(nuovi_cred_rosa)
                            save_state()
                            st.success("Crediti aggiornati!")
                            st.rerun()

                # --- Riepilogo vincoli (solo di proprietà) ---
                c_rosa = conteggio_rosa(dati["rosa"])
                vincoli_parts = []
                for r in ["P", "D", "C", "A"]:
                    mancano = max(0, VINCOLI_ROSA[r] - c_rosa[r])
                    emoji = "✅" if c_rosa[r] >= VINCOLI_ROSA[r] else "⚠️" if mancano <= 2 else "❌"
                    vincoli_parts.append(f"{emoji} {r}: {c_rosa[r]}/{VINCOLI_ROSA[r]}")
                st.caption("Vincoli rosa (di proprietà): " + " | ".join(vincoli_parts))

                # Bottone sincronizza squadre col listone
                if st.button("🔄 Sincronizza squadre col listone", key=f"sync_{sq}"):
                    db = st.session_state.giocatori_db
                    aggiornati = 0
                    for g in dati["rosa"]:
                        nome_base = g["Nome"].replace("(PRESTITO da", "").strip().split(")")[0].strip()
                        match = db[db["Nome"].str.lower() == nome_base.lower()]
                        if not match.empty:
                            nuova_sq = match.iloc[0]["Squadra_SerieA"]
                            if g.get("Squadra_SerieA") != nuova_sq:
                                g["Squadra_SerieA"] = nuova_sq
                                aggiornati += 1
                    if aggiornati > 0:
                        save_state()
                        st.success(f"✅ {aggiornati} giocatori aggiornati dal listone!")
                        st.rerun()
                    else:
                        st.info("Tutte le squadre sono già aggiornate.")

                # Separa proprietà da prestiti
                rosa_proprieta = [g for g in dati["rosa"] if "(PRESTITO da" not in g.get("Nome", "")]
                rosa_prestito = [g for g in dati["rosa"] if "(PRESTITO da" in g.get("Nome", "")]

                # --- Giocatori DI PROPRIETÀ ---
                if rosa_proprieta:
                    st.markdown("**🛡️ Giocatori di proprietà**")
                    df_prop = pd.DataFrame(rosa_proprieta)
                    # Usa Scadenza_Contratto (dal file) se presente, altrimenti calcolata
                    df_prop["Scadenza"] = df_prop.apply(
                        lambda r: r.get("Scadenza_Contratto", "N/D") if r.get("Scadenza_Contratto") and r.get("Scadenza_Contratto") != "N/D" else fmt_scadenza(r.get("Scadenza_Mese"), r.get("Scadenza_Anno")),
                        axis=1
                    )
                    df_prop["Fantasquadra"] = sq
                    df_prop = df_prop[["Nome", "Ruolo", "Fantasquadra", "Squadra_SerieA", "Scadenza"]]
                    df_prop = df_prop.rename(columns={"Squadra_SerieA": "Squadra Serie A"})
                    conti_prop = df_prop["Ruolo"].value_counts().to_dict()
                    st.caption(f"Proprietà: P: {conti_prop.get('P',0)} | D: {conti_prop.get('D',0)} | C: {conti_prop.get('C',0)} | A: {conti_prop.get('A',0)} | Tot: {len(df_prop)}")
                    st.dataframe(df_prop, use_container_width=True)

                    in_scadenza = [g for g in rosa_proprieta if is_scadenza_prossima(g)]
                    if in_scadenza:
                        st.warning("🟠 **In scadenza entro 6 mesi:** " + ", ".join([g["Nome"] for g in in_scadenza]))
                else:
                    st.info("Nessun giocatore di proprietà.")

                # --- Giocatori IN PRESTITO (entrata) ---
                if rosa_prestito:
                    st.markdown("**🔴 In prestito (non contano per i vincoli)**")
                    # Sincronizza squadra con il listone
                    db = st.session_state.giocatori_db
                    for g in rosa_prestito:
                        nome_base = g["Nome"].replace("(PRESTITO da", "").strip().split(")")[0].strip()
                        match = db[db["Nome"].str.lower() == nome_base.lower()]
                        if not match.empty:
                            g["Squadra_SerieA"] = match.iloc[0]["Squadra_SerieA"]
                    df_prest = pd.DataFrame(rosa_prestito)
                    df_prest["Scadenza"] = df_prest.apply(
                        lambda r: r.get("Scadenza_Contratto", "N/D") if r.get("Scadenza_Contratto") and r.get("Scadenza_Contratto") != "N/D" else fmt_scadenza(r.get("Scadenza_Mese"), r.get("Scadenza_Anno")),
                        axis=1
                    )
                    df_prest["Fantasquadra"] = sq
                    df_prest = df_prest[["Nome", "Ruolo", "Fantasquadra", "Squadra_SerieA", "Scadenza"]]
                    df_prest = df_prest.rename(columns={"Squadra_SerieA": "Squadra Serie A"})
                    conti_prest = df_prest["Ruolo"].value_counts().to_dict()
                    st.caption(f"Prestiti: P: {conti_prest.get('P',0)} | D: {conti_prest.get('D',0)} | C: {conti_prest.get('C',0)} | A: {conti_prest.get('A',0)} | Tot: {len(df_prest)}")
                    st.dataframe(df_prest, use_container_width=True)

                # --- Prestiti CEDUTI da questa squadra ---
                prestati = giocatori_prestati_da(sq)
                if prestati:
                    st.markdown("**🟢 Ceduti in prestito ad altre squadre**")
                    df_prest_ced = pd.DataFrame(prestati)
                    st.dataframe(df_prest_ced, use_container_width=True)

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
            # Conteggio SOLO giocatori di proprietà (esclusi prestiti in entrata)
            rosa_prop = [g for g in rosa if "(PRESTITO da" not in g.get("Nome", "")]
            p=d=c=a=spesa=0
            for g in rosa_prop:
                r = g.get("Ruolo","C")
                if r=="P": p+=1
                elif r=="D": d+=1
                elif r=="C": c+=1
                elif r=="A": a+=1
                spesa += g.get("Costo_Acquisto",0)
            n_prestiti = len(rosa) - len(rosa_prop)
            summary.append({"Squadra":sq, "Crediti":dati["crediti"], "Spesa":spesa, 
                          "Proprietà":len(rosa_prop), "P":p, "D":d, "C":c, "A":a, "Prestiti":n_prestiti})
            df_summary = pd.DataFrame(summary)
            def stato_vincoli(row):
                sq_n = row["Squadra"]
                c = conteggio_rosa(st.session_state.squadre[sq_n]["rosa"])
                ok = all(c[r] >= VINCOLI_ROSA[r] for r in ["P","D","C","A"])
                return "✅ Completa" if ok else "⚠️ Incompleta"
            df_summary["Stato Rosa"] = df_summary.apply(stato_vincoli, axis=1)
            st.dataframe(df_summary, use_container_width=True)

    with tab_contratti:
        st.subheader(f"📄 Gestione Contratti")

        st.markdown("---")
        st.markdown("### ✏️ Modifica Contratto")

        tutti_giocatori = []
        for sq, dati in st.session_state.squadre.items():
            for g in dati["rosa"]:
                if "(PRESTITO da" not in g.get("Nome", ""):
                    tutti_giocatori.append({
                        "Nome": g["Nome"],
                        "Squadra": sq,
                        "Scadenza_Anno": g.get("Scadenza_Anno", g.get("Anno_Acquisto", ANNO_CORRENTE) + g.get("Contratto_Anni", CONTRATTO_ANNI)),
                        "Scadenza_Mese": g.get("Scadenza_Mese", MESE_DEFAULT_SCADENZA)
                    })

        if tutti_giocatori:
            df_contr = pd.DataFrame(tutti_giocatori)
            df_contr["Label"] = df_contr["Nome"] + " (" + df_contr["Squadra"] + ")"

            g_mod = st.selectbox("Seleziona giocatore", df_contr["Label"].values, key="mod_contr")
            g_nome_mod = g_mod.split(" (")[0]
            g_info = df_contr[df_contr["Nome"] == g_nome_mod].iloc[0]

            c1, c2 = st.columns(2)
            with c1:
                nuovo_mese = st.selectbox("Nuovo mese scadenza", options=list(range(1,13)),
                                          format_func=lambda x: MESI_NOMI[x],
                                          index=int(g_info["Scadenza_Mese"])-1 if g_info["Scadenza_Mese"] else MESE_DEFAULT_SCADENZA-1,
                                          key="mod_mese")
            with c2:
                nuovo_anno = st.number_input("Nuovo anno scadenza", min_value=ANNO_CORRENTE, max_value=ANNO_CORRENTE+10,
                                             value=int(g_info["Scadenza_Anno"]) if g_info["Scadenza_Anno"] else ANNO_CORRENTE+CONTRATTO_ANNI,
                                             key="mod_anno")

            if st.button("💾 Salva modifica contratto", type="primary"):
                for sq, dati in st.session_state.squadre.items():
                    for g in dati["rosa"]:
                        if g["Nome"] == g_nome_mod:
                            g["Scadenza_Anno"] = int(nuovo_anno)
                            g["Scadenza_Mese"] = int(nuovo_mese)
                            g["Contratto_Anni"] = max(1, int(nuovo_anno) - g.get("Anno_Acquisto", ANNO_CORRENTE))
                            break
                if g_nome_mod in st.session_state.contratti:
                    st.session_state.contratti[g_nome_mod]["scadenza_anno"] = int(nuovo_anno)
                    st.session_state.contratti[g_nome_mod]["scadenza_mese"] = int(nuovo_mese)
                    st.session_state.contratti[g_nome_mod]["durata"] = max(1, int(nuovo_anno) - st.session_state.contratti[g_nome_mod].get("anno", ANNO_CORRENTE))

                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "MODIFICA CONTRATTO",
                    "Dettagli": f"{g_nome_mod} — nuova scadenza: {fmt_scadenza(nuovo_mese, nuovo_anno)}"
                })
                save_state()
                st.success(f"✅ Contratto di {g_nome_mod} aggiornato a {fmt_scadenza(nuovo_mese, nuovo_anno)}!")
                st.rerun()
        else:
            st.info("Nessun giocatore con contratto.")

        st.markdown("---")
        st.markdown("### 📋 Elenco Contratti")
        if st.session_state.contratti:
            rows = []
            for nome, c in st.session_state.contratti.items():
                scad = fmt_scadenza(c.get("scadenza_mese"), c.get("scadenza_anno"))
                rows.append({"Giocatore":nome, "Squadra":c["squadra"], "Anno":c["anno"], "Scadenza":scad, "Durata":c["durata"]})
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
                "consigliati": ["Vlasic (Torino) - rigorista", "Zaniolo (Udinese)", "Modric (Inter)", "Kone (Juve)", "Perrone (Como)"],
                "scommesse": ["Alajbegovic (Juve)", "Gaetano (Atalanta)", "Stankovic A. (Inter)", "Calo (Frosinone)", "Milla (Como)"]
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
    Carica i file CSV/Excel con le statistiche storiche dei giocatori.
    Puoi caricare **piu file diversi** (es. uno per stagione) — i dati verranno uniti automaticamente.

    **Colonne attese:** Nome, Stagione, Gol, Assist, FantaMedia, Partite, Rigori, Ammonizioni, Espulsioni
    (puoi aggiungere altre colonne, verranno mostrate automaticamente)
    """)

    up_stats = st.file_uploader("File Statistiche Storiche (carica piu file)", type=["csv","xlsx"], key="us")
    if up_stats is not None:
        try:
            if up_stats.name.endswith('.csv'):
                df_s = pd.read_csv(up_stats, encoding='utf-8', on_bad_lines='skip')
            else:
                df_s = pd.read_excel(up_stats)
            df_s.columns = [str(c).strip() for c in df_s.columns]
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

            existing = st.session_state.stats_storiche.copy()
            if existing.empty:
                st.session_state.stats_storiche = df_s
            else:
                combined = pd.concat([existing, df_s], ignore_index=True)
                if "Stagione" in combined.columns and "Nome" in combined.columns:
                    combined = combined.drop_duplicates(subset=["Nome", "Stagione"], keep="last")
                else:
                    combined = combined.drop_duplicates(keep="last")
                st.session_state.stats_storiche = combined

            save_state()
            total_rows = len(st.session_state.stats_storiche)
            st.success(f"✅ Caricato file con {len(df_s)} righe! Totale statistiche in archivio: {total_rows} righe.")
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

            numeric_cols = df_g.select_dtypes(include=['number']).columns.tolist()
            numeric_cols = [c for c in numeric_cols if c not in ['Stagione'] and 'Stagione' not in c]
            if numeric_cols and "Stagione" in df_g.columns:
                st.subheader("📊 Andamento")
                chart_data = df_g.set_index("Stagione")[numeric_cols]
                st.line_chart(chart_data)

            db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].str.lower() == g_sel.lower()]
            if not db_match.empty:
                st.info(f"💡 Quotazione attuale listone: **{int(db_match.iloc[0]['Quotazione'])}cr** | FantaMedia: **{db_match.iloc[0]['FantaMedia']}** | Squadra: **{db_match.iloc[0]['Squadra_SerieA']}**")

        st.markdown("---")
        st.subheader("📋 Tabella completa")
        st.dataframe(df_stats, use_container_width=True)

        if st.button("🗑️ Cancella TUTTE le statistiche storiche"):
            st.session_state.stats_storiche = pd.DataFrame()
            save_state()
            st.rerun()
    else:
        st.info("Nessuna statistica storica caricata. Usa l'uploader sopra.")
