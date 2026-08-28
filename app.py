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
        background: #1e1e3f; border-radius: 10px; padding: 12px;
        margin-bottom: 8px; border-left: 4px solid #00d26a;
    }
    .badge-prestito {
        background: #ff6b6b; color: white; padding: 2px 8px;
        border-radius: 12px; font-size: 0.75em; font-weight: bold;
    }
    .metric-box {
        background: #1a1a2e; border-radius: 10px; padding: 16px;
        text-align: center; border: 1px solid #2a2a4a;
    }
    div[data-testid="stMetricValue"] { font-size: 1.8rem !important; font-weight: 700 !important; }

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
</style>
""", unsafe_allow_html=True)

# ============================================================
# LISTONE DEFAULT
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":34,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Martinez L.","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":29,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ramos G.","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":27,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kolo Muani","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":26,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kean","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":25,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Douvikas","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Yildiz","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":23,"FantaMedia":8.1,"Consiglio":"top","Note":"Bomber implacabile da primo slot assoluto. Spendi il budget necessario.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Paz N.","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":30,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Calhanoglu","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":27,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"McTominay","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":26,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":25,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rabiot","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":22,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Bruyne","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":15,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Baturina","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":19,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mora","Ruolo":"C","Squadra_SerieA":"Roma","Quotazione":19,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Da Cunha","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":18,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":18,"FantaMedia":7.3,"Consiglio":"top","Note":"Top di centrocampo. Rigorista, trequartista o centrocampista con vizio costante del gol.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":32,"FantaMedia":6.7,"Consiglio":"top","Note":"Top di reparto. Bonus pesanti da trequartista aggiunto o garanzia da modificatore.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":17,"FantaMedia":6.7,"Consiglio":"top","Note":"Top di reparto. Bonus pesanti da trequartista aggiunto o garanzia da modificatore.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Molina N.","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.7,"Consiglio":"top","Note":"Top di reparto. Bonus pesanti da trequartista aggiunto o garanzia da modificatore.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":15,"FantaMedia":6.7,"Consiglio":"top","Note":"Top di reparto. Bonus pesanti da trequartista aggiunto o garanzia da modificatore.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Akanji","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":16,"FantaMedia":6.7,"Consiglio":"top","Note":"Top di reparto. Bonus pesanti da trequartista aggiunto o garanzia da modificatore.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":15,"FantaMedia":6.7,"Consiglio":"top","Note":"Top di reparto. Bonus pesanti da trequartista aggiunto o garanzia da modificatore.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Martinez Jo.","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":17,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vicario","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":16,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Butez","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":16,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Meret","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":11,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":16,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":15,"FantaMedia":5.7,"Consiglio":"top","Note":"Top player assoluto del reparto. Porta da modificatore e da clean sheet.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Scamacca","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Davis K.","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":19,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Esposito F.P.","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":16,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Berardi","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":18,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Krstovic","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":18,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Ketelaere","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":17,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dybala","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":14,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Laurientè","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":15,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Simeone","Ruolo":"A","Squadra_SerieA":"Torino","Quotazione":15,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Castro S.","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":14,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Raspadori","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":13,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Leao","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":18,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Santos A.","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":14,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dovbyk","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":16,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pellegrino M.","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":15,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Secondo slot di lusso. Attaccante titolare da doppia cifra garantita.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zaccagni","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":16,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Atta","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":17,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Barella","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":17,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":14,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"McKennie","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":17,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":7,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Conceicao","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Taylor K.","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":13,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mastantuono","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Moreira","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ederson D.S.","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Jones C.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zambo Anguissa","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":11,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ekkelenkamp","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zielinski","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":11,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Diouf","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":8,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Konè M.","Ruolo":"C","Squadra_SerieA":"Roma","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Samardzic","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gudmundsson A.","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":13,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Politano","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vergara","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":8,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Saelemaekers","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Thuram K.","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Casadei","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rodriguez Je.","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":12,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Baldanzi","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":11,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pellegrini Lo.","Ruolo":"C","Squadra_SerieA":"Roma","Quotazione":10,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Semitop di reparto. Centrocampista offensivo di inserimento o regista da bonus leggeri.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rrahmani","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":14,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pavlovic","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":14,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kalulu","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":13,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Solet","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":13,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"N'Dicka","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":13,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bastoni","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":14,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ostigard","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":11,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Di Lorenzo","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":12,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Spence","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":12,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":11,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ramon","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":10,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vasquez","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":9,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gila","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":12,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Chalobah T.","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":9,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Scalvini","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":10,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Hermoso","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":10,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cambiaso","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":9,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dodò","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":10,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Semidifensore top. Titolare fisso di ottima spinta o ottimo voto costante.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Gea","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":13,"FantaMedia":5.6,"Consiglio":"consigliato","Note":"Ottimo portiere titolare, ottimo rapporto qualità/prezzo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Skorupski","Ruolo":"P","Squadra_SerieA":"Bologna","Quotazione":10,"FantaMedia":5.6,"Consiglio":"consigliato","Note":"Ottimo portiere titolare, ottimo rapporto qualità/prezzo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Colombo","Ruolo":"A","Squadra_SerieA":"Genoa","Quotazione":11,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pinamonti","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":13,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Diao","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":11,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Adams A.","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":12,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Soulè","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":12,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Tourè E.","Ruolo":"A","Squadra_SerieA":"Parma","Quotazione":11,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Esposito Se.","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":13,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bowie","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":10,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kevin Carlos","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":13,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Romero D.","Ruolo":"A","Squadra_SerieA":"Parma","Quotazione":10,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"David","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":9,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Piccoli","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":8,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dia","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":10,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ratkov","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":10,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Nkunku","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":13,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Titolare da terzo/quarto slot per ruotare i tuoi titolari.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bernabè","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Locatelli","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":9,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cristante","Ruolo":"C","Squadra_SerieA":"Roma","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cancellieri","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":9,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Schmid","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Elmas","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Colpani","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ndour","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Calò","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cissè A.","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pasalic","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":9,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fazzini","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mandragora","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":9,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ferguson","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Volpato","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Isaksen","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":9,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fagioli","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lobotka","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Chukwueze","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cambiaghi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sucic P.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Liberali","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Konè I.","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":9,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Frendrup","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"El Aynaoui","Ruolo":"C","Squadra_SerieA":"Roma","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fitz-Jim","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Loftus-Cheek","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Odgaard","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":8,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Unai Gomez","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pessina","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sow","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Douglas Luiz","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Musah","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Oristanio","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":7,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Buon titolare di riempimento, garantisce voto ma pochi bonus.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dragusin","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Couto","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Spinazzola","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Carlos Augusto","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Miranda J.","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Valeri","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gabbia","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Jimenez A.","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bartesaghi","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Romagnoli","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Delprato","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Norton-Cuffy","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Badiashile","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Valle","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mina","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kristensen T.","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Tiago Gabriel","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Marusic","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vojvoda","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Idzes","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sutalo J.","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zortea","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lucumì","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bernasconi","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Valdepenas","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Koulierakis","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bellanova","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Viery","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Celik","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Buongiorno","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Obert","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Heggem","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mangas","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Obrador","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Coco","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ahanor","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Marcandalli","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pavard","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Provstgaard","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rodriguez Ju.","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Troilo","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ismajli","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bella-Kotchap","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Comuzzo","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gallo","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Monterisi","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Estupinan","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Beukema","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kamara H.","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Tavares N.","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":6,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Winter","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Hainaut","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Joao Mario","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kossounou","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Helland","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Hien","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":8,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Tomori","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":7,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Titolare di rendimento utile a completare il reparto.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mandas","Ruolo":"P","Squadra_SerieA":"Lazio","Quotazione":9,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Falcone","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":8,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Okoye","Ruolo":"P","Squadra_SerieA":"Udinese","Quotazione":9,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Caprile","Ruolo":"P","Squadra_SerieA":"Cagliari","Quotazione":9,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bijlow","Ruolo":"P","Squadra_SerieA":"Genoa","Quotazione":8,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Muric","Ruolo":"P","Squadra_SerieA":"Sassuolo","Quotazione":7,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Stankovic F.","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":6,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Palmisani","Ruolo":"P","Squadra_SerieA":"Frosinone","Quotazione":4,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Thiam","Ruolo":"P","Squadra_SerieA":"Monza","Quotazione":5,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Di Gregorio","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":9,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Daffara","Ruolo":"P","Squadra_SerieA":"Parma","Quotazione":7,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Milinkovic-Savic V.","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":5,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Perin","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":6,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Provedel","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":2,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Desplanches","Ruolo":"P","Squadra_SerieA":"Frosinone","Quotazione":2,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Portiere low-cost per alternanze o leghe numerose.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Adams C.","Ruolo":"A","Squadra_SerieA":"Torino","Quotazione":9,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cutrone","Ruolo":"A","Squadra_SerieA":"Monza","Quotazione":9,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Osmajic","Ruolo":"A","Squadra_SerieA":"Genoa","Quotazione":8,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ghedjemis","Ruolo":"A","Squadra_SerieA":"Frosinone","Quotazione":9,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Yeboah J.","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":8,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Boga","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":6,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Geubbels","Ruolo":"A","Squadra_SerieA":"Lecce","Quotazione":9,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Raimondo","Ruolo":"A","Squadra_SerieA":"Frosinone","Quotazione":7,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Maldini","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":5,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Camarda","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":5,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rrahmani Al.","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":8,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bonny","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":7,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zapata D.","Ruolo":"A","Squadra_SerieA":"Torino","Quotazione":7,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mota","Ruolo":"A","Squadra_SerieA":"Monza","Quotazione":5,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Neres","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":6,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Noslin","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":6,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vitinha O.","Ruolo":"A","Squadra_SerieA":"Genoa","Quotazione":8,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa dal potenziale interessante o terzo slot low-cost.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kvernadze","Ruolo":"A","Squadra_SerieA":"Frosinone","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"N'Dri","Ruolo":"A","Squadra_SerieA":"Lecce","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mendy P.","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Milik","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":5,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Stulic","Ruolo":"A","Squadra_SerieA":"Lecce","Quotazione":7,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Adorante","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":5,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lang","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Elphege","Ruolo":"A","Squadra_SerieA":"Parma","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gimenez","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":6,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mutandwa","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":6,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sulemana K.","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":6,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Frigan","Ruolo":"A","Squadra_SerieA":"Parma","Quotazione":5,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Giovane","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Robinson J.","Ruolo":"A","Squadra_SerieA":"Monza","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ekhator","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lucca","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Borrelli","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Havel","Ruolo":"A","Squadra_SerieA":"Genoa","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kulenovic","Ruolo":"A","Squadra_SerieA":"Torino","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gueye","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Morata","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":4,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Varela G.","Ruolo":"A","Squadra_SerieA":"Monza","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kuhn","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":3,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Scommessa d'attacco, da prendere a pochissimi crediti come scommessa.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Karlstrom","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Oulai","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zalewski","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zhegrova","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cacciamani","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Romano","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Basic","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pierotti","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ellertsson","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Caqueret","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Coulibaly L.","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pisilli","Ruolo":"C","Squadra_SerieA":"Roma","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Akinsanmiro","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Nicolussi Caviglia","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rovella","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Adzic","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Tourè I.","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Winks","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Keita M.","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Matic","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Perez K.","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Piotrowski","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bakola","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Busio","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Moro N.","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Njie","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Adopo","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pobega","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":6,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dele-Bashiru","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Koopmeiners","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Jashari","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ngom","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fini","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Amondarain","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Berisha M.","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gineitis","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zerbin","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cataldi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cichella","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Luis Henrique","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Brescianini","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Diallo O.","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dominguez B.","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Miller L.","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sorensen O.","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fadera","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Meichtry","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sohm","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Traorè Hj.","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Almqvist","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Amorim","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Koutsoupias","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Addai","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fofana Y.","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gandelman","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Grillitsch","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mkhitaryan","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ilkhan","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ricci S.","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gilmour","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"El Azzouzi O.","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Felici","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":5,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Giovane talento o scommessa da bonus a costi contenuti.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Roon","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fabbian","Ruolo":"C","Squadra_SerieA":"Fiorentina","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Deiola","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gelli F.","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Messias","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Masini","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Prati","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Colombo L.","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Miretti","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sulemana I.","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Maleh","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Chakvetadze","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ciurria","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Folorunsho","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":4,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Aboukhlal","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Boloca","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Hasa","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lipani","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ordonez C.","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Duncan","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Venturino","Ruolo":"C","Squadra_SerieA":"Genoa","Quotazione":2,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Helgason","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":3,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Scommessa da leghe numerose o scommessa low cost da ultimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pedraza","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Holm","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kempf","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Olivera","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zè Pedro","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bracaglia","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fortini","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gaspar K.","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kelly L.","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Leysen F.","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pedersen","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Veiga D.","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Birindelli","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Calvani","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Comert","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Correia T.","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kabasele","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lucchesi","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Siebert","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Delli Carri","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Favasuli","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Palma","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Haps","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Oyono A.","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Parisi","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vitik","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bertola","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Doig","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gatti","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ghilardi","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Halhal","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mitaj","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Smolcic I.","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Valenti","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Walukiewicz","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zanoli","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Britschgi","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Floriani Mussolini","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ranieri L.","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Schingtienne","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Carboni A.","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kouadio","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kofler","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kolasinac","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Martin","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Arizala","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pongracic","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Terzic","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cittadini","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Marin R.","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zappa","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":4,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Candè","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sverko","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Franjic","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pellegrini Lu.","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Moreno M.","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":5,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa intrigante per gli ultimi slot o titolare di provincia a basso costo.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Akpoguma","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Alhassane","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Casale","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Aurelio","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Biraghi","Ruolo":"D","Squadra_SerieA":"Torino","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ebosse","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lazzari","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Otoa","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sabelli","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Van Der Brempt","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Diawara S.","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Jean","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sagrado","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Terracciano F.","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Idrissi R.","Ruolo":"D","Squadra_SerieA":"Cagliari","Quotazione":3,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Puczka","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":2,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Scommessa low-cost a sorpresa o giovane in rampa di lancio.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lontani","Ruolo":"A","Squadra_SerieA":"Parma","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vaz","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bayo V.","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Trepy","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Azon","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Martis","Ruolo":"A","Squadra_SerieA":"Parma","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lauberbach","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lisman","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gorter","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ilic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Przyborek","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Anjorin","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Zarraga","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Belahyane","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cremaschi","Ruolo":"C","Squadra_SerieA":"Parma","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kone B.","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Kaba","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Comotto","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Dagasso","Ruolo":"C","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"El Azzouzi A.","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Fofana Sa.","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Forson O.","Ruolo":"C","Squadra_SerieA":"Monza","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Iannoni","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Laerke","Ruolo":"C","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lahdo","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Liteta","Ruolo":"C","Squadra_SerieA":"Cagliari","Quotazione":1,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Abankwah","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ndiaye","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Odenthal","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ndaba","Ruolo":"D","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bakoune","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cabal","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Cinquegrano","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Silvestri","Ruolo":"D","Squadra_SerieA":"Bologna","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Carboni F.","Ruolo":"D","Squadra_SerieA":"Parma","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Marianucci","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mazzocchi","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mlacic","Ruolo":"D","Squadra_SerieA":"Udinese","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Rugani","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Antov","Ruolo":"D","Squadra_SerieA":"Monza","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Matturro","Ruolo":"D","Squadra_SerieA":"Genoa","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Missori","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Oyono J.","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Ziolkowski","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Amey","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Corrado","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Goldaniga","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gomes","Ruolo":"D","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Omar Fayed","Ruolo":"D","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Patric","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pieragnolo","Ruolo":"D","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Riserva fissa o giovanissimo, scommessa estrema da ultimissimo slot.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Mascardi","Ruolo":"P","Squadra_SerieA":"Torino","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Corvi","Ruolo":"P","Squadra_SerieA":"Parma","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Bleve","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Christensen O.","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Contini","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"De Marzi","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Di Gennaro","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Gollini","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Grandi","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Happonen","Ruolo":"P","Squadra_SerieA":"Bologna","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lezzerini","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Lolic","Ruolo":"P","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Montipò","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Motta","Ruolo":"P","Squadra_SerieA":"Lazio","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Padelli","Ruolo":"P","Squadra_SerieA":"Udinese","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Paleari","Ruolo":"P","Squadra_SerieA":"Torino","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Penev","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pessina Mas.","Ruolo":"P","Squadra_SerieA":"Bologna","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Piana","Ruolo":"P","Squadra_SerieA":"Udinese","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pinsoglio","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pisseri","Ruolo":"P","Squadra_SerieA":"Frosinone","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pizzignacco","Ruolo":"P","Squadra_SerieA":"Monza","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Pozzi","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Radunovic","Ruolo":"P","Squadra_SerieA":"Cagliari","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Renzetti","Ruolo":"P","Squadra_SerieA":"Lazio","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Russo A.","Ruolo":"P","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Satalino","Ruolo":"P","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sherri","Ruolo":"P","Squadra_SerieA":"Cagliari","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Siviero","Ruolo":"P","Squadra_SerieA":"Torino","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sommariva","Ruolo":"P","Squadra_SerieA":"Genoa","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Sportiello","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Stolz","Ruolo":"P","Squadra_SerieA":"Genoa","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Strajnar","Ruolo":"P","Squadra_SerieA":"Monza","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Terracciano","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Tornqvist","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Torriani","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Turati","Ruolo":"P","Squadra_SerieA":"Sassuolo","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vigorito","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
    {"Nome":"Vismara","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":1,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Terzo portiere, acquistabile solo come copertura a 1 credito.", "Quotazione_2025_26":None, "Prezzo_Consigliato":None},
]

for g in LISTONE_DEFAULT:
    g.setdefault("Prezzo_Consigliato", None)

# ============================================================
# STATE MANAGER (Pickle Atomico + Undo)
# ============================================================
class StateManager:
    @staticmethod
    def snapshot():
        if "_undo_stack" not in st.session_state:
            st.session_state._undo_stack = []
        snap = {
            "squadre": pickle.loads(pickle.dumps(st.session_state.squadre)),
            "storico_mercato": list(st.session_state.storico_mercato),
            "watchlist": list(st.session_state.watchlist),
            "prestiti": pickle.loads(pickle.dumps(st.session_state.prestiti)),
            "contratti": pickle.loads(pickle.dumps(st.session_state.contratti)),
            "giocatori_db": st.session_state.giocatori_db.copy(),
            "stats_storiche": st.session_state.stats_storiche.copy() if not st.session_state.stats_storiche.empty else pd.DataFrame(),
            "stats_per_stagione": {k: v.copy() for k, v in st.session_state.get("stats_per_stagione", {}).items()},
            "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
            "quotazioni_2025_26": st.session_state.quotazioni_2025_26.copy() if not st.session_state.quotazioni_2025_26.empty else pd.DataFrame(),
            "wizard_completato": st.session_state.get("wizard_completato", False),
        }
        st.session_state._undo_stack.append(snap)
        if len(st.session_state._undo_stack) > MAX_UNDO:
            st.session_state._undo_stack.pop(0)

    @staticmethod
    def undo():
        if not st.session_state.get("_undo_stack"):
            return False
        snap = st.session_state._undo_stack.pop()
        st.session_state.squadre = snap["squadre"]
        st.session_state.storico_mercato = snap["storico_mercato"]
        st.session_state.watchlist = snap["watchlist"]
        st.session_state.prestiti = snap["prestiti"]
        st.session_state.contratti = snap["contratti"]
        st.session_state.giocatori_db = snap["giocatori_db"]
        st.session_state.stats_storiche = snap["stats_storiche"]
        st.session_state.stats_per_stagione = snap["stats_per_stagione"]
        st.session_state.crediti_iniziali = snap["crediti_iniziali"]
        st.session_state.quotazioni_2025_26 = snap["quotazioni_2025_26"]
        st.session_state.wizard_completato = snap["wizard_completato"]
        invalidate_cache()
        return True

    @staticmethod
    def save():
        data = {
            "squadre": st.session_state.squadre,
            "storico_mercato": st.session_state.storico_mercato,
            "watchlist": st.session_state.watchlist,
            "prestiti": st.session_state.prestiti,
            "contratti": st.session_state.contratti,
            "giocatori_db": st.session_state.giocatori_db,
            "stats_storiche": st.session_state.stats_storiche,
            "stats_per_stagione": st.session_state.get("stats_per_stagione", {}),
            "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
            "quotazioni_2025_26": st.session_state.quotazioni_2025_26,
            "wizard_completato": st.session_state.get("wizard_completato", False),
        }
        tmp = tempfile.NamedTemporaryFile(delete=False, dir=".")
        try:
            with open(tmp.name, "wb") as f:
                pickle.dump(data, f)
            shutil.move(tmp.name, SAVE_FILE_PKL)
        except Exception:
            if os.path.exists(tmp.name):
                os.remove(tmp.name)
            raise

    @staticmethod
    def load():
        if os.path.exists(SAVE_FILE_PKL):
            try:
                with open(SAVE_FILE_PKL, "rb") as f:
                    data = pickle.load(f)
                StateManager._hydrate(data)
                return True
            except Exception:
                pass
        if os.path.exists(SAVE_FILE_JSON):
            try:
                with open(SAVE_FILE_JSON, "r", encoding="utf-8") as f:
                    data = json.load(f)
                db = data.get("giocatori_db", [])
                data["giocatori_db"] = pd.DataFrame(db) if db else pd.DataFrame(LISTONE_DEFAULT)
                stats = data.get("stats_storiche", [])
                data["stats_storiche"] = pd.DataFrame(stats) if stats else pd.DataFrame()
                data["stats_per_stagione"] = {k: pd.DataFrame(v) if v else pd.DataFrame() for k, v in data.get("stats_per_stagione", {}).items()}
                q25 = data.get("quotazioni_2025_26", [])
                data["quotazioni_2025_26"] = pd.DataFrame(q25) if q25 else pd.DataFrame()
                StateManager._hydrate(data)
                return True
            except Exception:
                pass
        return False

    @staticmethod
    def _hydrate(data):
        st.session_state.squadre = data.get("squadre", {})
        st.session_state.storico_mercato = data.get("storico_mercato", [])
        st.session_state.watchlist = data.get("watchlist", [])
        st.session_state.prestiti = data.get("prestiti", [])
        st.session_state.contratti = data.get("contratti", {})
        st.session_state.giocatori_db = data.get("giocatori_db", pd.DataFrame(LISTONE_DEFAULT))
        if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
            st.session_state.giocatori_db["Prezzo_Consigliato"] = None
        st.session_state.stats_storiche = data.get("stats_storiche", pd.DataFrame())
        st.session_state.stats_per_stagione = data.get("stats_per_stagione", {})
        st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
        st.session_state.quotazioni_2025_26 = data.get("quotazioni_2025_26", pd.DataFrame())
        st.session_state.wizard_completato = data.get("wizard_completato", False)
        for sq in NOMI_SQUADRE:
            if sq not in st.session_state.squadre:
                st.session_state.squadre[sq] = {"crediti": st.session_state.crediti_iniziali, "rosa": []}
        invalidate_cache()

def save_state():
    StateManager.save()
    # Auto-save incrementale ogni 5 operazioni
    if "_ops_count" not in st.session_state:
        st.session_state._ops_count = 0
    st.session_state._ops_count += 1
    if st.session_state._ops_count % 5 == 0:
        # Salva anche un backup con timestamp
        try:
            ts = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"fantamanager_auto_{ts}.pkl"
            data = {
                "squadre": st.session_state.squadre,
                "storico_mercato": st.session_state.storico_mercato,
                "watchlist": st.session_state.watchlist,
                "prestiti": st.session_state.prestiti,
                "contratti": st.session_state.contratti,
                "giocatori_db": st.session_state.giocatori_db,
                "stats_storiche": st.session_state.stats_storiche,
                "stats_per_stagione": st.session_state.get("stats_per_stagione", {}),
                "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
                "quotazioni_2025_26": st.session_state.quotazioni_2025_26,
                "wizard_completato": st.session_state.get("wizard_completato", False),
            }
            with open(backup_name, "wb") as f:
                pickle.dump(data, f)
            st.toast(f"💾 Auto-backup #{st.session_state._ops_count} salvato", icon="💾")
        except Exception:
            pass

def load_state():
    return StateManager.load()

# ============================================================
# INDICI E CACHE
# ============================================================
def invalidate_cache():
    st.session_state._riepiloghi_dirty = True
    st.session_state._player_index_dirty = True

def get_player_index():
    if st.session_state.get("_player_index_dirty", True):
        idx = {}
        for sq, dati in st.session_state.squadre.items():
            for g in dati["rosa"]:
                idx[g["Nome"].lower()] = sq
        st.session_state._player_index = idx
        st.session_state._player_index_dirty = False
    return st.session_state.get("_player_index", {})

def get_svincolati(db: pd.DataFrame) -> pd.DataFrame:
    idx = get_player_index()
    mask = ~db["Nome"].str.lower().isin(idx.keys())
    return db[mask].copy()

def get_giocatore_in_rosa(nome: str) -> Optional[Tuple[str, dict]]:
    nome_l = nome.lower()
    for sq, dati in st.session_state.squadre.items():
        for g in dati["rosa"]:
            if g["Nome"].lower() == nome_l:
                return sq, g
    return None

def rosa_proprieta(squadra: str) -> List[dict]:
    return [g for g in st.session_state.squadre[squadra]["rosa"]
            if g.get("Prestito_Da") is None or g.get("Prestito_Da") == squadra]

# ============================================================
# UTILITY
# ============================================================
def fuzzy_match(name, choices, cutoff=0.75):
    name_clean = str(name).strip().lower()
    matches = difflib.get_close_matches(name_clean, [c.lower() for c in choices], n=1, cutoff=cutoff)
    if matches:
        idx = [c.lower() for c in choices].index(matches[0])
        return choices[idx]
    return None

def get_quotazione_listone(nome):
    db = st.session_state.giocatori_db
    match = db[db["Nome"].str.lower() == nome.lower()]
    if not match.empty:
        return int(match.iloc[0]["Quotazione"])
    nome_match = fuzzy_match(nome, db["Nome"].tolist())
    if nome_match:
        match = db[db["Nome"] == nome_match]
        if not match.empty:
            return int(match.iloc[0]["Quotazione"])
    return None

def get_db_info(nome):
    db = st.session_state.giocatori_db
    match = db[db["Nome"].str.lower() == nome.lower()]
    if not match.empty:
        return match.iloc[0].to_dict()
    nome_match = fuzzy_match(nome, db["Nome"].tolist())
    if nome_match:
        match = db[db["Nome"] == nome_match]
        if not match.empty:
            return match.iloc[0].to_dict()
    return None

# ============================================================
# BUSINESS LOGIC
# ============================================================
def calcola_prezzo_consigliato(g_info, stats_df=None):
    nome = g_info.get("Nome", "")
    ruolo = g_info.get("Ruolo", "C")
    quot = float(g_info.get("Quotazione", 10))
    fm = float(g_info.get("FantaMedia", 6.0))
    fascia = g_info.get("Consiglio", "consigliato")

    base = quot
    medie_ruolo = {"P": 5.5, "D": 6.2, "C": 6.8, "A": 7.5}
    media_rif = medie_ruolo.get(ruolo, 6.5)
    delta_fm = fm - media_rif
    fattore_fm = 1 + (delta_fm * 0.15)
    fattore_fascia = {"top": 1.15, "consigliato": 1.0, "scommessa": 0.85}.get(fascia, 1.0)

    db = st.session_state.giocatori_db
    svinc = get_svincolati(db)
    total_fascia = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == fascia)])
    rimasti = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == fascia)])
    fattore_scarsita = 1 + max(0, (3 - rimasti)) * 0.05 if total_fascia > 0 else 1.0

    fattore_trend = 1.0
    trend_note = ""
    if stats_df is not None and not stats_df.empty and "Nome" in stats_df.columns:
        g_stats = stats_df[stats_df["Nome"].str.lower() == nome.lower()]
        if g_stats.empty:
            nome_fuzzy = fuzzy_match(nome, stats_df["Nome"].tolist())
            if nome_fuzzy:
                g_stats = stats_df[stats_df["Nome"] == nome_fuzzy]
        if not g_stats.empty:
            if "Stagione" in g_stats.columns:
                g_stats = g_stats.sort_values("Stagione", ascending=False)
            ultima = g_stats.iloc[0]
            if "FantaMedia" in ultima and pd.notna(ultima["FantaMedia"]):
                fm_storica = float(ultima["FantaMedia"])
                if fm > fm_storica + 0.3:
                    fattore_trend += 0.10
                    trend_note = " 📈 Trend in crescita"
                elif fm < fm_storica - 0.3:
                    fattore_trend -= 0.10
                    trend_note = " 📉 Trend in calo"
                else:
                    trend_note = " ➡️ Trend stabile"
            gol = float(ultima.get("Gol", 0)) if "Gol" in ultima and pd.notna(ultima.get("Gol")) else 0
            if ruolo in ["D", "C"] and gol >= 5:
                fattore_trend += 0.08
                trend_note += f" | ⚽ {int(gol)} gol"
            if ruolo == "A" and gol >= 15:
                fattore_trend += 0.12
                trend_note += f" | ⚽ {int(gol)} gol"
            if "Partite" in ultima and pd.notna(ultima["Partite"]):
                partite = int(ultima["Partite"])
                if partite >= 30:
                    fattore_trend += 0.05
                    trend_note += f" | 🏃 {partite} presenze"

    indice_affare = fm / max(quot, 1)
    if indice_affare > 0.20:
        fattore_affare = 1.0
    elif indice_affare > 0.15:
        fattore_affare = 0.95
    else:
        fattore_affare = 0.90

    prezzo = base * fattore_fm * fattore_fascia * fattore_scarsita * fattore_trend * fattore_affare
    prezzo = max(1, round(prezzo))

    spiegazione = (
        f"**Base listone:** {int(base)}cr\n"
        f"**FantaMedia:** {fm} (media ruolo {ruolo}: {media_rif}) → fattore {fattore_fm:.2f}\n"
        f"**Fascia:** {fascia} → fattore {fattore_fascia:.2f}\n"
        f"**Scarsità:** {rimasti}/{total_fascia} rimasti → fattore {fattore_scarsita:.2f}\n"
        f"**Indice affare:** {indice_affare:.3f} → fattore {fattore_affare:.2f}\n"
    )
    if trend_note:
        spiegazione += f"**Statistiche:**{trend_note} → fattore {fattore_trend:.2f}\n"
    spiegazione += f"\n**💡 Prezzo consigliato: {prezzo}cr**"
    return prezzo, spiegazione

def riepilogo_rosa(squadra_nome):
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    crediti = st.session_state.squadre[squadra_nome]["crediti"]
    conti = {"P": 0, "D": 0, "C": 0, "A": 0}
    for g in rosa:
        r = g.get("Ruolo", "C")
        if r in conti:
            conti[r] += 1

    riepilogo = {}
    tot_mancanti = 0
    for ruolo, req in ROSA_REQ.items():
        posseduti = conti.get(ruolo, 0)
        mancanti = max(0, req - posseduti)
        riepilogo[ruolo] = {"posseduti": posseduti, "mancanti": mancanti, "req": req}
        tot_mancanti += mancanti

    posti_rimanenti = sum(v["mancanti"] for v in riepilogo.values())
    for ruolo in ROSA_REQ:
        mancanti_ruolo = riepilogo[ruolo]["mancanti"]
        if posti_rimanenti > 0 and mancanti_ruolo > 0:
            budget_libero = max(0, crediti - posti_rimanenti)
            offerta = int((budget_libero / mancanti_ruolo) + 1)
        else:
            offerta = crediti if mancanti_ruolo > 0 else 0
        riepilogo[ruolo]["offerta_max"] = offerta

    prestiti_uscita = [p for p in st.session_state.prestiti if p["Da"] == squadra_nome]
    riepilogo["crediti"] = crediti
    riepilogo["tot_mancanti"] = tot_mancanti
    riepilogo["tot_posseduti"] = len(rosa)
    riepilogo["tot_prestiti_uscita"] = len(prestiti_uscita)
    riepilogo["tot_giocatori_posseduti"] = len(rosa) + len(prestiti_uscita)
    return riepilogo

def get_all_riepiloghi():
    if st.session_state.get("_riepiloghi_dirty", True):
        st.session_state._riepiloghi = {sq: riepilogo_rosa(sq) for sq in NOMI_SQUADRE}
        st.session_state._riepiloghi_dirty = False
    return st.session_state._riepiloghi

def mostra_statistiche_giocatore(nome, stats_df):
    if stats_df is None or stats_df.empty or "Nome" not in stats_df.columns:
        return None
    g_stats = stats_df[stats_df["Nome"].str.lower() == nome.lower()]
    if g_stats.empty:
        nome_fuzzy = fuzzy_match(nome, stats_df["Nome"].tolist())
        if nome_fuzzy:
            g_stats = stats_df[stats_df["Nome"] == nome_fuzzy]
    if g_stats.empty:
        return None
    return g_stats.sort_values("Stagione") if "Stagione" in g_stats.columns else g_stats

def _get_fm_2627(nome):
    """Ritorna la FantaMedia 2026-27 se caricata, altrimenti None."""
    if "stats_per_stagione" not in st.session_state:
        return None
    if "2026-27" not in st.session_state.stats_per_stagione:
        return None
    s2627 = st.session_state.stats_per_stagione["2026-27"]
    if s2627.empty or "Nome" not in s2627.columns:
        return None
    match = s2627[s2627["Nome"].str.lower() == nome.lower()]
    if match.empty:
        nm = fuzzy_match(nome, s2627["Nome"].tolist())
        if nm:
            match = s2627[s2627["Nome"] == nm]
    if not match.empty and "FantaMedia" in match.columns and pd.notna(match.iloc[0]["FantaMedia"]):
        return float(match.iloc[0]["FantaMedia"])
    return None

def simula_formazione(squadra_nome, modulo):
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    if not rosa:
        return 0, [], []
    # Arricchisci con FM 2026/27 se disponibile
    enriched = []
    for g in rosa:
        g_copy = dict(g)
        fm_2627 = _get_fm_2627(g["Nome"])
        if fm_2627 is not None:
            g_copy["FantaMedia_Usata"] = fm_2627
            g_copy["FM_Origine"] = "📊 2026/27"
        else:
            g_copy["FantaMedia_Usata"] = g.get("FantaMedia", 0)
            g_copy["FM_Origine"] = "📋 Listone"
        enriched.append(g_copy)
    df = pd.DataFrame(enriched)
    try:
        d, c, a = map(int, modulo.split("-"))
    except:
        return 0, [], []
    p = 1
    titolari = []
    panchina = []
    for ruolo, n in [("P", p), ("D", d), ("C", c), ("A", a)]:
        subset = df[df["Ruolo"] == ruolo].sort_values("FantaMedia_Usata", ascending=False)
        presi = subset.head(n)
        rimasti = subset.iloc[n:]
        for _, row in presi.iterrows():
            titolari.append(row.to_dict())
        for _, row in rimasti.iterrows():
            panchina.append(row.to_dict())
    fm_tit = sum(g.get("FantaMedia_Usata", 0) for g in titolari)
    return round(fm_tit, 2), panchina, titolari

def arricchisci_con_stats_2627(df_listone):
    df = df_listone.copy()
    if "stats_per_stagione" not in st.session_state:
        return df
    if "2026-27" not in st.session_state.stats_per_stagione:
        return df
    stats_2627 = st.session_state.stats_per_stagione["2026-27"].copy()
    if stats_2627.empty or "Nome" not in stats_2627.columns:
        return df
    stats_2627["Nome_lower"] = stats_2627["Nome"].str.lower().str.strip()
    df["Nome_lower"] = df["Nome"].str.lower().str.strip()
    cols_stats = [c for c in stats_2627.columns if c not in ["Nome", "Stagione", "Nome_lower"]]
    if "FantaMedia" in cols_stats and "FantaMedia" in df.columns:
        df = df.drop(columns=["FantaMedia"])
    if "Gol" in cols_stats and "Gol" in df.columns:
        df = df.drop(columns=["Gol"])
    if "Assist" in cols_stats and "Assist" in df.columns:
        df = df.drop(columns=["Assist"])
    merge_df = stats_2627[["Nome_lower"] + [c for c in cols_stats if c not in df.columns]].copy()
    df = df.merge(merge_df, on="Nome_lower", how="left")
    df = df.drop(columns=["Nome_lower"])
    if "FantaMedia" in df.columns:
        df["FantaMedia"] = pd.to_numeric(df["FantaMedia"], errors="coerce")
    return df

def calcola_indice_titolarita(row, stats_2627=None):
    """Calcola un indice 0-100 di titolarità/solidità del giocatore."""
    fm = float(row.get("FantaMedia", 6.0))
    fascia = row.get("Consiglio", "consigliato")
    quot = float(row.get("Quotazione", 10))
    nome = str(row.get("Nome", ""))

    # Base da FantaMedia (0-50 punti)
    base = min(50, (fm / 10) * 50)

    # Bonus fascia (0-25 punti)
    bonus_fascia = {"top": 25, "consigliato": 15, "scommessa": 5}.get(fascia, 10)

    # Presenze da stats 2026/27 (0-25 punti)
    bonus_presenze = 12.5
    if stats_2627 is not None and not stats_2627.empty and "Nome" in stats_2627.columns:
        match = stats_2627[stats_2627["Nome"].str.lower() == nome.lower()]
        if match.empty:
            nm = fuzzy_match(nome, stats_2627["Nome"].tolist())
            if nm:
                match = stats_2627[stats_2627["Nome"] == nm]
        if not match.empty and "Partite" in match.columns and pd.notna(match.iloc[0]["Partite"]):
            partite = int(match.iloc[0]["Partite"])
            bonus_presenze = min(25, (partite / 38) * 25)

    # Quotazione come indicatore di fiducia del mercato (0-10 punti)
    bonus_quot = min(10, max(0, (quot / 100) * 10))

    totale = base + bonus_fascia + bonus_presenze + bonus_quot
    return min(100, round(totale, 1))



# ============================================================
# ANALISI BUDGET ASTA — UTILITY PER GIOCATORI COSTOSI (>40cr)
# ============================================================

def budget_libero_effettivo(squadra_nome):
    """Crediti spendibili su un top, dopo riserva minima per completare rosa."""
    riep = riepilogo_rosa(squadra_nome)
    crediti = riep["crediti"]
    posti_mancanti = riep["tot_mancanti"]
    budget_minimo = posti_mancanti * 1
    return max(0, crediti - budget_minimo)


def offerta_massima_realistica(squadra_nome, ruolo):
    """Offerta max consigliata per ruolo, lasciando margine per completare."""
    riep = riepilogo_rosa(squadra_nome)
    crediti = riep["crediti"]
    posti_mancanti = riep["tot_mancanti"]
    budget_sicurezza = posti_mancanti * 2
    return max(0, crediti - budget_sicurezza)


def spese_per_ruolo(squadra_nome):
    """Restituisce spese totali e media per ruolo."""
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    spese = {"P": {"tot": 0, "n": 0, "avg": 0}, "D": {"tot": 0, "n": 0, "avg": 0},
             "C": {"tot": 0, "n": 0, "avg": 0}, "A": {"tot": 0, "n": 0, "avg": 0}}
    for g in rosa:
        r = g.get("Ruolo", "C")
        costo = g.get("Costo_Acquisto", 0)
        if r in spese:
            spese[r]["tot"] += costo
            spese[r]["n"] += 1
    for r in spese:
        if spese[r]["n"] > 0:
            spese[r]["avg"] = round(spese[r]["tot"] / spese[r]["n"], 1)
    return spese


def fuga_top_tracker():
    """Quanti top/consigliati sono ancora liberi per ruolo."""
    db = st.session_state.giocatori_db.copy()
    idx = get_player_index()
    db["Proprietario"] = db["Nome"].apply(lambda x: idx.get(x.lower(), "Svincolato"))
    svinc = db[db["Proprietario"] == "Svincolato"]
    result = {}
    for ruolo in ["P", "D", "C", "A"]:
        total_top = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == "top")])
        rimasti_top = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == "top")])
        total_cons = len(db[(db["Ruolo"] == ruolo) & (db["Consiglio"] == "consigliato")])
        rimasti_cons = len(svinc[(svinc["Ruolo"] == ruolo) & (svinc["Consiglio"] == "consigliato")])
        result[ruolo] = {
            "top_totali": total_top, "top_rimasti": rimasti_top,
            "cons_totali": total_cons, "cons_rimasti": rimasti_cons,
            "pct_top_rimasti": round((rimasti_top / max(total_top, 1)) * 100, 1),
            "pct_cons_rimasti": round((rimasti_cons / max(total_cons, 1)) * 100, 1),
        }
    return result


def alert_scarsita_top(ruolo):
    """True se i top di un ruolo stanno per finire (< 30% rimasti, <= 2)."""
    tracker = fuga_top_tracker()
    if ruolo in tracker:
        return tracker[ruolo]["pct_top_rimasti"] < 30 and tracker[ruolo]["top_rimasti"] <= 2
    return False


# ============================================================
# ============================================================
# CLASSIFICAZIONE FASCE AUTOMATICA DA STATISTICHE STORICHE
# ============================================================

def calcola_fascia_da_storico(nome: str, stats_per_stagione: dict, ruolo: str = "C") -> str:
    """
    Classifica un giocatore in 'top', 'consigliato' o 'scommessa'
    basandosi sulle stagioni disponibili in stats_per_stagione.
    """
    storico = []
    for stagione, df in stats_per_stagione.items():
        if df.empty or "Nome" not in df.columns:
            continue
        match = df[df["Nome"].str.lower() == nome.lower()]
        if match.empty:
            close = difflib.get_close_matches(
                nome.lower(),
                [n.lower() for n in df["Nome"].dropna().unique().tolist()],
                n=1, cutoff=0.8
            )
            if close:
                match = df[df["Nome"].str.lower() == close[0]]
        if not match.empty:
            row = match.iloc[0].to_dict()
            row["Stagione"] = stagione
            storico.append(row)

    if not storico:
        return "consigliato"

    def safe_float(val, default=0.0):
        try:
            return float(val)
        except (TypeError, ValueError):
            return default

    def safe_int(val, default=0):
        try:
            return int(float(val))
        except (TypeError, ValueError):
            return default

    fm_list = [safe_float(r.get("FantaMedia")) for r in storico if safe_float(r.get("FantaMedia")) > 0]
    pres_list = [safe_int(r.get("Partite")) for r in storico if safe_int(r.get("Partite")) > 0]
    gol_list = [safe_int(r.get("Gol")) for r in storico]
    ast_list = [safe_int(r.get("Assist")) for r in storico]

    if not fm_list:
        return "consigliato"

    fm_media = sum(fm_list) / len(fm_list)
    pres_media = sum(pres_list) / len(pres_list) if pres_list else 0
    gol_totali = sum(gol_list)
    ast_totali = sum(ast_list)
    stagioni_giocate = len(fm_list)

    try:
        df_storico = pd.DataFrame(storico)
        df_storico_sorted = df_storico.sort_values("Stagione")
        fm_ultima = safe_float(df_storico_sorted.iloc[-1].get("FantaMedia"), fm_media)
        pres_ultima = safe_int(df_storico_sorted.iloc[-1].get("Partite"), 0)
    except Exception:
        fm_ultima = fm_list[-1]
        pres_ultima = pres_list[-1] if pres_list else 0

    soglie = {
        "P": {"top_fm": 5.8, "cons_fm": 5.4, "top_pres": 25, "cons_pres": 15},
        "D": {"top_fm": 6.5, "cons_fm": 6.0, "top_pres": 28, "cons_pres": 18},
        "C": {"top_fm": 6.8, "cons_fm": 6.3, "top_pres": 28, "cons_pres": 18},
        "A": {"top_fm": 7.2, "cons_fm": 6.8, "top_pres": 28, "cons_pres": 18},
    }
    s = soglie.get(ruolo, soglie["C"])

    punteggio = 0.0

    if fm_media >= s["top_fm"]:
        punteggio += 40
    elif fm_media >= s["cons_fm"]:
        punteggio += 25
    else:
        punteggio += max(0, (fm_media / s["cons_fm"]) * 15)

    if pres_media >= s["top_pres"]:
        punteggio += 30
    elif pres_media >= s["cons_pres"]:
        punteggio += 18
    else:
        punteggio += max(0, (pres_media / s["cons_pres"]) * 10)

    if fm_ultima >= fm_media + 0.3:
        punteggio += 20
    elif fm_ultima >= fm_media - 0.3:
        punteggio += 12
    else:
        punteggio += max(0, 5 + (fm_ultima - fm_media) * 10)

    if ruolo in ["D", "C"]:
        bonus_per_stag = (gol_totali + ast_totali) / max(stagioni_giocate, 1)
        if bonus_per_stag >= 8:
            punteggio += 10
        elif bonus_per_stag >= 4:
            punteggio += 5
    elif ruolo == "A":
        bonus_per_stag = gol_totali / max(stagioni_giocate, 1)
        if bonus_per_stag >= 15:
            punteggio += 10
        elif bonus_per_stag >= 10:
            punteggio += 5
    elif ruolo == "P":
        if pres_ultima >= 30:
            punteggio += 10
        elif pres_ultima >= 20:
            punteggio += 5

    if punteggio >= 70:
        return "top"
    elif punteggio >= 42:
        return "consigliato"
    else:
        return "scommessa"


def applica_fasce_automatiche():
    db = st.session_state.giocatori_db.copy()
    stats = st.session_state.get("stats_per_stagione", {})
    if not stats:
        st.warning("⚠️ Nessuna statistica storica caricata. Vai su 📈 Statistiche Storiche e carica almeno una stagione.")
        return
    conteggi = {"top": 0, "consigliato": 0, "scommessa": 0}
    for idx, row in db.iterrows():
        nome = row.get("Nome", "")
        ruolo = row.get("Ruolo", "C")
        nuova_fascia = calcola_fascia_da_storico(nome, stats, ruolo)
        db.at[idx, "Consiglio"] = nuova_fascia
        conteggi[nuova_fascia] = conteggi.get(nuova_fascia, 0) + 1
    st.session_state.giocatori_db = db
    save_state()
    st.success(
        f"✅ Fasce ricalcolate da storico!  "
        f"⭐ Top: {conteggi['top']} | 👍 Consigliati: {conteggi['consigliato']} | 🎲 Scommesse: {conteggi['scommessa']}"
    )



def _get_inline_stats(nome, stats_2627):
    """Restituisce HTML con badge stats dalla stagione 2026/27."""
    if stats_2627 is None or stats_2627.empty or "Nome" not in stats_2627.columns:
        return ""
    match = stats_2627[stats_2627["Nome"].str.lower() == nome.lower()]
    if match.empty:
        close = difflib.get_close_matches(nome.lower(), [n.lower() for n in stats_2627["Nome"].tolist()], n=1, cutoff=0.8)
        if close:
            match = stats_2627[stats_2627["Nome"].str.lower() == close[0]]
    if match.empty:
        return ""
    r = match.iloc[0]
    badges = []
    icons = {"Gol": "⚽", "Assist": "🅰️", "Partite": "🏃", "Rigori": "🎯", "Ammonizioni": "🟨", "Espulsioni": "🟥"}
    for col, icon in icons.items():
        if col in r and pd.notna(r[col]):
            val = int(r[col])
            if val > 0:
                badges.append(f'<span style="background:#1a1a2e;color:#ddd;padding:2px 6px;border-radius:8px;font-size:0.7em;margin-right:4px;">{icon} {val}</span>')
    return " ".join(badges)


def _get_fm_trend_badge(nome, row_fm, stats_2627):
    """Restituisce badge trend se FM 2026/27 diverge dal listone."""
    if stats_2627 is None or stats_2627.empty or "Nome" not in stats_2627.columns:
        return ""
    match = stats_2627[stats_2627["Nome"].str.lower() == nome.lower()]
    if match.empty:
        close = difflib.get_close_matches(nome.lower(), [n.lower() for n in stats_2627["Nome"].tolist()], n=1, cutoff=0.8)
        if close:
            match = stats_2627[stats_2627["Nome"].str.lower() == close[0]]
    if match.empty or "FantaMedia" not in match.columns or pd.isna(match.iloc[0]["FantaMedia"]):
        return ""
    fm_2627 = float(match.iloc[0]["FantaMedia"])
    delta = fm_2627 - row_fm
    if delta >= 0.5:
        return f'<span style="background:#00d26a20;color:#00d26a;padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:bold;border:1px solid #00d26a;">📈 +{delta:.1f}</span>'
    elif delta <= -0.5:
        return f'<span style="background:#ff6b6b20;color:#ff6b6b;padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:bold;border:1px solid #ff6b6b;">📉 {delta:.1f}</span>'
    return f'<span style="background:#2a2a4a;color:#888;padding:2px 8px;border-radius:12px;font-size:0.7em;">➡️ {delta:+.1f}</span>'

def render_card_giocatore(row, stats_2627=None, show_titolarita=True):
    """Restituisce HTML per una card giocatore accattivante."""
    nome = row["Nome"]
    ruolo = row["Ruolo"]
    sa = row.get("Squadra_SerieA", "N/D")
    fm = row.get("FantaMedia", 0)
    quot = int(row.get("Quotazione", 0))
    fascia = row.get("Consiglio", "consigliato")
    prop = row.get("Proprietario", "Svincolato 🟢")
    idx_aff = row.get("Indice_Affare", 0)
    idx_tit = row.get("Indice_Titolarita", 0)
    pc = row.get("Prezzo_Consigliato")
    pc_txt = f"💡 {int(pc)}cr" if pd.notna(pc) else ""

    colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
    colore = colori_ruolo.get(ruolo, "#888")

    badge_fascia = {
        "top": "⭐ TOP",
        "consigliato": "👍 CONSIGLIATO",
        "scommessa": "🎲 SCOMMESSA"
    }.get(fascia, "")

    barra_tit = ""
    if show_titolarita:
        col_bar = "#00d26a" if idx_tit >= 80 else "#eab308" if idx_tit >= 60 else "#ef4444"
        barra_tit = f'<div style="margin-top:6px;"><div style="display:flex;justify-content:space-between;font-size:0.75em;color:#aaa;"><span>Titolarità</span><span>{idx_tit}/100</span></div><div style="background:#2a2a4a;border-radius:4px;height:6px;overflow:hidden;"><div style="width:{idx_tit}%;background:{col_bar};height:100%;border-radius:4px;"></div></div></div>'

    if "Svincolato" in str(prop):
        badge_prop = '<span style="background:#00d26a20;color:#00d26a;padding:2px 8px;border-radius:12px;font-size:0.7em;border:1px solid #00d26a;">🟢 LIBERO</span>'
    else:
        badge_prop = f'<span style="background:#ff6b6b20;color:#ff6b6b;padding:2px 8px;border-radius:12px;font-size:0.7em;border:1px solid #ff6b6b;">🔒 {prop}</span>'

    pc_span = f'<span style="background:#1a1a2e;color:#00d26a;padding:2px 8px;border-radius:12px;font-size:0.7em;">{pc_txt}</span>' if pc_txt else ''

    # Effetto hover: ingrandimento + illuminazione
    hover_js = "onmouseover=\"this.style.transform='scale(1.04)';this.style.boxShadow='0 0 25px rgba(0,210,106,0.45)';this.style.zIndex='10';\" onmouseout=\"this.style.transform='scale(1)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.3)';this.style.zIndex='1';\""

    # Stats inline dalla stagione 2026/27
    inline_stats = _get_inline_stats(nome, stats_2627)
    trend_badge = _get_fm_trend_badge(nome, fm, stats_2627)

    # FM display con eventuale badge 2026/27
    fm_display = f'{fm}'
    if stats_2627 is not None and not stats_2627.empty and "Nome" in stats_2627.columns:
        match_fm = stats_2627[stats_2627["Nome"].str.lower() == nome.lower()]
        if match_fm.empty:
            close = difflib.get_close_matches(nome.lower(), [n.lower() for n in stats_2627["Nome"].tolist()], n=1, cutoff=0.8)
            if close:
                match_fm = stats_2627[stats_2627["Nome"].str.lower() == close[0]]
        if not match_fm.empty and "FantaMedia" in match_fm.columns and pd.notna(match_fm.iloc[0]["FantaMedia"]):
            fm_2627_val = float(match_fm.iloc[0]["FantaMedia"])
            fm_display = f'{fm_2627_val:.1f} <span style="font-size:0.6em;color:#00d26a;">📊</span>'

    html = f'''<div style="background:linear-gradient(135deg,#1e1e3f 0%,#2a2a4a 100%);border-radius:12px;padding:14px;margin-bottom:10px;border-left:4px solid {colore};box-shadow:0 2px 8px rgba(0,0,0,0.3);transition:all 0.3s ease;cursor:pointer;position:relative;" {hover_js}>
        <div style="display:flex;justify-content:space-between;align-items:start;">
            <div>
                <div style="font-size:1.1em;font-weight:bold;color:#fff;">{nome}</div>
                <div style="font-size:0.85em;color:#aaa;">{sa} | <span style="color:{colore};font-weight:600;">{ruolo}</span></div>
            </div>
            <div style="text-align:right;">
                <div style="font-size:1.3em;font-weight:bold;color:#ffd700;">{fm_display}</div>
                <div style="font-size:0.75em;color:#888;">FM</div>
                {trend_badge}
            </div>
        </div>
        <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
            <span style="background:{colore}20;color:{colore};padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:600;">{badge_fascia}</span>
            <span style="background:#1a1a2e;color:#ddd;padding:2px 8px;border-radius:12px;font-size:0.7em;">{quot}cr</span>
            {pc_span}
            <span style="background:#1a1a2e;color:#aaa;padding:2px 8px;border-radius:12px;font-size:0.7em;">IA {idx_aff}</span>
        </div>
        {barra_tit}
        <div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;">{inline_stats}</div>
        <div style="margin-top:8px;">{badge_prop}</div>
    </div>'''
    return html


def _build_stats_html(nome, stats_per_stagione):
    """Costruisce HTML con le statistiche storiche di un giocatore + mini grafico FM."""
    rows = []
    fm_points = []
    gol_points = []
    ast_points = []
    stagioni_label = []
    for stagione, df in sorted(stats_per_stagione.items()):
        if df.empty or "Nome" not in df.columns:
            continue
        match = df[df["Nome"].str.lower() == nome.lower()]
        if match.empty:
            close = difflib.get_close_matches(
                nome.lower(),
                [n.lower() for n in df["Nome"].dropna().unique().tolist()],
                n=1, cutoff=0.8
            )
            if close:
                match = df[df["Nome"].str.lower() == close[0]]
        if not match.empty:
            r = match.iloc[0]
            fm = r.get("FantaMedia", "—")
            gol = r.get("Gol", "—")
            ast = r.get("Assist", "—")
            part = r.get("Partite", "—")
            rig = r.get("Rigori", "—")
            amm = r.get("Ammonizioni", "—")
            esp = r.get("Espulsioni", "—")
            rows.append(f'<tr><td style="padding:4px 8px;color:#aaa;font-size:0.8em;">{stagione}</td><td style="padding:4px 8px;color:#ffd700;font-size:0.85em;font-weight:bold;">{fm}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{gol}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{ast}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{part}</td><td style="padding:4px 8px;color:#fff;font-size:0.8em;">{rig}</td><td style="padding:4px 8px;color:#eab308;font-size:0.8em;">{amm}</td><td style="padding:4px 8px;color:#ef4444;font-size:0.8em;">{esp}</td></tr>')
            try:
                fm_val = float(fm)
                if fm_val > 0:
                    fm_points.append(fm_val)
                    stagioni_label.append(stagione)
            except (TypeError, ValueError):
                pass
            try:
                g_val = float(gol)
                gol_points.append(g_val)
            except (TypeError, ValueError):
                gol_points.append(0)
            try:
                a_val = float(ast)
                ast_points.append(a_val)
            except (TypeError, ValueError):
                ast_points.append(0)

    # Mini grafico SVG andamento FM + Gol + Assist
    chart_svg = ""
    if len(fm_points) >= 2:
        w, h = 320, 100
        pad_x, pad_y = 25, 15
        max_fm = max(fm_points + [8.0])
        min_fm = min(fm_points + [4.0])
        rng = max_fm - min_fm if max_fm != min_fm else 1
        n = len(fm_points)
        pts = []
        pts_gol = []
        pts_ast = []
        for i, val in enumerate(fm_points):
            x = pad_x + (i / (n - 1)) * (w - 2 * pad_x)
            y = h - pad_y - ((val - min_fm) / rng) * (h - 2 * pad_y)
            pts.append(f"{x:.1f},{y:.1f}")
            # Gol scala 0-30
            y_g = h - pad_y - (gol_points[i] / 30) * (h - 2 * pad_y) if gol_points else h - pad_y
            pts_gol.append(f"{x:.1f},{max(pad_y, min(h-pad_y, y_g)):.1f}")
            # Assist scala 0-20
            y_a = h - pad_y - (ast_points[i] / 20) * (h - 2 * pad_y) if ast_points else h - pad_y
            pts_ast.append(f"{x:.1f},{max(pad_y, min(h-pad_y, y_a)):.1f}")
        polyline = " ".join(pts)
        poly_gol = " ".join(pts_gol)
        poly_ast = " ".join(pts_ast)
        circles = ""
        for i, val in enumerate(fm_points):
            x = pad_x + (i / (n - 1)) * (w - 2 * pad_x)
            y = h - pad_y - ((val - min_fm) / rng) * (h - 2 * pad_y)
            circles += f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3" fill="#00d26a"/><text x="{x:.1f}" y="{y-6:.1f}" text-anchor="middle" fill="#ffd700" font-size="8" font-weight="bold">{val:.1f}</text>'
        labels = ""
        for i, lbl in enumerate(stagioni_label):
            x = pad_x + (i / (n - 1)) * (w - 2 * pad_x)
            labels += f'<text x="{x:.1f}" y="{h-2:.1f}" text-anchor="middle" fill="#888" font-size="7">{lbl}</text>'
        legend = f'<text x="{w-5}" y="12" text-anchor="end" fill="#00d26a" font-size="8" font-weight="bold">● FM</text><text x="{w-5}" y="24" text-anchor="end" fill="#3b82f6" font-size="8" font-weight="bold">● Gol</text><text x="{w-5}" y="36" text-anchor="end" fill="#eab308" font-size="8" font-weight="bold">● Assist</text>'
        chart_svg = f'''<div style="margin:10px 0;">
            <svg width="{w}" height="{h}" style="background:#0f0f24;border-radius:6px;">
                <polyline points="{polyline}" fill="none" stroke="#00d26a" stroke-width="2.5"/>
                <polyline points="{poly_gol}" fill="none" stroke="#3b82f6" stroke-width="1.5" stroke-dasharray="4,2"/>
                <polyline points="{poly_ast}" fill="none" stroke="#eab308" stroke-width="1.5" stroke-dasharray="2,2"/>
                {circles}{labels}{legend}
            </svg>
        </div>'''

    if not rows:
        return '<div style="padding:8px;color:#888;font-size:0.8em;text-align:center;">📭 Nessuno storico disponibile</div>'
    return chart_svg + f'<table style="width:100%;border-collapse:collapse;margin-top:8px;"><thead><tr style="border-bottom:1px solid #2a2a4a;"><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">Stagione</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">FM</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">⚽</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">🅰️</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">🏃</th><th style="padding:4px 8px;color:#888;font-size:0.7em;text-align:left;">🎯</th><th style="padding:4px 8px;color:#eab308;font-size:0.7em;text-align:left;">🟨</th><th style="padding:4px 8px;color:#ef4444;font-size:0.7em;text-align:left;">🟥</th></tr></thead><tbody>{""".join(rows)}</tbody></table>'

