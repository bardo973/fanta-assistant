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
    .card-3d-titolare:active {
        transform: translateY(-2px) scale(1.01);
        box-shadow: 0 0 30px rgba(0,210,106,0.6), 0 8px 16px rgba(0,0,0,0.4);
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
    .card-3d-panchina:active {
        transform: translateY(-1px);
        box-shadow: 0 0 15px rgba(0,210,106,0.3);
    }

    .stButton>button {
        box-shadow: 0 0 15px rgba(0,210,106,0.2);
    }
    .stButton>button:hover {
        box-shadow: 0 0 25px rgba(0,210,106,0.5);
        transform: translateY(-2px) scale(1.02);
    }
    .stScatterChart {
        background: transparent !important;
    }

    /* 🎴 Flip Card 3D */
    .flip-card {
        background-color: transparent;
        perspective: 1000px;
    }
    .flip-card-inner {
        position: relative;
        width: 100%;
        height: 100%;
        text-align: left;
        transition: transform 0.6s cubic-bezier(0.4, 0, 0.2, 1);
        transform-style: preserve-3d;
    }
    .flip-card:hover .flip-card-inner {
        transform: rotateY(180deg);
    }
    .flip-card-front, .flip-card-back {
        position: absolute;
        width: 100%;
        height: 100%;
        -webkit-backface-visibility: hidden;
        backface-visibility: hidden;
        border-radius: 12px;
    }
    .flip-card-back {
        transform: rotateY(180deg);
    }
    
    /* 💎 PREMIUM CARDS — >40cr */
    .card-premium {
        position: relative;
        z-index: 1;
    }
    .card-premium::before {
        content: "";
        position: absolute;
        top: -3px; left: -3px; right: -3px; bottom: -3px;
        border-radius: 14px;
        background: linear-gradient(45deg, #ffd700, #ff8c00, #ffd700, #ffaa00);
        background-size: 400% 400%;
        z-index: -1;
        animation: gradient-rotate 3s ease infinite;
        opacity: 0.85;
    }
    @keyframes gradient-rotate {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }
    .card-premium .flip-card-front {
        border-left: 4px solid #ffd700 !important;
        box-shadow: 0 0 30px rgba(255, 215, 0, 0.4), inset 0 1px 0 rgba(255,255,255,0.1) !important;
    }
    .card-premium .flip-card-front::after {
        content: "✨";
        position: absolute;
        top: 6px;
        right: 10px;
        font-size: 1.1em;
        animation: sparkle 2s infinite;
        pointer-events: none;
    }
    @keyframes sparkle {
        0%, 100% { opacity: 0.3; transform: scale(1) rotate(0deg); }
        50% { opacity: 1; transform: scale(1.4) rotate(15deg); }
    }
    .card-premium .flip-card-back {
        border: 2px solid rgba(255, 215, 0, 0.5) !important;
        box-shadow: 0 0 25px rgba(255, 215, 0, 0.25) !important;
    }
    .badge-premium {
        background: linear-gradient(90deg, #ffd700, #ff8c00);
        color: #1a1a00;
        padding: 2px 10px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: bold;
        box-shadow: 0 0 10px rgba(255,215,0,0.5);
        text-shadow: none;
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
    {"Nome": "De Gea", "Ruolo": "P", "Squadra_SerieA": "Fiorentina", "Quotazione": 24, "FantaMedia": 5.6, "Consiglio": "consigliato", "Note": "Stagione del riscatto, hype sceso, low risk", "Quotazione_2025_26": 26, "Prezzo_Consigliato": None},
    {"Nome": "Vicario", "Ruolo": "P", "Squadra_SerieA": "Juventus", "Quotazione": 28, "FantaMedia": 5.7, "Consiglio": "consigliato", "Note": "Nuovo titolare, ex Empoli, top assoluto in Serie A", "Quotazione_2025_26": 15, "Prezzo_Consigliato": None},
    {"Nome": "Mandas", "Ruolo": "P", "Squadra_SerieA": "Lazio", "Quotazione": 22, "FantaMedia": 5.5, "Consiglio": "consigliato", "Note": "Titolare con Gattuso, portiere da modificatore", "Quotazione_2025_26": 12, "Prezzo_Consigliato": None},
    {"Nome": "Falcone", "Ruolo": "P", "Squadra_SerieA": "Lecce", "Quotazione": 17, "FantaMedia": 5.5, "Consiglio": "scommessa", "Note": "Media voto 6.41, low cost, garanzia voti alti", "Quotazione_2025_26": 5, "Prezzo_Consigliato": None},
    {"Nome": "Stankovic", "Ruolo": "P", "Squadra_SerieA": "Venezia", "Quota": 13, "FantaMedia": 5.3, "Consiglio": "scommessa", "Note": "Torna in Serie A, potenziale sorpresa", "Quotazione_2025_26": 6, "Prezzo_Consigliato": None},
    {"Nome": "Corvi", "Ruolo": "P", "Squadra_SerieA": "Parma", "Quotazione": 12, "FantaMedia": 5.4, "Consiglio": "scommessa", "Note": "Nuovo titolare, aveva fatto vedere buone cose", "Quotazione_2025_26": 4, "Prezzo_Consigliato": None},
    {"Nome": "Caprile", "Ruolo": "P", "Squadra_SerieA": "Cagliari", "Quotazione": 10, "FantaMedia": 5.3, "Consiglio": "scommessa", "Note": "Buon portiere da modificatore, low cost", "Quotazione_2025_26": 3, "Prezzo_Consigliato": None},
]