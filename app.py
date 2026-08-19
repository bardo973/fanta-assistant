import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.set_page_config(page_title="FantaManager Pro", layout="wide")
DB_NAME = "fantacalcio_career.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS fanta_squadre (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, budget REAL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calciatori (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT UNIQUE, ruolo TEXT, 
        squadra_reale TEXT, fantamedia REAL, gol INTEGER, assist INTEGER
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rose (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fanta_squadra_id INTEGER, 
        calciatore_id INTEGER, data_inizio TEXT, data_scadenza TEXT, tipo_possesso TEXT,
        UNIQUE(fanta_squadra_id, calciatore_id)
    )""")
    conn.commit()
    conn.close()

init_db()

st.title("⚽ FantaManager Career Pro")
menu = [
    "Visualizza Rose & Scadenze", 
    "Carica File (Dati)", 
    "Acquista Giocatore (4 Anni)", 
    "Mercato & Scambi", 
    "Scouting & Confronto"
]
scelta = st.sidebar.selectbox("Navigazione App", menu)

# --- CREAZIONE TEMPLATE SCARICABILI NELLA SIDEBAR ---
st.sidebar.markdown("---")
st.sidebar.subheader("📥 Scarica Template File")
template_listone = pd.DataFrame(columns=["nome", "ruolo", "squadra_reale", "fantamedia", "gol", "assist"])
template_rose = pd.DataFrame(columns=["fanta_squadra", "calciatore", "tipo_possesso", "anni_contratto"])

st.sidebar.download_button(
    label="Template Listone (CSV)",
    data=template_listone.to_csv(index=False).encode('utf-8'),
    file_name="template_listone.csv",
    mime="text/csv"
)
st.sidebar.download_button(
    label="Template Rose (CSV)",
    data=template_rose.to_csv(index=False).encode('utf-8'),
    file_name="template_rose.csv",
    mime="text/csv"
)

conn = sqlite3.connect(DB_NAME)

# ----------------------------------------------------
# NUOVA SEZIONE: CARICAMENTO FILE LISTONE E ROSE
# ----------------------------------------------------
if scelta == "Carica File (Dati)":
    st.header("📂 Caricamento Massivo Dati (.csv o .xlsx)")
    
    col_listone, col_rose = st.columns(2)
    
    with col_listone:
        st.subheader("1. Importa il Listone Calciatori")
        file_listone = st.file_uploader("Scegli il file del listone", type=["csv", "xlsx"], key="upl_listone")
        
        if file_listone is not None:
            try:
                if file_listone.name.endswith('.csv'):
                    df_l = pd.read_csv(file_listone)
                else:
                    df_l = pd.read_excel(file_listone)
                
                st.write("Anteprima dati caricati:")
                st.dataframe(df_l.head(3), use_container_width=True)
                
                if st.button("Salva Listone nel Database"):
                    cursor = conn.cursor()
                    successi = 0
                    for _, row in df_l.iterrows():
                        try:
                            cursor.execute("""
                                INSERT OR REPLACE INTO calciatori (nome, ruolo, squadra_reale, fantamedia, gol, assist)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (row['nome'], row['ruolo'], row['squadra_reale'], float(row['fantamedia']), int(row['gol']), int(row['assist'])))
                            successi += 1
                        except Exception as e:
                            pass
                    conn.commit()
                    st.success(f"🎉 Caricati/Aggiornati con successo {successi} calciatori nel listone!")
            except Exception as err:
                st.error(f"Errore nella lettura del file: {err}. Verifica che i nomi delle colonne siano corretti.")

    with col_rose:
        st.subheader("2. Importa le Rose delle Squadre")
        file_rose = st.file_uploader("Scegli il file delle rose", type=["csv", "xlsx"], key="upl_rose")
        
        if file_rose is not None:
            try:
                if file_rose.name.endswith('.csv'):
                    df_r = pd.read_csv(file_rose)
                else:
                    df_r = pd.read_excel(file_rose)
                
                st.write("Anteprima dati caricati:")
                st.dataframe(df_r.head(3), use_container_width=True)
                
                if st.button("Salva Rose nel Database"):
                    cursor = conn.cursor()
                    squadre_create = set()
                    rose_inserite = 0
                    
                    oggi = datetime.now()
                    inizio_str = oggi.strftime("%Y-%m-%d")
                    
                    for _, row in df_r.iterrows():
                        # 1. Gestione dinamica fanta_squadre (se non esiste, la inserisce)
                        nome_sq = row['fanta_squadra']
                        cursor.execute("INSERT OR IGNORE INTO fanta_squadre (nome, budget) VALUES (?, 500.0)", (nome_sq,))
                        
                        # Recupera gli ID corretti di squadra e calciatore
                        cursor.execute("SELECT id FROM fanta_squadre WHERE nome = ?", (nome_sq,))
                        sq_id = cursor.fetchone()[0]
                        
                        cursor.execute("SELECT id FROM calciatori WHERE nome = ?", (row['calciatore'],))
                        calciatore_res = cursor.fetchone()
                        
                        if calciatore_res is not None:
                            calciatore_id = calciatore_res[0]
                            # Calcola la durata del contratto personalizzata o fissa a 4 anni
                            anni = int(row['anni_contratto']) if 'anni_contratto' in row else 4
                            scadenza = oggi + timedelta(days=anni * 365)
                            scadenza_str = scadenza.strftime("%Y-%m-%d")
                            
                            cursor.execute("""
                                INSERT OR REPLACE INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso)
                                VALUES (?, ?, ?, ?, ?)
                            """, (sq_id, calciatore_id, inizio_str, scadenza_str, row['tipo_possesso'].upper()))
                            rose_inserite += 1
                    
                    conn.commit()
                    st.success(f"🎉 Associate con successo {rose_inserite} assegnazioni di contratto alle rispettive fanta-squadre!")
            except Exception as err:
                st.error(f"Errore nella lettura del file: {err}. Controlla i dati o se il calciatore esiste già nel listone.")