def render_card_giocatore_espandibile(row, stats_per_stagione=None, stats_2627=None, show_titolarita=True):
    """Card giocatore con hover + click per espandere statistiche."""
    nome = row["Nome"]
    ruolo = row["Ruolo"]
    sa = row.get("Squadra_SerieA", "N/D")
    fm = row.get("FantaMedia", 0)
    quot = int(row.get("Quotazione", 0))
    fascia = row.get("Consiglio", "consigliato")
    prop = row.get("Proprietario", "Svincolato 🟢")
    idx_aff = row.get("Indice_Affare", 0)
    idx_tit = row.get("Indice_Titolarita", 0)
    pc = row.get("Prezzo_Consigliato")
    pc_txt = f"💡 {int(pc)}cr" if pd.notna(pc) else ""
    note = row.get("Note", "")

    colori_ruolo = {"P": "#3b82f6", "D": "#22c55e", "C": "#eab308", "A": "#ef4444"}
    colore = colori_ruolo.get(ruolo, "#888")

    badge_fascia = {
        "top": "⭐ TOP",
        "consigliato": "👍 CONSIGLIATO",
        "scommessa": "🎲 SCOMMESSA"
    }.get(fascia, "")

    barra_tit = ""
    if show_titolarita:
        col_bar = "#00d26a" if idx_tit >= 80 else "#eab308" if idx_tit >= 60 else "#ef4444"
        barra_tit = f'<div style="margin-top:6px;"><div style="display:flex;justify-content:space-between;font-size:0.75em;color:#aaa;"><span>Titolarità</span><span>{idx_tit}/100</span></div><div style="background:#2a2a4a;border-radius:4px;height:6px;overflow:hidden;"><div style="width:{idx_tit}%;background:{col_bar};height:100%;border-radius:4px;"></div></div></div>'

    if "Svincolato" in str(prop):
        badge_prop = '<span style="background:#00d26a20;color:#00d26a;padding:2px 8px;border-radius:12px;font-size:0.7em;border:1px solid #00d26a;">🟢 LIBERO</span>'
    else:
        badge_prop = f'<span style="background:#ff6b6b20;color:#ff6b6b;padding:2px 8px;border-radius:12px;font-size:0.7em;border:1px solid #ff6b6b;">🔒 {prop}</span>'

    pc_span = f'<span style="background:#1a1a2e;color:#00d26a;padding:2px 8px;border-radius:12px;font-size:0.7em;">{pc_txt}</span>' if pc_txt else ''

    # Costruisci contenuto espanso
    stats_html = _build_stats_html(nome, stats_per_stagione if stats_per_stagione else {})
    note_html = f'<div style="margin-top:8px;padding-top:8px;border-top:1px solid #2a2a4a;color:#aaa;font-size:0.8em;font-style:italic;">📝 {note}</div>' if note else ''

    # Vari FM se disponibile
    fm_extra = ""
    if stats_2627 is not None and not stats_2627.empty and "Nome" in stats_2627.columns:
        match = stats_2627[stats_2627["Nome"].str.lower() == nome.lower()]
        if match.empty:
            close = difflib.get_close_matches(nome.lower(), [n.lower() for n in stats_2627["Nome"].tolist()], n=1, cutoff=0.8)
            if close:
                match = stats_2627[stats_2627["Nome"].str.lower() == close[0]]
        if not match.empty and "FantaMedia" in match.columns and pd.notna(match.iloc[0]["FantaMedia"]):
            fm_2627 = float(match.iloc[0]["FantaMedia"])
            fm_extra = f' <span style="color:#00d26a;font-size:0.85em;">(📊 2026/27: {fm_2627})</span>'

    # Stats inline dalla stagione 2026/27
    inline_stats = _get_inline_stats(nome, stats_2627)
    trend_badge = _get_fm_trend_badge(nome, fm, stats_2627)

    card_inner = f'''<div style="display:flex;justify-content:space-between;align-items:start;">
        <div>
            <div style="font-size:1.1em;font-weight:bold;color:#fff;">{nome}</div>
            <div style="font-size:0.85em;color:#aaa;">{sa} | <span style="color:{colore};font-weight:600;">{ruolo}</span></div>
        </div>
        <div style="text-align:right;">
            <div style="font-size:1.3em;font-weight:bold;color:#ffd700;">{fm}{fm_extra}</div>
            <div style="font-size:0.75em;color:#888;">FM</div>
            {trend_badge}
        </div>
    </div>
    <div style="display:flex;gap:6px;margin-top:8px;flex-wrap:wrap;">
        <span style="background:{colore}20;color:{colore};padding:2px 8px;border-radius:12px;font-size:0.7em;font-weight:600;">{badge_fascia}</span>
        <span style="background:#1a1a2e;color:#ddd;padding:2px 8px;border-radius:12px;font-size:0.7em;">{quot}cr</span>
        {pc_span}
        <span style="background:#1a1a2e;color:#aaa;padding:2px 8px;border-radius:12px;font-size:0.7em;">IA {idx_aff}</span>
    </div>
    {barra_tit}
    <div style="margin-top:6px;display:flex;gap:4px;flex-wrap:wrap;">{inline_stats}</div>
    <div style="margin-top:8px;">{badge_prop}</div>
    {note_html}'''

    html = f'''<details style="margin-bottom:10px;"><summary style="list-style:none;cursor:pointer;"><div style="background:linear-gradient(135deg,#1e1e3f 0%,#2a2a4a 100%);border-radius:12px;padding:14px;border-left:4px solid {colore};box-shadow:0 2px 8px rgba(0,0,0,0.3);transition:all 0.3s ease;" onmouseover="this.style.transform='scale(1.03)';this.style.boxShadow='0 0 25px rgba(0,210,106,0.45)';this.style.zIndex='10';" onmouseout="this.style.transform='scale(1)';this.style.boxShadow='0 2px 8px rgba(0,0,0,0.3)';this.style.zIndex='1';">{card_inner}</div></summary><div style="background:#15152b;border-radius:0 0 12px 12px;padding:12px;border-left:4px solid {colore};border-top:1px solid #2a2a4a;"><div style="font-size:0.85em;color:#00d26a;font-weight:bold;margin-bottom:6px;">📊 Statistiche Storiche</div>{stats_html}</div></details>'''
    return html


