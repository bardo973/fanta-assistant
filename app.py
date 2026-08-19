import sqlite3
from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

DB_NAME = "fantacalcio_career.db"


# --- INIZIALIZZAZIONE DATABASE ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fanta_squadre (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            budget REAL
        )"""
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS calciatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            nome TEXT, 
            ruolo TEXT, 
            squadra_reale TEXT, 
            fantamedia REAL, 
            gol INTEGER, 
            assist INTEGER
        )"""
    )
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rose (
            id INTEGER PRIMARY KEY AUTOINCREMENT, 
            fanta_squadra_id INTEGER, 
            calciatore_id INTEGER,
            data_inizio TEXT, 
            data_scadenza TEXT, 
            tipo_possesso TEXT
        )"""
    )

    cursor.execute("SELECT COUNT(*) FROM calciatori")
    if cursor.fetchone() == 0:
        cursor.executemany(
            "INSERT INTO calciatori (nome, ruolo, squadra_reale, fantamedia, gol, assist) VALUES (?, ?, ?, ?, ?, ?)",
            [
                ("Lautaro Martinez", "A", "Inter", 8.5, 22, 3),
                ("Rafael Leao", "A", "Milan", 7.8, 10, 8),
                ("Nicolò Barella", "C", "Inter", 6.9, 3, 5),
                ("Teun Koopmeiners", "C", "Juventus", 7.5, 11, 4),
                ("Alessandro Bastoni", "D", "Inter", 6.5, 1, 3),
                ("Marcus Thuram", "A", "Inter", 8.0, 15, 7),
                ("Dusan Vlahovic", "A", "Juventus", 7.9, 18, 2),
            ],
        )
        cursor.executemany(
            "INSERT INTO fanta_squadre (nome, budget) VALUES (?, ?)",
            [("FantaTeam A", 500.0), ("FantaTeam B", 500.0)],
        )

        oggi = datetime.now()
        scadenza_lunga = (oggi + timedelta(days=4 * 365)).strftime("%Y-%m-%d")
        scadenza_breve = (oggi + timedelta(days=90)).strftime(
            "%Y-%m-%d"
        )  # Scade tra 3 mesi (Evidenziato)

        cursor.execute(
            "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (1, 1, ?, ?, 'PROPRIETA')",
            (oggi.strftime("%Y-%m-%d"), scadenza_lunga),
        )
        cursor.execute(
            "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (1, 2, ?, ?, 'PROPRIETA')",
            (oggi.strftime("%Y-%m-%d"), scadenza_breve),
        )

    conn.commit()
    conn.close()


init_db()

# --- INTERFACCIA STREAMLIT ---
st.set_page_config(page_title="FantaManager Pro", layout="wide")
st.title("⚽ FantaManager Career Pro")

menu = [
    "Visualizza Rose & Scadenze",
    "Acquista Giocatore (4 Anni)",
    "Mercato & Scambi",
    "Scouting & Confronto",
]
scelta = st.sidebar.selectbox("Navigazione App", menu)

conn = sqlite3.connect(DB_NAME)

# 1. VISUALIZZA ROSE E SCADENZE
if scelta == "Visualizza Rose & Scadenze":
    st.header("📋 Gestione Rose della Lega")
    squadre = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
    squadra_scelta = st.selectbox(
        "Seleziona la FantaSquadra", squadre["nome"].tolist()
    )
    squadra_id = squadre[squadre["nome"] == squadra_scelta]["id"].values[0]

    query = """
        SELECT c.nome, c.ruolo, r.data_scadenza, r.tipo_possesso 
        FROM rose r JOIN calciatori c ON r.calciatore_id = c.id 
        WHERE r.fanta_squadra_id = ?
    """
    rosa_df = pd.read_sql_query(query, conn, params=(int(squadra_id),))

    if not rosa_df.empty:
        limite_scadenza = datetime.now() + timedelta(days=180)

        def evidenzia_scadenza(val):
            try:
                dt = datetime.strptime(val, "%Y-%m-%d")
                if datetime.now() <= dt <= limite_scadenza:
                    return "background-color: #ffcccc; color: black; font-weight: bold;"
            except:
                pass
            return ""

        st.subheader(f"Giocatori in Rosa: {squadra_scelta}")
        st.write("⚠️ I giocatori evidenziati in rosso scadono entro 6 mesi.")
        st.dataframe(
            rosa_df.style.map(evidenzia_scadenza, subset=["data_scadenza"]),
            use_container_width=True,
        )
    else:
        st.info("Questa squadra non ha ancora calciatori in rosa.")

# 2. ACQUISTA GIOCATORE CON CONTRATTO 4 ANNI
elif scelta == "Acquista Giocatore (4 Anni)":
    st.header("✍️ Nuovo Acquisto Cardine")
    squadre = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)
    squadra_scelta = st.selectbox("Affida a:", squadre["nome"].tolist())
    squadra_id = squadre[squadre["nome"] == squadra_scelta]["id"].values[0]

    svincolati_query = "SELECT * FROM calciatori WHERE id NOT IN (SELECT calciatore_id FROM rose)"
    svincolati_df = pd.read_sql_query(svincolati_query, conn)

    if not svincolati_df.empty:
        giocatore_scelto = st.selectbox(
            "Seleziona il calciatore da acquistare", svincolati_df["nome"].tolist()
        )
        giocatore_id = svincolati_df[svincolati_df["nome"] == giocatore_scelto][
            "id"
        ].values[0]

        if st.button("Firma Contratto (4 Anni)"):
            oggi = datetime.now()
            scadenza = oggi + timedelta(days=4 * 365)
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (?, ?, ?, ?, 'PROPRIETA')",
                (
                    int(squadra_id),
                    int(giocatore_id),
                    oggi.strftime("%Y-%m-%d"),
                    scadenza.strftime("%Y-%m-%d"),
                ),
            )
            conn.commit()
            st.success(
                f"Contratto depositato! {giocatore_scelto} è legato a {squadra_scelta} fino al {scadenza.strftime('%Y-%m-%d')}."
            )
            st.rerun()
    else:
        st.warning("Non ci sono giocatori svincolati nel listone.")

# 3. MERCATO, SCAMBI MULTIPLI E PRESTITI
elif scelta == "Mercato & Scambi":
    st.header("🤝 Tavolo delle Trattative")
    squadre = pd.read_sql_query("SELECT * FROM fanta_squadre", conn)

    col1, col2 = st.columns(2)
    with col1:
        sq_a = st.selectbox("FantaSquadra A", squadre["nome"].tolist(), index=0)
        id_a = squadre[squadre["nome"] == sq_a]["id"].values[0]
        giocatori_a = pd.read_sql_query(
            "SELECT c.id, c.nome FROM rose r JOIN calciatori c ON r.calciatore_id = c.id WHERE r.fanta_squadra_id = ?",
            conn,
            params=(int(id_a),),
        )
        da_a = st.multiselect(
            f"Giocatori da cedere da {sq_a}",
            giocatori_a["nome"].tolist(),
            key="da_a",
        )

    with col2:
        sq_b = st.selectbox("FantaSquadra B", squadre["nome"].tolist(), index=1)
        id_b = squadre[squadre["nome"] == sq_b]["id"].values[0]
        giocatori_b = pd.read_sql_query(
            "SELECT c.id, c.nome FROM rose r JOIN calciatori c ON r.calciatore_id = c.id WHERE r.fanta_squadra_id = ?",
            conn,
            params=(int(id_b),),
        )
        da_b = st.multiselect(
            f"Giocatori da cedere da {sq_b}",
            giocatori_b["nome"].tolist(),
            key="da_b",
        )

    tipo_affare = st.radio("Formula dell'operazione", ["PROPRIETA", "PRESTITO"])

    if st.button("Concludi Scambio"):
        if sq_a == sq_b:
            st.error("Seleziona due squadre diverse per negoziare!")
        elif not da_a and not da_b:
            st.warning("Inserisci almeno un giocatore nella trattativa.")
        else:
            cursor = conn.cursor()
            # Sposta da A a B
            for g_nome in da_a:
                g_id = giocatori_a[giocatori_a["nome"] == g_nome]["id"].values[0]
                if tipo_affare == "PROPRIETA":
                    cursor.execute(
                        "UPDATE rose SET fanta_squadra_id = ? WHERE calciatore_id = ?",
                        (int(id_b), int(g_id)),
                    )
                else:
                    fine_stagione = f"{datetime.now().year + 1}-06-30"
                    cursor.execute(
                        "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (?, ?, ?, ?, 'PRESTITO_SECCO')",
                        (
                            int(id_b),
                            int(g_id),
                            datetime.now().strftime("%Y-%m-%d"),
                            fine_stagione,
                        ),
                    )

            # Sposta da B a A
            for g_nome in da_b:
                g_id = giocatori_b[giocatori_b["nome"] == g_nome]["id"].values[0]
                if tipo_affare == "PROPRIETA":
                    cursor.execute(
                        "UPDATE rose SET fanta_squadra_id = ? WHERE calciatore_id = ?",
                        (int(id_a), int(g_id)),
                    )
                else:
                    fine_stagione = f"{datetime.now().year + 1}-06-30"
                    cursor.execute(
                        "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (?, ?, ?, ?, 'PRESTITO_SECCO')",
                        (
                            int(id_a),
                            int(g_id),
                            datetime.now().strftime("%Y-%m-%d"),
                            fine_stagione,
                        ),
                    )

            conn.commit()
            st.success("🤝 Affare concluso con successo!")
            st.rerun()

# 4. SCOUTING E CONFRONTO GIOCATORI
elif scelta == "Scouting & Confronto":
    st.header("🔬 Area Scouting Head-to-Head")
    tutti_calciatori = pd.read_sql_query(
