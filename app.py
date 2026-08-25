import streamlit as st
import pandas as pd
import json
import os
import difflib
from datetime import datetime

# ============================================================
# CONFIG & TEMA
# ============================================================
st.set_page_config(
    page_title="FantaManager 2026/27 - 10 Squadre",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS Custom per tema dark calcistico
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(180deg, #0e1117 0%, #1a1a2e 100%);
    }
    .stSidebar {
        background-color: #16162a !important;
    }
    h1, h2, h3 {
        color: #00d26a !important;
        font-family: 'Segoe UI', sans-serif;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    .stButton>button:hover {
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,210,106,0.3);
    }
    .card-giocatore {
        background: #1e1e3f;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 8px;
        border-left: 4px solid #00d26a;
    }
    .badge-prestito {
        background: #ff6b6b;
        color: white;
        padding: 2px 8px;
        border-radius: 12px;
        font-size: 0.75em;
        font-weight: bold;
    }
    .metric-box {
        background: #1a1a2e;
        border-radius: 10px;
        padding: 16px;
        text-align: center;
        border: 1px solid #2a2a4a;
    }
    div[data-testid="stMetricValue"] {
        font-size: 1.8rem !important;
        font-weight: 700 !important;
    }
</style>
""", unsafe_allow_html=True)

SAVE_FILE = "fantamanager_save.json"
NOMI_SQUADRE = ["BARDO", "NILO", "GALVA", "ROBBA", "PAOLO B.", "ASTI", "DODO", "PECU", "GIOPPY", "BEPPE"]
ANNO_CORRENTE = 2026
CONTRATTO_ANNI = 3
CREDITI_INIZIALI = 50

ROSA_REQ = {"P": 3, "D": 9, "C": 9, "A": 7}

# ============================================================
# LISTONE DEFAULT 2026/2027
# ============================================================
LISTONE_DEFAULT = [
    # ========== PORTIERI ==========
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

    # ========== DIFENSORI ==========
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

    # ========== CENTROCAMPISTI ==========
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

    # ========== ATTACCANTI ==========
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
# UTILITY
# ============================================================
def fuzzy_match(name, choices, cutoff=0.75):
    """Trova il match migliore usando difflib (standard library)."""
    name_clean = str(name).strip().lower()
    matches = difflib.get_close_matches(name_clean, [c.lower() for c in choices], n=1, cutoff=cutoff)
    if matches:
        idx = [c.lower() for c in choices].index(matches[0])
        return choices[idx]
    return None

def get_quotazione_listone(nome):
    """Ritorna la quotazione attuale dal listone."""
    db = st.session_state.giocatori_db
    match = db[db["Nome"].str.lower() == nome.lower()]
    if not match.empty:
        return int(match.iloc[0]["Quotazione"])
    # fallback fuzzy
    nome_match = fuzzy_match(nome, db["Nome"].tolist())
    if nome_match:
        match = db[db["Nome"] == nome_match]
        if not match.empty:
            return int(match.iloc[0]["Quotazione"])
    return None

# ============================================================
# PERSISTENZA
# ============================================================
def save_state():
    data = {
        "squadre": st.session_state.squadre,
        "storico_mercato": st.session_state.storico_mercato,
        "watchlist": st.session_state.watchlist,
        "prestiti": st.session_state.prestiti,
        "contratti": st.session_state.contratti,
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
        "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if hasattr(st.session_state.stats_storiche, 'to_dict') else [],
        "stats_per_stagione": {k: v.to_dict(orient="records") for k, v in st.session_state.get("stats_per_stagione", {}).items()},
        "crediti_iniziali": st.session_state.get("crediti_iniziali", CREDITI_INIZIALI),
        "quotazioni_2025_26": st.session_state.quotazioni_2025_26.to_dict(orient="records") if hasattr(st.session_state.quotazioni_2025_26, 'to_dict') else [],
        "wizard_completato": st.session_state.get("wizard_completato", False),
    }
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def load_state():
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
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
            st.session_state.crediti_iniziali = data.get("crediti_iniziali", CREDITI_INIZIALI)
            q25 = data.get("quotazioni_2025_26", [])
            st.session_state.quotazioni_2025_26 = pd.DataFrame(q25) if q25 else pd.DataFrame()
            st.session_state.wizard_completato = data.get("wizard_completato", False)
            for sq in NOMI_SQUADRE:
                if sq not in st.session_state.squadre:
                    st.session_state.squadre[sq] = {"crediti": st.session_state.crediti_iniziali, "rosa": []}
            return True
        except Exception:
            pass
    return False

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
    st.session_state.wizard_completato = False

    if not load_state():
        for sq in NOMI_SQUADRE:
            st.session_state.squadre[sq] = {"crediti": CREDITI_INIZIALI, "rosa": []}

    st.session_state.initialized = True

# ============================================================
# RIEPILOGO ROSA
# ============================================================
def riepilogo_rosa(squadra_nome):
    rosa = st.session_state.squadre[squadra_nome]["rosa"]
    crediti = st.session_state.squadre[squadra_nome]["crediti"]
    # Conta TUTTI i giocatori in rosa (compresi prestiti in entrata) per i 28
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

    # Prestiti in uscita = giocatori che ho dato io in prestito (tracciati in prestiti)
    prestiti_uscita = [p for p in st.session_state.prestiti if p["Da"] == squadra_nome]
    riepilogo["crediti"] = crediti
    riepilogo["tot_mancanti"] = tot_mancanti
    riepilogo["tot_posseduti"] = len(rosa)
    riepilogo["tot_prestiti_uscita"] = len(prestiti_uscita)
    riepilogo["tot_giocatori_posseduti"] = len(rosa) + len(prestiti_uscita)
    return riepilogo

# ============================================================
# CALCOLO PREZZO CONSIGLIATO
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

    prezzo = base * fattore_fm * fattore_fascia * fattore_trend * fattore_affare
    prezzo = max(1, round(prezzo))

    spiegazione = (
        f"**Base listone:** {int(base)}cr\n"
        f"**FantaMedia:** {fm} (media ruolo {ruolo}: {media_rif}) → fattore {fattore_fm:.2f}\n"
        f"**Fascia:** {fascia} → fattore {fattore_fascia:.2f}\n"
        f"**Indice affare:** {indice_affare:.3f} → fattore {fattore_affare:.2f}\n"
    )
    if trend_note:
        spiegazione += f"**Statistiche:**{trend_note} → fattore {fattore_trend:.2f}\n"
    spiegazione += f"\n**💡 Prezzo consigliato: {prezzo}cr**"
    return prezzo, spiegazione

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

# ============================================================
# WIZARD SETUP INIZIALE
# ============================================================
def check_wizard_needed():
    """Ritorna True se tutte le rose sono vuote e il wizard non è stato completato."""
    if st.session_state.get("wizard_completato", False):
        return False
    return all(len(st.session_state.squadre[sq]["rosa"]) == 0 for sq in NOMI_SQUADRE)

def render_wizard():
    st.header("⚽ Benvenuto in FantaManager 2026/27")
    st.markdown("Configura la tua lega in pochi passaggi.")

    step = st.session_state.get("wizard_step", 1)
    progress = (step / 4) * 100
    st.progress(int(progress), text=f"Passaggio {step} di 4")

    if step == 1:
        st.subheader("1. Listone Giocatori")
        st.markdown("Puoi usare il listone pre-caricato o importarne uno personalizzato.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("✅ Usa Listone Default", use_container_width=True):
                st.session_state.giocatori_db = pd.DataFrame(LISTONE_DEFAULT)
                st.session_state.wizard_step = 2
                save_state()
                st.rerun()
        with c2:
            st.markdown("📁 *Importa listone personalizzato dalla sidebar dopo il setup*")
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
        st.markdown("Se hai un file con le rose della stagione scorsa, puoi importarlo ora. Altrimenti salta.")
        c1, c2 = st.columns(2)
        with c1:
            if st.button("⏭️ Salta", use_container_width=True):
                st.session_state.wizard_step = 4
                st.rerun()
        with c2:
            st.markdown("📁 *Usa la sezione Importa Rose nella sidebar dopo il setup*")
            if st.button("Vai alla sidebar per importare", use_container_width=True):
                st.info("Usa l'expander 'Importa Rose' nella sidebar a sinistra, poi torna qui e clicca Salta.")

    elif step == 4:
        st.subheader("4. Pronto!")
        st.success("Setup completato. Buon divertimento!")
        if st.button("🚀 Inizia", type="primary", use_container_width=True):
            st.session_state.wizard_completato = True
            save_state()
            st.rerun()

# ============================================================
# SIDEBAR RISTRUTTURATA
# ============================================================
with st.sidebar:
    st.title("⚽ FantaManager")
    st.caption("2026/27 — 10 Squadre")
    st.markdown("---")

    # --- SALVATAGGIO RAPIDO ---
    st.subheader("💾 Backup Rapido")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("💾 Salva", use_container_width=True):
            save_state()
            st.success("Salvato!")
    with c2:
        if st.button("📂 Carica", use_container_width=True):
            if load_state():
                st.success("Caricato!")
                st.rerun()
            else:
                st.warning("Nessun salvataggio trovato.")

    # Download stato completo
    save_data = {
        "squadre": st.session_state.squadre,
        "storico_mercato": st.session_state.storico_mercato,
        "watchlist": st.session_state.watchlist,
        "prestiti": st.session_state.prestiti,
        "contratti": st.session_state.contratti,
        "giocatori_db": st.session_state.giocatori_db.to_dict(orient="records"),
        "stats_storiche": st.session_state.stats_storiche.to_dict(orient="records") if hasattr(st.session_state.stats_storiche, 'to_dict') else [],
        "stats_per_stagione": {k: v.to_dict(orient="records") for k, v in st.session_state.get("stats_per_stagione", {}).items()},
        "quotazioni_2025_26": st.session_state.quotazioni_2025_26.to_dict(orient="records") if hasattr(st.session_state.quotazioni_2025_26, 'to_dict') else [],
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

    # Carica da PC
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
        save_state()
        st.success("Crediti squadre aggiornati!")
        st.rerun()

    st.markdown("---")
    with st.expander("📁 Importa Dati"):
        st.caption("Listone, Rose, Quotazioni 2025/26, Statistiche")
        st.info("Usa le pagine dedicate nel menu principale per importare dati.")

    with st.expander("⚠️ Reset"):
        if st.button("🗑️ Resetta TUTTO", use_container_width=True):
            if os.path.exists(SAVE_FILE):
                os.remove(SAVE_FILE)
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.success("Resettato! Ricarica la pagina.")
            st.rerun()

    st.markdown("---")
    st.markdown("---")

# ============================================================
# NAVIGAZIONE
# ============================================================
menu = st.sidebar.selectbox("Navigazione", [
    "🏠 Dashboard",
    "🔍 Scouting & Database",
    "🔨 Asta Live",
    "🛒 Mercato",
    "🤝 Scambi & Prestiti",
    "📋 Rose & Contratti",
    "📈 Statistiche Storiche",
    "⚙️ Importa & Esporta"
])

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

    # Alert scadenze all'avvio
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
        # Prestiti in uscita
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
        in_rosa = set()
        for d in st.session_state.squadre.values():
            for g in d["rosa"]:
                in_rosa.add(g["Nome"].lower())
        svinc = db[~db["Nome"].str.lower().isin(in_rosa)] if not db.empty else pd.DataFrame()
        st.metric("Svincolati", len(svinc))
    with c5:
        st.metric("Contratti in Scadenza", tot_scadenze)

    st.markdown("---")
    st.subheader("🏆 Top 5 Affari Liberi")
    if not svinc.empty:
        svinc["Indice_Affare"] = round(svinc["FantaMedia"] / svinc["Quotazione"].replace(0,1), 2)
        top5 = svinc.nlargest(5, "Indice_Affare")[["Nome","Ruolo","Squadra_SerieA","Quotazione","FantaMedia","Indice_Affare","Consiglio"]]
        st.dataframe(top5, use_container_width=True, hide_index=True)
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
    st.subheader("💰 Classifica Crediti")
    crediti_df = pd.DataFrame([{"Squadra": sq, "Crediti": st.session_state.squadre[sq]["crediti"]} for sq in NOMI_SQUADRE]).sort_values("Crediti", ascending=False)
    st.bar_chart(crediti_df.set_index("Squadra"))


# ============================================================
# UTIL: Merge stats 2026-27 nel listone
# ============================================================
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

# ============================================================
# 1. SCOUTING
# ============================================================
if menu == "🔍 Scouting & Database":
    st.header("🔍 Hub Scouting 2026/27")
    df = st.session_state.giocatori_db.copy()
    df = arricchisci_con_stats_2627(df)
    if "2026-27" in st.session_state.get("stats_per_stagione", {}):
        st.caption("📊 Dati arricchiti con statistiche 2026/27 caricate")

    if df.empty:
        st.warning("Nessun giocatore nel database.")
    else:
        df["Indice_Affare"] = round(df["FantaMedia"] / df["Quotazione"].replace(0,1), 2)
        if "Quotazione_2025_26" in df.columns:
            df["Variazione_%"] = round((df["Quotazione"] - df["Quotazione_2025_26"]) / df["Quotazione_2025_26"].replace(0,1) * 100, 1)
        else:
            df["Variazione_%"] = None

        assegnati = {}
        for sq, dati in st.session_state.squadre.items():
            for g in dati["rosa"]:
                assegnati[g["Nome"].lower()] = sq
        df["Proprietario"] = df["Nome"].apply(lambda x: assegnati.get(x.lower(), "Svincolato 🟢"))

        with st.expander("🔧 Filtri Avanzati", expanded=True):
            f0, f1, f2, f3, f4, f5 = st.columns(6)
            with f0:
                sq_budget = st.selectbox("Budget Squadra", ["Nessuno"] + NOMI_SQUADRE, key="scout_budget_sq")
                filtro_budget = st.checkbox("Solo chi posso permettermi", value=False, key="scout_budget_chk")
            with f1:
                ruoli = sorted(df["Ruolo"].unique()) if "Ruolo" in df.columns else ["P","D","C","A"]
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
                min_fm_s, max_fm_s = (round(float(fm_vals.min()),1), round(float(fm_vals.max()),1)) if len(fm_vals) > 0 else (4.0, 10.0)
                if min_fm_s == max_fm_s:
                    min_fm_s, max_fm_s = round(max(4.0, min_fm_s - 1.0), 1), round(min(10.0, max_fm_s + 1.0), 1)
                range_fm = st.slider("FantaMedia", min_value=min_fm_s, max_value=max_fm_s, value=(min_fm_s, max_fm_s), step=0.1, key="scout_fm")
            with f5:
                consigli_fasce = st.multiselect("Fascia", ["top","consigliato","scommessa"], default=["top","consigliato","scommessa"], key="scout_fascia")

            f6, f7 = st.columns(2)
            with f6:
                solo_svinc = st.checkbox("Solo Svincolati", value=False, key="scout_svinc")
                search = st.text_input("Cerca nome", key="scout_search")
            with f7:
                if "Variazione_%" in df.columns:
                    var_vals = pd.to_numeric(df["Variazione_%"], errors="coerce").dropna()
                    var_min, var_max = (round(float(var_vals.min()),1), round(float(var_vals.max()),1)) if len(var_vals) > 0 else (-100.0, 100.0)
                    if var_min == var_max:
                        var_min, var_max = var_min - 5.0, var_max + 5.0
                    range_var = st.slider("Variazione % (2025→2026)", min_value=var_min, max_value=var_max, value=(var_min, var_max), key="scout_var")
                else:
                    range_var = (-100, 100)

        df_f = df[
            (df["Ruolo"].isin(filtro_ruolo)) &
            (df["FantaMedia"] >= range_fm[0]) & (df["FantaMedia"] <= range_fm[1]) &
            (df["Quotazione"] >= range_q[0]) & (df["Quotazione"] <= range_q[1]) &
            (df["Consiglio"].isin(consigli_fasce))
        ]
        if "Tutte" not in filtro_sa and "Squadra_SerieA" in df.columns:
            df_f = df_f[df_f["Squadra_SerieA"].isin(filtro_sa)]
        if solo_svinc:
            df_f = df_f[df_f["Proprietario"] == "Svincolato 🟢"]
        if search:
            df_f = df_f[df_f["Nome"].str.contains(search, case=False, na=False)]
        if "Variazione_%" in df.columns:
            df_f = df_f[(df_f["Variazione_%"] >= range_var[0]) & (df_f["Variazione_%"] <= range_var[1])]

        if filtro_budget and sq_budget != "Nessuno":
            riep_b = riepilogo_rosa(sq_budget)
            crediti_disp = riep_b["crediti"]
            ruoli_mancanti = [r for r in ROSA_REQ if riep_b[r]["mancanti"] > 0]
            df_f = df_f[df_f["Quotazione"] <= crediti_disp]
            df_f = df_f[df_f["Ruolo"].isin(ruoli_mancanti)]
            st.info(f"💰 Filtro budget attivo per **{sq_budget}**: {crediti_disp}cr disponibili, ruoli mancanti: {', '.join(ruoli_mancanti)}")

        df_f = df_f.sort_values(by="Indice_Affare", ascending=False)

        st.markdown("---")
        st.subheader("📊 Riepilogo Mercato")
        col_m1, col_m2, col_m3, col_m4 = st.columns(4)
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
                        st.markdown(
                            f"<div style='background:#1a1a2e;padding:6px;border-radius:6px;margin-bottom:4px;'>"
                            f"<b>{row['Nome']}</b> ({row['Squadra_SerieA']})<br/>"
                            f"<span style='color:#888;font-size:0.85em;'>FM {row['FantaMedia']} | Q {int(row['Quotazione'])}cr | IA {row['Indice_Affare']}</span> {pc_txt}"
                            f"</div>",
                            unsafe_allow_html=True
                        )
                else:
                    st.caption("Nessuno svincolato")

        st.markdown("---")
        st.subheader(f"📋 Risultati: {len(df_f)} giocatori")
        display_cols = [c for c in ["Nome","Ruolo","Squadra_SerieA","Quotazione","Prezzo_Consigliato","Quotazione_2025_26","Variazione_%","FantaMedia","Indice_Affare","Proprietario","Consiglio","Note"] if c in df_f.columns]
        st.dataframe(df_f[display_cols], use_container_width=True)

        st.markdown("---")
        st.subheader("⚔️ Confronto Giocatori")
        g1_c = st.selectbox("Giocatore 1", df["Nome"].values, key="comp1")
        g2_c = st.selectbox("Giocatore 2", df["Nome"].values, index=1 if len(df) > 1 else 0, key="comp2")
        if g1_c and g2_c:
            r1 = df[df["Nome"] == g1_c].iloc[0]
            r2 = df[df["Nome"] == g2_c].iloc[0]
            comp_data = {
                "Stat": ["Ruolo", "Squadra", "Quotazione", "FantaMedia", "Indice Affare", "Proprietario"],
                g1_c: [r1["Ruolo"], r1["Squadra_SerieA"], f"{int(r1['Quotazione'])}cr", r1["FantaMedia"], r1["Indice_Affare"], r1["Proprietario"]],
                g2_c: [r2["Ruolo"], r2["Squadra_SerieA"], f"{int(r2['Quotazione'])}cr", r2["FantaMedia"], r2["Indice_Affare"], r2["Proprietario"]]
            }
            if "Variazione_%" in df.columns:
                comp_data["Stat"].insert(4, "Variazione %")
                comp_data[g1_c].insert(4, f"{r1['Variazione_%']}%")
                comp_data[g2_c].insert(4, f"{r2['Variazione_%']}%")
            st.dataframe(pd.DataFrame(comp_data), use_container_width=True, hide_index=True)
            if r1["Indice_Affare"] > r2["Indice_Affare"]:
                st.success(f"🏆 {g1_c} ha un indice affare migliore ({r1['Indice_Affare']} vs {r2['Indice_Affare']})")
            elif r2["Indice_Affare"] > r1["Indice_Affare"]:
                st.success(f"🏆 {g2_c} ha un indice affare migliore ({r2['Indice_Affare']} vs {r1['Indice_Affare']})")
            else:
                st.info("⚖️ Indice affare identico")

        st.markdown("---")
        st.subheader("💰 Chi può Permetterselo?")
        g_target = st.selectbox("Giocatore da analizzare", df["Nome"].values, key="g_target")
        if g_target:
            info_t = df[df["Nome"] == g_target].iloc[0]
            ruolo_t = info_t["Ruolo"]
            quot_t = int(info_t["Quotazione"])
            st.markdown(f"**{g_target}** — {ruolo_t} | Quotazione: {quot_t}cr")
            avv_data = []
            for sq_avv in NOMI_SQUADRE:
                riep_avv = riepilogo_rosa(sq_avv)
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

        st.markdown("---")
        st.subheader("✏️ Modifica Prezzi Consigliati")
        editor_cols = [c for c in ["Nome","Ruolo","Squadra_SerieA","Quotazione","FantaMedia","Prezzo_Consigliato","Consiglio","Note"] if c in df.columns]
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
        st.subheader("⭐ Watchlist")
        g_sel = st.selectbox("Aggiungi giocatore", df["Nome"].values, key="wl")
        if st.button("Aggiungi"):
            if g_sel not in st.session_state.watchlist:
                st.session_state.watchlist.append(g_sel)
                save_state()
                st.success(f"{g_sel} aggiunto!")
                st.rerun()
        if st.session_state.watchlist:
            df_wl = df[df["Nome"].isin(st.session_state.watchlist)].copy()
            stats_df = st.session_state.stats_storiche if not st.session_state.stats_storiche.empty else None
            df_wl["Prezzo_AI"] = df_wl.apply(lambda row: calcola_prezzo_consigliato(row.to_dict(), stats_df)[0], axis=1)
            if "Quotazione_2025_26" in df_wl.columns and "Variazione_%" not in df_wl.columns:
                df_wl["Variazione_%"] = round((df_wl["Quotazione"] - df_wl["Quotazione_2025_26"]) / df_wl["Quotazione_2025_26"].replace(0,1) * 100, 1)
            wl_cols = ["Nome","Ruolo","Squadra_SerieA","Quotazione","Quotazione_2025_26","Variazione_%","Prezzo_Consigliato","Prezzo_AI","FantaMedia","Indice_Affare","Proprietario"]
            wl_cols = [c for c in wl_cols if c in df_wl.columns]
            st.dataframe(df_wl[wl_cols], use_container_width=True)
            if st.button("Svuota Watchlist"):
                st.session_state.watchlist = []
                save_state()
                st.rerun()


# ============================================================
# 2. ASTA LIVE (NUOVO)
# ============================================================
if menu == "🔨 Asta Live":
    st.header("🔨 Gestione Asta")
    st.caption("Gestisci l'asta in tempo reale: seleziona giocatore, raccogli offerte, assegna.")

    db = st.session_state.giocatori_db
    if db.empty:
        st.warning("Importa prima un listone.")
    else:
        in_rosa = set()
        for d in st.session_state.squadre.values():
            for g in d["rosa"]:
                in_rosa.add(g["Nome"].lower())
        svinc = db[~db["Nome"].str.lower().isin(in_rosa)].copy()

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
                        import random
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

                st.markdown(f"### {g_asta} — {info['Ruolo']} | {info['Squadra_SerieA']}")
                st.caption(f"FantaMedia: {info['FantaMedia']} | Fascia: {info.get('Consiglio','')} | {info.get('Note','')}")

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

                offerte = {}
                ruolo_g = info["Ruolo"]
                quot_g = int(info["Quotazione"])
                cols_off = st.columns(5)
                for idx_sq, sq in enumerate(NOMI_SQUADRE):
                    with cols_off[idx_sq % 5]:
                        riep_sq = riepilogo_rosa(sq)
                        off_max = riep_sq[ruolo_g]["offerta_max"]
                        crediti_sq = riep_sq["crediti"]
                        ha_gia = any(g["Nome"].lower() == g_asta.lower() for g in st.session_state.squadre[sq]["rosa"])
                        st.markdown(f"**{sq}**")
                        st.caption(f"💰 {crediti_sq}cr | Max: {off_max}cr")
                        if ha_gia:
                            st.warning("Già in rosa")
                            offerte[sq] = 0
                        else:
                            offerte[sq] = st.number_input(
                                f"Offerta {sq}", min_value=0, max_value=crediti_sq,
                                value=min(pc_ai, off_max) if off_max >= quot_g else 0,
                                step=1, key=f"off_{sq}"
                            )
                            if offerte[sq] > off_max:
                                st.caption(f"⚠️ Superiore al max ({off_max})")
                            elif offerte[sq] > crediti_sq:
                                st.caption("❌ Oltre i crediti")

                st.markdown("---")
                # Trova vincitore
                offerte_valide = {k: v for k, v in offerte.items() if v > 0}
                if offerte_valide:
                    vincitore = max(offerte_valide, key=offerte_valide.get)
                    prezzo_vincita = offerte_valide[vincitore]
                    st.success(f"🏆 Miglior offerente: **{vincitore}** con **{prezzo_vincita}cr**")

                    if st.button("✅ Assegna Giocatore", type="primary", use_container_width=True):
                        if st.session_state.squadre[vincitore]["crediti"] >= prezzo_vincita:
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
                            # Pulisci asta corrente
                            if "asta_giocatore_corrente" in st.session_state:
                                del st.session_state["asta_giocatore_corrente"]
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
            in_rosa = set()
            for d in st.session_state.squadre.values():
                for g in d["rosa"]:
                    in_rosa.add(g["Nome"].lower())
            svinc = db[~db["Nome"].str.lower().isin(in_rosa)]
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
                for sq_avv in NOMI_SQUADRE:
                    if sq_avv == sq:
                        continue
                    riep_avv = riepilogo_rosa(sq_avv)
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
        # Escludi i prestiti in entrata (quelli che hanno Prestito_Da diverso dalla squadra corrente)
        rosa_proprieta = [g for g in rosa if g.get("Prestito_Da") is None or g.get("Prestito_Da") == sq_v]
        if rosa_proprieta:
            nomi = [g["Nome"] for g in rosa_proprieta]
            g_v = st.selectbox("Giocatore", nomi, key="vend_g")
            g_obj = next(g for g in rosa_proprieta if g["Nome"] == g_v)

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
                st.session_state.squadre[sq_v]["rosa"] = [g for g in rosa if g["Nome"] != g_v]
                st.session_state.squadre[sq_v]["crediti"] += prezzo_v
                if g_v in st.session_state.contratti:
                    del st.session_state.contratti[g_v]
                st.session_state.storico_mercato.insert(0, {
                    "Data": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "Operazione": "SVINCOLO",
                    "Dettagli": f"{sq_v} svincola {g_v}, incassa {prezzo_v}cr"
                })
                save_state()
                st.success(f"🗑️ {g_v} svincolato! Incassati {prezzo_v}cr.")
                st.rerun()
        else:
            st.info("Nessun giocatore di proprietà nella rosa.")

    with t_rinn:
        st.subheader("🔄 Rinnova Contratto")
        st.info("Il rinnovo estende il contratto a 3 anni dalla data attuale (con mese di scadenza) e aggiorna il costo alla quotazione di listone corrente.")
        sq_r = st.selectbox("Squadra", NOMI_SQUADRE, key="rinn_sq")
        rosa_r = st.session_state.squadre[sq_r]["rosa"]
        # Solo giocatori di proprietà (non prestiti in entrata)
        rosa_rinnovabili = [g for g in rosa_r if g.get("Prestito_Da") is None or g.get("Prestito_Da") == sq_r]
        if rosa_rinnovabili:
            nomi_r = [g["Nome"] for g in rosa_rinnovabili]
            g_r = st.selectbox("Giocatore da rinnovare", nomi_r, key="rinn_g")
            g_obj_r = next(g for g in rosa_rinnovabili if g["Nome"] == g_r)

            scad_attuale = g_obj_r.get("Scadenza_Anno", ANNO_CORRENTE + CONTRATTO_ANNI)
            costo_attuale = g_obj_r.get("Costo_Acquisto", 0)

            # Trova quotazione listone attuale
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
                    # Scala i crediti
                    st.session_state.squadre[sq_r]["crediti"] -= costo_rinnovo
                    # Aggiorna giocatore in rosa
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
# 4. SCAMBI & PRESTITI (RIVISTO — campi strutturati, nome pulito)
# ============================================================
if menu == "🤝 Scambi & Prestiti":
    st.header("🤝 Scambi Definitivi & Prestiti")

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("Squadra A")
        sq1 = st.selectbox("Squadra 1", NOMI_SQUADRE, key="sc1")
        # Rosa di proprietà (esclude prestiti in entrata)
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
                    # Rimuovi dalla rosa in prestito
                    st.session_state.squadre[a_sq]["rosa"] = [
                        g for g in st.session_state.squadre[a_sq]["rosa"]
                        if not (g.get("Nome") == gp and g.get("Prestito_Da") == da_sq)
                    ]
                    # Verifica se è già in rosa al proprietario
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
                save_state()
                st.success(f"✅ {gp} rientrato da prestito!")
                st.rerun()

# ============================================================
# 5. ROSE, CREDITI & CONTRATTI (con Rinnovo)
# ============================================================
if menu == "📋 Rose & Contratti":
    st.header("📋 Riepilogo Rose, Crediti & Contratti")

    tab_singole, tab_matrice, tab_contratti, tab_consigli = st.tabs(["🛡️ Squadre", "📊 Matrice", "📄 Contratti", "💡 Consigli 2026/27"])

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
                    display = rosa_df.copy()

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

                    # Badge prestito
                    def badge_prestito(row):
                        if pd.notna(row.get("Prestito_Da")) and row.get("Prestito_Da") != sq:
                            return f"<span class='badge-prestito'>PRESTITO da {row['Prestito_Da']}</span>"
                        return ""
                    display["Badge"] = display.apply(badge_prestito, axis=1)

                    if "Quotazione_2025_26" in st.session_state.giocatori_db.columns:
                        db_q = st.session_state.giocatori_db[["Nome","Quotazione_2025_26"]].copy()
                        display = display.merge(db_q, on="Nome", how="left")
                        display["Variazione_%"] = round((display["Quotazione"] - display["Quotazione_2025_26"]) / display["Quotazione_2025_26"].replace(0,1) * 100, 1)

                    hide_cols = ["Anno_Acquisto", "Contratto_Anni", "Prestito_A", "Prestito_Durata_Mesi", "Prestito_Anno_Inizio"]
                    display = display.drop(columns=[c for c in hide_cols if c in display.columns])

                    first_cols = [c for c in ["Nome", "Ruolo", "Stato_Contratto", "Scadenza", "Badge"] if c in display.columns]
                    other_cols = [c for c in display.columns if c not in first_cols]
                    display = display[first_cols + other_cols]

                    # Visualizza come HTML per i badge
                    st.write(display.to_html(escape=False, index=False), unsafe_allow_html=True)

                    # Rinnovo rapido inline
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
                                    save_state()
                                    st.success(f"✅ {g_rinn} rinnovato!")
                                    st.rerun()

                    # Riepilogo rosa
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
        consigli = {
            "Portieri": {
                "top": ["Svilar (Roma) - 18 clean sheet, FM 6.0", "Carnesecchi (Atalanta) - 13 CS, media 6.5", "Maignan (Milan) - 13 CS, 2 rigori parati", "Butez (Como) - 19 CS, miglior difesa"],
                "consigliati": ["Martinez (Inter) - nuovo titolare, fiducia Chivu", "Meret (Napoli) - sottovalutato con Allegri", "De Gea (Fiorentina) - stagione del riscatto", "Vicario (Juve) - ex Empoli, top in Serie A", "Mandas (Lazio) - portiere da modificatore"],
                "scommesse": ["Falcone (Lecce) - media voto 6.41, low cost", "Stankovic (Venezia) - torna in A", "Corvi (Parma) - nuovo titolare", "Caprile (Cagliari) - modificatore"]
            },
            "Difensori": {
                "top": ["Dimarco (Inter) - top assoluto, +3 a giornata", "Bremer (Juve) - 4 gol, 3 assist, FM 6.9", "Bisseck (Inter) - voti alti e bonus", "Mancini (Roma) - 4 gol, leader difesa Gasperini", "Wesley (Roma) - 5 gol, potenziale alla Gosens"],
                "consigliati": ["Pavlovic (Milan) - 5 gol, media 6.24", "Ostigard (Napoli) - 5 gol, centrale prolifico", "Cambiaso (Juve) - 3 gol, 4 assist", "Spinazzola (Roma) - sottovalutato, bonus garantiti", "Zappacosta (Atalanta) - gran gamba", "Di Lorenzo (Napoli) - 6-7 bonus potenziali", "Kempf (Como) - certezza voti e bonus"],
                "scommesse": ["Rensch (Roma) - 1 gol, 4 assist in 19 partite", "Doekhi (Lazio) - 7 gol in Europa, sostituto Gila", "Jimenez (Fiorentina) - jolly tattico", "Kaiki (Como) - terzino di spinta", "Çelik (Juve) - duttile, Spalletti lo schiera"]
            },
            "Centrocampisti": {
                "top": ["Pulisic (Milan) - cambio ruolo, doppia-doppia potenziale", "Orsolini (Bologna) - cambio ruolo, bonus garantiti", "McTominay (Napoli) - doppia cifra, sposta equilibri", "Nico Paz (Inter) - doppia cifra, top assoluto", "Calhanoglu (Inter) - 9 gol, media >6.5", "Rabiot (Milan) - 6 gol, 4 assist"],
                "consigliati": ["Vlasic (Torino) - 8 gol, rigorista", "Frattesi (Lazio) - alla Milinkovic-Savic", "Zaniolo (Udinese) - 5 gol, 6 assist", "Modric (Inter) - rendimento garantito", "Koné (Juve) - mai sotto sufficienza", "De Bruyne (Juve) - calcia rigori", "Barella (Inter) - secondo slot ideale", "Bernardeschi (Bologna) - da prendere con Rowe", "Rowe (Bologna) - 3 gol, 3 assist", "Thorstvedt (Sassuolo) - 5-6 gol potenziali"],
                "scommesse": ["Alajbegovic (Juve) - talentino trequarti", "Douglas Luiz (Juve) - può tornare ai livelli di 2 anni fa", "Gaetano (Atalanta) - Sarri lo vuole", "Stankovic A. (Inter) - fiducia Chivu", "Calò (Frosinone) - 10 gol, 14 assist in B", "Milla (Como) - solo Yamal più assist in Liga", "Liberali (Como) - giovane, spazio con Champions"]
            },
            "Attaccanti": {
                "top": ["Lautaro (Inter) - capocannoniere 17 gol", "Malen (Roma) - vice-cannoniere 14 gol", "Thuram (Inter) - 13 gol, primo slot", "Hojlund (Napoli) - obiettivo 15 gol, Allegri punta forte", "Goncalo Ramos (Milan) - colpo 70M, titolare Amorim", "Kolo Muani (Juve) - Spalletti lo vuole", "Leao (Milan) - prima fascia, talento puro"],
                "consigliati": ["Kean (Fiorentina) - doppia cifra garantita", "Yildiz (Juve) - 10 gol, centro progetto", "Douvikas (Como) - 14 gol, sorpresa 2024-25", "Dybala (Roma) - sempre utile, clutch", "Davis (Udinese) - 10 gol, rigorista", "Scamacca (Atalanta) - attenzione infortuni", "Simeone (Napoli) - 11 gol, conferma", "Dovbyk (Bologna) - doppia cifra", "Colombo (Roma) - 7 gol, obiettivo doppia cifra"],
                "scommesse": ["Yeboah (Venezia) - doppia cifra in Serie B, convocato Mondiale", "Bowie (Sassuolo) - ex Verona, goal li sa fare", "Alajbegovic K. (Juve) - colpo di mercato", "Rrahmani (Venezia) - 15 gol in Rep. Ceca", "Ekhator (Juve) - low cost, potenziale", "Mendy (Cagliari) - 2 gol in 8 partite, 2007", "Camarda (Milan) - vice Ramos, a 1cr ci sta", "Ratkov (Lazio) - Gattuso lo rilancia"]
            }
        }
        for ruolo, dati in consigli.items():
            with st.expander(ruolo):
                st.markdown("**⭐ Top:** " + " • ".join(dati["top"]))
                st.markdown("**👍 Consigliati:** " + " • ".join(dati["consigliati"]))
                st.markdown("**🎲 Scommesse:** " + " • ".join(dati["scommesse"]))


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
# 7. IMPORTA & ESPORTA (pagina dedicata)
# ============================================================
if menu == "⚙️ Importa & Esporta":
    st.header("⚙️ Importa & Esporta Dati")
    st.caption("Tutte le operazioni di import/export in un'unica pagina.")

    tab_exp, tab_imp_listone, tab_imp_rose, tab_imp_q25 = st.tabs([
        "📤 Esporta Backup", "📁 Importa Listone", "📋 Importa Rose", "📊 Importa Quotazioni 2025/26"
    ])

    with tab_exp:
        st.subheader("📤 Esporta Backup Completo (Excel)")
        import io
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
                                df_q['Quotazione_2025_26'] = pd.to_numeric(df_q[col], errors='coerce')
                                break
                    df_q['Quotazione_2025_26'] = pd.to_numeric(df_q['Quotazione_2025_26'], errors='coerce').fillna(1).astype(int)
                    df_q = df_q[['Nome', 'Quotazione_2025_26']].dropna()
                    st.session_state.quotazioni_2025_26 = df_q
                    save_state()
                    st.success(f"✅ Caricate {len(df_q)} quotazioni 2025/26!")
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