# ============================================================
# INIZIALIZZAZIONE
# ============================================================
if "initialized" not in st.session_state:
    st.session_state.squadre = {}
    st.session_state.storico_mercato = []
    st.session_state.watchlist = []
    st.session_state.prestiti = []
    st.session_state.contratti = {}
    st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
    if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
        st.session_state.giocatori_db["Prezzo_Consigliato"] = None
    st.session_state.stats_storiche = pd.DataFrame()
    st.session_state.quotazioni_2025_26 = pd.DataFrame()
    st.session_state.stats_per_stagione = {}
    st.session_state.wizard_completato = False
    st.session_state.crediti_iniziali = CREDITI_INIZIALI
    st.session_state._riepiloghi_dirty = True
    st.session_state._player_index_dirty = True
    st.session_state._undo_stack = []

    if not load_state():
        for sq in NOMI_SQUADRE:
            st.session_state.squadre[sq] = {"crediti": CREDITI_INIZIALI, "rosa": []}

    st.session_state.initialized = True

# ============================================================
# WIZARD
# ============================================================
def check_wizard_needed():
    if st.session_state.get("wizard_completato", False):
        return False
    return all(len(st.session_state.squadre[sq]["rosa"]) == 0 for sq in NOMI_SQUADRE)

def render_wizard():
    st.header("⚽ Benvenuto in FantaManager 2026/27")
    step = st.session_state.get("wizard_step", 1)
    progress = (step / 4) * 100
    st.progress(int(progress), text=f"Passaggio {step} di 4")

    if step == 1:
        st.subheader("1. Listone Giocatori")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Usa Listone Default", use_container_width=True):
                st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
                st.session_state.wizard_step = 2
                save_state()
                st.rerun()
        with c2:
            if st.button("⏭️ Salta per ora", use_container_width=True):
                st.session_state.wizard_step = 2
                st.rerun()

    elif step == 2:
        st.subheader("2. Crediti Iniziali")
        cred = st.number_input("Crediti iniziali per squadra", min_value=10, max_value=500, value=CREDITI_INIZIALI, step=5)
        if st.button("💾 Imposta Crediti", type="primary", use_container_width=True):
            st.session_state.crediti_iniziali = cred
            for sq in NOMI_SQUADRE:
                st.session_state.squadre[sq]["crediti"] = cred
            st.session_state.wizard_step = 3
            save_state()
            st.rerun()

    elif step == 3:
        st.subheader("3. Importa Rose Pregresse (Opzionale)")
        if st.button("⏭️ Salta", use_container_width=True):
            st.session_state.wizard_step = 4
            st.rerun()

    elif step == 4:
        st.subheader("4. Pronto!")
        st.success("Setup completato. Buon divertimento!")
        if st.button("🚀 Inizia", type="primary", use_container_width=True):
            st.session_state.wizard_completato = True
            save_state()
            st.rerun()

# ============================================================
# SIDEBAR
# ============================================================
with st.sidebar:
    st.title("⚽ FantaManager")
    st.caption("2026/27 — 10 Squadre")
    st.markdown("---")

    if st.session_state.get("_undo_stack"):
        if st.button("↩️ Annulla Ultima Operazione", use_container_width=True):
            if StateManager.undo():
                save_state()
                st.toast("✅ Operazione annullata!", icon="↩️")
                st.rerun()
            else:
                st.toast("⚠️ Impossibile annullare", icon="⚠️")

    st.subheader("💾 Backup Rapido")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salva", use_container_width=True):
            save_state()
            st.toast("💾 Salvataggio completato", icon="✅")
    with c2:
        if st.button("📂 Carica", use_container_width=True):
            if load_state():
                st.toast("📂 Stato caricato!", icon="✅")
                st.rerun()
            else:
                st.toast("⚠️ Nessun salvataggio trovato", icon="⚠️")

    save_data = {
        "squadre": st.session_state.squadre,
        "storico_mercato": st.session_state.storico_mercato,
        "watchlist": st.session_state.watchlist,
        "prestiti": st.session_state.prestiti,
        "contratti": st.session_state.contratti,
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
        "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if not st.session_state.stats_storiche.empty else [],
        "stats_per_stagione": {k: v.to_dict(orient="records") for k, v in st.session_state.get("stats_per_stagione", {}).items()},
        "quotazioni_2025_26": st.session_state.quotazioni_2025_26.to_dict(orient="records") if not st.session_state.quotazioni_2025_26.empty else [],
        "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
        "wizard_completato": st.session_state.get("wizard_completato", False),
    }
    json_bytes = json.dumps(save_data, ensure_ascii=False, indent=2).encode('utf-8')
    st.download_button(
        label="⬇️ Scarica Stato (JSON)",
        data=json_bytes,
        file_name=f"fantamanager_{datetime.now().strftime('%Y%m%d_%H%M')}.json",
        mime="application/json",
        use_container_width=True
    )

    st.markdown("---")
    st.subheader("📂 Ripristina da PC")
    up_json = st.file_uploader("File JSON stato", type=["json"], key="up_json")
    if "last_json_key" not in st.session_state:
        st.session_state.last_json_key = ""
    if up_json is not None:
        file_key = f"{up_json.name}_{up_json.size}"
        if file_key != st.session_state.last_json_key:
            try:
                data = json.load(up_json)
                st.session_state.squadre = data.get("squadre", {})
                st.session_state.storico_mercato = data.get("storico_mercato", [])
                st.session_state.watchlist = data.get("watchlist", [])
                st.session_state.prestiti = data.get("prestiti", [])
                st.session_state.contratti = data.get("contratti", {})
                db = data.get("giocatori_db", [])
                st.session_state.giocatori_db = pd.DataFrame(db) if db else pd.DataFrame(LISTONE_DEFAULT)
                if "Prezzo_Consigliato" not in st.session_state.giocatori_db.columns:
                    st.session_state.giocatori_db["Prezzo_Consigliato"] = None
                else:
                    st.session_state.giocatori_db["Prezzo_Consigliato"] = pd.to_numeric(
                        st.session_state.giocatori_db["Prezzo_Consigliato"], errors="coerce"
                    )
                stats = data.get("stats_storiche", [])
                st.session_state.stats_storiche = pd.DataFrame(stats) if stats else pd.DataFrame()
                st.session_state.stats_per_stagione = {}
                for stag, records in data.get("stats_per_stagione", {}).items():
                    st.session_state.stats_per_stagione[stag] = pd.DataFrame(records) if records else pd.DataFrame()
                q25 = data.get("quotazioni_2025_26", [])
                st.session_state.quotazioni_2025_26 = pd.DataFrame(q25) if q25 else pd.DataFrame()
                st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
                st.session_state.wizard_completato = data.get("wizard_completato", False)
                for sq in NOMI_SQUADRE:
                    if sq not in st.session_state.squadre:
                        st.session_state.squadre[sq] = {"crediti": st.session_state.crediti_iniziali, "rosa": []}
                st.session_state.last_json_key = file_key
                invalidate_cache()
                save_state()
                st.success("✅ Stato caricato!")
                st.rerun()
            except Exception as e:
                st.error(f"Errore: {e}")

    st.markdown("---")
    st.subheader("⚙️ Configurazione")
    if "crediti_iniziali" not in st.session_state:
        st.session_state.crediti_iniziali = CREDITI_INIZIALI
    new_cred = st.number_input("Crediti iniziali", min_value=10, max_value=1000, value=int(st.session_state.crediti_iniziali), step=10, key="cred_ini")
    if new_cred != st.session_state.crediti_iniziali:
        st.session_state.crediti_iniziali = new_cred
        for sq in NOMI_SQUADRE:
            if len(st.session_state.squadre[sq]["rosa"]) == 0:
                st.session_state.squadre[sq]["crediti"] = new_cred
        save_state()
        st.success(f"Crediti iniziali aggiornati a {new_cred}!")

    st.markdown("---")
    st.subheader("💰 Crediti per Squadra")
    st.caption("Modifica i crediti attuali di ogni squadra")
    crediti_df_edit = pd.DataFrame([
        {"Squadra": sq, "Crediti": st.session_state.squadre[sq]["crediti"]} for sq in NOMI_SQUADRE
    ])
    edited_crediti = st.data_editor(
        crediti_df_edit,
        column_config={
            "Squadra": st.column_config.TextColumn("Squadra", disabled=True),
            "Crediti": st.column_config.NumberColumn("Crediti", min_value=0, max_value=1000, step=1),
        },
        use_container_width=True,
        hide_index=True,
        key="editor_crediti_squadre"
    )
    if st.button("💾 Salva Crediti Squadre", use_container_width=True):
        for _, row in edited_crediti.iterrows():
            st.session_state.squadre[row["Squadra"]]["crediti"] = int(row["Crediti"])
        invalidate_cache()
        save_state()
        st.success("Crediti squadre aggiornati!")
        st.rerun()

    st.markdown("---")
    with st.expander("📁 Importa Dati"):
        st.caption("Listone, Rose, Quotazioni 2025/26, Statistiche")
        st.info("Usa le pagine dedicate nel menu principale per importare dati.")

    with st.expander("⚠️ Reset"):
        if st.button("🗑️ Resetta TUTTO", use_container_width=True):
            for f in [SAVE_FILE_PKL, SAVE_FILE_JSON]:
                if os.path.exists(f):
                    os.remove(f)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.success("Resettato! Ricarica la pagina.")
            st.rerun()

    st.markdown("---")
    st.markdown("---")

