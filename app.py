from datetime import datetime, timedelta
import sqlite3
from flask import Flask, jsonify, request

app = Flask(__name__)
DB_NAME = "fantacalcio_career.db"


def init_db():
    """Inizializza il database con le tabelle necessarie."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # Tabella Squadre del Fantacalcio
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS fanta_squadre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            budget REAL NOT NULL
        )
    """
    )

    # Tabella Listone Generale Calciatori
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS calciatori (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            ruolo TEXT NOT NULL,
            squadra_reale TEXT NOT NULL,
            fantamedia REAL DEFAULT 0.0,
            gol INTEGER DEFAULT 0,
            assist INTEGER DEFAULT 0
        )
    """
    )

    # Tabella Rose e Contratti (Gestisce Proprietà, Scadenze e Prestiti)
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS rose (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fanta_squadra_id INTEGER,
            calciatore_id INTEGER,
            data_inizio TEXT NOT NULL,
            data_scadenza TEXT NOT NULL,
            tipo_possesso TEXT CHECK(tipo_possesso IN ('PROPRIETA', 'PRESTITO_SECCO')) NOT NULL,
            FOREIGN KEY(fanta_squadra_id) REFERENCES fanta_squadre(id),
            FOREIGN KEY(calciatore_id) REFERENCES calciatori(id)
        )
    """
    )

    # Inserimento dati dimostrativi (Popolamento iniziale se vuoto)
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
            ],
        )
        cursor.executemany(
            "INSERT INTO fanta_squadre (nome, budget) VALUES (?, ?)",
            [("FantaTeam A", 500.0), ("FantaTeam B", 500.0)],
        )
        # Assegna Lautaro a Team A con contratto di 4 anni (scadenza nel 2030)
        cursor.execute(
            "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (1, 1, '2026-08-19', '2030-08-19', 'PROPRIETA')"
        )
        # Assegna Leao a Team A ma in scadenza imminente (es. tra 3 mesi) per il test
        scadenza_breve = (datetime.now() + timedelta(days=90)).strftime(
            "%Y-%m-%d"
        )
        cursor.execute(
            "INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso) VALUES (1, 2, '2023-08-19', ?, 'PROPRIETA')",
            (scadenza_breve,),
        )

    conn.commit()
    conn.close()


