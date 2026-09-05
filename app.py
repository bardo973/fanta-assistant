import plotly.graph_objects as go
import streamlit as st
import pandas as pd
import json
import os
import difflib
import pickle
import tempfile
import shutil
from datetime import datetime
from typing import Dict, List, Optional, Any, Tuple
import io
import random
import hashlib

# ============================================================
# CONFIGURAZIONE
# ============================================================
st.set_page_config(
    page_title="FantaManager 2026/27",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

SAVE_FILE_PKL = "fantamanager_state_v2.pkl"
SAVE_FILE_JSON = "fantamanager_save.json"
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]

def get_nomi_squadre():
    """Ritorna la lista dinamica delle squadre dallo stato, o il default."""
    return st.session_state.get("nomi_squadre", list(NOMI_SQUADRE))

ANNO_CORRENTE = 2026
CONTRATTO_ANNI = 3
CREDITI_INIZIALI = 50
ROSA_REQ = {"P": 3, "D": 9, "C": 9, "A": 7}
MAX_UNDO = 10

# ============================================================
# CSS CUSTOM
# ============================================================
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0b0f19 0%, #12122e 100%);
    }
    .stSidebar { background-color: #0f0f24 !important; }
    h1, h2, h3 { color: #00d26a !important; font-family: 'Segoe UI', sans-serif; }
    .stButton>button {
        border-radius: 8px; font-weight: 600; transition: all 0.2s;
        background: linear-gradient(90deg, #00d26a, #00a854);
        color: white; border: none;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,210,106,0.3);
    }
    .stButton>button[kind="secondary"] {
        background: #2a2a4a; color: #ddd;
    }
    .card-giocatore {
        background: rgba(30,30,63,0.7) !important;
        backdrop-filter: blur(10px);
        border-radius: 10px; padding: 12px;
        margin-bottom: 8px; border-left: 4px solid #00d26a;
        border: 1px solid rgba(255,255,255,0.08);
        box-shadow: 0 8px 32px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05);
    }
    .badge-prestito {
        background: #ff6b6b; color: white; padding: 2px 8px;
        border-radius: 12px; font-size: 0.75em; font-weight: bold;
    }
    .metric-box {
        background: #1a1a2e; border-radius: 10px; padding: 16px;
        text-align: center; border: 1px solid #2a2a4a;
    }
    div[data-testid="stMetricValue"] { 
        font-size: 1.8rem !important; 
        font-weight: 700 !important; 
        text-shadow: 0 0 10px rgba(0,210,106,0.3);
    }

    .card-3d-titolare {
        background: linear-gradient(145deg, #1e1e3f, #2a2a4a);
        border-radius: 12px;
        padding: 10px 12px;
        margin-bottom: 8px;
        box-shadow: 0 6px 12px rgba(0,0,0,0.4), 0 2px 4px rgba(0,0,0,0.3);
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
        cursor: pointer;
        position: relative;
    }
    .card-3d-titolare:hover {
        transform: translateY(-6px) scale(1.03);
        box-shadow: 0 20px 40px rgba(0,210,106,0.25), 0 0 0 1px rgba(0,210,106,0.1);
    }
    .card-3d-panchina {
        background: linear-gradient(145deg, #15152b, #1a1a2e);
        border-radius: 10px;
        padding: 8px 12px;
        margin-bottom: 6px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.2);
        opacity: 0.75;
        transition: all 0.3s ease;
        cursor: pointer;
    }
    .card-3d-panchina:hover {
        transform: translateY(-3px) scale(1.02);
        opacity: 1;
        box-shadow: 0 8px 16px rgba(0,0,0,0.3);
    }
</style>
""", unsafe_allow_html=True)

# ============================================================
# LISTONE DEFAULT
# ============================================================
LISTONE_DEFAULT = [
    {"Nome": "Svilar", "Ruolo": "P", "Squadra_SerieA": "Roma", "Quotazione": 38, "FantaMedia": 6.0, "Consiglio": "top", "Note": "18 clean sheet, fantamedia 6, media voto 6.35", "Quotazione_2025_26": 35, "Prezzo_Consigliato": None},
    {"Nome": "Carnesecchi", "Ruolo": "P", "Squadra_SerieA": "Atalanta", "Quotazione": 34, "FantaMedia": 6.1, "Consiglio": "top", "Note": "13 clean sheet, media voto 6.5, con Sarri può migliorare", "Quotazione_2025_26": 34, "Prezzo_Consigliato": None},
    {"Nome": "Maignan", "Ruolo": "P", "Squadra_SerieA": "Milan", "Quotazione": 34, "FantaMedia": 5.9, "Consiglio": "top", "Note": "13 clean sheet, 2 rigori parati, affidabile", "Quotazione_2025_26": 29, "Prezzo_Consigliato": None},
    {"Nome": "Butez", "Ruolo": "P", "Squadra_SerieA": "Como", "Quotazione": 32, "FantaMedia": 5.8, "Consiglio": "top", "Note": "19 clean sheet, miglior difesa del campionato", "Quotazione_2025_26": 32, "Prezzo_Consigliato": None},
    {"Nome": "Martinez", "Ruolo": "P", "Squadra_SerieA": "Inter", "Quotazione": 29, "FantaMedia": 5.7, "Consiglio": "consigliato", "Note": "Nuovo titolare, ex Genoa, fiducia Chivu", "Quotazione_2025_26": 23, "Prezzo_Consigliato": None},
    {"Nome": "Meret", "Ruolo": "P", "Squadra_SerieA": "Napoli", "Quotazione": 30, "FantaMedia": 5.8, "Consiglio": "consigliato", "Note": "Titolare con Allegri, sottovalutato, ottimo rapporto qualità-prezzo", "Quotazione_2025_26": 31, "Prezzo_Consigliato": None},
    {"Nome": "De Gea", "Ruolo": "P", "Squadra_SerieA": "Fiorentina", "Quotazione": 24, "FantaMedia": 5.6, "Consigliato": "consigliato", "Note": "Stagione del riscatto, hype sceso, low risk", "Quotazione_2025_26": 26, "Prezzo_Consigliato": None},
    {"Nome": "Vicario", "Ruolo": "P", "Squadra_SerieA": "Juventus", "Quotazione": 28, "FantaMedia": 5.7, "Consiglio": "consigliato", "Note": "Nuovo titolare, ex Empoli, top assoluto in Serie A", "Quotazione_2025_26": 15, "Prezzo_Consigliato": None},
    {"Nome": "Mandas", "Ruolo": "P", "Squadra_SerieA": "Lazio", "Quotazione": 22, "FantaMedia": 5.5, "Consiglio": "consigliato", "Note": "Titolare con Gattuso, portiere da modificatore", "Quotazione_2025_26": 12, "Prezzo_Consigliato": None},
    {"Nome": "Falcone", "Ruolo": "P", "Squadra_SerieA": "Lecce", "Quotazione": 17, "FantaMedia": 5.5, "Consiglio": "scommessa", "Note": "Media voto 6.41, low cost, garanzia voti alti", "Quotazione_2025_26": 5, "Prezzo_Consigliato": None},
    {"Nome": "Stankovic", "Ruolo": "P", "Squadra_SerieA": "Venezia", "Quotazione": 13, "FantaMedia": 5.3, "Consiglio": "scommessa", "Note": "Torna in Serie A, potenziale sorpresa", "Quotazione_2025_26": 6, "Prezzo_Consigliato": None},
    {"Nome": "Corvi", "Ruolo": "P", "Squadra_SerieA": "Parma", "Quotazione": 12, "FantaMedia": 5.4, "Consiglio": "scommessa", "Note": "Nuovo titolare, aveva fatto vedere buone cose", "Quotazione_2025_26": 4, "Prezzo_Consigliato": None},
    {"Nome": "Caprile", "Ruolo": "P", "Squadra_SerieA": "Cagliari", "Quotazione": 10, "FantaMedia": 5.3, "Consiglio": "scommessa", "Note": "Buon portiere da modificatore, low cost", "Quotazione_2025_26": 3, "Prezzo_Consigliato": None},
]

# ============================================================
# INIZIALIZZAZIONE SESSION STATE
# ============================================================
if "nomi_squadre" not in st.session_state:
    st.session_state["nomi_squadre"] = list(NOMI_SQUADRE)

if "listone" not in st.session_state:
    st.session_state["listone"] = pd.DataFrame(LISTONE_DEFAULT)

if "rose" not in st.session_state:
    # Inizializza un dizionario vuoto per le rose di ogni squadra
    st.session_state["rose"] = {squadra: [] for squadra in get_nomi_squadre()}

if "crediti" not in st.session_state:
    st.session_state["crediti"] = {squadra: CREDITI_INIZIALI for squadra in get_nomi_squadre()}

# ============================================================
# INTERFACCIA PRINCIPALE E NAVIGAZIONE
# ============================================================
st.sidebar.title("⚙️ Pannello di Controllo")
scelta_sezione = st.sidebar.radio(
    "Vai a:",
    ["🏠 Home & Panoramica", "📋 Listone Giocatori", "👥 Gestione Rose", "💰 Crediti & Bilancio"]
)

if scelta_sezione == "🏠 Home & Panoramica":
    st.title("⚽ FantaManager 2026/27 - Dashboard")
    st.markdown("Benvenuto nel tuo gestore di fantacalcio avanzato. Usa il menu laterale per navigare tra le sezioni.")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Squadre Partecipanti", len(get_nomi_squadre()))
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Giocatori nel Listone", len(st.session_state["listone"]))
        st.markdown('</div>', unsafe_allow_html=True)
    with col3:
        st.markdown('<div class="metric-box">', unsafe_allow_html=True)
        st.metric("Crediti Iniziali", CREDITI_INIZIALI)
        st.markdown('</div>', unsafe_allow_html=True)

elif scelta_sezione == "📋 Listone Giocatori":
    st.title("📋 Listone Giocatori")
    df_listone = st.session_state["listone"]
    
    # Filtro rapido per ruolo
    ruolo_filtro = st.selectbox("Filtra per Ruolo", ["Tutti", "P", "D", "C", "A"])
    if ruolo_filtro != "Tutti":
        df_mostra = df_listone[df_listone["Ruolo"] == ruolo_filtro]
    else:
        df_mostra = df_listone
        
    st.dataframe(df_mostra, use_container_width=True)

elif scelta_sezione == "👥 Gestione Rose":
    st.title("👥 Gestione Rose delle Squadre")
    squadra_selezionata = st.selectbox("Seleziona Squadra", get_nomi_squadre())
    
    st.subheader(f"Rosa di: {squadra_selezionata}")
    rosa_corrente = st.session_state["rose"].get(squadra_selezionata, [])
    
    if len(rosa_corrente) == 0:
        st.info("Nessun giocatore in rosa al momento.")
    else:
        for p in rosa_corrente:
            st.markdown(f'<div class="card-giocatore"><b>{p.get("Nome")}</b> ({p.get("Ruolo")}) - {p.get("Squadra_SerieA")}</div>', unsafe_allow_html=True)

elif scelta_sezione == "💰 Crediti & Bilancio":
    st.title("💰 Gestione Crediti")
    crediti_df = pd.DataFrame(list(st.session_state["crediti"].items()), columns=["Squadra", "Crediti Residui"])
    st.dataframe(crediti_df, use_container_width=True)