# ============================================================
# NAVIGAZIONE IN ALTO
# ============================================================
st.markdown("<div style='margin-top: -20px;'></div>", unsafe_allow_html=True)
menu = st.radio(
    "",
    options=[
        "🏠 Dashboard",
        "🔍 Scouting & Database",
        "🔨 Asta Live",
        "🛒 Mercato",
        "🤝 Scambi & Prestiti",
        "📋 Rose & Contratti",
        "📈 Statistiche Storiche",
        "⚙️ Importa & Esporta"
    ],
    horizontal=True,
    label_visibility="collapsed",
    key="nav_top"
)
st.markdown("---")

# ============================================================
# WIZARD (se necessario)
# ============================================================
if check_wizard_needed() and menu == "🏠 Dashboard":
    render_wizard()
    st.stop()

# ============================================================
# 0. DASHBOARD
# ============================================================
if menu == "🏠 Dashboard":
    st.header("🏠 FantaManager Dashboard")
    st.caption("Panoramica completa dello stato del fantacalcio 2026/27")

    tot_scadenze = sum(1 for sq in NOMI_SQUADRE for g in st.session_state.squadre[sq]["rosa"]
                      if g.get("Scadenza_Anno", ANNO_CORRENTE + CONTRATTO_ANNI) <= ANNO_CORRENTE + 1)
    if tot_scadenze > 0:
        st.toast(f"🔔 {tot_scadenze} contratti in scadenza! Vai su Rose & Contratti.", icon="⚠️")

    st.subheader("📊 Stato delle Squadre")
    dash_data = []
    for sq in NOMI_SQUADRE:
        dati = st.session_state.squadre[sq]
        rosa = dati["rosa"]
        p=d=c=a=spesa=0
        in_scadenza = 0
        for g in rosa:
            r = g.get("Ruolo","C")
            if r=="P": p+=1
            elif r=="D": d+=1
            elif r=="C": c+=1
            elif r=="A": a+=1
            spesa += g.get("Costo_Acquisto",0)
            sa = g.get("Scadenza_Anno", ANNO_CORRENTE + CONTRATTO_ANNI)
            if sa <= ANNO_CORRENTE + 1:
                in_scadenza += 1
        prestiti_out = len([p for p in st.session_state.prestiti if p["Da"] == sq])
        dash_data.append({
            "Squadra": sq, "Crediti": dati["crediti"], "Rosa": len(rosa),
            "P": p, "D": d, "C": c, "A": a, "Spesa": spesa,
            "Completata": "✅" if len(rosa) >= 28 else f"{len(rosa)}/28",
            "Scadenze": in_scadenza,
            "Prestiti Uscita": prestiti_out,
            "Totale Posseduti": len(rosa) + prestiti_out
        })
    df_dash = pd.DataFrame(dash_data)
    st.dataframe(df_dash, use_container_width=True)

    st.markdown("---")
    st.subheader("📈 Metriche Chiave")
    c1, c2, c3, c4, c5 = st.columns(5)
    with c1:
        tot_giocatori = sum(len(st.session_state.squadre[sq]["rosa"]) for sq in NOMI_SQUADRE)
        st.metric("Giocatori Assegnati", tot_giocatori)
    with c2:
        tot_crediti = sum(st.session_state.squadre[sq]["crediti"] for sq in NOMI_SQUADRE)
        st.metric("Crediti Liberi", tot_crediti)
    with c3:
        squadre_complete = sum(1 for sq in NOMI_SQUADRE if len(st.session_state.squadre[sq]["rosa"]) >= 25)
        st.metric("Rose Completate", f"{squadre_complete}/10")
    with c4:
        db = st.session_state.giocatori_db
        in_rosa = set(get_player_index().keys())
        svinc = db[~db["Nome"].str.lower().isin(in_rosa)] if not db.empty else pd.DataFrame()
        st.metric("Svincolati", len(svinc))
    with c5:
        st.metric("Contratti in Scadenza", tot_scadenze)

    st.markdown("---")
    st.subheader("🏆 Top 5 Affari Liberi per Ruolo")
    if not svinc.empty:
        # Arricchisci con FantaMedia 2026/27 se disponibili
        svinc["FantaMedia_Originale"] = svinc["FantaMedia"]
        svinc["FantaMedia"] = svinc["Nome"].apply(lambda n: _get_fm_2627(n) if _get_fm_2627(n) is not None else svinc.loc[svinc["Nome"]==n, "FantaMedia"].values[0])
        svinc["Indice_Affare"] = round(svinc["FantaMedia"] / svinc["Quotazione"].replace(0,1), 2)
        ruolo_sel = st.select_slider(
            "Seleziona ruolo",
            options=["P", "D", "C", "A"],
            value="P",
            format_func=lambda x: {"P": "🧤 Portieri", "D": "🛡️ Difensori", "C": "⚙️ Centrocampisti", "A": "⚔️ Attaccanti"}[x],
            key="dash_top5_ruolo"
        )
        svinc_r = svinc[svinc["Ruolo"] == ruolo_sel]
        if not svinc_r.empty:
            top5 = svinc_r.nlargest(5, "Indice_Affare")[["Nome","Ruolo","Squadra_SerieA","Quotazione","FantaMedia","Indice_Affare","Consiglio"]].copy()
            # Aggiungi indicatore se la FM viene dalle stats 2026/27
            def _badge_fm(row):
                fm_2627 = _get_fm_2627(row["Nome"])
                if fm_2627 is not None:
                    return f"{row['FantaMedia']} 📊"
                return f"{row['FantaMedia']} 📋"
            top5["FantaMedia"] = top5.apply(_badge_fm, axis=1)
            st.dataframe(top5, use_container_width=True, hide_index=True)
            st.caption("📊 = FantaMedia da statistiche 2026/27 | 📋 = FantaMedia da listone")
        else:
            st.info(f"Nessuno svincolato nel ruolo {ruolo_sel}.")
    else:
        st.info("Nessuno svincolato.")

    st.markdown("---")
    st.subheader("🔔 Alert Contratti in Scadenza")
    scad_rows = []
    for sq in NOMI_SQUADRE:
        for g in st.session_state.squadre[sq]["rosa"]:
            sa = g.get("Scadenza_Anno", ANNO_CORRENTE + CONTRATTO_ANNI)
            if sa <= ANNO_CORRENTE + 1:
                scad_rows.append({
                    "Squadra": sq, "Giocatore": g["Nome"], "Ruolo": g["Ruolo"],
                    "Scadenza": sa,
                    "Stato": "🔴 SCADE QUEST'ANNO" if sa == ANNO_CORRENTE else "🟠 SCADE IL PROSSIMO"
                })
    if scad_rows:
        # Alert visivo in alto
        st.error(f"⚠️ ATTENZIONE: {len(scad_rows)} contratti in scadenza! Controlla la tabella sotto.")
        df_scad = pd.DataFrame(scad_rows).sort_values("Scadenza")
        st.dataframe(df_scad, use_container_width=True, hide_index=True)
    else:
        st.success("✅ Nessun contratto in scadenza imminente.")

    if st.session_state.storico_mercato:
        st.markdown("---")
        st.subheader("📈 Andamento Mercato")
        hist = pd.DataFrame(st.session_state.storico_mercato)
        if not hist.empty and "Data" in hist.columns:
            hist["Data_dt"] = pd.to_datetime(hist["Data"])
            hist = hist.sort_values("Data_dt")
            daily = hist.groupby(hist["Data_dt"].dt.date).size().reset_index(name="Operazioni")
            st.line_chart(daily.set_index("Data_dt"))

    st.markdown("---")
    st.subheader("🌡️ Heatmap Composizione Rose")
    heat_data = []
    for sq in NOMI_SQUADRE:
        rosa = st.session_state.squadre[sq]["rosa"]
        conti = {"P": 0, "D": 0, "C": 0, "A": 0}
        for g in rosa:
            r = g.get("Ruolo", "C")
            if r in conti:
                conti[r] += 1
        for ruolo in ["P", "D", "C", "A"]:
            req = ROSA_REQ[ruolo]
            poss = conti[ruolo]
            pct = min(100, round((poss / req) * 100, 1))
            heat_data.append({"Squadra": sq, "Ruolo": ruolo, "Completamento %": pct, "Posseduti": f"{poss}/{req}"})
    df_heat = pd.DataFrame(heat_data)
    pivot_heat = df_heat.pivot(index="Squadra", columns="Ruolo", values="Completamento %")

    # Tabella HTML con colori inline (no matplotlib required)
    def _heat_color(pct):
        if pct >= 100:
            return "#14532d"  # verde scuro
        elif pct >= 75:
            return "#166534"
        elif pct >= 50:
            return "#ca8a04"  # giallo
        elif pct >= 25:
            return "#9a3412"  # arancione
        else:
            return "#7f1d1d"  # rosso scuro

    html_table = '<table style="width:100%;border-collapse:collapse;font-size:0.9em;"><thead><tr style="background:#1a1a2e;"><th style="padding:8px;text-align:left;color:#888;border-bottom:2px solid #2a2a4a;">Squadra</th>'
    for ruolo in ["P", "D", "C", "A"]:
        html_table += f'<th style="padding:8px;text-align:center;color:#888;border-bottom:2px solid #2a2a4a;">{ruolo}</th>'
    html_table += '</tr></thead><tbody>'
    for sq in NOMI_SQUADRE:
        html_table += f'<tr><td style="padding:8px;color:#fff;font-weight:600;border-bottom:1px solid #2a2a4a;">{sq}</td>'
        for ruolo in ["P", "D", "C", "A"]:
            val = pivot_heat.loc[sq, ruolo] if sq in pivot_heat.index and ruolo in pivot_heat.columns else 0
            bg = _heat_color(val)
            txt = "#fff" if val < 50 else "#fff"
            html_table += f'<td style="padding:8px;text-align:center;border-bottom:1px solid #2a2a4a;background:{bg};color:{txt};font-weight:bold;border-radius:4px;">{val:.0f}%</td>'
        html_table += '</tr>'
    html_table += '</tbody></table>'
    st.html(html_table)

    st.markdown("---")
    st.subheader("🎯 Budget Libero per Top (>40cr)")
    st.caption("Crediti effettivamente spendibili su un giocatore costoso, dopo riserva minima per completare la rosa.")
    budget_top_data = []
    for sq in NOMI_SQUADRE:
        riep = riepilogo_rosa(sq)
        libero = budget_libero_effettivo(sq)
        budget_top_data.append({
            "Squadra": sq, "Crediti Totali": riep["crediti"], "Posti Mancanti": riep["tot_mancanti"],
            "🎯 Budget Libero Top": libero, "💰 Può spendere >40cr?": "✅ SÌ" if libero >= 40 else "❌ NO"
        })
    st.dataframe(pd.DataFrame(budget_top_data).sort_values("🎯 Budget Libero Top", ascending=False), use_container_width=True, hide_index=True)

    st.markdown("---")
    st.subheader("🔥 Fuga Top Tracker")
    st.caption("Quanti top e consigliati sono ancora liberi? Rosso = ultima chiamata!")
    tracker = fuga_top_tracker()
    cols_track = st.columns(4)
    ruoli_track = {"P": "🧤 Portieri", "D": "🛡️ Difensori", "C": "⚙️ Centrocampisti", "A": "⚔️ Attaccanti"}
    for idx_r, ruolo in enumerate(["P", "D", "C", "A"]):
        with cols_track[idx_r]:
            t = tracker[ruolo]
            colore = "#ef4444" if t["pct_top_rimasti"] < 30 else "#eab308" if t["pct_top_rimasti"] < 60 else "#00d26a"
            st.markdown(f"<div style='text-align:center;padding:10px;border-radius:8px;background:#1a1a2e;border:1px solid {colore};'>"
                        f"<div style='font-size:1em;font-weight:bold;color:#fff;'>{ruoli_track[ruolo]}</div>"
                        f"<div style='font-size:1.8em;font-weight:bold;color:{colore};'>{t['top_rimasti']}/{t['top_totali']} ⭐</div>"
                        f"<div style='font-size:0.8em;color:#aaa;'>{t['pct_top_rimasti']:.0f}% top rimasti</div>"
                        f"<div style='font-size:1.1em;color:#888;margin-top:4px;'>{t['cons_rimasti']}/{t['cons_totali']} 👍</div></div>", unsafe_allow_html=True)
            if t["pct_top_rimasti"] < 30 and t["top_rimasti"] <= 2:
                st.error(f"⚠️ Ultimi {t['top_rimasti']} top!")

    st.markdown("---")
    st.subheader("💸 Heatmap Spese per Ruolo")
    spese_data = []
    for sq in NOMI_SQUADRE:
        spese = spese_per_ruolo(sq)
        for ruolo in ["P", "D", "C", "A"]:
            spese_data.append({"Squadra": sq, "Ruolo": ruolo, "Spesa": spese[ruolo]["tot"], "N": spese[ruolo]["n"]})
    df_spese = pd.DataFrame(spese_data)
    max_spesa = df_spese["Spesa"].max() or 1
    def _heat_spese(val):
        pct = val / max_spesa
        return "#7f1d1d" if pct >= 0.8 else "#9a3412" if pct >= 0.6 else "#ca8a04" if pct >= 0.4 else "#166534" if pct >= 0.2 else "#14532d"
    html_spese = '<table style="width:100%;border-collapse:collapse;font-size:0.9em;"><thead><tr style="background:#1a1a2e;"><th style="padding:8px;text-align:left;color:#888;border-bottom:2px solid #2a2a4a;">Squadra</th>'
    for ruolo in ["P", "D", "C", "A"]: html_spese += f'<th style="padding:8px;text-align:center;color:#888;border-bottom:2px solid #2a2a4a;">{ruolo}</th>'
    html_spese += '</tr></thead><tbody>'
    for sq in NOMI_SQUADRE:
        html_spese += f'<tr><td style="padding:8px;color:#fff;font-weight:600;border-bottom:1px solid #2a2a4a;">{sq}</td>'
        for ruolo in ["P", "D", "C", "A"]:
            val = df_spese[(df_spese["Squadra"]==sq)&(df_spese["Ruolo"]==ruolo)]["Spesa"].values
            val = val[0] if len(val)>0 else 0
            n_val = df_spese[(df_spese["Squadra"]==sq)&(df_spese["Ruolo"]==ruolo)]["N"].values
            n_val = int(n_val[0]) if len(n_val)>0 else 0
            html_spese += f'<td style="padding:8px;text-align:center;border-bottom:1px solid #2a2a4a;background:{_heat_spese(val)};color:#fff;font-weight:bold;border-radius:4px;">{int(val)}cr<br><span style="font-size:0.7em;color:#ccc;">({n_val})</span></td>'
        html_spese += '</tr>'
    html_spese += '</tbody></table>'
    st.html(html_spese)
    st.markdown("---")
    st.subheader("💰 Classifica Crediti")
    crediti_df = pd.DataFrame([{"Squadra": sq, "Crediti": st.session_state.squadre[sq]["crediti"]} for sq in NOMI_SQUADRE]).sort_values("Crediti", ascending=False)
    st.bar_chart(crediti_df.set_index("Squadra"))