# ----------------------------------------------------
# ENDPOINT 1: ACQUISTO CON CONTRATTO A 4 ANNI
# ----------------------------------------------------
@app.route("/acquista", methods=["POST"])
def acquista_giocatore():
    """Registra l'acquisto di un giocatore impostando un contratto di 4 anni."""
    data = request.json
    squadra_id = data["fanta_squadra_id"]
    calciatore_id = data["calciatore_id"]

    oggi = datetime.now()
    # Logica business richiesta: contratto fisso di 4 anni (4 * 365 giorni)
    scadenza = oggi + timedelta(days=4 * 365)

    data_inizio_str = oggi.strftime("%Y-%m-%d")
    data_scadenza_str = scadenza.strftime("%Y-%m-%d")

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso)
        VALUES (?, ?, ?, ?, 'PROPRIETA')
    """,
        (squadra_id, calciatore_id, data_inizio_str, data_scadenza_str),
    )
    conn.commit()
    conn.close()

    return (
        jsonify(
            {
                "status": "success",
                "message": f"Giocatore acquistato fino al {data_scadenza_str}",
            }
        ),
        201,
    )


# ----------------------------------------------------
# ENDPOINT 2: ROSA E GIOCATORI IN SCADENZA (< 6 MESI)
# ----------------------------------------------------
@app.route("/rosa/<int:squadra_id>", methods=["GET"])
def get_rosa(squadra_id):
    """Restituisce la rosa evidenziando i contratti che scadono entro 6 mesi."""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute(
        """
        SELECT r.id as contratto_id, c.nome, c.ruolo, r.data_scadenza, r.tipo_possesso
        FROM rose r
        JOIN calciatori c ON r.calciatore_id = c.id
        WHERE r.fanta_squadra_id = ?
    """,
        (squadra_id,),
    )
    giocatori = cursor.fetchall()

    rosa_output = []
    limite_scadenza = datetime.now() + timedelta(
        days=180
    )  # Finestra di 6 mesi

    for g in giocatori:
        data_scad_obj = datetime.strptime(g["data_scadenza"], "%Y-%m-%d")
        # Controllo se scade entro i prossimi 6 mesi e non è già scaduto
        in_scadenza = datetime.now() <= data_scad_obj <= limite_scadenza

        rosa_output.append(
            {
                "nome": g["nome"],
                "ruolo": g["ruolo"],
                "scadenza": g["data_scadenza"],
                "tipo": g["tipo_possesso"],
                "allerta_scadenza_6_mesi": in_scadenza,  # Flag per l'interfaccia frontend
            }
        )

    conn.close()
    return jsonify(rosa_output)


# ----------------------------------------------------
# ENDPOINT 3: SCAMBI MULTIPLI E PRESTITI
# ----------------------------------------------------
@app.route("/scambio", methods=["POST"])
def gestisci_scambio():
    """Gestisce scambi complessi (1 o più giocatori) e prestiti."""
    data = request.json
    squadra_a = data["squadra_a_id"]
    squadra_b = data["squadra_b_id"]

    # Liste di ID calciatori coinvolti
    giocatori_da_a_a_b = data.get("da_a_a_b", [])  # Es: [{"id": 1, "tipo": "PROPRIETA"}, {"id": 2, "tipo": "PRESTITO"}]
    giocatori_da_b_a_a = data.get("da_b_a_a", [])

    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    try:
        # Sposta i giocatori da Squadra A a Squadra B
        for item in giocatori_da_a_a_b:
            if item["tipo"] == "PROPRIETA":
                cursor.execute(
                    "UPDATE rose SET fanta_squadra_id = ? WHERE fanta_squadra_id = ? AND calciatore_id = ?",
                    (squadra_b, squadra_a, item["id"]),
                )
            elif item["tipo"] == "PRESTITO":
                # Il prestito secco scade a fine stagione calcistica (es. 30 Giugno)
                fine_stagione = f"{datetime.now().year + 1}-06-30"
                cursor.execute(
                    """
                    INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso)
                    VALUES (?, ?, ?, ?, 'PRESTITO_SECCO')
                """,
                    (
                        squadra_b,
                        item["id"],
                        datetime.now().strftime("%Y-%m-%d"),
                        fine_stagione,
                    ),
                )

        # Sposta i giocatori da Squadra B a Squadra A
        for item in giocatori_da_b_a_a:
            if item["tipo"] == "PROPRIETA":
                cursor.execute(
                    "UPDATE rose SET fanta_squadra_id = ? WHERE fanta_squadra_id = ? AND calciatore_id = ?",
                    (squadra_a, squadra_b, item["id"]),
                )
            elif item["tipo"] == "PRESTITO":
                fine_stagione = f"{datetime.now().year + 1}-06-30"
                cursor.execute(
                    """
                    INSERT INTO rose (fanta_squadra_id, calciatore_id, data_inizio, data_scadenza, tipo_possesso)
                    VALUES (?, ?, ?, ?, 'PRESTITO_SECCO')
                """,
                    (
                        squadra_a,
                        item["id"],
                        datetime.now().strftime("%Y-%m-%d"),
                        fine_stagione,
                    ),
                )

        conn.commit()
    except Exception as e:
        conn.rollback()
        return jsonify({"status": "error", "message": str(e)}), 400
    finally:
        conn.close()

    return jsonify({"status": "success", "message": "Operazione di mercato conclusa."})


# ----------------------------------------------------
# ENDPOINT 4: SCOUTING E CONFRONTO
# ----------------------------------------------------
@app.route("/scout/confronto", methods=["GET"])
def confronta_giocatori():
    """Confronta i dati statistici di due giocatori (es. uno nel listone e uno in rosa)."""
    id_g1 = request.args.get("id1")
    id_g2 = request.args.get("id2")

    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM calciatori WHERE id IN (?, ?)", (id_g1, id_g2))
    risultati = cursor.fetchall()
    conn.close()

    confronto = [dict(r) for r in risultati]
    return jsonify(confronto)


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
