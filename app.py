import streamlit as st
import pandas as pd
import numpy as np

# Configurazione iniziale della pagina
st.set_page_config(
    page_title="FantaManager & Scouting Hub 10 Squadre", 
    page_icon="⚽", 
    layout="wide"
)

# --- LISTA DELLE 10 SQUADRE UFFICIALI ---
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

# --- FUNZIONI DI CALCOLO E PULIZIA DATI ---
def calcola_prezzo_consigliato(row):
    quot = row.get('Quotazione', 10)
    fm = row.get('FantaMedia', 6.0)
    fm_2026 = row.get('FM_2026', fm)
    fm_2025 = row.get('FM_2025', fm)
    
    # Media pesata per dare più valore all'ultima stagione disputata
    media_storica = (fm * 0.5) + (fm_2026 * 0.3) + (fm_2025 * 0.2)
    bonus_rendimento = max(0, (media_storica - 6.0) * 6)
    
    ruolo = row.get('Ruolo', 'C')
    moltiplicatore_ruolo = {'A': 1.4, 'C': 1.15, 'D': 1.0, 'P': 0.85}.get(ruolo, 1.0)
    
    prezzo_stimato = (quot + bonus_rendimento) * moltiplicatore_ruolo
    return max(1, int(round(prezzo_stimato)))

def calcola_trend(row):
    fm_attuale = row.get('FantaMedia', 6.0)
    fm_passata = row.get('FM_2026', fm_attuale)
    diff = fm_attuale - fm_passata
    if diff > 0.15:
        return "📈 In Crescita"
    elif diff < -0.15:
        return "📉 In Calo"
    else:
        return "➡️ Stabile"

def calcola_costanza(row):
    # Simula un indice di regolarità basato sulla differenza tra fantamedia e voto base (6.0)
    fm = row.get('FantaMedia', 6.0)
    if fm >= 6.5:
        return "⭐ Altissima"
    elif fm >= 6.1:
        return "✅ Buona"
    elif fm >= 5.8:
        return "⚠️ Altalenante"
    else:
        return "🚨 Rischiosa"

def pulisci_colonna_numerica(valore):
    if pd.isna(valore):
        return 6.0
    if isinstance(valore, (int, float)):
        return float(valore)
    s = str(valore).strip().replace(',', '.')
    try:
        return float(s)
    except:
        return 6.0

def pulisci_colonna_intera(valore):
    if pd.isna(valore):
        return 10
    if isinstance(valore, (int, float)):
        return int(valore)
    s = str(valore).strip().replace(',', '.')
    try:
        return int(float(s))
    except:
        return 10

# --- INIZIALIZZAZIONE SICURA DELLO STATO DELLA SESSIONE ---
if 'squadre' not in st.session_state or not isinstance(st.session_state.squadre, dict):
    st.session_state.squadre = {}

for sq in NOMI_SQUADRE:
    if sq not in st.session_state.squadre:
        st.session_state.squadre[sq] = {"crediti": 500, "rosa": []}

if 'listone_calciatori' not in st.session_state:
    # Popoliamo un listone iniziale di esempio con dati di Serie A reali/simulati
    st.session_state.listone_calciatori = [
        {"Nome": "Skorupski", "Ruolo": "P", "Squadra_SerieA": "Bologna", "Quotazione": 14, "FantaMedia": 5.2, "FM_2026": 5.3, "FM_2025": 5.1},
        {"Nome": "Gabbia", "Ruolo": "D", "Squadra_SerieA": "Milan", "Quotazione": 8, "FantaMedia": 6.3, "FM_2026": 6.2, "FM_2025": 6.0},
        {"Nome": "Cambiaso", "Ruolo": "D", "Squadra_SerieA": "Juventus", "Quotazione": 14, "FantaMedia": 6.7, "FM_2026": 6.6, "FM_2025": 6.4},
        {"Nome": "Dimarco", "Ruolo": "D", "Squadra_SerieA": "Inter", "Quotazione": 18, "FantaMedia": 7.1, "FM_2026": 6.9, "FM_2025": 7.0},
        {"Nome": "Zaccagni", "Ruolo": "C", "Squadra_SerieA": "Lazio", "Quotazione": 19, "FantaMedia": 7.5, "FM_2026": 7.4, "FM_2025": 7.3},
        {"Nome": "Barella", "Ruolo": "C", "Squadra_SerieA": "Inter", "Quotazione": 16, "FantaMedia": 6.8, "FM_2026": 6.7, "FM_2025": 6.8},
        {"Nome": "Pulisic", "Ruolo": "C", "Squadra_SerieA": "Milan", "Quotazione": 22, "FantaMedia": 7.9, "FM_2026": 7.8, "FM_2025": 7.5},
        {"Nome": "Lautaro Martinez", "Ruolo": "A", "Squadra_SerieA": "Inter", "Quotazione": 38, "FantaMedia": 8.5, "FM_2026": 8.2, "FM_2025": 8.6},
        {"Nome": "Kvaratskhelia", "Ruolo": "A", "Squadra_SerieA": "Napoli", "Quotazione": 32, "FantaMedia": 7.8, "FM_2026": 7.6, "FM_2025": 7.9},
        {"Nome": "Vlahovic", "Ruolo": "A", "Squadra_SerieA": "Juventus", "Quotazione": 34, "FantaMedia": 8.1, "FM_2026": 7.9, "FM_2025": 8.0},
        {"Nome": "Lookman", "Ruolo": "A", "Squadra_SerieA": "Atalanta", "Quotazione": 30, "FantaMedia": 8.0, "FM_2026": 8.1, "FM_2025": 7.7},
        {"Nome": "Camarda", "Ruolo": "A", "Squadra_SerieA": "Milan", "Quotazione": 5, "FantaMedia": 6.5, "FM_2026": 6.0, "FM_2025": 5.8}
    ]

