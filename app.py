from datetime import datetime, timedelta
import pandas as pd
import streamlit as st

st.title("Gestione Prestiti")

# Esempio di database/session state per i prestiti
if "prestiti" not in st.session_state:
  st.session_state.prestiti = pd.DataFrame(
      columns=[
          "ID",
          "Oggetto / Articolo",
          "A chi",
          "Data Inizio",
          "Durata",
          "Stato",
      ]
  )

# --- SEZIONE: Aggiungi un nuovo prestito ---
st.subheader("Registra Nuovo Prestito")
with st.form("form_prestito"):
  articolo = st.text_input("Oggetto o Strumento in prestito")
  destinatario = st.text_input("A chi è stato prestato")
  data_inizio = st.date_input("Data di inizio", value=datetime.today())
  durata = st.selectbox("Durata prestito", ["6 mesi", "1 anno"])

  submitted = st.form_submit_button("Registra Prestito")
  if submitted:
    nuovo_id = len(st.session_state.prestiti) + 1
    nuovo_record = pd.DataFrame({
        "ID": [nuovo_id],
        "Oggetto / Articolo": [articolo],
        "A chi": [destinatario],
        "Data Inizio": [data_inizio],
        "Durata": [durata],
        "Stato": ["Attivo"],
    })
    st.session_state.prestiti = pd.concat(
        [st.session_state.prestiti, nuovo_record], ignore_index=True
    )
    st.success("Prestito registrato con successo!")

# --- SEZIONE: Gestione Prestiti Attivi (Rinnova / Interrompi) ---
st.subheader("Prestiti in Corso & Gestione")

if not st.session_state.prestiti.empty:
  for index, row in st.session_state.prestiti.iterrows():
    col1, col2, col3, col4 = st.columns([2, 2, 2, 2])

    with col1:
      st.write(f"**{row['Oggetto / Articolo']}** a {row['A chi']}")
      st.write(f"Inizio: {row['Data Inizio']} ({row['Durata']})")

    with col2:
      st.badge = st.markdown(f"Stato: **{row['Stato']}**")

    with col3:
      # Pulsante per rinnovare (estende di altri 6 mesi o 1 anno in base alla durata scelta)
      if row["Stato"] == "Attivo":
        if st.button(f"Rinnova", key=f"rinnova_{index}"):
          st.session_state.prestiti.loc[index, "Stato"] = "Rinnovato"
          # Opzionalmente puoi aggiornare la data di inizio o aggiungere un log
          st.rerun()

    with col4:
      # Pulsante per interrompere il prestito
      if row["Stato"] in ["Attivo", "Rinnovato"]:
        if st.button(f"Interrompi", key=f"interrompi_{index}"):
          st.session_state.prestiti.loc[index, "Stato"] = "Interrotto"
          st.rerun()

  # Mostra la tabella completa aggiornata
  st.dataframe(st.session_state.prestiti, use_container_width=True)
else:
  st.info("Nessun prestito registrato al momento.")