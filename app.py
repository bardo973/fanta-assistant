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
</style>
""", unsafe_allow_html=True)

# ============================================================
# LISTONE DEFAULT
# ============================================================
LISTONE_DEFAULT = [
    {"Nome":"Svilar","Ruolo":"P","Squadra_SerieA":"Roma","Quotazione":38,"FantaMedia":6.0,"Consiglio":"top","Note":"18 clean sheet, fantamedia 6, media voto 6.35", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Carnesecchi","Ruolo":"P","Squadra_SerieA":"Atalanta","Quotazione":34,"FantaMedia":6.1,"Consiglio":"top","Note":"13 clean sheet, media voto 6.5, con Sarri può migliorare", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Maignan","Ruolo":"P","Squadra_SerieA":"Milan","Quotazione":34,"FantaMedia":5.9,"Consiglio":"top","Note":"13 clean sheet, 2 rigori parati, affidabile", "Quotazione_2025_26":29, "Prezzo_Consigliato":None},
    {"Nome":"Butez","Ruolo":"P","Squadra_SerieA":"Como","Quotazione":32,"FantaMedia":5.8,"Consiglio":"top","Note":"19 clean sheet, miglior difesa del campionato", "Quotazione_2025_26":32, "Prezzo_Consigliato":None},
    {"Nome":"Martinez","Ruolo":"P","Squadra_SerieA":"Inter","Quotazione":29,"FantaMedia":5.7,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Genoa, fiducia Chivu", "Quotazione_2025_26":23, "Prezzo_Consigliato":None},
    {"Nome":"Meret","Ruolo":"P","Squadra_SerieA":"Napoli","Quotazione":30,"FantaMedia":5.8,"Consiglio":"consigliato","Note":"Titolare con Allegri, sottovalutato, ottimo rapporto qualità-prezzo", "Quotazione_2025_26":31, "Prezzo_Consigliato":None},
    {"Nome":"De Gea","Ruolo":"P","Squadra_SerieA":"Fiorentina","Quotazione":24,"FantaMedia":5.6,"Consiglio":"consigliato","Note":"Stagione del riscatto, hype sceso, low risk", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Vicario","Ruolo":"P","Squadra_SerieA":"Juventus","Quotazione":28,"FantaMedia":5.7,"Consiglio":"consigliato","Note":"Nuovo titolare, ex Empoli, top assoluto in Serie A", "Quotazione_2025_26":15, "Prezzo_Consigliato":None},
    {"Nome":"Mandas","Ruolo":"P","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":5.5,"Consiglio":"consigliato","Note":"Titolare con Gattuso, portiere da modificatore", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Falcone","Ruolo":"P","Squadra_SerieA":"Lecce","Quotazione":17,"FantaMedia":5.5,"Consiglio":"scommessa","Note":"Media voto 6.41, low cost, garanzia voti alti", "Quotazione_2025_26":5, "Prezzo_Consigliato":None},
    {"Nome":"Stankovic","Ruolo":"P","Squadra_SerieA":"Venezia","Quotazione":13,"FantaMedia":5.3,"Consiglio":"scommessa","Note":"Torna in Serie A, potenziale sorpresa", "Quotazione_2025_26":6, "Prezzo_Consigliato":None},
    {"Nome":"Corvi","Ruolo":"P","Squadra_SerieA":"Parma","Quotazione":12,"FantaMedia":5.4,"Consiglio":"scommessa","Note":"Nuovo titolare, aveva fatto vedere buone cose", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},
    {"Nome":"Caprile","Ruolo":"P","Squadra_SerieA":"Cagliari","Quotazione":10,"FantaMedia":5.3,"Consiglio":"scommessa","Note":"Buon portiere da modificatore, low cost", "Quotazione_2025_26":3, "Prezzo_Consigliato":None},
    {"Nome":"Dimarco","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":45,"FantaMedia":7.2,"Consiglio":"top","Note":"Top assoluto, vale un +3 a giornata, irraggiungibile", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},
    {"Nome":"Bremer","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":38,"FantaMedia":6.9,"Consiglio":"top","Note":"4 gol, 3 assist, fantamedia alta, primo slot", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Bisseck","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":35,"FantaMedia":6.8,"Consiglio":"top","Note":"Voti alti e bonus, può diventare top", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Mancini","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":32,"FantaMedia":6.7,"Consiglio":"top","Note":"4 gol, leader difesa Gasperini, solido", "Quotazione_2025_26":27, "Prezzo_Consigliato":None},
    {"Nome":"Wesley","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":28,"FantaMedia":6.6,"Consiglio":"top","Note":"5 gol, potenziale stagione alla Gosens", "Quotazione_2025_26":25, "Prezzo_Consigliato":None},
    {"Nome":"Pavlovic","Ruolo":"D","Squadra_SerieA":"Milan","Quotazione":33,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5 gol, media 6.24, centrale prolifico", "Quotazione_2025_26":33, "Prezzo_Consigliato":None},
    {"Nome":"Ostigard","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":28,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"5 gol, centrale prolifico, solido", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Cambiaso","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":29,"FantaMedia":6.6,"Consiglio":"consigliato","Note":"3 gol, 4 assist, titolare a sinistra", "Quotazione_2025_26":23, "Prezzo_Consigliato":None},
    {"Nome":"Spinazzola","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":27,"FantaMedia":6.3,"Consiglio":"consigliato","Note":"Sottovalutato, bonus garantiti, media buona", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Zappacosta","Ruolo":"D","Squadra_SerieA":"Atalanta","Quotazione":32,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"Gran gamba, qualità offensiva, bonus sicuri", "Quotazione_2025_26":34, "Prezzo_Consigliato":None},
    {"Nome":"Di Lorenzo","Ruolo":"D","Squadra_SerieA":"Napoli","Quotazione":26,"FantaMedia":6.4,"Consiglio":"consigliato","Note":"Sempre buona chiamata, 6-7 bonus potenziali", "Quotazione_2025_26":24, "Prezzo_Consigliato":None},
    {"Nome":"Kempf","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.2,"Consiglio":"consigliato","Note":"Certezza, voti e bonus, solido", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},
    {"Nome":"Stones","Ruolo":"D","Squadra_SerieA":"Inter","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"Ex City, rotazioni Chivu, minutaggio garantito", "Quotazione_2025_26":21, "Prezzo_Consigliato":None},
    {"Nome":"Rensch","Ruolo":"D","Squadra_SerieA":"Roma","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"1 gol, 4 assist in 19 partite, può esplodere", "Quotazione_2025_26":11, "Prezzo_Consigliato":None},
    {"Nome":"Doekhi","Ruolo":"D","Squadra_SerieA":"Lazio","Quotazione":22,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"7 gol in Europa, sostituto Gila, centrale prolifico", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Jimenez","Ruolo":"D","Squadra_SerieA":"Fiorentina","Quotazione":21,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Torna in Serie A, jolly tattico, può giocare ovunque", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
    {"Nome":"Kaiki","Ruolo":"D","Squadra_SerieA":"Como","Quotazione":14,"FantaMedia":5.9,"Consiglio":"scommessa","Note":"Nuovo titolare sinistra, terzino di spinta", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},
    {"Nome":"Çelik","Ruolo":"D","Squadra_SerieA":"Juventus","Quotazione":19,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Duttile, Spalletti può schierarlo in varie occasioni", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},
    {"Nome":"Pulisic","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":57,"FantaMedia":7.8,"Consiglio":"top","Note":"Cambio ruolo, più appetibile, potenziale doppia-doppia", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},
    {"Nome":"Orsolini","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":53,"FantaMedia":7.6,"Consiglio":"top","Note":"Cambio ruolo, bonus garantiti, doppia cifra potenziale", "Quotazione_2025_26":46, "Prezzo_Consigliato":None},
    {"Nome":"McTominay","Ruolo":"C","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.4,"Consiglio":"top","Note":"Doppia cifra, sposta gli equilibri, top", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},
    {"Nome":"Nico Paz","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":48,"FantaMedia":7.3,"Consiglio":"top","Note":"Doppia cifra, top assoluto, crescita esponenziale", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Calhanoglu","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"top","Note":"9 gol, media voto >6.5, migliore del reparto", "Quotazione_2025_26":40, "Prezzo_Consigliato":None},
    {"Nome":"Rabiot","Ruolo":"C","Squadra_SerieA":"Milan","Quotazione":42,"FantaMedia":7.0,"Consiglio":"top","Note":"6 gol, 4 assist, con Allegri era il migliore", "Quotazione_2025_26":38, "Prezzo_Consigliato":None},
    {"Nome":"Vlasic","Ruolo":"C","Squadra_SerieA":"Torino","Quotazione":52,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"8 gol, 3 assist, rigorista, garanzia", "Quotazione_2025_26":39, "Prezzo_Consigliato":None},
    {"Nome":"Frattesi","Ruolo":"C","Squadra_SerieA":"Lazio","Quotazione":48,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Potenziale top, alla Milinkovic-Savic, può esplodere", "Quotazione_2025_26":52, "Prezzo_Consigliato":None},
    {"Nome":"Zaniolo","Ruolo":"C","Squadra_SerieA":"Udinese","Quotazione":48,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"5 gol, 6 assist, attaccante aggiunto", "Quotazione_2025_26":52, "Prezzo_Consigliato":None},
    {"Nome":"Modric","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":43,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Rendimento garantito, media >6.5, esperienza", "Quotazione_2025_26":42, "Prezzo_Consigliato":None},
    {"Nome":"Koné","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":40,"FantaMedia":6.9,"Consiglio":"consigliato","Note":"Media 6.26, mai sotto sufficienza, solido", "Quotazione_2025_26":43, "Prezzo_Consigliato":None},
    {"Nome":"De Bruyne","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":46,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"Se sta bene fa la differenza, calcia rigori", "Quotazione_2025_26":48, "Prezzo_Consigliato":None},
    {"Nome":"Barella","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":44,"FantaMedia":7.0,"Consiglio":"consigliato","Note":"Sempre Barella, secondo slot ideale, affidabile", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},
    {"Nome":"Bernardeschi","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":38,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"Da prendere con Rowe, coppia ideale", "Quotazione_2025_26":36, "Prezzo_Consigliato":None},
    {"Nome":"Rowe","Ruolo":"C","Squadra_SerieA":"Bologna","Quotazione":36,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 3 assist, può crescere", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},
    {"Nome":"Thorstvedt","Ruolo":"C","Squadra_SerieA":"Sassuolo","Quotazione":30,"FantaMedia":6.5,"Consiglio":"consigliato","Note":"5-6 gol potenziali, buon rapporto", "Quotazione_2025_26":26, "Prezzo_Consigliato":None},
    {"Nome":"Perrone","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":35,"FantaMedia":6.7,"Consiglio":"consigliato","Note":"3 gol, 4 assist, voti alti, sottovalutato", "Quotazione_2025_26":36, "Prezzo_Consigliato":None},
    {"Nome":"Alajbegovic","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.6,"Consiglio":"scommessa","Note":"Talentino trequarti, attenzione hype, può fare bene", "Quotazione_2025_26":16, "Prezzo_Consigliato":None},
    {"Nome":"Douglas Luiz","Ruolo":"C","Squadra_SerieA":"Juventus","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Intenzionato a restare, può tornare ai livelli di 2 anni fa", "Quotazione_2025_26":18, "Prezzo_Consigliato":None},
    {"Nome":"Gaetano","Ruolo":"C","Squadra_SerieA":"Atalanta","Quotazione":19,"FantaMedia":6.2,"Consiglio":"scommessa","Note":"Sarri lo vuole, grande intuizione", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Stankovic A.","Ruolo":"C","Squadra_SerieA":"Inter","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Fiducia Chivu, sostituto Calhanoglu", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},
    {"Nome":"Calò","Ruolo":"C","Squadra_SerieA":"Frosinone","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"10 gol, 14 assist in Serie B, grande salto", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},
    {"Nome":"Milla","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":20,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Solo Yamal più assist in Liga, possibile crack", "Quotazione_2025_26":10, "Prezzo_Consigliato":None},
    {"Nome":"Liberali","Ruolo":"C","Squadra_SerieA":"Como","Quotazione":18,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"Giovane dal grande potenziale, spazio con Champions", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
    {"Nome":"Lautaro","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":88,"FantaMedia":8.5,"Consiglio":"top","Note":"Capocannoniere 17 gol, 6 assist, primo slot assoluto", "Quotazione_2025_26":90, "Prezzo_Consigliato":None},
    {"Nome":"Malen","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":84,"FantaMedia":8.2,"Consiglio":"top","Note":"Vice-cannoniere 14 gol, sposta gli equilibri", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
    {"Nome":"Thuram","Ruolo":"A","Squadra_SerieA":"Inter","Quotazione":74,"FantaMedia":7.9,"Consiglio":"top","Note":"13 gol, 6 assist, primo slot nonostante annata deludente", "Quotazione_2025_26":67, "Prezzo_Consigliato":None},
    {"Nome":"Hojlund","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Tornato in Serie A, obiettivo 15 gol, Allegri punta forte", "Quotazione_2025_26":72, "Prezzo_Consigliato":None},
    {"Nome":"Goncalo Ramos","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":78,"FantaMedia":8.0,"Consiglio":"top","Note":"Colpo da 70M, titolare Amorim, può superare doppia cifra", "Quotazione_2025_26":68, "Prezzo_Consigliato":None},
    {"Nome":"Kolo Muani","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":76,"FantaMedia":7.9,"Consiglio":"top","Note":"Tornato alla Juve, Spalletti lo vuole, garanzia", "Quotazione_2025_26":69, "Prezzo_Consigliato":None},
    {"Nome":"Leao","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":72,"FantaMedia":7.8,"Consiglio":"top","Note":"Prima fascia, può migliorare, talento puro", "Quotazione_2025_26":65, "Prezzo_Consigliato":None},
    {"Nome":"Kean","Ruolo":"A","Squadra_SerieA":"Fiorentina","Quotazione":65,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"Doppia cifra garantita, solido", "Quotazione_2025_26":48, "Prezzo_Consigliato":None},
    {"Nome":"Yildiz","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":70,"FantaMedia":7.7,"Consiglio":"consigliato","Note":"10 gol, 6 assist, centro progetto, può esplodere", "Quotazione_2025_26":58, "Prezzo_Consigliato":None},
    {"Nome":"Douvikas","Ruolo":"A","Squadra_SerieA":"Como","Quotazione":65,"FantaMedia":7.8,"Consiglio":"consigliato","Note":"14 gol, sorpresa 2024-25, doppia cifra sicura", "Quotazione_2025_26":64, "Prezzo_Consigliato":None},
    {"Nome":"Dybala","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":58,"FantaMedia":7.4,"Consiglio":"consigliato","Note":"Sempre utile, momento della differenza, clutch", "Quotazione_2025_26":50, "Prezzo_Consigliato":None},
    {"Nome":"Davis","Ruolo":"A","Squadra_SerieA":"Udinese","Quotazione":61,"FantaMedia":7.5,"Consiglio":"consigliato","Note":"10 gol, rigorista, garanzia bonus", "Quotazione_2025_26":53, "Prezzo_Consigliato":None},
    {"Nome":"Scamacca","Ruolo":"A","Squadra_SerieA":"Atalanta","Quotazione":55,"FantaMedia":7.3,"Consiglio":"consigliato","Note":"Attenzione infortuni, ma potenziale top", "Quotazione_2025_26":44, "Prezzo_Consigliato":None},
    {"Nome":"Simeone","Ruolo":"A","Squadra_SerieA":"Napoli","Quotazione":50,"FantaMedia":7.2,"Consiglio":"consigliato","Note":"11 gol, conferma, affidabile", "Quotazione_2025_26":41, "Prezzo_Consigliato":None},
    {"Nome":"Dovbyk","Ruolo":"A","Squadra_SerieA":"Bologna","Quotazione":48,"FantaMedia":7.1,"Consiglio":"consigliato","Note":"Doppia cifra a Bologna, solido", "Quotazione_2025_26":54, "Prezzo_Consigliato":None},
    {"Nome":"Colombo","Ruolo":"A","Squadra_SerieA":"Roma","Quotazione":35,"FantaMedia":6.8,"Consiglio":"consigliato","Note":"7 gol, obiettivo doppia cifra, può crescere", "Quotazione_2025_26":35, "Prezzo_Consigliato":None},
    {"Nome":"Yeboah","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":24,"FantaMedia":6.5,"Consiglio":"scommessa","Note":"Doppia cifra in Serie B, convocato al Mondiale", "Quotazione_2025_26":12, "Prezzo_Consigliato":None},
    {"Nome":"Bowie","Ruolo":"A","Squadra_SerieA":"Sassuolo","Quotazione":25,"FantaMedia":6.4,"Consiglio":"scommessa","Note":"Ex Verona, goal in Serie A li sa fare", "Quotazione_2025_26":14, "Prezzo_Consigliato":None},
    {"Nome":"Alajbegovic K.","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":33,"FantaMedia":6.7,"Consiglio":"scommessa","Note":"Colpo di mercato, trequarti, attenzione hype", "Quotazione_2025_26":17, "Prezzo_Consigliato":None},
    {"Nome":"Rrahmani","Ruolo":"A","Squadra_SerieA":"Venezia","Quotazione":22,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"15 gol in Rep. Ceca, nuovo attaccante titolare", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
    {"Nome":"Ekhator","Ruolo":"A","Squadra_SerieA":"Juventus","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Low cost, potenziale, parte dietro nelle gerarchie", "Quotazione_2025_26":7, "Prezzo_Consigliato":None},
    {"Nome":"Mendy","Ruolo":"A","Squadra_SerieA":"Cagliari","Quotazione":15,"FantaMedia":6.1,"Consiglio":"scommessa","Note":"2 gol in 8 partite, 2007, può esplodere", "Quotazione_2025_26":9, "Prezzo_Consigliato":None},
    {"Nome":"Camarda","Ruolo":"A","Squadra_SerieA":"Milan","Quotazione":12,"FantaMedia":6.0,"Consiglio":"scommessa","Note":"Vice Ramos, a 1 credito ci sta", "Quotazione_2025_26":4, "Prezzo_Consigliato":None},
    {"Nome":"Ratkov","Ruolo":"A","Squadra_SerieA":"Lazio","Quotazione":20,"FantaMedia":6.3,"Consiglio":"scommessa","Note":"Gattuso lo rilancia, puntatina senza esagerare", "Quotazione_2025_26":8, "Prezzo_Consigliato":None},
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

    # Ordina per stagione per trovare l'ultima
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

    # 40% FantaMedia media
    if fm_media >= s["top_fm"]:
        punteggio += 40
    elif fm_media >= s["cons_fm"]:
        punteggio += 25
    else:
        punteggio += max(0, (fm_media / s["cons_fm"]) * 15)

    # 30% Presenze medie
    if pres_media >= s["top_pres"]:
        punteggio += 30
    elif pres_media >= s["cons_pres"]:
        punteggio += 18
    else:
        punteggio += max(0, (pres_media / s["cons_pres"]) * 10)

    # 20% Trend ultima stagione vs media
    if fm_ultima >= fm_media + 0.3:
        punteggio += 20
    elif fm_ultima >= fm_media - 0.3:
        punteggio += 12
    else:
        punteggio += max(0, 5 + (fm_ultima - fm_media) * 10)

    # 10% Bonus produzione offensiva
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


def get_formazione_titolare_serie_a