if 'voti_giornata' not in st.session_state:
    st.session_state.voti_giornata = {}

# --- INTERFACCIA GRAFICA STREAMLIT ---
st.title("⚽ FantaManager & Scouting Hub")
st.markdown("### Sistema di gestione 10 Squadre, Analisi Costanza e Monitoraggio Voti")

# Sidebar con riepilogo rapido del Budget delle 10 Squadre
st.sidebar.header("📊 Crediti Rimanenti")
for sq in NOMI_SQUADRE:
    spesi = sum(p['Costo_Acquisto'] for p in st.session_state.squadre[sq]["rosa"])
    rimanenti = st.session_state.squadre[sq]["crediti"] - spesi
    st.sidebar.markdown(f"**{sq}**: `{rimanenti} / {st.session_state.squadre[sq]['crediti']} CR`")

# Creazione dei Tab principali richiesti
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📋 Listone & Scouting", 
    "🛡️ Gestione 10 Rose", 
    "📈 Grafici & Statistiche", 
    "🎯 Voti Giornata & Live", 
    "📥 Carica Listone"
])

# --- TAB 1: LISTONE & SCOUTING AVANZATO ---
with tab1:
    st.header("🔍 Tabella Scouting dei Calciatori")
    st.write("Usa i filtri per scovare i giocatori con il miglior rapporto qualità/prezzo ed esaminare il loro trend di costanza.")
    
    df_listone = pd.DataFrame(st.session_state.listone_calciatori)
    
    # Calcolo dinamico delle nuove metriche avanzate
    df_listone['Prezzo_Consigliato'] = df_listone.apply(calcola_prezzo_consigliato, axis=1)
    df_listone['Trend'] = df_listone.apply(calcola_trend, axis=1)
    df_listone['Costanza'] = df_listone.apply(calcola_costanza, axis=1)
    
    # Filtri Interattivi
    col_f1, col_f2, col_f3 = st.columns(3)
    with col_f1:
        filtro_ruolo = st.multiselect("Filtra per Ruolo", options=['P', 'D', 'C', 'A'], default=['P', 'D', 'C', 'A'])
    with col_f2:
        filtro_squadra = st.text_input("Cerca Squadra Serie A (es. Inter, Milan)")
    with col_f3:
        ordina_convenienza = st.checkbox("Ordina per convenienza (Prezzo Consigliato decrescente)", value=True)
        
    # Applicazione dei filtri al dataframe
    df_filtrato = df_listone[df_listone['Ruolo'].isin(filtro_ruolo)]
    if filtro_squadra:
        df_filtrato = df_filtrato[df_filtrato['Squadra_SerieA'].str.contains(filtro_squadra, case=False, na=False)]
        
    if ordina_convenienza:
        df_filtrato = df_filtrato.sort_values(by='Prezzo_Consigliato', ascending=False)
        
    st.dataframe(df_filtrato, use_container_width=True)
    
    # Modulo rapido per assegnare un giocatore dal listone a una rosa
    st.subheader("🔨 Assegna Giocatore ad una Squadra (Asta/Mercato)")
    col_as1, col_as2, col_as3 = st.columns(3)
    with col_as1:
        giocatore_scelto = st.selectbox("Seleziona Giocatore dal Listone", options=df_listone['Nome'].tolist())
    with col_as2:
        squadra_destinataria = st.selectbox("Assegna alla Fanta-Squadra", options=NOMI_SQUADRE)
    with col_as3:
        prezzo_asta = st.number_input("Prezzo di Acquisto (Crediti)", min_value=1, max_value=500, value=1)
        
    if st.button("Conferma Acquisto e Assegna alla Rosa"):
        info_giocatore = df_listone[df_listone['Nome'] == giocatore_scelto].iloc[0].to_dict()
        info_giocatore['Costo_Acquisto'] = int(prezzo_asta)
        
        # Verifica duplicati nella rosa della squadra
        nomi_in_rosa = [p['Nome'] for p in st.session_state.squadre[squadra_destinataria]["rosa"]]
        if info_giocatore['Nome'] in nomi_in_rosa:
            st.error(f"Il giocatore {info_giocatore['Nome']} è già presente nella rosa di {squadra_destinataria}!")
        else:
            st.session_state.squadre[squadra_destinataria]["rosa"].append(info_giocatore)
            st.success(f"Acquisto registrato: {info_giocatore['Nome']} va a {squadra_destinataria} per {prezzo_asta} crediti!")
            st.rerun()