# ============================================================
# 1. SCOUTING
# ============================================================
if menu == "🔍 Scouting & Database":
    st.header("🔍 Hub Scouting 2026/27")
    df = st.session_state.giocatori_db.copy()
    df = arricchisci_con_stats_2627(df)
    stats_2627 = None
    if "2026-27" in st.session_state.get("stats_per_stagione", {}):
        stats_2627 = st.session_state.stats_per_stagione["2026-27"]
        st.caption("📊 Dati arricchiti con statistiche 2026/27 caricate")

    if df.empty:
        st.warning("Nessun giocatore nel database.")
    else:
        df["Indice_Affare"] = round(df["FantaMedia"] / df["Quotazione"].replace(0, 1), 2)
        df["Indice_Titolarita"] = df.apply(lambda r: calcola_indice_titolarita(r, stats_2627), axis=1)

        if "Quotazione_2025_26" in df.columns:
            df["Variazione_%"] = round((df["Quotazione"] - df["Quotazione_2025_26"]) / df["Quotazione_2025_26"].replace(0, 1) * 100, 1)
        else:
            df["Variazione_%"] = None

        idx = get_player_index()
        df["Proprietario"] = df["Nome"].apply(lambda x: idx.get(x.lower(), "Svincolato 🟢"))

        # ============================================================
        # FILTRI
        # ============================================================
        with st.expander("🔧 Filtri Avanzati", expanded=True):
            f0, f1, f2, f3, f4, f5 = st.columns(6)
            with f0:
                sq_budget = st.selectbox("Budget Squadra", ["Nessuno"] + NOMI_SQUADRE, key="scout_budget_sq")
                filtro_budget = st.checkbox("Solo chi posso permettermi", value=False, key="scout_budget_chk")
            with f1:
                ruoli = sorted(df["Ruolo"].unique()) if "Ruolo" in df.columns else ["P", "D", "C", "A"]
                filtro_ruolo = st.multiselect("Ruolo", ruoli, default=ruoli, key="scout_ruolo")
            with f2:
                squadre_sa = sorted(df["Squadra_SerieA"].unique()) if "Squadra_SerieA" in df.columns else []
                filtro_sa = st.multiselect("Squadra Serie A", ["Tutte"] + squadre_sa, default=["Tutte"], key="scout_sa")
            with f3:
                q_vals = pd.to_numeric(df["Quotazione"], errors="coerce").dropna()
                min_q, max_q = (int(q_vals.min()), int(q_vals.max())) if len(q_vals) > 0 else (1, 100)
                if min_q == max_q:
                    min_q, max_q = max(1, min_q - 5), max_q + 5
                range_q = st.slider("Quotazione", min_q, max_q, (min_q, max_q), key="scout_q")
            with f4:
                fm_vals = pd.to_numeric(df["FantaMedia"], errors="coerce").dropna()
                min_fm_s, max_fm_s = (round(float(fm_vals.min()), 1), round(float(fm_vals.max()), 1)) if len(fm_vals) > 0 else (4.0, 10.0)
                if min_fm_s == max_fm_s:
                    min_fm_s, max_fm_s = round(max(4.0, min_fm_s - 1.0), 1), round(min(10.0, max_fm_s + 1.0), 1)
                range_fm = st.slider("FantaMedia", min_value=min_fm_s, max_value=max_fm_s, value=(min_fm_s, max_fm_s), step=0.1, key="scout_fm")
            with f5:
                consigli_fasce = st.multiselect("Fascia", ["top", "consigliato", "scommessa"], default=["top", "consigliato", "scommessa"], key="scout_fascia")

            f6, f7 = st.columns(2)
            with f6:
                solo_svinc = st.checkbox("Solo Svincolati", value=False, key="scout_svinc")
                search = st.text_input("Cerca nome", key="scout_search")
            with f7:
                sq_mancanti = st.selectbox("🎯 Solo ruoli che mi mancano", ["Nessuno"] + NOMI_SQUADRE, key="scout_mancanti")
                if sq_mancanti != "Nessuno":
                    riep_m = riepilogo_rosa(sq_mancanti)
                    ruoli_mancanti = [r for r in ROSA_REQ if riep_m[r]["mancanti"] > 0]
                    st.caption(f"Mancano: {', '.join(ruoli_mancanti) if ruoli_mancanti else 'Nessuno'}")
                if "Variazione_%" in df.columns:
                    var_vals = pd.to_numeric(df["Variazione_%"], errors="coerce").dropna()
                    var_min, var_max = (round(float(var_vals.min()), 1), round(float(var_vals.max()), 1)) if len(var_vals) > 0 else (-100.0, 100.0)
                    if var_min == var_max:
                        var_min, var_max = var_min - 5.0, var_max + 5.0
                    range_var = st.slider("Variazione % (2025→2026)", min_value=var_min, max_value=var_max, value=(var_min, var_max), key="scout_var")
                else:
                    range_var = (-100, 100)

        # Normalizza tipi numerici
        df["FantaMedia"] = pd.to_numeric(df["FantaMedia"], errors="coerce")
        df["Quotazione"] = pd.to_numeric(df["Quotazione"], errors="coerce")
        df["Consiglio"] = df["Consiglio"].fillna("consigliato")

        df_f = df[
            (df["Ruolo"].isin(filtro_ruolo)) &
            (df["FantaMedia"].notna()) & (df["FantaMedia"] >= range_fm[0]) & (df["FantaMedia"] <= range_fm[1]) &
            (df["Quotazione"].notna()) & (df["Quotazione"] >= range_q[0]) & (df["Quotazione"] <= range_q[1]) &
            (df["Consiglio"].isin(consigli_fasce))
        ].copy()
        if "Tutte" not in filtro_sa and "Squadra_SerieA" in df.columns:
            df_f = df_f[df_f["Squadra_SerieA"].isin(filtro_sa)]
        if solo_svinc:
            df_f = df_f[df_f["Proprietario"] == "Svincolato 🟢"]
        if sq_mancanti != "Nessuno":
            riep_m = riepilogo_rosa(sq_mancanti)
            ruoli_mancanti = [r for r in ROSA_REQ if riep_m[r]["mancanti"] > 0]
            if ruoli_mancanti:
                df_f = df_f[df_f["Ruolo"].isin(ruoli_mancanti)]
                st.info(f"🎯 Filtro attivo per **{sq_mancanti}**: mostro solo {', '.join(ruoli_mancanti)} (mancano {sum(riep_m[r]['mancanti'] for r in ruoli_mancanti)} giocatori)")
            else:
                st.success(f"✅ **{sq_mancanti}** ha la rosa completa!")
                df_f = df_f.iloc[0:0]  # dataframe vuoto
        if search:
            df_f = df_f[df_f["Nome"].str.contains(search, case=False, na=False)]
        if "Variazione_%" in df_f.columns and df_f["Variazione_%"].notna().any():
            df_f = df_f[(df_f["Variazione_%"].isna()) | ((df_f["Variazione_%"] >= range_var[0]) & (df_f["Variazione_%"] <= range_var[1]))]

        if filtro_budget and sq_budget != "Nessuno":
            riep_b = riepilogo_rosa(sq_budget)
            crediti_disp = riep_b["crediti"]
            ruoli_mancanti = [r for r in ROSA_REQ if riep_b[r]["mancanti"] > 0]
            df_f = df_f[df_f["Quotazione"] <= crediti_disp]
            df_f = df_f[df_f["Ruolo"].isin(ruoli_mancanti)]
            st.info(f"💰 Filtro budget attivo per **{sq_budget}**: {crediti_disp}cr disponibili, ruoli mancanti: {', '.join(ruoli_mancanti)}")

        # ============================================================
        # METRICHE RIEPOLOGO
        # ============================================================
        st.markdown("---")
        st.subheader("📊 Riepilogo Mercato")
        col_m1, col_m2, col_m3, col_m4, col_m5 = st.columns(5)
        with col_m1:
            st.metric("Svincolati", len(df[df["Proprietario"] == "Svincolato 🟢"]))
        with col_m2:
            st.metric("Assegnati", len(df[df["Proprietario"] != "Svincolato 🟢"]))
        with col_m3:
            top_affari = len(df[(df["Indice_Affare"] > 0.18) & (df["Proprietario"] == "Svincolato 🟢")])
            st.metric("Top Affari Liberi", top_affari)
        with col_m4:
            if "Variazione_%" in df.columns:
                rialzati = len(df[(df["Variazione_%"] > 20) & (df["Proprietario"] == "Svincolato 🟢")])
                st.metric("Rialzati >20%", rialzati)
        with col_m5:
            top_titolari = len(df[(df["Indice_Titolarita"] >= 85) & (df["Proprietario"] == "Svincolato 🟢")])
            st.metric("Top Titolarità Liberi", top_titolari)

        # ============================================================
        # TOP CARD — I MIGLIORI SVINCOLATI
        # ============================================================
        with st.expander("🏆 Top Picks — Schede & Best Buy", expanded=True):
            st.subheader("🏆 Top Svincolati — Schede Giocatore")
            svinc_df = df[df["Proprietario"] == "Svincolato 🟢"].copy()
            if not svinc_df.empty:
                top_mixed = svinc_df.nlargest(8, "Indice_Titolarita")
                cards = st.columns(4)
                stats_ps = st.session_state.get("stats_per_stagione", {})
                for i, (_, row) in enumerate(top_mixed.iterrows()):
                    with cards[i % 4]:
                        st.html(render_card_giocatore_espandibile(row, stats_ps, stats_2627))
            else:
                st.info("Nessuno svincolato disponibile.")

            # ============================================================
            # BEST BUY PER RUOLO (con titolarità)
            # ============================================================
            st.markdown("---")
            st.subheader("🏆 Best Buy — Top 3 Sottovalutati per Ruolo")
            best_cols = st.columns(4)
            ruoli_color = {"P": "🔵", "D": "🟢", "C": "🟡", "A": "🔴"}
            for idx_r, ruolo in enumerate(["P", "D", "C", "A"]):
                with best_cols[idx_r]:
                    df_r = df[(df["Ruolo"] == ruolo) & (df["Proprietario"] == "Svincolato 🟢")].sort_values("Indice_Affare", ascending=False).head(3)
                    st.markdown(f"**{ruoli_color[ruolo]} {ruolo}**")
                    if not df_r.empty:
                        for _, row in df_r.iterrows():
                            pc = row.get("Prezzo_Consigliato")
                            pc_txt = f"💡{int(pc)}cr" if pd.notna(pc) else ""
                            tit_bar = ""
                            if row["Indice_Titolarita"] >= 80:
                                tit_bar = f'<span style="color:#00d26a;font-size:0.75em;">● Tit. {row["Indice_Titolarita"]}</span>'
                            elif row["Indice_Titolarita"] >= 60:
                                tit_bar = f'<span style="color:#eab308;font-size:0.75em;">● Tit. {row["Indice_Titolarita"]}</span>'
                            else:
                                tit_bar = f'<span style="color:#ef4444;font-size:0.75em;">● Tit. {row["Indice_Titolarita"]}</span>'
                            st.html(
                                f'<div style="background:#1a1a2e;padding:8px;border-radius:6px;margin-bottom:4px;">'
                                f'<b>{row["Nome"]}</b> ({row["Squadra_SerieA"]})<br/>'
                                f'<span style="color:#888;font-size:0.85em;">FM {row["FantaMedia"]} | Q {int(row["Quotazione"])}cr | IA {row["Indice_Affare"]}</span> {pc_txt}<br/>'
                                f'{tit_bar}'
                                f'</div>'
                            )
                    else:
                        st.caption("Nessuno svincolato")

            # ============================================================
            # 🎲 RANDOM PICK
            # ============================================================
        with st.expander("🎲 Estrazione Casuale", expanded=False):
            st.subheader("🎲 Estrazione Casuale")
            st.caption("Lascia che il caso ti suggerisca un giocatore in base ai tuoi filtri attuali.")
            c_rand1, c_rand2, c_rand3 = st.columns([2, 2, 1])
            with c_rand1:
                rand_ruolo = st.selectbox("Ruolo", ["Qualsiasi", "P", "D", "C", "A"], key="rand_ruolo")
            with c_rand2:
                rand_budget_sq = st.selectbox("Budget squadra", ["Nessuno"] + NOMI_SQUADRE, key="rand_budget")
            with c_rand3:
                st.write("")
                st.write("")
                if st.button("🎲 Estrai", type="primary", use_container_width=True):
                    pool = df_f.copy()
                    if rand_ruolo != "Qualsiasi":
                        pool = pool[pool["Ruolo"] == rand_ruolo]
                    if rand_budget_sq != "Nessuno":
                        cred_disp = st.session_state.squadre[rand_budget_sq]["crediti"]
                        pool = pool[pool["Quotazione"] <= cred_disp]
                    if not pool.empty:
                        estratto = pool.sample(1).iloc[0]
                        st.session_state["rand_estratto"] = estratto.to_dict()
                        st.rerun()
                    else:
                        st.warning("Nessun giocatore matcha i filtri!")

            if "rand_estratto" in st.session_state:
                estr = st.session_state["rand_estratto"]
                st.markdown("---")
                st.markdown(f"### 🎰 Estratto: **{estr['Nome']}**")
                c_e1, c_e2, c_e3 = st.columns(3)
                with c_e1:
                    st.metric("Ruolo", estr['Ruolo'])
                with c_e2:
                    st.metric("FantaMedia", estr['FantaMedia'])
                with c_e3:
                    st.metric("Quotazione", f"{int(estr['Quotazione'])}cr")
                st.caption(f"{estr.get('Squadra_SerieA', 'N/D')} | Fascia: {estr.get('Consiglio', 'N/D')} | IA: {estr.get('Indice_Affare', 'N/D')}")
                if st.button("🗑️ Chiudi estrazione"):
                    del st.session_state["rand_estratto"]
                    st.rerun()

            # ============================================================
        with st.expander("📋 Risultati Tabella", expanded=True):
            st.subheader(f"📋 Risultati: {len(df_f)} giocatori")
            display_cols = [c for c in ["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "Prezzo_Consigliato",
                                        "Quotazione_2025_26", "Variazione_%", "FantaMedia", "Indice_Affare",
                                        "Indice_Titolarita", "Proprietario", "Consiglio", "Note"] if c in df_f.columns]
            st.dataframe(df_f[display_cols].sort_values("Indice_Titolarita", ascending=False),
                         use_container_width=True, hide_index=True)

            # ============================================================
            # CONFRONTO MULTI-GIOCATORI (fino a 4)
            # ============================================================
        with st.expander("⚔️ Confronto Multi-Giocatore", expanded=False):
            st.subheader("⚔️ Confronto Multi-Giocatore")
            n_giocatori = st.segmented_control("Quanti confrontare?", [2, 3, 4], default=2, key="n_comp")
            n_giocatori = n_giocatori or 2
            nomi = df["Nome"].values.tolist()
            selezionati = []
            cols_comp = st.columns(n_giocatori)
            for i in range(n_giocatori):
                with cols_comp[i]:
                    default_idx = min(i, len(nomi)-1)
                    g = st.selectbox(f"Giocatore {i+1}", nomi, index=default_idx, key=f"comp{i}")
                    selezionati.append(g)

            selezionati = list(dict.fromkeys(selezionati))  # rimuovi duplicati
            if len(selezionati) >= 2:
                rows = []
                for nome_g in selezionati:
                    r = df[df["Nome"] == nome_g].iloc[0]
                    row = {
                        "Giocatore": nome_g,
                        "Ruolo": r["Ruolo"],
                        "Squadra": r["Squadra_SerieA"],
                        "Quotazione": f"{int(r['Quotazione'])}cr",
                        "FantaMedia": r["FantaMedia"],
                        "Indice Affare": r["Indice_Affare"],
                        "Titolarità": r["Indice_Titolarita"],
                        "Proprietario": r["Proprietario"],
                    }
                    if "Variazione_%" in df.columns:
                        row["Variazione %"] = f"{r['Variazione_%']}%"
                    rows.append(row)
                df_comp = pd.DataFrame(rows)
                st.dataframe(df_comp.set_index("Giocatore").T, use_container_width=True)

                # Grafico radar-like con barre
                chart_rows = []
                for nome_g in selezionati:
                    r = df[df["Nome"] == nome_g].iloc[0]
                    chart_rows.append({"Giocatore": nome_g, "Metrica": "FantaMedia", "Valore": r["FantaMedia"]})
                    chart_rows.append({"Giocatore": nome_g, "Metrica": "Titolarità/10", "Valore": r["Indice_Titolarita"]/10})
                    chart_rows.append({"Giocatore": nome_g, "Metrica": "Affare×50", "Valore": r["Indice_Affare"]*50})
                chart_df = pd.DataFrame(chart_rows)
                pivot = chart_df.pivot(index="Metrica", columns="Giocatore", values="Valore")
                st.bar_chart(pivot, use_container_width=True)

                # Vincitore per indice affare
                best = max(rows, key=lambda x: x["Indice Affare"])
                st.success(f"🏆 Miglior indice affare: **{best['Giocatore']}** ({best['Indice Affare']})")

            # ============================================================
            # CHI PUO PERMETTERSELO
            # ============================================================
        with st.expander("💰 Chi può Permetterselo? — Analisi Avversari", expanded=False):
            st.subheader("💰 Chi può Permetterselo?")
            g_target = st.selectbox("Giocatore da analizzare", df["Nome"].values, key="g_target")
            if g_target:
                info_t = df[df["Nome"] == g_target].iloc[0]
                ruolo_t = info_t["Ruolo"]
                quot_t = int(info_t["Quotazione"])
                st.markdown(f"**{g_target}** — {ruolo_t} | Quotazione: {quot_t}cr | Titolarità: {info_t['Indice_Titolarita']}/100")
                avv_data = []
                riepiloghi = get_all_riepiloghi()
                for sq_avv in NOMI_SQUADRE:
                    riep_avv = riepiloghi[sq_avv]
                    mancanti_avv = riep_avv[ruolo_t]["mancanti"]
                    off_max_avv = riep_avv[ruolo_t]["offerta_max"]
                    crediti_avv = riep_avv["crediti"]
                    ha_giocatore = any(g["Nome"].lower() == g_target.lower() for g in st.session_state.squadre[sq_avv]["rosa"])
                    avv_data.append({
                        "Squadra": sq_avv, "Crediti": crediti_avv,
                        f"Mancano {ruolo_t}": mancanti_avv, "Offerta Max": off_max_avv,
                        "Può Permetterselo": "✅ SÌ" if off_max_avv >= quot_t and not ha_giocatore else ("❌ NO" if not ha_giocatore else "🔄 GIÀ IN ROSA"),
                        "Distanza": off_max_avv - quot_t if not ha_giocatore else None
                    })
                df_avv_target = pd.DataFrame(avv_data).sort_values("Offerta Max", ascending=False)
                st.dataframe(df_avv_target, use_container_width=True, hide_index=True)
                possono = df_avv_target[df_avv_target["Può Permetterselo"] == "✅ SÌ"]
                if not possono.empty:
                    st.info(f"📢 **{len(possono)} squadre** possono permettersi {g_target} alla quotazione di listone ({quot_t}cr)")
                else:
                    st.success(f"🛡️ Nessuna squadra può permettersi {g_target} alla quotazione di listone.")

            # ============================================================
            # EDITOR PREZZI + WATCHLIST
            # ============================================================
        with st.expander("🛠️ Tools Editing — Prezzi, AI & Fasce", expanded=False):
            st.subheader("✏️ Modifica Prezzi Consigliati")
            editor_cols = [c for c in ["Nome", "Ruolo", "Squadra_SerieA", "Quotazione", "FantaMedia", "Prezzo_Consigliato", "Consiglio", "Note"] if c in df.columns]
            df_edit = df[editor_cols].copy()
            df_edited = st.data_editor(
                df_edit,
                column_config={
                    "Prezzo_Consigliato": st.column_config.NumberColumn("Prezzo Consigliato", min_value=0, max_value=500, step=1, format="%d cr"),
                    "Nome": st.column_config.TextColumn("Nome", disabled=True),
                    "Ruolo": st.column_config.TextColumn("Ruolo", disabled=True),
                    "Squadra_SerieA": st.column_config.TextColumn("Squadra Serie A", disabled=True),
                    "Quotazione": st.column_config.NumberColumn("Quotazione", disabled=True),
                    "FantaMedia": st.column_config.NumberColumn("FantaMedia", disabled=True),
                    "Consiglio": st.column_config.TextColumn("Consiglio", disabled=True),
                    "Note": st.column_config.TextColumn("Note", disabled=True),
                },
                use_container_width=True, num_rows="fixed", key="editor_prezzi"
            )
            if st.button("💾 Salva Prezzi Consigliati", type="primary"):
                if "Prezzo_Consigliato" in df_edited.columns:
                    st.session_state.giocatori_db = st.session_state.giocatori_db.drop(columns=["Prezzo_Consigliato"], errors="ignore")
                    st.session_state.giocatori_db = st.session_state.giocatori_db.merge(
                        df_edited[["Nome", "Prezzo_Consigliato"]], on="Nome", how="left"
                    )
                    save_state()
                    st.success("✅ Prezzi consigliati salvati!")
                    st.rerun()

            st.markdown("---")
            st.subheader("🧠 Calcola Prezzi Consigliati AI")
            if st.button("🚀 Calcola Tutti i Prezzi AI", type="primary"):
                stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                count = 0
                for idx, row in st.session_state.giocatori_db.iterrows():
                    if pd.isna(row.get("Prezzo_Consigliato")):
                        pc_ai, _ = calcola_prezzo_consigliato(row.to_dict(), stats_df)
                        st.session_state.giocatori_db.at[idx, "Prezzo_Consigliato"] = pc_ai
                        count += 1
                save_state()
                st.success(f"✅ Calcolati {count} prezzi consigliati!")
                st.rerun()

            st.markdown("---")
            st.subheader("🎯 Ricalcola Fasce da Storico")
            st.caption("Sovrascrive le fasce attuali analizzando le statistiche caricate nelle ultime stagioni.")
            if st.button("🚀 Applica Classificazione Automatica", type="primary"):
                applica_fasce_automatiche()
                st.rerun()

        with st.expander("⭐ Watchlist", expanded=True):
            st.subheader("⭐ Watchlist")
            g_sel = st.selectbox("Aggiungi giocatore", df["Nome"].values, key="wl")
            c1_wl, c2_wl = st.columns([1, 1])
            with c1_wl:
                if st.button("Aggiungi", use_container_width=True):
                    if g_sel not in st.session_state.watchlist:
                        st.session_state.watchlist.append(g_sel)
                        save_state()
                        st.success(f"{g_sel} aggiunto!")
                        st.rerun()
            with c2_wl:
                if st.button("🗑️ Svuota Watchlist", use_container_width=True):
                    st.session_state.watchlist = []
                    save_state()
                    st.rerun()

            if st.session_state.watchlist:
                df_wl = df[df["Nome"].isin(st.session_state.watchlist)].copy()
                stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                df_wl["Prezzo_AI"] = df_wl.apply(lambda row: calcola_prezzo_consigliato(row.to_dict(), stats_df)[0], axis=1)
                if "Quotazione_2025_26" in df_wl.columns and "Variazione_%" not in df_wl.columns:
                    df_wl["Variazione_%"] = round((df_wl["Quotazione"] - df_wl["Quotazione_2025_26"]) / df_wl["Quotazione_2025_26"].replace(0, 1) * 100, 1)

                # Metriche riassuntive
                tot_wl = len(df_wl)
                conti_wl = {"P": 0, "D": 0, "C": 0, "A": 0}
                budget_wl = 0
                for _, r in df_wl.iterrows():
                    ru = r.get("Ruolo", "C")
                    if ru in conti_wl:
                        conti_wl[ru] += 1
                    budget_wl += int(r.get("Quotazione", 0))
                m1, m2, m3, m4, m5 = st.columns(5)
                with m1:
                    st.metric("Totale Watchlist", tot_wl)
                with m2:
                    st.metric("🧤 Portieri", conti_wl["P"])
                with m3:
                    st.metric("🛡️ Difensori", conti_wl["D"])
                with m4:
                    st.metric("⚙️ Centrocampisti", conti_wl["C"])
                with m5:
                    st.metric("⚔️ Attaccanti", conti_wl["A"])
                st.caption(f"💰 Budget totale quotazioni: **{budget_wl}cr** | Prezzo AI medio: **{int(df_wl['Prezzo_AI'].mean())}cr**")

                stats_ps_wl = st.session_state.get("stats_per_stagione", {})
                stats_2627_wl = stats_ps_wl.get("2026-27") if "2026-27" in stats_ps_wl else None
                idx_wl = get_player_index()

                # Card per ruolo
                ruoli_wl = ["P", "D", "C", "A"]
                ruoli_nomi_wl = {"P": "🧤 Portieri", "D": "🛡️ Difensori", "C": "⚙️ Centrocampisti", "A": "⚔️ Attaccanti"}
                cols_wl = st.columns(4)
                for idx_r, ruolo in enumerate(ruoli_wl):
                    with cols_wl[idx_r]:
                        st.markdown(f"**{ruoli_nomi_wl[ruolo]}**")
                        df_r_wl = df_wl[df_wl["Ruolo"] == ruolo].sort_values("Indice_Titolarita", ascending=False)
                        if not df_r_wl.empty:
                            for _, row_wl in df_r_wl.iterrows():
                                rdict = row_wl.to_dict()
                                rdict["Proprietario"] = idx_wl.get(str(rdict.get("Nome", "")).lower(), "Svincolato 🟢")
                                if pd.isna(rdict.get("Indice_Affare")):
                                    rdict["Indice_Affare"] = round(float(rdict.get("FantaMedia", 6.0)) / max(float(rdict.get("Quotazione", 1)), 1), 2)
                                if pd.isna(rdict.get("Indice_Titolarita")):
                                    rdict["Indice_Titolarita"] = calcola_indice_titolarita(rdict, stats_2627_wl)
                                st.html(render_card_giocatore_espandibile(rdict, stats_ps_wl, stats_2627_wl))
                        else:
                            st.caption("Nessuno")

