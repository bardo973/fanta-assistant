import pandas as pd
import streamlit as st
from datetime import datetime

st.title("Gestione Rosa / Contratti")

# Esempio di inizializzazione dello stato o del DataFrame
if "giocatori" not in st.session_state:
    st.session_state["giocatori"] = pd.DataFrame(
        {
            "Nome": ["Giocatore 1", "Giocatore 2"],
            "Ruolo": ["A", "C"],
            "Squadra": ["Team A", "Team B"],
            "Scadenza Contratto": ["2027-06-30", "2028-06-30"],
            "Crediti": [20, 10],
        }
    )

df = st.session_state["giocatori"]

st.subheader("Modifica o Aggiungi Giocatore")

# Form per inserire o modificare un giocatore
with st.form("form_giocatore"):
    nome = st.text_input("Nome Giocatore")
    ruolo = st.selectbox("Ruolo", ["P", "D", "C", "A"])
    squadra = st.text_input("Squadra di Serie A")

    # Sostituito anni di contratto con la data di scadenza del contratto
    scadenza_contratto = st.date_input(
        "Data Scadenza Contratto", value=datetime.strptime("2027-06-30", "%Y-%m-%d")
    )

    crediti = st.number_input("Crediti pagati", min_value=1, value=1)

    submitted = st.form_submit_button("Salva Giocatore")
    if submitted and nome:
        nuova_riga = pd.DataFrame(
            {
                "Nome": [nome],
                "Ruolo": [ruolo],
                "Squadra": [squadra],
                "Scadenza Contratto": [str(scadenza_contratto)],
                "Crediti": [crediti],
            }
        )
        st.session_state["giocatori"] = pd.concat(
            [df, nuova_riga], ignore_index=True
        )
        st.success(f"Giocatore {nome} aggiunto con successo!")
        st.rerun()

st.subheader("Rosa Attuale")
# Mostra la tabella aggiornata con la scadenza del contratto
st.dataframe(st.session_state["giocatori"])