# --- TAB 2: GESTIONE DELLE 10 ROSE ---
with tab2:
    st.header("🛡️ Gestione Rose e Svincoli")
    squadra_selezionata = st.selectbox("Scegli la Fanta-Squadra da visualizzare/modificare", options=NOMI_SQUADRE)
    
    rosa_attuale = st.session_state.squadre[squadra_selezionata]["rosa"]
    
    if len(rosa_attuale) == 0:
        st.warning(f"La rosa di {squadra_selezionata} è attualmente vuota. Vai nel tab 'Listone' per assegnare i giocatori.")
    else:
        df_rosa = pd.DataFrame(rosa_attuale)
        
        # Conteggio ruoli
        conteggio_ruoli = df_rosa['Ruolo'].value_counts()
        st.write(f"**Composizione Rosa:** Portieri: {conteggio_ruoli.get('P', 0)} | Difensori: {conteggio_ruoli.get('D', 0)} | Centrocampisti: {conteggio_ruoli.get('C', 0)} | Attaccanti: {conteggio_ruoli.get('A', 0)}")
        
        st.dataframe(df_rosa[['Nome', 'Ruolo', 'Squadra_SerieA', 'Quotazione', 'FantaMedia', 'Costo_Acquisto']], use_container_width=True)
        
        # Sistema di svincolo rapido
        st.subheader("❌ Svincola un Giocatore")
        giocatore_da_svincolare = st.selectbox("Seleziona il calciatore da rimuovere dalla rosa", options=[p['Nome'] for p in rosa_attuale])
        if st.button(f"Svincola {giocatore_da_svincolare}"):
            st.session_state.squadre[squadra_selezionata]["rosa"] = [p for p in rosa_attuale if p['Nome'] != giocatore_da_svincolare]
            st.success(f"{giocatore_da_svincolare} è stato svincolato correttamente!")
            st.rerun()

# --- TAB 3: GRAFICI & STATISTICHE (DATAVIZ) ---
with tab3:
    st.header("📈 Grafici e Analisi Comparativa delle Squadre")
    
    # Preparazione dati per il grafico dei crediti
    nomi_barres = []
    crediti_rimanenti_barres = []
    for sq in NOMI_SQUADRE:
        spesi = sum(p['Costo_Acquisto'] for p in st.session_state.squadre[sq]["rosa"])
        rimanenti = st.session_state.squadre[sq]["crediti"] - spesi
        nomi_barres.append(sq)
        crediti_rimanenti_barres.append(rimanenti)
        
    df_grafico = pd.DataFrame({
        'Fanta-Squadra': nomi_barres,
        'Crediti Rimanenti': crediti_rimanenti_barres
    })
    
    st.subheader("💰 Distribuzione dei Portafogli della Lega")
    st.bar_chart(data=df_grafico, x='Fanta-Squadra', y='Crediti Rimanenti', use_container_width=True)
    
    # Statistica extra: FantaMedia complessiva teorica della rosa
    st.subheader("📊 FantaMedia Totale Accumulata dalle Rose")
    medie_rose = []
    for sq in NOMI_SQUADRE:
        rosa = st.session_state.squadre[sq]["rosa"]
        if len(rosa) > 0:
            media_fm = sum(p['FantaMedia'] for p in rosa) / len(rosa)
        else:
            media_fm = 0.0
        medie_rose.append(round(media_fm, 2))
        
    df_medie = pd.DataFrame({
        'Fanta-Squadra': NOMI_SQUADRE,
        'FantaMedia Media': medie_rose
    })
    st.bar_chart(data=df_medie, x='Fanta-Squadra', y='FantaMedia Media', color="#4CAF50", use_container_width=True)