# ============================================================
# 2. ASTA LIVE
# ============================================================
if menu == "🔨 Asta Live":
    st.header("🔨 Gestione Asta")
    st.caption("Gestisci l'asta in tempo reale: seleziona giocatore, raccogli offerte, assegna.")

    # --- SIMULAZIONE ASTA AVVERSARIA ---
    with st.expander("🔮 Simula Asta Avversaria", expanded=False):
        st.caption("Inserisci il giocatore che stanno chiamando gli altri: scopri chi può permetterselo e a quanto.")
        db_sim = st.session_state.giocatori_db
        svinc_sim = get_svincolati(db_sim)
        if not svinc_sim.empty:
            g_sim = st.selectbox("Giocatore all'asta", svinc_sim["Nome"].values, key="sim_avv_g")
            if g_sim:
                info_sim = db_sim[db_sim["Nome"] == g_sim].iloc[0]
                ruolo_sim = info_sim["Ruolo"]
                quot_sim = int(info_sim["Quotazione"])
                stats_ps_sim = st.session_state.get("stats_per_stagione", {})
                stats_2627_sim = stats_ps_sim.get("2026-27") if "2026-27" in stats_ps_sim else None
                rdict_sim = info_sim.to_dict()
                rdict_sim["Proprietario"] = "Svincolato 🟢"
                rdict_sim["Indice_Affare"] = round(float(rdict_sim.get("FantaMedia", 6.0)) / max(float(rdict_sim.get("Quotazione", 1)), 1), 2)
                rdict_sim["Indice_Titolarita"] = calcola_indice_titolarita(rdict_sim, stats_2627_sim)
                st.html(render_card_giocatore_espandibile(rdict_sim, stats_ps_sim, stats_2627_sim))
                riep_sim = get_all_riepiloghi()
                avv_data = []
                for sq_avv in NOMI_SQUADRE:
                    riep_avv = riep_sim[sq_avv]
                    mancanti_avv = riep_avv[ruolo_sim]["mancanti"]
                    off_max_avv = riep_avv[ruolo_sim]["offerta_max"]
                    crediti_avv = riep_avv["crediti"]
                    ha_gia = any(g["Nome"].lower() == g_sim.lower() for g in st.session_state.squadre[sq_avv]["rosa"])
                    if not ha_gia and mancanti_avv > 0:
                        pericolo = "🔴 ALTO" if off_max_avv >= quot_sim else ("🟠 MEDIO" if off_max_avv >= quot_sim * 0.7 else "🟢 BASSO")
                        avv_data.append({
                            "Squadra": sq_avv, "Crediti": crediti_avv,
                            f"Mancano {ruolo_sim}": mancanti_avv, "Offerta Max": off_max_avv,
                            "Pericolo": pericolo,
                            "Può Prenderlo": "✅ SÌ" if off_max_avv >= quot_sim else "❌ NO"
                        })
                if avv_data:
                    df_avv_sim = pd.DataFrame(avv_data).sort_values("Offerta Max", ascending=False)
                    st.dataframe(df_avv_sim, use_container_width=True, hide_index=True)
                    minacciose = df_avv_sim[df_avv_sim["Offerta Max"] >= quot_sim]
                    if not minacciose.empty:
                        st.error(f"⚠️ **{len(minacciose)} squadre** possono permettersi {g_sim} alla quotazione ({quot_sim}cr): {', '.join(minacciose['Squadra'].tolist())}")
                    else:
                        st.success(f"🛡️ Nessuna squadra può permettersi {g_sim} alla quotazione di listone.")
                else:
                    st.info("Nessuna squadra ha bisogno di questo ruolo.")
        else:
            st.info("Nessuno svincolato disponibile.")

    # --- ASTA RAPIDA ---
    with st.expander("📱 Modalità Asta Rapida", expanded=False):
        st.caption("Scorri automaticamente i giocatori svincolati in sequenza. Utile per le prime tornate.")
        db_rap = st.session_state.giocatori_db
        svinc_rap = get_svincolati(db_rap)
        if not svinc_rap.empty:
            # Inizializza indice se non presente
            if "asta_rapida_idx" not in st.session_state:
                st.session_state.asta_rapida_idx = 0
            if "asta_rapida_filtro_ruolo" not in st.session_state:
                st.session_state.asta_rapida_filtro_ruolo = "Tutti"

            filtro_rap = st.selectbox("Filtra per ruolo", ["Tutti", "P", "D", "C", "A"], key="rap_filtro")
            if filtro_rap != st.session_state.asta_rapida_filtro_ruolo:
                st.session_state.asta_rapida_filtro_ruolo = filtro_rap
                st.session_state.asta_rapida_idx = 0
                st.rerun()

            if filtro_rap != "Tutti":
                svinc_rap = svinc_rap[svinc_rap["Ruolo"] == filtro_rap]

            if not svinc_rap.empty:
                idx = st.session_state.asta_rapida_idx % len(svinc_rap)
                g_rap = svinc_rap.iloc[idx]
                nome_rap = g_rap["Nome"]

                stats_ps_rap = st.session_state.get("stats_per_stagione", {})
                stats_2627_rap = stats_ps_rap.get("2026-27") if "2026-27" in stats_ps_rap else None
                rdict_rap = g_rap.to_dict()
                rdict_rap["Proprietario"] = "Svincolato 🟢"
                rdict_rap["Indice_Affare"] = round(float(rdict_rap.get("FantaMedia", 6.0)) / max(float(rdict_rap.get("Quotazione", 1)), 1), 2)
                rdict_rap["Indice_Titolarita"] = calcola_indice_titolarita(rdict_rap, stats_2627_rap)
                st.html(render_card_giocatore_espandibile(rdict_rap, stats_ps_rap, stats_2627_rap))

                # Prezzo consigliato
                stats_df_rap = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                pc_rap, _ = calcola_prezzo_consigliato(g_rap.to_dict(), stats_df_rap)
                st.info(f"💡 Prezzo consigliato: **{pc_rap}cr**")

                # Bottoni navigazione
                c_nav1, c_nav2, c_nav3 = st.columns(3)
                with c_nav1:
                    if st.button("⏮️ Precedente", use_container_width=True):
                        st.session_state.asta_rapida_idx = max(0, idx - 1)
                        st.rerun()
                with c_nav2:
                    if st.button("▶️ Prossimo", type="primary", use_container_width=True):
                        st.session_state.asta_rapida_idx = idx + 1
                        st.rerun()
                with c_nav3:
                    if st.button("🎯 Assegna da qui", use_container_width=True):
                        st.session_state["asta_giocatore_corrente"] = nome_rap
                        st.session_state.asta_rapida_idx = idx
                        st.toast(f"🎯 {nome_rap} selezionato per l'asta! Scorri sopra per assegnarlo.")
                        st.rerun()

                st.progress((idx + 1) / len(svinc_rap), text=f"Giocatore {idx + 1} di {len(svinc_rap)}")
            else:
                st.info("Nessun giocatore svincolato per questo ruolo.")
        else:
            st.success("🎉 Tutti i giocatori sono stati assegnati!")

    # --- TIMER ASTA ---
    with st.expander("⏱️ Timer Asta", expanded=False):
        t1, t2, t3 = st.columns(3)
        with t1:
            durata_timer = st.number_input("Durata offerta (sec)", min_value=5, max_value=300, value=30, step=5, key="timer_durata")
        with t2:
            if st.button("▶️ Avvia Timer", use_container_width=True):
                st.session_state.asta_timer_end = datetime.now().timestamp() + durata_timer
                st.session_state.asta_timer_active = True
                st.rerun()
        with t3:
            if st.button("⏹️ Stop", use_container_width=True):
                st.session_state.asta_timer_active = False
                if "asta_timer_end" in st.session_state:
                    del st.session_state.asta_timer_end
                st.rerun()

        if st.session_state.get("asta_timer_active") and "asta_timer_end" in st.session_state:
            rimanente = max(0, int(st.session_state.asta_timer_end - datetime.now().timestamp()))
            progresso = 1 - (rimanente / durata_timer)
            colore_timer = "#00d26a" if rimanente > 10 else "#eab308" if rimanente > 5 else "#ef4444"
            st.markdown(
                f"<div style='text-align:center;'><div style='font-size:3em;font-weight:bold;color:{colore_timer};'>{rimanente}s</div>"
                f"<div style='background:#2a2a4a;border-radius:8px;height:12px;overflow:hidden;'>"
                f"<div style='width:{progresso*100}%;background:{colore_timer};height:100%;transition:width 1s;'></div></div></div>",
                unsafe_allow_html=True
            )
            if rimanente <= 0:
                st.session_state.asta_timer_active = False
                st.toast("⏰ TEMPO SCADUTO!", icon="⏰")
            else:
                st.rerun()

    # --- WATCHLIST ALERT ---
    if st.session_state.watchlist:
        db = st.session_state.giocatori_db
        svinc = get_svincolati(db)
        wl_in_asta = [g for g in st.session_state.watchlist if g in svinc["Nome"].values]
        if wl_in_asta:
            st.info(f"🔔 **Watchlist Alert**: {len(wl_in_asta)} giocatori della tua watchlist sono ancora liberi: {', '.join(wl_in_asta[:5])}{'...' if len(wl_in_asta) > 5 else ''}")

    db = st.session_state.giocatori_db
    if db.empty:
        st.warning("Importa prima un listone.")
    else:
        svinc = get_svincolati(db).copy()

        if svinc.empty:
            st.success("🎉 Tutti i giocatori sono stati assegnati!")
        else:
            st.subheader("🎯 Giocatore all'Asta")
            col1, col2 = st.columns([3, 1])
            with col1:
                modo = st.radio("Modalità", ["Seleziona Manualmente", "Estrazione Casuale"], horizontal=True, key="asta_modo")
                if modo == "Seleziona Manualmente":
                    g_asta = st.selectbox("Giocatore", svinc["Nome"].values, key="asta_sel")
                else:
                    if st.button("🎲 Estrai Casuale", use_container_width=True):
                        g_asta = random.choice(svinc["Nome"].values)
                        st.session_state["asta_giocatore_corrente"] = g_asta
                        st.rerun()
                    g_asta = st.session_state.get("asta_giocatore_corrente", svinc["Nome"].values[0] if len(svinc) > 0 else None)

            if g_asta:
                info = svinc[svinc["Nome"] == g_asta].iloc[0]
                with col2:
                    st.markdown(
                        f"<div style='background:#1a1a2e;padding:12px;border-radius:8px;text-align:center;'>"
                        f"<div style='font-size:0.85em;color:#aaa;'>QUOTAZIONE</div>"
                        f"<div style='font-size:2em;font-weight:bold;color:#00d26a;'>{int(info['Quotazione'])}cr</div>"
                        f"<div style='font-size:0.8em;color:#888;'>{info['Ruolo']} | {info['Squadra_SerieA']}</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )

                stats_ps_ast = st.session_state.get("stats_per_stagione", {})
                stats_2627_ast = stats_ps_ast.get("2026-27") if "2026-27" in stats_ps_ast else None
                rdict_ast = info.to_dict()
                rdict_ast["Proprietario"] = "Svincolato 🟢"
                rdict_ast["Indice_Affare"] = round(float(rdict_ast.get("FantaMedia", 6.0)) / max(float(rdict_ast.get("Quotazione", 1)), 1), 2)
                rdict_ast["Indice_Titolarita"] = calcola_indice_titolarita(rdict_ast, stats_2627_ast)
                st.html(render_card_giocatore_espandibile(rdict_ast, stats_ps_ast, stats_2627_ast))

                stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                pc_ai, spiegazione = calcola_prezzo_consigliato(info.to_dict(), stats_df)
                col_ai, col_spieg = st.columns([1, 2])
                with col_ai:
                    st.metric("💡 Prezzo AI", f"{pc_ai}cr")
                with col_spieg:
                    with st.expander("🧠 Spiegazione prezzo"):
                        st.markdown(spiegazione)

                st.markdown("---")
                st.subheader("💰 Offerte")
                st.caption("Inserisci l'offerta di ciascuna squadra. Il sistema evidenzia chi può permetterselo.")

                # --- SUGGERIMENTO SMART ---
                ruolo_g = info["Ruolo"]
                quot_g = int(info["Quotazione"])
                riepiloghi = get_all_riepiloghi()

                # Calcola offerta smart: media tra prezzo AI e offerta max del ruolo, con margine
                offerte_smart = {}
                for sq in NOMI_SQUADRE:
                    riep_sq = riepiloghi[sq]
                    off_max = riep_sq[ruolo_g]["offerta_max"]
                    mancanti = riep_sq[ruolo_g]["mancanti"]
                    ha_gia = any(g["Nome"].lower() == g_asta.lower() for g in st.session_state.squadre[sq]["rosa"])
                    if not ha_gia and mancanti_avv > 0:
                        # Formula smart: min(pc_ai*1.1, off_max*0.9, crediti_sq)
                        sug = min(int(pc_ai * 1.05), int(off_max * 0.95), st.session_state.squadre[sq]["crediti"])
                        offerte_smart[sq] = max(1, sug)
                    else:
                        offerte_smart[sq] = 0

                offerte = {}
                with st.form("offerte_asta"):
                    cols_off = st.columns(5)
                    for idx_sq, sq in enumerate(NOMI_SQUADRE):
                        with cols_off[idx_sq % 5]:
                            riep_sq = riepiloghi[sq]
                            off_max = riep_sq[ruolo_g]["offerta_max"]
                            crediti_sq = riep_sq["crediti"]
                            ha_gia = any(g["Nome"].lower() == g_asta.lower() for g in st.session_state.squadre[sq]["rosa"])
                            st.markdown(f"**{sq}**")
                            st.caption(f"💰 {crediti_sq}cr | Max: {off_max}cr")
                            if ha_gia:
                                st.warning("Già in rosa")
                                offerte[sq] = 0
                            else:
                                sug_val = offerte_smart.get(sq, 0)
                                if sug_val > 0:
                                    st.caption(f"💡 Suggerito: {sug_val}cr")
                                offerte[sq] = st.number_input(
                                    f"Offerta {sq}", min_value=0, max_value=crediti_sq,
                                    value=sug_val,
                                    step=1, key=f"off_{sq}"
                                )
                    submitted = st.form_submit_button("📊 Calcola Vincitore", use_container_width=True)

                if submitted:
                    offerte_valide = {k: v for k, v in offerte.items() if v > 0}
                    if offerte_valide:
                        vincitore = max(offerte_valide, key=offerte_valide.get)
                        prezzo_vincita = offerte_valide[vincitore]
                        st.success(f"🏆 Miglior offerente: **{vincitore}** con **{prezzo_vincita}cr**")

                        if st.button("✅ Assegna Giocatore", type="primary", use_container_width=True):
                            if st.session_state.squadre[vincitore]["crediti"] >= prezzo_vincita:
                                StateManager.snapshot()
                                st.session_state.squadre[vincitore]["crediti"] -= prezzo_vincita
                                scad_acq = ANNO_CORRENTE + CONTRATTO_ANNI
                                st.session_state.squadre[vincitore]["rosa"].append({
                                    "Nome": g_asta, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                                    "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                                    "Costo_Acquisto": prezzo_vincita, "Scadenza_Anno": scad_acq
                                })
                                st.session_state.contratti[g_asta] = {"squadra": vincitore, "scadenza_anno": scad_acq}
                                st.session_state.storico_mercato.insert(0, {
                                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                    "Operazione": "ASTA",
                                    "Dettagli": f"{vincitore} aggiudica {g_asta} ({info['Ruolo']}) per {prezzo_vincita}cr — Contratto fino al {scad_acq}"
                                })
                                if "asta_giocatore_corrente" in st.session_state:
                                    del st.session_state["asta_giocatore_corrente"]
                                invalidate_cache()
                                save_state()
                                st.balloons()
                                st.success(f"🎉 {g_asta} assegnato a {vincitore} per {prezzo_vincita}cr!")
                                st.rerun()
                            else:
                                st.error("Crediti insufficienti!")
                    else:
                        st.info("Nessuna offerta valida inserita.")

# ============================================================
# 3. MERCATO (Acquisti/Vendite/Rinnovi)
# ============================================================
if menu == "🛒 Mercato":
    st.header("🛒 Gestione Mercato")
    t_acq, t_vend, t_rinn, t_reg = st.tabs(["📥 Acquista", "📤 Vendi/Svincola", "🔄 Rinnova Contratto", "📜 Registro"])

    with t_acq:
        st.subheader("Acquista giocatore svincolato")
        sq = st.selectbox("Squadra acquirente", NOMI_SQUADRE, key="acq_sq")
        cred = st.session_state.squadre[sq]["crediti"]
        rosa_len = len(st.session_state.squadre[sq]["rosa"])
        c1, c2 = st.columns(2)
        c1.metric("Crediti", f"{cred} 🪙")
        c2.metric("Rosa", f"{rosa_len}")

        db = st.session_state.giocatori_db
        if db.empty:
            st.warning("Importa prima un listone.")
        else:
            svinc = get_svincolati(db)
            if len(svinc) > 0:
                g_sel = st.selectbox("Giocatore", svinc["Nome"].values)
                info = svinc[svinc["Nome"] == g_sel].iloc[0]

                st.markdown("---")
                col_info, col_prezzo = st.columns([2, 1])
                stats_2627_row = None
                if "stats_per_stagione" in st.session_state and "2026-27" in st.session_state.stats_per_stagione:
                    s2627 = st.session_state.stats_per_stagione["2026-27"]
                    if not s2627.empty and "Nome" in s2627.columns:
                        match_2627 = s2627[s2627["Nome"].str.lower() == g_sel.lower()]
                        if match_2627.empty:
                            nm_f = fuzzy_match(g_sel, s2627["Nome"].tolist())
                            if nm_f:
                                match_2627 = s2627[s2627["Nome"] == nm_f]
                        if not match_2627.empty:
                            stats_2627_row = match_2627.iloc[0]

                with col_info:
                    st.markdown(f"**{g_sel}** — {info['Ruolo']} | {info['Squadra_SerieA']}")
                    fm_display = f"**{info['FantaMedia']}**"
                    if stats_2627_row is not None and "FantaMedia" in stats_2627_row and pd.notna(stats_2627_row["FantaMedia"]):
                        fm_display += f" <span style='color:#00d26a;'>(📊 2026/27: {stats_2627_row['FantaMedia']})</span>"
                    st.markdown(f"Quotazione listone: **{int(info['Quotazione'])}cr** | FantaMedia: {fm_display} | Fascia: **{info.get('Consiglio','')}**", unsafe_allow_html=True)
                    if stats_2627_row is not None:
                        extra_stats = []
                        for col in ["Gol", "Assist", "Partite", "Rigori"]:
                            if col in stats_2627_row and pd.notna(stats_2627_row[col]):
                                extra_stats.append(f"{col}: **{stats_2627_row[col]}**")
                        if extra_stats:
                            st.caption("📊 Stagione 2026/27 — " + " | ".join(extra_stats))

                stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
                pc_ai, spiegazione = calcola_prezzo_consigliato(info.to_dict(), stats_df)
                with col_prezzo:
                    st.markdown(
                        f"<div style='background:#1a1a2e;padding:12px;border-radius:8px;text-align:center;'>"
                        f"<div style='font-size:0.85em;color:#aaa;'>💡 PREZZO CONSIGLIATO</div>"
                        f"<div style='font-size:1.8em;font-weight:bold;color:#00d26a;'>{pc_ai}cr</div>"
                        f"</div>",
                        unsafe_allow_html=True
                    )
                with st.expander("🧠 Come è calcolato il prezzo consigliato?"):
                    st.markdown(spiegazione)

                stats_g = mostra_statistiche_giocatore(g_sel, stats_df)
                if stats_g is not None:
                    with st.expander("📊 Statistiche Storiche"):
                        st.dataframe(stats_g, use_container_width=True)
                        numeric_cols = stats_g.select_dtypes(include=['number']).columns.tolist()
                        numeric_cols = [c for c in numeric_cols if c not in ['Stagione']]
                        if numeric_cols and "Stagione" in stats_g.columns:
                            st.line_chart(stats_g.set_index("Stagione")[numeric_cols])
                else:
                    st.caption("📭 Nessuna statistica storica caricata.")

                st.markdown("---")
                pc_manuale = info.get('Prezzo_Consigliato')
                if pd.notna(pc_manuale):
                    default_price = int(pc_manuale)
                    st.caption(f"💾 Prezzo consigliato salvato manualmente: {default_price}cr")
                else:
                    default_price = pc_ai

                prezzo = st.number_input("Prezzo da pagare all'asta", min_value=1, max_value=max(1,cred), value=default_price, key="acq_p")

                riep_sq = riepilogo_rosa(sq)
                ruolo_sel = info["Ruolo"]
                mancanti_ruolo = riep_sq[ruolo_sel]["mancanti"]
                off_max_ruolo = riep_sq[ruolo_sel]["offerta_max"]
                tot_mancanti = riep_sq["tot_mancanti"]

                st.markdown("---")
                st.subheader("🎯 Offerta Massima per questo Ruolo")
                c1_off, c2_off, c3_off = st.columns(3)
                with c1_off:
                    st.metric(f"Mancano {ruolo_sel}", f"{mancanti_ruolo}")
                with c2_off:
                    st.metric("Posti liberi totali", f"{tot_mancanti}")
                with c3_off:
                    st.metric("Offerta max sicura", f"{off_max_ruolo}cr")

                if prezzo > off_max_ruolo:
                    st.warning(f"⚠️ Stai offrendo **{prezzo}cr** che supera l'offerta max consigliata di **{off_max_ruolo}cr** per il ruolo {ruolo_sel}.")
                elif prezzo > int(pc_ai * 1.3):
                    st.info(f"ℹ️ Offerta superiore del 30% al prezzo consigliato.")

                st.markdown("---")
                st.subheader("🎭 Cosa Possono Offrire gli Avversari?")
                avversari = []
                riepiloghi = get_all_riepiloghi()
                for sq_avv in NOMI_SQUADRE:
                    if sq_avv == sq:
                        continue
                    riep_avv = riepiloghi[sq_avv]
                    mancanti_avv = riep_avv[ruolo_sel]["mancanti"]
                    off_max_avv = riep_avv[ruolo_sel]["offerta_max"]
                    crediti_avv = riep_avv["crediti"]
                    tot_avv = riep_avv["tot_posseduti"]
                    avversari.append({
                        "Squadra": sq_avv, "Crediti": crediti_avv, "Rosa": tot_avv,
                        f"Mancano {ruolo_sel}": mancanti_avv, "Offerta Max": off_max_avv,
                        "Pericolo": "🔴 ALTO" if off_max_avv >= prezzo else ("🟠 MEDIO" if off_max_avv >= prezzo * 0.7 else "🟢 BASSO")
                    })
                df_avv = pd.DataFrame(avversari).sort_values("Offerta Max", ascending=False)
                st.dataframe(df_avv, use_container_width=True, hide_index=True)

                minacci = df_avv[df_avv["Offerta Max"] >= prezzo]
                if not minacci.empty:
                    st.warning(f"⚠️ **{len(minacci)} squadre** possono offrire uguale o più di te ({prezzo}cr) per questo {ruolo_sel}: {', '.join(minacci['Squadra'].tolist())}")
                else:
                    st.success(f"✅ Sei il più alto offerente! Nessuno può superare i tuoi {prezzo}cr per un {ruolo_sel}.")

                if st.button("Conferma Acquisto", type="primary"):
                    if cred >= prezzo:
                        StateManager.snapshot()
                        st.session_state.squadre[sq]["crediti"] -= prezzo
                        scad_acq = ANNO_CORRENTE + CONTRATTO_ANNI
                        st.session_state.squadre[sq]["rosa"].append({
                            "Nome": g_sel, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                            "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                            "Costo_Acquisto": prezzo, "Scadenza_Anno": scad_acq
                        })
                        st.session_state.contratti[g_sel] = {"squadra": sq, "scadenza_anno": scad_acq}
                        st.session_state.storico_mercato.insert(0, {
                            "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "Operazione": "ACQUISTO",
                            "Dettagli": f"{sq} acquista {g_sel} ({info['Ruolo']}) per {prezzo}cr — Contratto fino al {scad_acq}"
                        })
                        invalidate_cache()
                        save_state()
                        st.success(f"✅ {g_sel} acquistato! Contratto 3 anni (fino al {ANNO_CORRENTE+CONTRATTO_ANNI}).")
                        st.rerun()
                    else:
                        st.error("Crediti insufficienti!")
            else:
                st.warning("Nessuno svincolato disponibile.")

    with t_vend:
        st.subheader("Vendi / Svincola giocatore")
        sq_v = st.selectbox("Squadra", NOMI_SQUADRE, key="vend_sq")
        rosa = st.session_state.squadre[sq_v]["rosa"]
        rosa_proprieta_list = [g for g in rosa if g.get("Prestito_Da") is None or g.get("Prestito_Da") == sq_v]
        if rosa_proprieta_list:
            nomi = [g["Nome"] for g in rosa_proprieta_list]
            g_v = st.selectbox("Giocatore", nomi, key="vend_g")
            g_obj = next(g for g in rosa_proprieta_list if g["Nome"] == g_v)

            db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].str.lower() == g_v.lower()]
            if not db_match.empty:
                prezzo_listone = int(db_match.iloc[0]["Quotazione"])
                st.info(f"💡 Quotazione attuale listone 2026/27: **{prezzo_listone}cr** (valore di rimborso)")
            else:
                q25_match = None
                if not st.session_state.quotazioni_2025_26.empty and "Nome" in st.session_state.quotazioni_2025_26.columns:
                    q25_match = st.session_state.quotazioni_2025_26[
                        st.session_state.quotazioni_2025_26["Nome"].str.lower() == g_v.lower()
                    ]
                if q25_match is not None and not q25_match.empty:
                    prezzo_listone = int(q25_match.iloc[0]["Quotazione_2025_26"])
                    st.info(f"💡 Giocatore non nel listone 2026/27. Rimborso da quotazioni 2025/26: **{prezzo_listone}cr**")
                else:
                    prezzo_listone = g_obj.get("Costo_Acquisto", 10)
                    st.info(f"💡 Rimborso al costo d'acquisto: **{prezzo_listone}cr**")

            prezzo_v = st.number_input("Prezzo rimborso (modificabile)", min_value=0, value=prezzo_listone, key="vend_p")

            if st.button("Conferma Vendita"):
                StateManager.snapshot()
                st.session_state.squadre[sq_v]["rosa"] = [g for g in rosa if g["Nome"] != g_v]
                st.session_state.squadre[sq_v]["crediti"] += prezzo_v
                if g_v in st.session_state.contratti:
                    del st.session_state.contratti[g_v]
                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "SVINCOLO",
                    "Dettagli": f"{sq_v} svincola {g_v}, incassa {prezzo_v}cr"
                })
                invalidate_cache()
                save_state()
                st.success(f"🗑️ {g_v} svincolato! Incassati {prezzo_v}cr.")
                st.rerun()
        else:
            st.info("Nessun giocatore di proprietà nella rosa.")

    with t_rinn:
        st.subheader("🔄 Rinnova Contratto")
        st.info("Il rinnovo estende il contratto a 3 anni dalla data attuale e aggiorna il costo alla quotazione di listone corrente.")
        sq_r = st.selectbox("Squadra", NOMI_SQUADRE, key="rinn_sq")
        rosa_r = st.session_state.squadre[sq_r]["rosa"]
        rosa_rinnovabili = [g for g in rosa_r if g.get("Prestito_Da") is None or g.get("Prestito_Da") == sq_r]
        if rosa_rinnovabili:
            nomi_r = [g["Nome"] for g in rosa_rinnovabili]
            g_r = st.selectbox("Giocatore da rinnovare", nomi_r, key="rinn_g")
            g_obj_r = next(g for g in rosa_rinnovabili if g["Nome"] == g_r)

            scad_attuale = g_obj_r.get("Scadenza_Anno", ANNO_CORRENTE + CONTRATTO_ANNI)
            costo_attuale = g_obj_r.get("Costo_Acquisto", 0)

            quot_attuale = get_quotazione_listone(g_r)
            if quot_attuale is None:
                quot_attuale = costo_attuale
                st.warning("Giocatore non trovato nel listone attuale. Usato costo d'acquisto come fallback.")

            nuova_scadenza = datetime.now().year + CONTRATTO_ANNI
            nuovo_mese = datetime.now().month
            costo_rinnovo = quot_attuale

            col1, col2, col3 = st.columns(3)
            col1.metric("Scadenza attuale", scad_attuale)
            col2.metric("Nuova scadenza", f"{nuovo_mese:02d}/{nuova_scadenza}")
            col3.metric("Costo rinnovo", f"{costo_rinnovo}cr")

            st.caption(f"Costo precedente: {costo_attuale}cr | Differenza da pagare: {max(0, costo_rinnovo - costo_attuale)}cr")

            crediti_disp = st.session_state.squadre[sq_r]["crediti"]
            if crediti_disp < costo_rinnovo:
                st.error(f"❌ Crediti insufficienti! Hai {crediti_disp}cr, servono {costo_rinnovo}cr.")
            else:
                if st.button("📝 Conferma Rinnovo", type="primary"):
                    StateManager.snapshot()
                    st.session_state.squadre[sq_r]["crediti"] -= costo_rinnovo
                    for g in st.session_state.squadre[sq_r]["rosa"]:
                        if g["Nome"] == g_r:
                            g["Scadenza_Anno"] = nuova_scadenza
                            g["Scadenza_Mese"] = nuovo_mese
                            g["Costo_Acquisto"] = costo_rinnovo
                            break
                    st.session_state.contratti[g_r] = {"squadra": sq_r, "scadenza_anno": nuova_scadenza, "scadenza_mese": nuovo_mese}
                    st.session_state.storico_mercato.insert(0, {
                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "Operazione": "RINNOVO",
                        "Dettagli": f"{sq_r} rinnova {g_r} fino al {nuovo_mese:02d}/{nuova_scadenza} per {costo_rinnovo}cr (quotazione listone)"
                    })
                    invalidate_cache()
                    save_state()
                    st.success(f"✅ Contratto di {g_r} rinnovato fino al {nuova_scadenza} al costo di {costo_rinnovo}cr!")
                    st.rerun()
        else:
            st.info("Nessun giocatore rinnovabile in rosa.")

    with t_reg:
        st.subheader("📜 Storico Operazioni")
        if st.session_state.storico_mercato:
            st.dataframe(pd.DataFrame(st.session_state.storico_mercato), use_container_width=True)
            if st.button("🗑️ Svuota registro"):
                st.session_state.storico_mercato = []
                save_state()
                st.rerun()
        else:
            st.info("Nessuna operazione.")

# ============================================================
# 4. SCAMBI & PRESTITI
# ============================================================
if menu == "🤝 Scambi & Prestiti":
    st.header("🤝 Scambi Definitivi & Prestiti")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Squadra A")
        sq1 = st.selectbox("Squadra 1", NOMI_SQUADRE, key="sc1")
        rosa1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g.get("Prestito_Da") is None or g.get("Prestito_Da") == sq1]
        g1 = st.multiselect("Cede giocatori", [g["Nome"] for g in rosa1], key="g1")
        d1 = st.number_input(f"Conguaglio da {sq1}", min_value=0, max_value=st.session_state.squadre[sq1]["crediti"], value=0, key="d1")
    with c2:
        st.subheader("Squadra B")
        sq2 = st.selectbox("Squadra 2", [s for s in NOMI_SQUADRE if s != sq1], key="sc2")
        rosa2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g.get("Prestito_Da") is None or g.get("Prestito_Da") == sq2]
        g2 = st.multiselect("Cede giocatori", [g["Nome"] for g in rosa2], key="g2")
        d2 = st.number_input(f"Conguaglio da {sq2}", min_value=0, max_value=st.session_state.squadre[sq2]["crediti"], value=0, key="d2")

    tipo = st.radio("Tipo operazione", ["Scambio Definitivo", "Prestito 6 mesi", "Prestito 1 anno"], horizontal=True)

    if st.button("Finalizza", type="primary"):
        if not g1 and not g2 and d1 == 0 and d2 == 0:
            st.warning("Seleziona qualcosa.")
        elif st.session_state.squadre[sq1]["crediti"] < d1:
            st.error(f"{sq1} non ha abbastanza crediti.")
        elif st.session_state.squadre[sq2]["crediti"] < d2:
            st.error(f"{sq2} non ha abbastanza crediti.")
        else:
            StateManager.snapshot()
            st.session_state.squadre[sq1]["crediti"] = st.session_state.squadre[sq1]["crediti"] - d1 + d2
            st.session_state.squadre[sq2]["crediti"] = st.session_state.squadre[sq2]["crediti"] - d2 + d1

            oggetti1 = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] in g1]
            st.session_state.squadre[sq1]["rosa"] = [g for g in st.session_state.squadre[sq1]["rosa"] if g["Nome"] not in g1]
            oggetti2 = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] in g2]
            st.session_state.squadre[sq2]["rosa"] = [g for g in st.session_state.squadre[sq2]["rosa"] if g["Nome"] not in g2]

            if tipo == "Scambio Definitivo":
                st.session_state.squadre[sq1]["rosa"].extend(oggetti2)
                st.session_state.squadre[sq2]["rosa"].extend(oggetti1)
                for g in oggetti2:
                    st.session_state.contratti[g["Nome"]] = {"squadra": sq1, "scadenza_anno": ANNO_CORRENTE + CONTRATTO_ANNI}
                for g in oggetti1:
                    st.session_state.contratti[g["Nome"]] = {"squadra": sq2, "scadenza_anno": ANNO_CORRENTE + CONTRATTO_ANNI}
                msg = f"Scambio definitivo: {sq1} ↔ {sq2}"
                st.success(f"🎉 {msg}")
            else:
                durata = 6 if tipo == "Prestito 6 mesi" else 12
                for g in oggetti2:
                    g_p = g.copy()
                    g_p["Prestito_Da"] = sq2
                    g_p["Prestito_A"] = sq1
                    g_p["Prestito_Durata_Mesi"] = durata
                    g_p["Prestito_Anno_Inizio"] = ANNO_CORRENTE
                    st.session_state.squadre[sq1]["rosa"].append(g_p)
                    st.session_state.prestiti.append({
                        "Giocatore": g["Nome"], "Da": sq2, "A": sq1,
                        "Durata_Mesi": durata, "Anno_Inizio": ANNO_CORRENTE, "Denaro": d2 - d1
                    })
                for g in oggetti1:
                    g_p = g.copy()
                    g_p["Prestito_Da"] = sq1
                    g_p["Prestito_A"] = sq2
                    g_p["Prestito_Durata_Mesi"] = durata
                    g_p["Prestito_Anno_Inizio"] = ANNO_CORRENTE
                    st.session_state.squadre[sq2]["rosa"].append(g_p)
                    st.session_state.prestiti.append({
                        "Giocatore": g["Nome"], "Da": sq1, "A": sq2,
                        "Durata_Mesi": durata, "Anno_Inizio": ANNO_CORRENTE, "Denaro": d1 - d2
                    })
                msg = f"Prestito ({durata} mesi): {sq1} ↔ {sq2}"
                st.success(f"🤝 {msg}")

            st.session_state.storico_mercato.insert(0, {
                "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "Operazione": tipo.upper(),
                "Dettagli": msg + (f" | Conguaglio: {d1}cr vs {d2}cr" if d1 or d2 else "")
            })
            invalidate_cache()
            save_state()
            st.rerun()

    if st.session_state.prestiti:
        st.markdown("---")
        st.subheader("📋 Prestiti Attivi")
        df_prest = pd.DataFrame(st.session_state.prestiti)
        st.dataframe(df_prest, use_container_width=True)

        st.subheader("Termina prestito")
        nomi_prestito = list(df_prest["Giocatore"].unique())
        gp = st.selectbox("Seleziona giocatore", nomi_prestito, key="term_p")
        if st.button("Termina prestito e riporta in rosa originale"):
            to_remove = None
            for i, p in enumerate(st.session_state.prestiti):
                if p["Giocatore"] == gp:
                    to_remove = i
                    da_sq = p["Da"]
                    a_sq = p["A"]
                    st.session_state.squadre[a_sq]["rosa"] = [
                        g for g in st.session_state.squadre[a_sq]["rosa"]
                        if not (g.get("Nome") == gp and g.get("Prestito_Da") == da_sq)
                    ]
                    g_orig = None
                    for g in st.session_state.squadre[da_sq]["rosa"]:
                        if g["Nome"] == gp and (g.get("Prestito_Da") is None or g.get("Prestito_Da") == da_sq):
                            g_orig = g
                            break
                    if not g_orig:
                        db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"] == gp]
                        if not db_match.empty:
                            info = db_match.iloc[0]
                            g_orig = {
                                "Nome": gp, "Ruolo": info["Ruolo"], "Squadra_SerieA": info["Squadra_SerieA"],
                                "Quotazione": int(info["Quotazione"]), "FantaMedia": float(info["FantaMedia"]),
                                "Costo_Acquisto": 0, "Scadenza_Anno": ANNO_CORRENTE + CONTRATTO_ANNI
                            }
                        else:
                            g_orig = {"Nome": gp, "Ruolo": "C", "Squadra_SerieA": "N/D", "Quotazione": 1, "FantaMedia": 6.0, "Costo_Acquisto": 0, "Scadenza_Anno": ANNO_CORRENTE + CONTRATTO_ANNI}
                        st.session_state.squadre[da_sq]["rosa"].append(g_orig)
                    break
            if to_remove is not None:
                st.session_state.prestiti.pop(to_remove)
                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "FINE PRESTITO",
                    "Dettagli": f"{gp} torna a {da_sq}"
                })
                invalidate_cache()
                save_state()
                st.success(f"✅ {gp} rientrato da prestito!")
                st.rerun()

