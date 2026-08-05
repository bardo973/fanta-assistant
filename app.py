import streamlit as st
from pypdf import PdfReader

# Configurazione della pagina
st.set_page_config(
    page_title="Gestione Fantacalcio a 10",
    page_icon="⚽",
    layout="wide"
)

# Inizializzazione dello stato dell'applicazione (per mantenere i dati attivi nella sessione)
if 'squadre' not in st.session_state:
    # 10 squadre come da impostazione della tua lega
    st.session_state.squadre = {
        "BARDO": [],
        "NILO": [],
        "GALVA": [],
        "ROBBA": [],
        "Squadra 5": [],
        "Squadra 6": [],
        "Squadra 7": [],
        "Squadra 8": [],
        "Squadra 9": [],
        "Squadra 10": []
    }

st.title("⚽ Gestione Fantacalcio & Lettura Rose PDF")
st.markdown("Gestisci la tua lega a 10 squadre, importa i file PDF delle rose e controlla i giocatori.")

# --- BARRA LATERALE: NAVIGAZIONE E CARICAMENTO PDF ---
st.sidebar.header("Navigazione & Strumenti")
scelta_menu = st.sidebar.selectbox(
    "Scegli sezione", 
    ["Visualizza Rose", "Carica Rosa da PDF", "Aggiungi Giocatore Manualmente"]
)

st.sidebar.markdown("---")
st.sidebar.subheader("Squadre della Lega")
nome_squadre = list(st.session_state.squadre.keys())
st.sidebar.text(", ".join(nome_squadre))


# --- SEZIONE 1: VISUALIZZA ROSE ---
if scelta_menu == "Visualizza Rose":
    st.header("📋 Rose delle Squadre")
    
    squadra_selezionata = st.selectbox("Seleziona la squadra da visualizzare", nome_squadre)
    
    giocatori = st.session_state.squadre[squadra_selezionata]
    
    st.subheader(f"Rosa di: {squadra_selezionata} ({len(giocatori)} giocatori)")
    
    if giocatori:
        for idx, giocatore in enumerate(giocatori, 1):
            st.write(f"{idx}. {giocatore}")
            
        if st.button(f"Svuota la rosa di {squadra_selezionata}"):
            st.session_state.squadre[squadra_selezionata] = []
            st.rerun()
    else:
        info_testo = f"Nessun giocatore inserito per {squadra_selezionata}."
        st.info(info_testo)


# --- SEZIONE 2: CARICA ROSA DA PDF ---
elif scelta_menu == "Carica Rosa da PDF":
    st.header("📄 Importa Rosa da File PDF")
    st.markdown("Carica il file PDF contenente la rosa o il listino. L'app estrarrà il testo e ti permetterà di associarlo a una squadra.")
    
    squadra_destinazione = st.selectbox("A quale squadra vuoi assegnare i giocatori del PDF?", nome_squadre)
    
    uploaded_pdf = st.file_uploader("Seleziona il file PDF", type=["pdf"])
    
    if uploaded_pdf is not None:
        try:
            # Lettura del PDF
            reader = PdfReader(uploaded_pdf)
            testo_pdf = ""
            
            for page in reader.pages:
                testo_estratto = page.extract_text()
                if testo_estratto:
                    testo_pdf += testo_estratto + "\n"
            
            st.success("File PDF letto con successo!")
            
            # Mostra anteprima del testo grezzo
            with st.expander("Visualizza testo estratto dal PDF"):
                st.text(testo_pdf)
            
            # Elaborazione delle righe
            righe = [r.strip() for r in testo_pdf.split("\n") if r.strip()]
            
            st.write(f"Trovate **{len(righe)}** righe di testo potenziali nel documento.")
            
            # Opzione per importare
            if st.button(f"Conferma e Importa in {squadra_destinazione}"):
                # Aggiunge le righe lette alla squadra selezionata
                st.session_state.squadre[squadra_destinazione].extend(righe)
                st.success(f"Aggiunti {len(righe)} elementi alla rosa di {squadra_destinazione}!")
                st.rerun()
                
        except Exception as e:
            st.error(f"Errore durante l'elaborazione del PDF: {e}")


# --- SEZIONE 3: AGGIUNGI GIOCATORE MANUALMENTE ---
elif scelta_menu == "Aggiungi Giocatore Manualmente":
    st.header("➕ Inserimento Manuale")
    
    squadra_scelta = st.selectbox("Seleziona squadra", nome_squadre, key="manual_sq")
    nuovo_giocatore = st.text_input("Nome del giocatore (es. Ruolo - Nome - Squadra - Crediti)")
    
    if st.button("Aggiungi Giocatore"):
        if nuovo_giocatore.strip():
            st.session_state.squadre[squadra_scelta].append(nuovo_giocatore.strip())
            st.success(f"Giocatore aggiunto con successo a {squadra_scelta}!")
        else:
            st.warning("Inserisci un nome valido per il giocatore.")