# ----------------------------------------------------
# 1. FUNZIONALITÀ: VISUALIZZA ROSE & SCADENZE
# ----------------------------------------------------
elif scelta == "Visualizza Rose & Scadenze":
    st.header("📋 Rose della Lega & Allerta Contratti")
    sq_df = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
    
    if not sq_df.empty:
        sq_scelta = st.selectbox("Seleziona la FantaSquadra", sq_df["nome"].tolist())
        sq_id = int(sq_df[sq_df["nome"] == sq_scelta]["id"].values[0])
        
        rosa_df = pd.read_sql_query("""
            SELECT c.nome AS Calciatore, c.ruolo AS Ruolo, r.data_scadenza AS Scadenza, r.tipo_possesso AS Stato
            FROM rose r JOIN calciatori c ON r.calciatore_id = c.id WHERE r.fanta_squadra_id = ?
        """, conn, params=(sq_id,))
        
        if not rosa_df.empty:
            limite = datetime.now() + timedelta(days=180)
            def colora_scadenze(val):
                try:
                    dt = datetime.strptime(val, "%Y-%m-%d")
                    if datetime.now() <= dt <= limite:
                        return "background-color: #ffcccc; color: #cc0000; font-weight: bold;"
                except: pass
                return ""
            st.info("💡 I giocatori evidenziati in rosso scadono entro 6 mesi.")
            st.dataframe(rosa_df.style.map(colora_scadenze, subset=["Scadenza"]), use_container_width=True)
        else:
            st.warning("Nessun giocatore associato a questa rosa.")
    else:
        st.info("Nessuna squadra presente. Carica prima i dati nella sezione 'Carica File (Dati)'.")

# 2. FUNZIONALITÀ: ACQUISTA GIOCATORE (4 ANNI)
elif scelta == "Acquista Giocatore (4 Anni)":
    st.header("✍️ Nuovo Acquisto nel Listone")
    sq_df = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
    
    if not sq_df.empty:
        sq_scelta = st.selectbox("Assegna a:", sq_df["nome"].tolist())
        sq_id = int(sq_df[sq_df["nome"] == sq_scelta]["id"].values[0])
        
        svincolati = pd.read_sql_query("SELECT * FROM calciatori WHERE id NOT IN (SELECT calciatore_id FROM rose)", conn)
        if not svincolati.empty:
            gioc_scelto = st.selectbox("Calciatore da acquistare", svincolati["nome"].tolist())
            gioc_id = int(svincolati[svincolati["nome"] == gioc_scelto]["id"].values[0])
            
            if st.button("Firma Contratto Pluriennale"):
                oggi = datetime.now()
                scadenza = oggi + timedelta(days=4*365)
                cursor = conn.cursor()
                cursor.execute("INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (?, ?, ?, ?, 'PROPRIETA')",
                               (sq_id, gioc_id, oggi.strftime("%Y-%m-%d"), scadenza.strftime("%Y-%m-%d")))
                conn.commit()
                st.success(f"✅ {gioc_scelto} acquistato fino al {scadenza.strftime('%Y-%m-%d')}!")
                st.rerun()
        else:
            st.error("Nessun giocatore svincolato nel listone.")
    else:
        st.info("Nessuna squadra presente. Carica prima i dati nella sezione 'Carica File (Dati)'.")