# ============================================================
# 5. ROSE, CREDITI & CONTRATTI
# ============================================================
if menu == "📋 Rose & Contratti":
    st.header("📋 Riepilogo Rose, Crediti & Contratti")

    tab_singole, tab_matrice, tab_contratti, tab_consigli, tab_formazione = st.tabs(
        ["🛡️ Squadre", "📊 Matrice", "📄 Contratti", "💡 Consigli 2026/27", "🎮 Simula Formazione"]
    )

    with tab_singole:
        tabs = st.tabs(NOMI_SQUADRE)
        for i, sq in enumerate(NOMI_SQUADRE):
            with tabs[i]:
                dati = st.session_state.squadre[sq]
                c1, c2 = st.columns([3, 1])
                with c1:
                    st.subheader(f"🛡️ {sq}")
                with c2:
                    st.metric("Crediti", f"{dati['crediti']} 🪙")

                rosa_df = pd.DataFrame(dati["rosa"])
                if not rosa_df.empty:
                    conti = rosa_df["Ruolo"].value_counts().to_dict()
                    st.caption(f"P: {conti.get('P',0)} | D: {conti.get('D',0)} | C: {conti.get('C',0)} | A: {conti.get('A',0)} | Tot: {len(rosa_df)}")

                    # --- ORDINAMENTO MANUALE ---
                    c_ord1, c_ord2 = st.columns([2, 1])
                    with c_ord1:
                        ordine = st.selectbox(
                            "📋 Ordina per",
                            ["Ruolo → FantaMedia ↓", "Ruolo → Costo ↓", "Ruolo → Nome", "FantaMedia ↓", "Costo ↓", "Nome", "Scadenza", "Inserimento (default)"],
                            index=0,
                            key=f"ordine_{sq}"
                        )
                    with c_ord2:
                        if ordine.startswith("Ruolo"):
                            ordine_ruoli = st.selectbox(
                                "Ordine ruoli",
                                ["P → D → C → A", "A → C → D → P", "D → C → A → P"],
                                index=0,
                                key=f"ord_ruoli_{sq}"
                            )

                    # Applica ordinamento
                    if ordine == "Ruolo → FantaMedia ↓":
                        rosa_df = rosa_df.sort_values(["Ruolo", "FantaMedia"], ascending=[True, False])
                    elif ordine == "Ruolo → Costo ↓":
                        rosa_df = rosa_df.sort_values(["Ruolo", "Costo_Acquisto"], ascending=[True, False])
                    elif ordine == "Ruolo → Nome":
                        rosa_df = rosa_df.sort_values(["Ruolo", "Nome"], ascending=[True, True])
                    elif ordine == "FantaMedia ↓":
                        rosa_df = rosa_df.sort_values("FantaMedia", ascending=False)
                    elif ordine == "Costo ↓":
                        rosa_df = rosa_df.sort_values("Costo_Acquisto", ascending=False)
                    elif ordine == "Nome":
                        rosa_df = rosa_df.sort_values("Nome", ascending=True)
                    elif ordine == "Scadenza":
                        rosa_df["_scad_temp"] = rosa_df.get("Scadenza_Anno", ANNO_CORRENTE + CONTRATTO_ANNI)
                        rosa_df = rosa_df.sort_values("_scad_temp", ascending=True)
                        rosa_df = rosa_df.drop(columns=["_scad_temp"], errors="ignore")
                    # "Inserimento (default)" → lascia l'ordine originale

                    # Se ordinamento per ruolo con ordine custom dei ruoli
                    if ordine.startswith("Ruolo") and 'ordine_ruoli' in locals():
                        mappa_ordine = {
                            "P → D → C → A": {"P": 0, "D": 1, "C": 2, "A": 3},
                            "A → C → D → P": {"P": 3, "D": 2, "C": 1, "A": 0},
                            "D → C → A → P": {"P": 3, "D": 0, "C": 1, "A": 2},
                        }
                        ord_map = mappa_ordine.get(ordine_ruoli, {"P": 0, "D": 1, "C": 2, "A": 3})
                        rosa_df["_ruolo_ord"] = rosa_df["Ruolo"].map(ord_map)
                        # Ri-ordina mantenendo il secondo criterio
                        if "FantaMedia" in ordine:
                            rosa_df = rosa_df.sort_values(["_ruolo_ord", "FantaMedia"], ascending=[True, False])
                        elif "Costo" in ordine:
                            rosa_df = rosa_df.sort_values(["_ruolo_ord", "Costo_Acquisto"], ascending=[True, False])
                        else:
                            rosa_df = rosa_df.sort_values(["_ruolo_ord", "Nome"], ascending=[True, True])
                        rosa_df = rosa_df.drop(columns=["_ruolo_ord"], errors="ignore")

                    display = rosa_df.copy()

                    # --- FIX FANTAMEDIA: arricchisci con stats 2026/27 ---
                    def _enrich_fm(row):
                        nome = row.get("Nome", "")
                        fm_db = row.get("FantaMedia", 6.0)
                        fm_2627 = _get_fm_2627(nome)
                        if fm_2627 is not None:
                            return fm_2627
                        # Cerca nelle stats storiche aggregate
                        if not st.session_state.stats_storiche.empty and "Nome" in st.session_state.stats_storiche.columns:
                            stats_all = st.session_state.stats_storiche
                            match = stats_all[stats_all["Nome"].str.lower() == nome.lower()]
                            if match.empty:
                                close = difflib.get_close_matches(nome.lower(), [n.lower() for n in stats_all["Nome"].tolist()], n=1, cutoff=0.8)
                                if close:
                                    match = stats_all[stats_all["Nome"].str.lower() == close[0]]
                            if not match.empty and "FantaMedia" in match.columns and pd.notna(match.iloc[0]["FantaMedia"]):
                                return float(match.iloc[0]["FantaMedia"])
                        return fm_db

                    display["FantaMedia"] = display.apply(_enrich_fm, axis=1)

                    # --- FIX QUOTAZIONI 2025/26: cerca sia nel listone che nel file caricato ---
                    def _get_q2526(nome):
                        # 1. Cerca nel listone
                        db = st.session_state.giocatori_db
                        match = db[db["Nome"].str.lower() == nome.lower()]
                        if not match.empty and "Quotazione_2025_26" in match.columns and pd.notna(match.iloc[0]["Quotazione_2025_26"]):
                            return float(match.iloc[0]["Quotazione_2025_26"])
                        # 2. Cerca nel file quotazioni_2025_26 caricato separatamente
                        q25 = st.session_state.quotazioni_2025_26
                        if not q25.empty and "Nome" in q25.columns:
                            match_q = q25[q25["Nome"].str.lower() == nome.lower()]
                            if match_q.empty:
                                close = difflib.get_close_matches(nome.lower(), [n.lower() for n in q25["Nome"].tolist()], n=1, cutoff=0.8)
                                if close:
                                    match_q = q25[q25["Nome"].str.lower() == close[0]]
                            if not match_q.empty:
                                col_q = "Quotazione_2025_26" if "Quotazione_2025_26" in match_q.columns else ("Quotazione" if "Quotazione" in match_q.columns else None)
                                if col_q and pd.notna(match_q.iloc[0][col_q]):
                                    return float(match_q.iloc[0][col_q])
                        return None

                    display["Quotazione_2025_26"] = display["Nome"].apply(_get_q2526)
                    display["Variazione_%"] = display.apply(
                        lambda r: round((r["Quotazione"] - r["Quotazione_2025_26"]) / r["Quotazione_2025_26"] * 100, 1) if pd.notna(r.get("Quotazione_2025_26")) and r.get("Quotazione_2025_26", 0) > 0 else None,
                        axis=1
                    )

                    if "Scadenza_Anno" not in display.columns:
                        display["Scadenza_Anno"] = ANNO_CORRENTE + CONTRATTO_ANNI
                    display["Scadenza_Anno"] = pd.to_numeric(display["Scadenza_Anno"], errors="coerce").fillna(ANNO_CORRENTE + CONTRATTO_ANNI).astype(int)

                    def stato_scadenza(row):
                        sa = int(row["Scadenza_Anno"])
                        sm = int(row["Scadenza_Mese"]) if "Scadenza_Mese" in row and pd.notna(row["Scadenza_Mese"]) else None
                        if sm:
                            testo = f"{sm}/{sa}"
                        else:
                            testo = str(sa)
                        if sa < ANNO_CORRENTE:
                            return f"🔴 {testo}"
                        elif sa == ANNO_CORRENTE:
                            return f"🟠 {testo}"
                        elif sa == ANNO_CORRENTE + 1:
                            return f"🟡 {testo}"
                        else:
                            return f"🟢 {testo}"

                    display["Stato_Contratto"] = display.apply(stato_scadenza, axis=1)
                    display["Scadenza"] = display["Scadenza_Anno"].astype(str)
                    if "Scadenza_Mese" in display.columns:
                        display["Scadenza"] = display["Scadenza_Mese"].astype(str) + "/" + display["Scadenza_Anno"].astype(str)

                    # --- FIX BADGE: mostra solo se c'è un prestito attivo ---
                    def badge_prestito(row):
                        if pd.notna(row.get("Prestito_Da")) and str(row.get("Prestito_Da")).strip() != "" and row.get("Prestito_Da") != sq:
                            return f"<span style='background:#ff6b6b;color:white;padding:2px 8px;border-radius:12px;font-size:0.75em;font-weight:bold;'>📤 PRESTITO da {row['Prestito_Da']}</span>"
                        return "<span style='color:#444;font-size:0.75em;'>—</span>"
                    display["Prestito"] = display.apply(badge_prestito, axis=1)

                    # Rimuovi colonne tecniche
                    hide_cols = ["Anno_Acquisto", "Contratto_Anni", "Prestito_A", "Prestito_Durata_Mesi", "Prestito_Anno_Inizio", "Prestito_Da", "Prestito_Anno_Inizio"]
                    display = display.drop(columns=[c for c in hide_cols if c in display.columns], errors="ignore")

                    # Ordina colonne: Nome, Ruolo, FM, Squadra, Costo, Quotazione, Q2526, Var%, Scadenza, Stato, Prestito
                    preferred_order = ["Nome", "Ruolo", "FantaMedia", "Squadra_SerieA", "Costo_Acquisto", "Quotazione", "Quotazione_2025_26", "Variazione_%", "Scadenza", "Stato_Contratto", "Prestito"]
                    first_cols = [c for c in preferred_order if c in display.columns]
                    other_cols = [c for c in display.columns if c not in first_cols and c not in ["Scadenza_Anno", "Scadenza_Mese"]]
                    display = display[first_cols + other_cols]

                    st.write(display.to_html(escape=False, index=False), unsafe_allow_html=True)

                    in_scadenza = display[display["Stato_Contratto"].str.contains("🟠|🔴")]
                    if not in_scadenza.empty:
                        st.warning(f"⚠️ {len(in_scadenza)} giocatori in scadenza: " + ", ".join(in_scadenza["Nome"].tolist()))
                        st.subheader("🔄 Rinnovi Rapidi")
                        st.caption("Seleziona un giocatore in scadenza per rinnovare subito (3 anni, prezzo listone).")
                        g_rinn = st.selectbox(f"Rinnova giocatore {sq}", in_scadenza["Nome"].tolist(), key=f"rinn_{sq}")
                        if g_rinn:
                            quot_rinn = get_quotazione_listone(g_rinn)
                            if quot_rinn is None:
                                g_obj_r = next(g for g in dati["rosa"] if g["Nome"] == g_rinn)
                                quot_rinn = g_obj_r.get("Costo_Acquisto", 1)
                            st.info(f"Costo rinnovo: **{quot_rinn}cr** | Nuova scadenza: **{datetime.now().month:02d}/{datetime.now().year + CONTRATTO_ANNI}**")
                            if st.session_state.squadre[sq]["crediti"] < quot_rinn:
                                st.error("Crediti insufficienti!")
                            else:
                                if st.button(f"📝 Rinnova {g_rinn}", key=f"btn_rinn_{sq}_{g_rinn}"):
                                    StateManager.snapshot()
                                    nuovo_anno_rinn = datetime.now().year + CONTRATTO_ANNI
                                    nuovo_mese_rinn = datetime.now().month
                                    st.session_state.squadre[sq]["crediti"] -= quot_rinn
                                    for g in st.session_state.squadre[sq]["rosa"]:
                                        if g["Nome"] == g_rinn:
                                            g["Scadenza_Anno"] = nuovo_anno_rinn
                                            g["Scadenza_Mese"] = nuovo_mese_rinn
                                            g["Costo_Acquisto"] = quot_rinn
                                            break
                                    st.session_state.contratti[g_rinn] = {"squadra": sq, "scadenza_anno": nuovo_anno_rinn, "scadenza_mese": nuovo_mese_rinn}
                                    st.session_state.storico_mercato.insert(0, {
                                        "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                                        "Operazione": "RINNOVO",
                                        "Dettagli": f"{sq} rinnova {g_rinn} fino al {nuovo_mese_rinn:02d}/{nuovo_anno_rinn} per {quot_rinn}cr"
                                    })
                                    invalidate_cache()
                                    save_state()
                                    st.success(f"✅ {g_rinn} rinnovato!")
                                    st.rerun()

                    st.markdown("---")
                    st.subheader("📊 Stato Rosa")
                    cols_riep = st.columns(5)
                    ruoli_ord = ["P", "D", "C", "A"]
                    colori_ruolo = {"P": "🔵", "D": "🟢", "C": "🟡", "A": "🔴"}
                    riep = riepilogo_rosa(sq)
                    for idx_r, ruolo in enumerate(ruoli_ord):
                        with cols_riep[idx_r]:
                            r_data = riep[ruolo]
                            mancanti = r_data["mancanti"]
                            posseduti = r_data["posseduti"]
                            req = r_data["req"]
                            off_max = r_data["offerta_max"]
                            if mancanti == 0:
                                stato = "✅"
                                colore = "#00d26a"
                            else:
                                stato = f"+{mancanti}"
                                colore = "#ff6b6b"
                            st.markdown(
                                f"<div style='text-align:center;padding:8px;border-radius:6px;background:#1a1a2e;'>"
                                f"<div style='font-size:1.2em;'>{colori_ruolo[ruolo]} {ruolo}</div>"
                                f"<div style='font-size:1.5em;font-weight:bold;color:{colore};'>{stato}</div>"
                                f"<div style='font-size:0.75em;color:#888;'>{posseduti}/{req}</div>"
                                f"<div style='font-size:0.75em;color:#aaa;'>Max: {off_max}cr</div>"
                                f"</div>",
                                unsafe_allow_html=True
                            )
                    with cols_riep[4]:
                        prestiti_out_txt = f" | 📤 {riep['tot_prestiti_uscita']} prestiti" if riep['tot_prestiti_uscita'] > 0 else ""
                        st.markdown(
                            f"<div style='text-align:center;padding:8px;border-radius:6px;background:#1a1a2e;'>"
                            f"<div style='font-size:1.2em;'>💰 Crediti</div>"
                            f"<div style='font-size:1.5em;font-weight:bold;color:#ffd700;'>{riep['crediti']}</div>"
                            f"<div style='font-size:0.75em;color:#888;'>Rosa: {riep['tot_posseduti']}/28{prestiti_out_txt}</div>"
                            f"<div style='font-size:0.75em;color:#aaa;'>Mancano: {riep['tot_mancanti']}</div>"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.info("Rosa vuota.")

    with tab_matrice:
        st.subheader("📊 Quadro Generale")
        summary = []
        for sq in NOMI_SQUADRE:
            dati = st.session_state.squadre[sq]
            rosa = dati["rosa"]
            p=d=c=a=spesa=0
            for g in rosa:
                r = g.get("Ruolo","C")
                if r=="P": p+=1
                elif r=="D": d+=1
                elif r=="C": c+=1
                elif r=="A": a+=1
                spesa += g.get("Costo_Acquisto",0)
            prestiti_out = len([p for p in st.session_state.prestiti if p["Da"] == sq])
            summary.append({"Squadra":sq, "Crediti":dati["crediti"], "Spesa":spesa, "Tot Rosa":len(rosa), "P":p, "D":d, "C":c, "A":a, "Prestiti Uscita":prestiti_out, "Tot Posseduti":len(rosa)+prestiti_out})
        st.dataframe(pd.DataFrame(summary), use_container_width=True)

    with tab_contratti:
        st.subheader(f"📄 Contratti — Scadenze")
        if st.session_state.contratti:
            rows = []
            for nome, c in st.session_state.contratti.items():
                scad = ""
                if c.get("scadenza_mese") and c.get("scadenza_anno"):
                    scad = f"{c['scadenza_mese']}/{c['scadenza_anno']}"
                elif c.get("scadenza_anno"):
                    scad = str(c["scadenza_anno"])
                else:
                    scad = "N/D"
                rows.append({"Giocatore":nome, "Squadra":c["squadra"], "Scadenza":scad})
            df_contr = pd.DataFrame(rows)
            df_contr = df_contr.sort_values("Scadenza")
            st.dataframe(df_contr, use_container_width=True)
        else:
            st.info("Nessun contratto registrato.")

    with tab_consigli:
        st.subheader("💡 Consigli Fantacalcio 2026/27")
        st.caption("I consigli sono generati automaticamente dalla colonna 'Consiglio' del listone.")

        db_consigli = st.session_state.giocatori_db.copy()
        if db_consigli.empty or "Consiglio" not in db_consigli.columns:
            st.warning("⚠️ Nessun listone con colonna 'Consiglio' disponibile. Importa un listone valido.")
        else:
            # Arricchisci con dati proprietà
            idx_prop = get_player_index()
            db_consigli["Proprietario"] = db_consigli["Nome"].apply(lambda x: idx_prop.get(x.lower(), None))
            db_consigli["Stato"] = db_consigli["Proprietario"].apply(lambda x: "🔒 Assegnato" if x else "🟢 Libero")

            # Arricchisci con FM 2026/27 se disponibile
            if "stats_per_stagione" in st.session_state and "2026-27" in st.session_state.stats_per_stagione:
                s2627 = st.session_state.stats_per_stagione["2026-27"]
                if not s2627.empty and "Nome" in s2627.columns and "FantaMedia" in s2627.columns:
                    s2627_f = s2627[["Nome", "FantaMedia"]].copy()
                    s2627_f["Nome_lower"] = s2627_f["Nome"].str.lower().str.strip()
                    db_consigli["Nome_lower"] = db_consigli["Nome"].str.lower().str.strip()
                    db_consigli = db_consigli.merge(s2627_f[["Nome_lower", "FantaMedia"]], on="Nome_lower", how="left", suffixes=("", "_2627"))
                    db_consigli["FantaMedia_Display"] = db_consigli["FantaMedia_2627"].fillna(db_consigli["FantaMedia"])
                    db_consigli["FM_Badge"] = db_consigli.apply(lambda r: f"{r['FantaMedia_Display']:.1f} 📊" if pd.notna(r.get('FantaMedia_2627')) else f"{r['FantaMedia']:.1f} 📋", axis=1)
                    db_consigli = db_consigli.drop(columns=["Nome_lower", "FantaMedia_2627"], errors="ignore")
                else:
                    db_consigli["FantaMedia_Display"] = db_consigli["FantaMedia"]
                    db_consigli["FM_Badge"] = db_consigli["FantaMedia"].apply(lambda x: f"{x:.1f} 📋")
            else:
                db_consigli["FantaMedia_Display"] = db_consigli["FantaMedia"]
                db_consigli["FM_Badge"] = db_consigli["FantaMedia"].apply(lambda x: f"{x:.1f} 📋")

            ruoli_map = {"Portieri": "P", "Difensori": "D", "Centrocampisti": "C", "Attaccanti": "A"}
            colori_fascia = {"top": "⭐", "consigliato": "👍", "scommessa": "🎲"}
            nomi_fascia = {"top": "Top", "consigliato": "Consigliati", "scommessa": "Scommesse"}

            for ruolo_nome, ruolo_cod in ruoli_map.items():
                with st.expander(ruolo_nome):
                    df_ruolo = db_consigli[db_consigli["Ruolo"] == ruolo_cod].copy()
                    if df_ruolo.empty:
                        st.caption("Nessun giocatore trovato per questo ruolo.")
                        continue

                    for fascia in ["top", "consigliato", "scommessa"]:
                        df_fascia = df_ruolo[df_ruolo["Consiglio"] == fascia].sort_values("FantaMedia_Display", ascending=False)
                        if df_fascia.empty:
                            continue

                        st.markdown(f"**{colori_fascia[fascia]} {nomi_fascia[fascia]}:**")
                        righe = []
                        for _, row in df_fascia.iterrows():
                            nome = row["Nome"]
                            sa = row.get("Squadra_SerieA", "N/D")
                            quot = int(row.get("Quotazione", 0))
                            fm = row.get("FM_Badge", "N/D")
                            pc = row.get("Prezzo_Consigliato")
                            pc_txt = f" | 💡{int(pc)}cr" if pd.notna(pc) else ""
                            stato = row.get("Stato", "")
                            righe.append(f"**{nome}** ({sa}) — FM {fm} | Q {quot}cr{pc_txt} {stato}")
                        st.markdown(" • ".join(righe))

    with tab_formazione:
        st.subheader("🎮 Simula Formazione")
        st.caption("Seleziona una squadra e un modulo per vedere la fantamedia potenziale della formazione titolare.")
        sq_form = st.selectbox("Squadra", NOMI_SQUADRE, key="sim_sq")
        modulo = st.selectbox("Modulo", ["3-4-3", "3-5-2", "4-3-3", "4-4-2", "4-5-1", "5-3-2", "5-4-1"], key="sim_mod")
        if st.button("🚀 Simula", type="primary"):
            fm_tot, panchina, titolari = simula_formazione(sq_form, modulo)
            st.metric("FantaMedia Totale Titolari", f"{fm_tot}")
            col_t, col_p = st.columns(2)
            with col_t:
                st.subheader("⭐ Titolari")
                for g in titolari:
                    orig = g.get("FM_Origine", "")
                    st.markdown(f"**{g['Nome']}** ({g['Ruolo']}) — FM {g.get('FantaMedia_Usata', 0)} <span style='color:#888;font-size:0.8em;'>{orig}</span>", unsafe_allow_html=True)
            with col_p:
                st.subheader("🪑 Panchina")
                for g in panchina:
                    orig = g.get("FM_Origine", "")
                    st.markdown(f"**{g['Nome']}** ({g['Ruolo']}) — FM {g.get('FantaMedia_Usata', 0)} <span style='color:#888;font-size:0.8em;'>{orig}</span>", unsafe_allow_html=True)

# ============================================================
# 6. STATISTICHE STORICHE
# ============================================================
if menu == "📈 Statistiche Storiche":
    st.header("📈 Statistiche Storiche — Ultimi 3 Anni")
    st.markdown("Carica i file CSV/Excel con le statistiche storiche **separati per stagione**. Ogni file viene taggato automaticamente con l'anno selezionato.")

    STAGIONI = ["2023-24", "2024-25", "2025-26", "2026-27"]

    if "stats_per_stagione" not in st.session_state:
        st.session_state.stats_per_stagione = {}

    tabs = st.tabs(["⬆️ Carica", "📋 Visualizza", "🗑️ Gestione"])

    with tabs[0]:
        st.subheader("Carica statistiche per stagione")
        col1, col2 = st.columns([1, 2])
        with col1:
            stagione_sel = st.selectbox("Seleziona stagione", STAGIONI, key="stagione_sel")
        with col2:
            up_stats = st.file_uploader(f"File statistiche {stagione_sel}", type=["csv","xlsx"], key=f"us_{stagione_sel.replace('-','_')}")

        if up_stats is not None:
            try:
                if up_stats.name.endswith('.csv'):
                    df_s = pd.read_csv(up_stats, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_s = pd.read_excel(up_stats)
                df_s.columns = [str(c).strip() for c in df_s.columns]

                col_map = {}
                for col in df_s.columns:
                    cl = str(col).lower().strip()
                    if any(k in cl for k in ['nome','giocatore','calciatore','name','player','cognome']):
                        col_map[col] = 'Nome'
                    elif any(k in cl for k in ['stagione','anno','season','year']):
                        col_map[col] = 'Stagione'
                    elif any(k in cl for k in ['gol','goal','reti']):
                        col_map[col] = 'Gol'
                    elif 'assist' in cl:
                        col_map[col] = 'Assist'
                    elif any(k in cl for k in ['fm','fantamedia','fanta media','media']):
                        col_map[col] = 'FantaMedia'
                    elif any(k in cl for k in ['partite','presenze','pg','match','played']):
                        col_map[col] = 'Partite'
                    elif 'rigor' in cl:
                        col_map[col] = 'Rigori'
                    elif any(k in cl for k in ['amm','yellow','gialli']):
                        col_map[col] = 'Ammonizioni'
                    elif any(k in cl for k in ['esp','red','rossi']):
                        col_map[col] = 'Espulsioni'
                df_s = df_s.rename(columns=col_map)

                if 'Nome' not in df_s.columns:
                    st.error(f"❌ Colonna 'Nome' non trovata. Colonne rilevate: {list(df_s.columns)}")
                    st.info("💡 Assicurati che il file contenga una colonna con il nome del giocatore")
                    st.stop()

                df_s["Stagione"] = stagione_sel
                st.session_state.stats_per_stagione[stagione_sel] = df_s

                all_stats = []
                for stag, df_stag in st.session_state.stats_per_stagione.items():
                    all_stats.append(df_stag)
                if all_stats:
                    st.session_state.stats_storiche = pd.concat(all_stats, ignore_index=True)

                save_state()
                st.success(f"✅ Caricate {len(df_s)} righe per la stagione **{stagione_sel}**!")
            except Exception as e:
                st.error(f"Errore: {e}")

        if st.session_state.stats_per_stagione:
            st.markdown("---")
            st.subheader("📂 Stagioni caricate")
            for stag, df_stag in st.session_state.stats_per_stagione.items():
                if 'Nome' in df_stag.columns:
                    n_giocatori = df_stag['Nome'].nunique()
                else:
                    n_giocatori = "N/D"
                st.caption(f"**{stag}**: {len(df_stag)} righe | {n_giocatori} giocatori")

    with tabs[1]:
        if not st.session_state.stats_storiche.empty:
            df_stats = st.session_state.stats_storiche.copy()
            st.subheader("🔍 Visualizza per giocatore")
            giocatori_stats = df_stats["Nome"].unique() if "Nome" in df_stats.columns else []
            if len(giocatori_stats) > 0:
                g_sel = st.selectbox("Seleziona giocatore", sorted(giocatori_stats), key="stats_sel")
                df_g = df_stats[df_stats["Nome"] == g_sel].sort_values("Stagione")
                st.markdown(f"**{g_sel}** — {len(df_g)} stagioni trovate")
                if "Stagione" in df_g.columns and "2026-27" in df_g["Stagione"].values:
                    st.success("📊 Dati stagione 2026/27 disponibili")
                st.dataframe(df_g, use_container_width=True)
                numeric_cols = df_g.select_dtypes(include=['number']).columns.tolist()
                numeric_cols = [c for c in numeric_cols if c not in ['Stagione']]
                if numeric_cols and "Stagione" in df_g.columns:
                    st.subheader("📊 Andamento")
                    chart_data = df_g.set_index("Stagione")[numeric_cols]
                    st.line_chart(chart_data)

                db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"].str.lower() == g_sel.lower()]
                if db_match.empty:
                    nm_f = fuzzy_match(g_sel, st.session_state.giocatori_db["Nome"].tolist())
                    if nm_f:
                        db_match = st.session_state.giocatori_db[st.session_state.giocatori_db["Nome"] == nm_f]
                if not db_match.empty:
                    st.info(f"💡 Quotazione attuale listone: **{int(db_match.iloc[0]['Quotazione'])}cr** | FantaMedia: **{db_match.iloc[0]['FantaMedia']}** | Squadra: **{db_match.iloc[0]['Squadra_SerieA']}**")

            st.markdown("---")
            st.subheader("📋 Tabella completa")
            st.dataframe(df_stats, use_container_width=True)
        else:
            st.info("Nessuna statistica storica caricata.")

    with tabs[2]:
        st.subheader("🗑️ Gestione dati storici")
        if st.session_state.stats_per_stagione:
            st.markdown("**Stagioni caricate:**")
            for stag in list(st.session_state.stats_per_stagione.keys()):
                col_a, col_b = st.columns([3, 1])
                with col_a:
                    df_stag = st.session_state.stats_per_stagione[stag]
                    st.write(f"📁 **{stag}** — {len(df_stag)} righe, {df_stag['Nome'].nunique()} giocatori")
                with col_b:
                    if st.button(f"🗑️ Cancella {stag}", key=f"del_{stag.replace('-','_')}"):
                        del st.session_state.stats_per_stagione[stag]
                        all_stats = []
                        for s, df_s in st.session_state.stats_per_stagione.items():
                            all_stats.append(df_s)
                        st.session_state.stats_storiche = pd.concat(all_stats, ignore_index=True) if all_stats else pd.DataFrame()
                        save_state()
                        st.success(f"Stagione {stag} cancellata!")
                        st.rerun()
            st.markdown("---")
            if st.button("🗑️ Cancella TUTTE le statistiche", type="primary"):
                st.session_state.stats_per_stagione = {}
                st.session_state.stats_storiche = pd.DataFrame()
                save_state()
                st.success("Tutte le statistiche cancellate!")
                st.rerun()
        else:
            st.info("Nessuna stagione caricata.")

# ============================================================
# 7. IMPORTA & ESPORTA
# ============================================================
if menu == "⚙️ Importa & Esporta":
    st.header("⚙️ Importa & Esporta Dati")
    st.caption("Tutte le operazioni di import/export in un'unica pagina.")

    tab_exp, tab_imp_listone, tab_imp_rose, tab_imp_q25 = st.tabs([
        "📤 Esporta Backup", "📁 Importa Listone", "📋 Importa Rose", "📊 Importa Quotazioni 2025/26"
    ])

    with tab_exp:
        st.subheader("📤 Esporta Backup Completo (Excel)")
        buffer_exp = io.BytesIO()
        df_exp = st.session_state.giocatori_db.copy()
        if "Prezzo_Consigliato" not in df_exp.columns:
            df_exp["Prezzo_Consigliato"] = None
        if not st.session_state.stats_storiche.empty and "Nome" in st.session_state.stats_storiche.columns:
            for idx, row in df_exp.iterrows():
                if pd.isna(row.get("Prezzo_Consigliato")):
                    pc_ai, _ = calcola_prezzo_consigliato(row.to_dict(), st.session_state.stats_storiche)
                    df_exp.at[idx, "Prezzo_Consigliato"] = pc_ai
        cols_exp = [c for c in ["Nome","Ruolo","Squadra_SerieA","Quotazione","Prezzo_Consigliato","FantaMedia","Consiglio","Note","Quotazione_2025_26"] if c in df_exp.columns]
        df_exp = df_exp[cols_exp]
        with pd.ExcelWriter(buffer_exp, engine="openpyxl") as writer:
            df_exp.to_excel(writer, index=False, sheet_name="Listone")
            rose_exp = []
            for sq_name, sq_data in st.session_state.squadre.items():
                for g in sq_data["rosa"]:
                    g_copy = dict(g)
                    g_copy["Squadra_Fanta"] = sq_name
                    rose_exp.append(g_copy)
            if rose_exp:
                pd.DataFrame(rose_exp).to_excel(writer, index=False, sheet_name="Rose")
            if st.session_state.storico_mercato:
                pd.DataFrame(st.session_state.storico_mercato).to_excel(writer, index=False, sheet_name="Storico")
        st.download_button(
            label="⬇️ Scarica Backup Completo (Excel)",
            data=buffer_exp.getvalue(),
            file_name=f"fantamanager_backup_{datetime.now().strftime('%Y%m%d_%H%M')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )

    with tab_imp_listone:
        st.subheader("📁 Importa Listone (CSV/Excel)")
        st.markdown("Colonne attese: Nome, Ruolo, Squadra, Quotazione, FantaMedia.")
        up_listone = st.file_uploader("File Listone", type=["csv","xlsx"], key="ul")
        if up_listone is not None:
            try:
                if up_listone.name.endswith('.csv'):
                    df_load = pd.read_csv(up_listone, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_load = pd.read_excel(up_listone)
                df_load.columns = [str(c).strip() for c in df_load.columns]
                col_mappa = {}
                for col in df_load.columns:
                    cl = str(col).lower()
                    if 'nome' in cl or 'giocatore' in cl: col_mappa[col] = 'Nome'
                    elif cl in ['r','ruolo']: col_mappa[col] = 'Ruolo'
                    elif 'squadra' in cl or 'team' in cl: col_mappa[col] = 'Squadra_SerieA'
                    elif 'quot' in cl or 'valore' in cl or 'fc' in cl or 'qt' in cl:
                        if '2025' in cl or 'prec' in cl or 'old' in cl or 'last' in cl or 'precedente' in cl:
                            col_mappa[col] = 'Quotazione_2025_26'
                        else:
                            col_mappa[col] = 'Quotazione'
                    elif 'fm' in cl or 'fantamedia' in cl or 'media' in cl: col_mappa[col] = 'FantaMedia'
                    elif 'prezzo' in cl or 'consigliato' in cl or 'suggerito' in cl or 'acquisto' in cl or 'buy' in cl: col_mappa[col] = 'Prezzo_Consigliato'
                df_load = df_load.rename(columns=col_mappa)
                if 'Nome' in df_load.columns:
                    df_load = df_load.loc[:, ~df_load.columns.duplicated()]
                    for c, d in [('Ruolo','C'),('Squadra_SerieA','N/D'),('Quotazione',10),('FantaMedia',6.0),('Quotazione_2025_26',None)]:
                        if c not in df_load.columns: df_load[c] = d
                    if 'Quotazione_2025_26' in df_load.columns:
                        df_load['Quotazione_2025_26'] = pd.to_numeric(df_load['Quotazione_2025_26'], errors='coerce')
                    df_load['Quotazione'] = pd.to_numeric(df_load['Quotazione'], errors='coerce').fillna(10).astype(int)
                    fm = df_load['FantaMedia']
                    if isinstance(fm, pd.DataFrame): fm = fm.iloc[:,0]
                    df_load['FantaMedia'] = pd.to_numeric(fm.astype(str).str.replace(',','.',regex=False), errors='coerce').fillna(6.0)
                    if 'Consiglio' not in df_load.columns: df_load['Consiglio'] = 'consigliato'
                    if 'Note' not in df_load.columns: df_load['Note'] = ''
                    if 'Prezzo_Consigliato' not in df_load.columns: df_load['Prezzo_Consigliato'] = None
                    else:
                        df_load['Prezzo_Consigliato'] = pd.to_numeric(df_load['Prezzo_Consigliato'], errors='coerce')
                    cols_final = ['Nome','Ruolo','Squadra_SerieA','Quotazione','FantaMedia','Consiglio','Note','Prezzo_Consigliato']
                    if 'Quotazione_2025_26' in df_load.columns: cols_final.append('Quotazione_2025_26')
                    st.session_state.giocatori_db = df_load[cols_final]
                    save_state()
                    st.success(f"✅ Listone importato! {len(df_load)} giocatori.")
                else:
                    st.error("Colonna 'Nome' mancante.")
            except Exception as e:
                st.error(f"Errore: {e}")

    with tab_imp_rose:
        st.subheader("📋 Importa Rose (con anteprima)")
        st.markdown("""
        **Colonne attese:** Squadra, Nome, Ruolo, Costo
        **Opzionali per scadenze:** Scadenza_Anno, Scadenza_Mese
        Se mancano, il contratto parte da 2026 per 3 anni.
        """)
        up_rose = st.file_uploader("File Rose", type=["csv","xlsx"], key="ur")
        if up_rose is not None:
            try:
                if up_rose.name.endswith('.csv'):
                    df_r = pd.read_csv(up_rose, encoding='utf-8', on_bad_lines='skip')
                else:
                    xl = pd.ExcelFile(up_rose)
                    sheets = xl.sheet_names
                    if len(sheets) > 1:
                        sheet_sel = st.selectbox("Seleziona sheet", sheets, key="sheet_sel")
                        df_r = pd.read_excel(up_rose, sheet_name=sheet_sel)
                    else:
                        df_r = pd.read_excel(up_rose)

                df_r.columns = [str(c).strip() for c in df_r.columns]
                st.write(f"**File letto:** {len(df_r)} righe, colonne: {', '.join(df_r.columns)}")

                def find_best_match(options, keywords):
                    for kw in keywords:
                        for opt in options:
                            if kw in str(opt).lower():
                                return opt
                    return None

                cols = [""] + list(df_r.columns)
                col_sq = st.selectbox("Colonna SQUADRA", cols,
                                       index=cols.index(find_best_match(cols, ['squadra','team','proprietario','fantateam'])) if find_best_match(cols, ['squadra','team','proprietario','fantateam']) in cols else 0,
                                       key="map_sq")
                col_nm = st.selectbox("Colonna NOME", cols,
                                       index=cols.index(find_best_match(cols, ['nome','giocatore','player'])) if find_best_match(cols, ['nome','giocatore','player']) in cols else 0,
                                       key="map_nm")
                col_rl = st.selectbox("Colonna RUOLO (opzionale)", cols,
                                       index=cols.index(find_best_match(cols, ['ruolo','r ','role'])) if find_best_match(cols, ['ruolo','r ','role']) in cols else 0,
                                       key="map_rl")
                col_cs = st.selectbox("Colonna COSTO (opzionale)", cols,
                                       index=cols.index(find_best_match(cols, ['costo','prezzo','pagato','quotazione','quot','valore'])) if find_best_match(cols, ['costo','prezzo','pagato','quotazione','quot','valore']) in cols else 0,
                                       key="map_cs")
                col_scad_a = st.selectbox("Colonna SCADENZA ANNO (opzionale)", cols,
                                       index=cols.index(find_best_match(cols, ['scadenza anno','scadenza_anno','scad_anno','anno_scadenza','fine','fine_contratto'])) if find_best_match(cols, ['scadenza anno','scadenza_anno','scad_anno','anno_scadenza','fine','fine_contratto']) in cols else 0,
                                       key="map_scad_a")
                col_scad_m = st.selectbox("Colonna SCADENZA MESE (opzionale)", cols,
                                       index=cols.index(find_best_match(cols, ['scadenza mese','scadenza_mese','scad_mese','mese_scadenza','mese_fine'])) if find_best_match(cols, ['scadenza mese','scadenza_mese','scad_mese','mese_scadenza','mese_fine']) in cols else 0,
                                       key="map_scad_m")

                if col_sq and col_nm and col_sq != "" and col_nm != "":
                    st.subheader("👁️ Anteprima dati")
                    preview_cols = [col_sq, col_nm]
                    if col_rl and col_rl != "": preview_cols.append(col_rl)
                    if col_cs and col_cs != "": preview_cols.append(col_cs)
                    if col_scad_a and col_scad_a != "": preview_cols.append(col_scad_a)
                    if col_scad_m and col_scad_m != "": preview_cols.append(col_scad_m)
                    st.dataframe(df_r[preview_cols].head(10), use_container_width=True)

                    if st.button("✅ IMPORTA ROSE", type="primary", use_container_width=True):
                        count = 0
                        skipped = 0
                        errors = []
                        for idx, row in df_r.iterrows():
                            try:
                                sq_nome = str(row[col_sq]).strip().upper() if pd.notna(row[col_sq]) else ""
                                if not sq_nome: continue
                                sq_match = None
                                for s in NOMI_SQUADRE:
                                    if s.upper() == sq_nome or s.upper() in sq_nome or sq_nome in s.upper():
                                        sq_match = s
                                        break
                                if not sq_match:
                                    skipped += 1
                                    continue
                                g_nome = str(row[col_nm]).strip() if pd.notna(row[col_nm]) else ""
                                if not g_nome or g_nome.lower() in ['nan', 'none', 'null', '']:
                                    continue
                                g_ruolo = str(row[col_rl]).strip().upper() if col_rl and col_rl != "" and pd.notna(row[col_rl]) else "C"
                                if len(g_ruolo) > 1 and g_ruolo[0] in "PDCA":
                                    g_ruolo = g_ruolo[0]
                                elif g_ruolo not in ["P","D","C","A"]:
                                    g_ruolo = "C"
                                g_costo = 1
                                if col_cs and col_cs != "" and pd.notna(row[col_cs]):
                                    try:
                                        g_costo = int(float(str(row[col_cs]).replace(',','.')))
                                    except:
                                        g_costo = 1

                                scad_anno = None
                                scad_mese = None
                                if col_scad_a and col_scad_a != "" and pd.notna(row[col_scad_a]):
                                    try:
                                        val = row[col_scad_a]
                                        if hasattr(val, 'year'):
                                            scad_anno = int(val.year)
                                            scad_mese = int(val.month)
                                        else:
                                            num = float(str(val).replace(',','.'))
                                            if num > 40000:
                                                dt = pd.to_datetime(int(num), unit='D', origin='1899-12-30')
                                                scad_anno = int(dt.year)
                                                scad_mese = int(dt.month)
                                            else:
                                                scad_anno = int(num)
                                    except Exception:
                                        scad_anno = None
                                if col_scad_m and col_scad_m != "" and pd.notna(row[col_scad_m]) and scad_mese is None:
                                    try:
                                        val = row[col_scad_m]
                                        if hasattr(val, 'month'):
                                            scad_mese = int(val.month)
                                        else:
                                            scad_mese = int(float(str(val).replace(',','.')))
                                    except Exception:
                                        scad_mese = None

                                db_g = st.session_state.giocatori_db
                                match_db = db_g[db_g['Nome'].str.lower() == g_nome.lower()]
                                if match_db.empty:
                                    nm_f = fuzzy_match(g_nome, db_g['Nome'].tolist())
                                    if nm_f:
                                        match_db = db_g[db_g['Nome'] == nm_f]
                                sq_sa = "N/D"
                                quot = 10
                                fm = 6.0
                                if not match_db.empty:
                                    sq_sa = match_db.iloc[0]['Squadra_SerieA']
                                    quot = int(match_db.iloc[0]['Quotazione'])
                                    fm = float(match_db.iloc[0]['FantaMedia'])
                                    g_ruolo = str(match_db.iloc[0]['Ruolo'])

                                if any(g['Nome'].lower() == g_nome.lower() for g in st.session_state.squadre[sq_match]["rosa"]):
                                    skipped += 1
                                    continue
                                if st.session_state.squadre[sq_match]["crediti"] < g_costo:
                                    errors.append(f"{sq_match}: crediti insufficienti per {g_nome} ({g_costo}cr)")
                                    continue

                                if not scad_anno:
                                    scad_anno = ANNO_CORRENTE + CONTRATTO_ANNI

                                st.session_state.squadre[sq_match]["crediti"] -= g_costo
                                entry = {
                                    "Nome": g_nome, "Ruolo": g_ruolo, "Squadra_SerieA": sq_sa,
                                    "Quotazione": quot, "FantaMedia": fm, "Costo_Acquisto": g_costo,
                                    "Scadenza_Anno": scad_anno,
                                }
                                if scad_mese:
                                    entry["Scadenza_Mese"] = scad_mese
                                st.session_state.squadre[sq_match]["rosa"].append(entry)
                                st.session_state.contratti[g_nome] = {
                                    "squadra": sq_match, "scadenza_anno": scad_anno, "scadenza_mese": scad_mese
                                }
                                count += 1
                            except Exception as e:
                                errors.append(f"Riga {idx}: {e}")

                        invalidate_cache()
                        save_state()
                        st.success(f"✅ Importati {count} giocatori! ({skipped} saltati)")
                        if errors:
                            with st.expander("⚠️ Errori/Avvisi"):
                                for e in errors[:20]:
                                    st.write(f"- {e}")
                                if len(errors) > 20:
                                    st.write(f"... e altri {len(errors)-20} errori")
                        st.rerun()
                else:
                    st.warning("Seleziona almeno le colonne Squadra e Nome.")
            except Exception as e:
                st.error(f"Errore lettura file: {e}")

    with tab_imp_q25:
        st.subheader("📊 Importa Quotazioni 2025/26")
        st.markdown("""
        Carica un file con le quotazioni dell'ultima giornata 2025/2026.
        **Colonne attese:** Nome, Quotazione (o Quotazione_2025_26)
        Queste quotazioni verranno usate come **prezzo di rimborso** quando un giocatore non viene trovato nel listone attuale.
        """)
        up_q25 = st.file_uploader("File Quotazioni 2025/26", type=["csv","xlsx"], key="uq25")
        if up_q25 is not None:
            try:
                if up_q25.name.endswith('.csv'):
                    df_q = pd.read_csv(up_q25, encoding='utf-8', on_bad_lines='skip')
                else:
                    df_q = pd.read_excel(up_q25)
                df_q.columns = [str(c).strip() for c in df_q.columns]
                col_map_q = {}
                for col in df_q.columns:
                    cl = str(col).lower()
                    if 'nome' in cl or 'giocatore' in cl or 'player' in cl:
                        col_map_q[col] = 'Nome'
                    elif 'quot' in cl or 'valore' in cl or 'prezzo' in cl or 'fc' in cl:
                        col_map_q[col] = 'Quotazione_2025_26'
                df_q = df_q.rename(columns=col_map_q)
                if 'Nome' not in df_q.columns:
                    st.error("Colonna 'Nome' mancante nel file.")
                else:
                    if 'Quotazione_2025_26' not in df_q.columns:
                        for col in df_q.columns:
                            if col != 'Nome' and pd.api.types.is_numeric_dtype(df_q[col]):
                                df_q['Quotazione_2025_26'] = pd.to_numeric(df_q['Quotazione_2025_26'], errors='coerce').fillna(1).astype(int)
                df_q = df_q[['Nome', 'Quotazione_2025_26']].dropna()
                st.session_state.quotazioni_2025_26 = df_q

                # >>> FIX: unisce le quotazioni 2025/26 nel giocatori_db principale
                db = st.session_state.giocatori_db.copy()
                db["_tmp_lower"] = db["Nome"].str.lower().str.strip()
                df_q_merge = df_q.copy()
                df_q_merge["_tmp_lower"] = df_q_merge["Nome"].str.lower().str.strip()
                if "Quotazione_2025_26" in db.columns:
                    db = db.drop(columns=["Quotazione_2025_26"])
                db = db.merge(df_q_merge[["_tmp_lower", "Quotazione_2025_26"]], on="_tmp_lower", how="left")
                db = db.drop(columns=["_tmp_lower"])
                st.session_state.giocatori_db = db
                # <<<

                save_state()
                aggiornati = db['Quotazione_2025_26'].notna().sum()
                st.success(f"✅ Caricate {len(df_q)} quotazioni 2025/26! Aggiornati {aggiornati} giocatori nel listone.")
                with st.expander("👁️ Anteprima"):
                    st.dataframe(df_q.head(10), use_container_width=True)
            except Exception as e:
                st.error(f"Errore: {e}")

        if not st.session_state.quotazioni_2025_26.empty:
            st.caption(f"📊 {len(st.session_state.quotazioni_2025_26)} quotazioni 2025/26 caricate")
            if st.button("🗑️ Cancella quotazioni 2025/26", use_container_width=True):
                st.session_state.quotazioni_2025_26 = pd.DataFrame()
                save_state()
                st.success("Cancellate!")
                st.rerun()