# --- TAB 4: VOTI GIORNATA & LIVE ---
with tab4:
    st.header("🎯 Inserimento Voti Settimanali e Calcolo Punteggi Live")
    st.write("Inserisci i voti reali della giornata di Serie A per calcolare istantaneamente i punteggi accumulati dalle 10 squadre.")
    
    df_listone_voti = pd.DataFrame(st.session_state.listone_calciatori)
    
    st.subheader("📝 Compila i Voti della Giornata Corrente")
    col_v1, col_v2 = st.columns(2)
    with col_v1:
        giocatore_voto = st.selectbox("Seleziona il Giocatore che ha preso il voto", options=df_listone_voti['Nome'].tolist(), key="voto_gioc")
    with col_v2:
        voto_preso = st.number_input("Inserisci il Fantavoto (Voto + Bonus/Malus)", min_value=1.0, max_value=15.0, value=6.0, step=0.5)
        
    if st.button("Salva Voto Giocatore"):
        st.session_state.voti_giornata[giocatore_voto] = voto_preso
        st.success(f"Registrato: {giocatore_voto} = {voto_preso}")
        
    if len(st.session_state.voti_giornata) > 0:
        st.write("**Tabellone dei Voti Inseriti:**")
        st.json(st.session_state.voti_giornata)
        
        # Calcolo live dei punteggi per le 10 squadre basato sui giocatori in rosa che hanno preso il voto
        st.subheader("🏆 Classifica Punteggio Live della Giornata")
        punteggi_squadre_live = {}
        for sq in NOMI_SQUADRE:
            punteggio_totale = 0.0
            giocatori_voti_presi = 0
            for p in st.session_state.squadre[sq]["rosa"]:
                if p['Nome'] in st.session_state.voti_giornata:
                    punteggio_totale += st.session_state.voti_giornata[p['Nome']]
                    giocatori_voti_presi += 1
            punteggi_squadre_live[sq] = {"Punti Live": punteggio_totale, "Giocatori a Voto": giocatori_voti_presi}
            
        df_live = pd.DataFrame.from_dict(punteggi_squadre_live, orient='index').reset_index().rename(columns={'index': 'Fanta-Squadra'})
        st.dataframe(df_live.sort_values(by="Punti Live", ascending=False), use_container_width=True)
    else:
        st.info("Nessun voto inserito per questa giornata. Digita i voti sopra per vedere i punteggi calcolati live.")

# --- TAB 5: CARICA E AGGIORNA LISTONE (EXCEL) ---
with tab5:
    st.header("📥 Importazione Automatica Listone da Excel/CSV")
    st.write("Scarica il file Excel delle quotazioni ufficiali da Fantacalcio.it e trascinalo qui sotto per aggiornare i dati dell'applicazione.")
    
    file_caricato = st.file_uploader("Scegli un file Excel (.xlsx) o CSV (.csv)", type=["xlsx", "csv"])
    
    if file_caricato is not None:
        try:
            if file_caricato.name.endswith('.xlsx'):
                df_caricato = pd.read_excel(file_caricato)
            else:
                df_caricato = pd.read_csv(file_caricato)
                
            st.success("File caricato con successo! Ecco un'anteprima dei dati rilevati:")
            st.dataframe(df_caricato.head(10), use_container_width=True)
            
            st.subheader("🔄 Mappatura e Sincronizzazione delle Colonne")
            st.write("Seleziona quali colonne del tuo file corrispondono ai dati richiesti dall'applicazione:")
            
            col_m1, col_m2 = st.columns(2)
            with col_m1:
                col_nome = st.selectbox("Colonna per il NOME", options=df_caricato.columns.tolist())
                col_ruolo = st.selectbox("Colonna per il RUOLO", options=df_caricato.columns.tolist())
            with col_m2:
                col_squadra = st.selectbox("Colonna per la SQUADRA", options=df_caricato.columns.tolist())
                col_quot = st.selectbox("Colonna per la QUOTAZIONE attuale", options=df_caricato.columns.tolist())
                
            if st.button("Sovrascrivi Listone con i Nuovi Dati Importati"):
                nuovo_listone = []
                for _, row in df_caricato.iterrows():
                    nuovo_listone.append({
                        "Nome": str(row[col_nome]),
                        "Ruolo": str(row[col_ruolo]).upper()[0] if pd.notna(row[col_ruolo]) else 'C',
                        "Squadra_SerieA": str(row[col_squadra]),
                        "Quotazione": pulisci_colonna_intera(row[col_quot]),
                        "FantaMedia": 6.0, # Valori di default pronti per essere sovrascritti dai voti della giornata
                        "FM_2026": 6.0,
                        "FM_2025": 6.0
                    })
                st.session_state.listone_calciatori = nuovo_listone
                st.success(f"Sincronizzazione completata! {len(nuovo_listone)} calciatori inseriti nel database attivo.")
                st.rerun()
                
        except Exception as e:
            st.error(f"Si è verificato un errore durante la lettura del file: {e}")
