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
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, budget REAL
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS calciatori (
        id INTEGER PRIMARY KEY AUTOINCREMENT, nome TEXT, ruolo TEXT, 
        squadra_reale TEXT, fantamedia REAL, gol INTEGER, assist INTEGER
    )""")
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS rose (
        id INTEGER PRIMARY KEY AUTOINCREMENT, fanta_squadra_id INTEGER, 
        calciatore_id INTEGER, data_inizio TEXT, data_scadenza TEXT, tipo_possesso TEXT
    )""")
    cursor.execute("SELECT COUNT(*) FROM calciatori")
    if cursor.fetchone()[0] == 0:
        cursor.executemany(
            "INSERT INTO calciatori (nome, ruolo, squadra_reale, fantamedia, gol, assist) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Lautaro Martinez", "A", "Inter", 8.5, 22, 3),
                ("Rafael Leao", "A", "Milan", 7.8, 10, 8),
                ("Nicolò Barella", "C", "Inter", 6.9, 3, 5),
                ("Teun Koopmeiners", "C", "Juventus", 7.5, 11, 4),
                ("Alessandro Bastoni", "D", "Inter", 6.5, 1, 3),
                ("Marcus Thuram", "A", "Inter", 8.0, 15, 7),
                ("Dusan Vlahovic", "A", "Juventus", 7.9, 18, 2)
            ]
        )
        cursor.executemany(
            "INSERT INTO fanta_squadre (nome, budget) VALUES (?, ?)",
            [("FantaTeam A", 500.0), ("FantaTeam B", 500.0)]
        )
        oggi = datetime.now()
        scad_lunga = (oggi + timedelta(days=4*365)).strftime("%Y-%m-%d")
        scad_breve = (oggi + timedelta(days=90)).strftime("%Y-%m-%d")
        cursor.execute("INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (1, 1, ?, ?, 'PROPRIETA')", (oggi.strftime("%Y-%m-%d"), scad_lunga))
        cursor.execute("INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (1, 2, ?, ?, 'PROPRIETA')", (oggi.strftime("%Y-%m-%d"), scad_breve))
    conn.commit()
    conn.close()

init_db()

st.title("⚽ FantaManager Career Pro")
menu = ["Visualizza Rose & Scadenze", "Acquista Giocatore (4 Anni)", "Mercato & Scambi", "Scouting & Confronto"]
scelta = st.sidebar.selectbox("Navigazione App", menu)
conn = sqlite3.connect(DB_NAME)

if scelta == "Visualizza Rose & Scadenze":
    st.header("📋 Rose della Lega & Allerta Contratti")
    sq_df = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
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
        st.warning("Nessun giocatore in rosa.")

elif scelta == "Acquista Giocatore (4 Anni)":
    st.header("✍️ Nuovo Acquisto nel Listone")
    sq_df = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
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
        st.error("Nessun giocatore svincolato.")

elif scelta == "Mercato & Scambi":
    st.header("🤝 Area Trattative e Trasferimenti")
    sq_df = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
    col1, col2 = st.columns(2)
    
    with col1:
        sq_a = st.selectbox("FantaSquadra A", sq_df["nome"].tolist(), index=0)
        id_a = int(sq_df[sq_df["nome"] == sq_a]["id"].values[0])
        gioc_a = pd.read_sql_query("SELECT c.id, c.nome FROM rose r JOIN calciatori c ON r.calciatore_id = c.id WHERE r.fanta_squadra_id = ?", conn, params=(id_a,))
        cessioni_a = st.multiselect(f"Cessioni da {sq_a}", gioc_a["nome"].tolist())
        
    with col2:
        sq_b = st.selectbox("FantaSquadra B", sq_df["nome"].tolist(), index=1)
        id_b = int(sq_df[sq_df["nome"] == sq_b]["id"].values[0])
        gioc_b = pd.read_sql_query("SELECT c.id, c.nome FROM rose r JOIN calciatori c ON r.calciatore_id = c.id WHERE r.fanta_squadra_id = ?", conn, params=(id_b,))
        cessioni_b = st.multiselect(f"Cessioni da {sq_b}", gioc_b["nome"].tolist())
        
    formula = st.radio("Formula dell'accordo:", ["PROPRIETÀ (Scambio)", "PRESTITO"])
    
    if st.button("Concludi Accordo"):
        if sq_a == sq_b:
            st.error("Scegli squadre diverse.")
        elif not cessioni_a and not cessioni_b:
            st.warning("Seleziona almeno un giocatore.")
        else:
            cursor = conn.cursor()
            for nome in cessioni_a:
                g_id = int(gioc_a[gioc_a["nome"] == nome]["id"].values[0])
                if formula == "PROPRIETÀ (Scambio)":
                    cursor.execute("UPDATE rose SET fanta_squadra_id = ? WHERE calciatore_id = ?", (id_b, g_id))
                else:
                    cursor.execute("INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (?, ?, ?, ?, 'PRESTITO')",
                                   (id_b, g_id, datetime.now().strftime("%Y-%m-%d"), f"{datetime.now().year + 1}-06-30"))
            for nome in cessioni_b:
                g_id = int(gioc_b[gioc_b["nome"] == nome]["id"].values[0])
                if formula == "PROPRIETÀ (Scambio)":
                    cursor.execute("UPDATE rose SET fanta_squadra_id = ? WHERE calciatore_id = ?", (id_a, g_id))
                else:
                    cursor.execute("INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (?, ?, ?, ?, 'PRESTITO')",
                                   (id_a, g_id, datetime.now().strftime("%Y-%m-%d"), f"{datetime.now().year + 1}-06-30"))
            conn.commit()
            st.success("🤝 Scambio registrato!")
            st.rerun()

elif scelta == "Scouting & Confronto":
    st.header("🔬 Area Scouting Head-to-Head")
    scout_df = pd.read_sql_query("SELECT * FROM calciatori ORDER BY nome ASC", conn)
    elenco = scout_df["nome"].tolist()
    
    c_sx, c_dx = st.columns(2)
    with c_sx:
        p1 = st.selectbox("Primo Giocatore", elenco, index=0)
        d1 = scout_df[scout_df["nome"] == p1].iloc[0]
        st.metric("Fantamedia", float(d1["fantamedia"]))
        st.write(f"⚽ Gol: **{int(d1['gol'])}** | 👟 Assist: **{int(d1['assist'])}**")
        st.write(f"🛡️ Ruolo: **{d1['ruolo']}** | Club: **{d1['squadra_reale']}**")
    with c_dx:
        p2 = st.selectbox("Secondo Giocatore", elenco, index=3)
        d2 = scout_df[scout_df["nome"] == p2].iloc[0]
        st.metric("Fantamedia", float(d2["fantamedia"]))
        st.write(f"⚽ Gol: **{int(d2['gol'])}** | 👟 Assist: **{int(d2['assist'])}**")
        st.write(f"🛡️ Ruolo: **{d2['ruolo']}** | Club: **{d2['squadra_reale']}**")

conn.close()
