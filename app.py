#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FantaManager 2026/27 - Gestione Fantacalcio
===========================================
App Python per gestire rose, acquisti, scambi, prestiti e consigli
per la stagione di Fantacalcio 2026/2027.

Funzionalità:
- Gestione squadre e rose
- Listone giocatori Serie A con consigli
- Acquisti (contratto automatico 4 anni)
- Scambi tra squadre (con denaro)
- Prestiti (6 mesi o 1 anno, con denaro)
- Consigli per l'asta per ruolo
- Salvataggio/caricamento dati su file JSON

Uso:
    python fantamanager.py
"""

import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DATA_FILE = "fantamanager_data.json"

# ============================================================
# DATI DI DEFAULT - Listone Serie A 2026/2027
# ============================================================
DEFAULT_PLAYERS = [
    # PORTIERI
    {"id": "p1", "nome": "Butez", "ruolo": "P", "squadra": "Como", "prezzo": 32, "consiglio": "top", "note": "19 clean sheet, miglior difesa"},
    {"id": "p2", "nome": "Maignan", "ruolo": "P", "squadra": "Milan", "prezzo": 34, "consiglio": "top", "note": "13 clean sheet, 2 rigori parati"},
    {"id": "p3", "nome": "Svilar", "ruolo": "P", "squadra": "Roma", "prezzo": 38, "consiglio": "top", "note": "18 clean sheet, fantamedia 6"},
    {"id": "p4", "nome": "Martinez", "ruolo": "P", "squadra": "Inter", "prezzo": 29, "consiglio": "consigliato", "note": "Nuovo titolare, ex Genoa"},
    {"id": "p5", "nome": "Meret", "ruolo": "P", "squadra": "Napoli", "prezzo": 30, "consiglio": "consigliato", "note": "Titolare con Allegri"},
    {"id": "p6", "nome": "Carnesecchi", "ruolo": "P", "squadra": "Atalanta", "prezzo": 34, "consiglio": "consigliato", "note": "Miglior fantamedia, 13 clean sheet"},
    {"id": "p7", "nome": "De Gea", "ruolo": "P", "squadra": "Fiorentina", "prezzo": 24, "consiglio": "consigliato", "note": "Stagione del riscatto"},
    {"id": "p8", "nome": "Falcone", "ruolo": "P", "squadra": "Lecce", "prezzo": 17, "consiglio": "scommessa", "note": "Media voto 6.41, low cost"},
    {"id": "p9", "nome": "Stankovic", "ruolo": "P", "squadra": "Venezia", "prezzo": 13, "consiglio": "scommessa", "note": "Torna in Serie A"},
    # DIFENSORI
    {"id": "d1", "nome": "Dimarco", "ruolo": "D", "squadra": "Inter", "prezzo": 45, "consiglio": "top", "note": "Top assoluto, vale un +3 a giornata"},
    {"id": "d2", "nome": "Bremer", "ruolo": "D", "squadra": "Juventus", "prezzo": 38, "consiglio": "top", "note": "4 gol, 3 assist, fantamedia alta"},
    {"id": "d3", "nome": "Bisseck", "ruolo": "D", "squadra": "Inter", "prezzo": 35, "consiglio": "top", "note": "Voti alti e bonus"},
    {"id": "d4", "nome": "Mancini", "ruolo": "D", "squadra": "Roma", "prezzo": 32, "consiglio": "top", "note": "4 gol, leader difesa Gasperini"},
    {"id": "d5", "nome": "Wesley", "ruolo": "D", "squadra": "Roma", "prezzo": 28, "consiglio": "top", "note": "5 gol, potenziale stagione alla Gosens"},
    {"id": "d6", "nome": "Pavlovic", "ruolo": "D", "squadra": "Milan", "prezzo": 33, "consiglio": "consigliato", "note": "5 gol, media 6.24"},
    {"id": "d7", "nome": "Ostigard", "ruolo": "D", "squadra": "Napoli", "prezzo": 28, "consiglio": "consigliato", "note": "5 gol, centrale prolifico"},
    {"id": "d8", "nome": "Cambiaso", "ruolo": "D", "squadra": "Juventus", "prezzo": 29, "consiglio": "consigliato", "note": "3 gol, 4 assist"},
    {"id": "d9", "nome": "Spinazzola", "ruolo": "D", "squadra": "Roma", "prezzo": 27, "consiglio": "consigliato", "note": "Sottovalutato, bonus garantiti"},
    {"id": "d10", "nome": "Zappacosta", "ruolo": "D", "squadra": "Atalanta", "prezzo": 32, "consiglio": "consigliato", "note": "Gran gamba, qualità offensiva"},
    {"id": "d11", "nome": "Stones", "ruolo": "D", "squadra": "Inter", "prezzo": 30, "consiglio": "consigliato", "note": "Ex City, rotazioni Chivu"},
    {"id": "d12", "nome": "Rensch", "ruolo": "D", "squadra": "Roma", "prezzo": 18, "consiglio": "scommessa", "note": "1 gol, 4 assist in 19 partite"},
    {"id": "d13", "nome": "Doekhi", "ruolo": "D", "squadra": "Lazio", "prezzo": 22, "consiglio": "scommessa", "note": "7 gol in Europa, sostituto Gila"},
    {"id": "d14", "nome": "Jimenez", "ruolo": "D", "squadra": "Fiorentina", "prezzo": 21, "consiglio": "scommessa", "note": "Torna in Serie A, jolly tattico"},
    {"id": "d15", "nome": "Kaiki", "ruolo": "D", "squadra": "Como", "prezzo": 14, "consiglio": "scommessa", "note": "Nuovo titolare sinistra"},
    # CENTROCAMPISTI
    {"id": "c1", "nome": "Frattesi", "ruolo": "C", "squadra": "Lazio", "prezzo": 48, "consiglio": "top", "note": "Potenziale top, alla Milinkovic-Savic"},
    {"id": "c2", "nome": "Pulisic", "ruolo": "C", "squadra": "Milan", "prezzo": 57, "consiglio": "top", "note": "Cambio ruolo, più appetibile"},
    {"id": "c3", "nome": "Orsolini", "ruolo": "C", "squadra": "Bologna", "prezzo": 53, "consiglio": "top", "note": "Cambio ruolo, bonus garantiti"},
    {"id": "c4", "nome": "Vlasic", "ruolo": "C", "squadra": "Torino", "prezzo": 52, "consiglio": "consigliato", "note": "8 gol, 3 assist, rigorista"},
    {"id": "c5", "nome": "Zaniolo", "ruolo": "C", "squadra": "Udinese", "prezzo": 48, "consiglio": "consigliato", "note": "5 gol, 6 assist, attaccante aggiunto"},
    {"id": "c6", "nome": "Modric", "ruolo": "C", "squadra": "Inter", "prezzo": 43, "consiglio": "consigliato", "note": "Rendimento garantito"},
    {"id": "c7", "nome": "Koné", "ruolo": "C", "squadra": "Juventus", "prezzo": 40, "consiglio": "consigliato", "note": "Media 6.26, mai sotto sufficienza"},
    {"id": "c8", "nome": "Perrone", "ruolo": "C", "squadra": "Como", "prezzo": 35, "consiglio": "consigliato", "note": "3 gol, 4 assist, voti alti"},
    {"id": "c9", "nome": "Bernardeschi", "ruolo": "C", "squadra": "Bologna", "prezzo": 38, "consiglio": "consigliato", "note": "Da prendere con Rowe"},
    {"id": "c10", "nome": "Rowe", "ruolo": "C", "squadra": "Bologna", "prezzo": 36, "consiglio": "consigliato", "note": "3 gol, 3 assist, può crescere"},
    {"id": "c11", "nome": "Thorstvedt", "ruolo": "C", "squadra": "Sassuolo", "prezzo": 30, "consiglio": "consigliato", "note": "5-6 gol potenziali"},
    {"id": "c12", "nome": "Alajbegovic", "ruolo": "C", "squadra": "Juventus", "prezzo": 33, "consiglio": "scommessa", "note": "Talentino trequarti, attenzione hype"},
    {"id": "c13", "nome": "Gaetano", "ruolo": "C", "squadra": "Atalanta", "prezzo": 19, "consiglio": "scommessa", "note": "Sarri lo vuole, grande intuizione"},
    {"id": "c14", "nome": "Stankovic A.", "ruolo": "C", "squadra": "Inter", "prezzo": 18, "consiglio": "scommessa", "note": "Fiducia Chivu, sostituto Calhanoglu"},
    {"id": "c15", "nome": "Calò", "ruolo": "C", "squadra": "Frosinone", "prezzo": 22, "consiglio": "scommessa", "note": "10 gol, 14 assist in Serie B"},
    {"id": "c16", "nome": "Milla", "ruolo": "C", "squadra": "Como", "prezzo": 20, "consiglio": "scommessa", "note": "Solo Yamal più assist in Liga"},
    # ATTACCANTI
    {"id": "a1", "nome": "Lautaro", "ruolo": "A", "squadra": "Inter", "prezzo": 88, "consiglio": "top", "note": "Capocannoniere 17 gol, 6 assist"},
    {"id": "a2", "nome": "Malen", "ruolo": "A", "squadra": "Roma", "prezzo": 84, "consiglio": "top", "note": "14 gol in mezzo campionato, vice-cannonieri"},
    {"id": "a3", "nome": "Thuram", "ruolo": "A", "squadra": "Inter", "prezzo": 74, "consiglio": "top", "note": "13 gol, 6 assist"},
    {"id": "a4", "nome": "Hojlund", "ruolo": "A", "squadra": "Napoli", "prezzo": 78, "consiglio": "top", "note": "Tornato in Serie A, obiettivo 15 gol"},
    {"id": "a5", "nome": "Goncalo Ramos", "ruolo": "A", "squadra": "Milan", "prezzo": 78, "consiglio": "top", "note": "Colpo da 70M, titolare Amorim"},
    {"id": "a6", "nome": "Kolo Muani", "ruolo": "A", "squadra": "Juventus", "prezzo": 76, "consiglio": "top", "note": "Tornato alla Juve, Spalletti lo vuole"},
    {"id": "a7", "nome": "Kean", "ruolo": "A", "squadra": "Fiorentina", "prezzo": 65, "consiglio": "consigliato", "note": "Doppia cifra garantita"},
    {"id": "a8", "nome": "Yildiz", "ruolo": "A", "squadra": "Juventus", "prezzo": 70, "consiglio": "consigliato", "note": "10 gol, 6 assist, centro progetto"},
    {"id": "a9", "nome": "Douvikas", "ruolo": "A", "squadra": "Como", "prezzo": 65, "consiglio": "consigliato", "note": "14 gol, sorpresa 2024-25"},
    {"id": "a10", "nome": "Dybala", "ruolo": "A", "squadra": "Roma", "prezzo": 58, "consiglio": "consigliato", "note": "Sempre utile, momento della differenza"},
    {"id": "a11", "nome": "Davis", "ruolo": "A", "squadra": "Udinese", "prezzo": 61, "consiglio": "consigliato", "note": "10 gol, rigorista"},
    {"id": "a12", "nome": "Scamacca", "ruolo": "A", "squadra": "Atalanta", "prezzo": 55, "consiglio": "consigliato", "note": "Attenzione infortuni"},
    {"id": "a13", "nome": "Simeone", "ruolo": "A", "squadra": "Napoli", "prezzo": 50, "consiglio": "consigliato", "note": "11 gol, conferma"},
    {"id": "a14", "nome": "Dovbyk", "ruolo": "A", "squadra": "Bologna", "prezzo": 48, "consiglio": "consigliato", "note": "Doppia cifra a Bologna"},
    {"id": "a15", "nome": "Colombo", "ruolo": "A", "squadra": "Roma", "prezzo": 35, "consiglio": "consigliato", "note": "7 gol, obiettivo doppia cifra"},
    {"id": "a16", "nome": "Alajbegovic K.", "ruolo": "A", "squadra": "Juventus", "prezzo": 33, "consiglio": "scommessa", "note": "Colpo di mercato, trequarti"},
    {"id": "a17", "nome": "Ekhator", "ruolo": "A", "squadra": "Juventus", "prezzo": 20, "consiglio": "scommessa", "note": "Low cost, potenziale"},
    {"id": "a18", "nome": "Mendy", "ruolo": "A", "squadra": "Cagliari", "prezzo": 15, "consiglio": "scommessa", "note": "2 gol in 8 partite, 2007"},
    {"id": "a19", "nome": "Camarda", "ruolo": "A", "squadra": "Milan", "prezzo": 12, "consiglio": "scommessa", "note": "Vice Ramos, a 1 credito ci sta"},
    {"id": "a20", "nome": "Ratkov", "ruolo": "A", "squadra": "Lazio", "prezzo": 20, "consiglio": "scommessa", "note": "Gattuso lo rilancia"},
]

CONSIGLI_DATA = {
    "Portieri": {
        "top": ["Butez (Como) - 19 clean sheet, miglior difesa", "Svilar (Roma) - 18 clean sheet, fantamedia 6", "Maignan (Milan) - 13 clean sheet, 2 rigori parati"],
        "consigliati": ["Martinez (Inter) - nuovo titolare, ex Genoa", "Meret (Napoli) - titolare Allegri", "Carnesecchi (Atalanta) - miglior fantamedia", "De Gea (Fiorentina) - stagione del riscatto"],
        "scommesse": ["Falcone (Lecce) - media voto 6.41, low cost", "Stankovic (Venezia) - torna in Serie A", "Perri (Torino) - nuovo titolare"]
    },
    "Difensori": {
        "top": ["Dimarco (Inter) - top assoluto, +3 a giornata", "Bremer (Juve) - 4 gol, 3 assist", "Bisseck (Inter) - voti alti e bonus", "Mancini (Roma) - 4 gol, leader", "Wesley (Roma) - 5 gol, potenziale Gosens"],
        "consigliati": ["Pavlovic (Milan) - 5 gol, media 6.24", "Ostigard (Napoli) - 5 gol", "Cambiaso (Juve) - 3 gol, 4 assist", "Spinazzola (Roma) - sottovalutato", "Zappacosta (Atalanta) - gran gamba", "Stones (Inter) - ex City"],
        "scommesse": ["Rensch (Roma) - 1 gol, 4 assist in 19g", "Doekhi (Lazio) - 7 gol in Europa", "Jimenez (Fiorentina) - jolly tattico", "Kaiki (Como) - titolare sinistra", "Ahanor (Atalanta) - terzino sinistro Sarri"]
    },
    "Centrocampisti": {
        "top": ["Frattesi (Lazio) - potenziale alla Milinkovic", "Pulisic (Milan) - cambio ruolo, più appetibile", "Orsolini (Bologna) - cambio ruolo, bonus garantiti"],
        "consigliati": ["Vlasic (Torino) - 8 gol, rigorista", "Zaniolo (Udinese) - 5 gol, 6 assist", "Modric (Inter) - rendimento garantito", "Koné (Juve) - media 6.26", "Perrone (Como) - 3 gol, 4 assist", "Bernardeschi+Rowe (Bologna) - da prendere insieme"],
        "scommesse": ["Alajbegovic (Juve) - talento trequarti", "Gaetano (Atalanta) - Sarri lo vuole", "Stankovic A. (Inter) - fiducia Chivu", "Calò (Frosinone) - 10 gol, 14 assist in B", "Milla (Como) - solo Yamal più assist in Liga", "Ethan-Meichtry (Genoa) - 8 gol in Svizzera"]
    },
    "Attaccanti": {
        "top": ["Lautaro (Inter) - 17 gol, capocannoniere", "Malen (Roma) - 14 gol in mezzo campionato", "Thuram (Inter) - 13 gol, 6 assist", "Hojlund (Napoli) - obiettivo 15 gol", "Goncalo Ramos (Milan) - colpo da 70M", "Kolo Muani (Juve) - tornato, Spalletti lo vuole"],
        "consigliati": ["Kean (Fiorentina) - doppia cifra", "Yildiz (Juve) - 10 gol, 6 assist", "Douvikas (Como) - 14 gol, sorpresa", "Dybala (Roma) - sempre utile", "Davis (Udinese) - rigorista", "Scamacca (Atalanta) - attenzione infortuni", "Simeone (Napoli) - 11 gol", "Dovbyk (Bologna) - doppia cifra", "Colombo (Roma) - 7 gol"],
        "scommesse": ["Alajbegovic K. (Juve) - colpo mercato", "Ekhator (Juve) - low cost", "Mendy (Cagliari) - 2 gol in 8g, 2007", "Camarda (Milan) - vice Ramos", "Ratkov (Lazio) - Gattuso lo rilancia", "Bowie (Sassuolo) - ex Verona", "Rrahmani (Venezia) - 15 gol in Rep. Ceca"]
    }
}


# ============================================================
# CLASSI
# ============================================================

class Giocatore:
    def __init__(self, data: dict):
        self.id = data["id"]
        self.nome = data["nome"]
        self.ruolo = data["ruolo"]
        self.squadra = data["squadra"]
        self.prezzo = data["prezzo"]
        self.consiglio = data.get("consiglio", "")
        self.note = data.get("note", "")

    def to_dict(self):
        return {"id": self.id, "nome": self.nome, "ruolo": self.ruolo,
                "squadra": self.squadra, "prezzo": self.prezzo,
                "consiglio": self.consiglio, "note": self.note}

    def __repr__(self):
        return f"{self.nome} ({self.ruolo}) - {self.squadra} [{self.prezzo}cr]"


class RosaEntry:
    def __init__(self, player_id: str, year: int, price: int, loan: Optional[dict] = None):
        self.player_id = player_id
        self.year = year
        self.price = price
        self.loan = loan  # dict: {to_team_id, duration_months, money, start_year}

    def to_dict(self):
        return {"player_id": self.player_id, "year": self.year,
                "price": self.price, "loan": self.loan}

    @classmethod
    def from_dict(cls, d):
        return cls(d["player_id"], d["year"], d["price"], d.get("loan"))


class Squadra:
    def __init__(self, team_id: int, name: str, budget: int = 500):
        self.id = team_id
        self.name = name
        self.budget = budget
        self.rosa: List[RosaEntry] = []

    def to_dict(self):
        return {"id": self.id, "name": self.name, "budget": self.budget,
                "rosa": [r.to_dict() for r in self.rosa]}

    @classmethod
    def from_dict(cls, d):
        s = cls(d["id"], d["name"], d["budget"])
        s.rosa = [RosaEntry.from_dict(r) for r in d.get("rosa", [])]
        return s

    def has_player(self, player_id: str) -> bool:
        return any(r.player_id == player_id for r in self.rosa)

    def add_player(self, player_id: str, price: int, year: int):
        self.rosa.append(RosaEntry(player_id, year, price))
        self.budget -= price

    def remove_player(self, player_id: str) -> Optional[RosaEntry]:
        for i, r in enumerate(self.rosa):
            if r.player_id == player_id:
                self.budget += r.price
                return self.rosa.pop(i)
        return None

    def stats(self, players_map: Dict[str, Giocatore]) -> Dict[str, int]:
        stats = {"P": 0, "D": 0, "C": 0, "A": 0}
        for r in self.rosa:
            p = players_map.get(r.player_id)
            if p:
                stats[p.ruolo] = stats.get(p.ruolo, 0) + 1
        return stats


class Prestito:
    def __init__(self, player_id: str, from_team_id: int, to_team_id: int,
                 duration: int, money: int, year: int):
        self.player_id = player_id
        self.from_team_id = from_team_id
        self.to_team_id = to_team_id
        self.duration = duration
        self.money = money
        self.year = year

    def to_dict(self):
        return {"player_id": self.player_id, "from_team_id": self.from_team_id,
                "to_team_id": self.to_team_id, "duration": self.duration,
                "money": self.money, "year": self.year}

    @classmethod
    def from_dict(cls, d):
        return cls(d["player_id"], d["from_team_id"], d["to_team_id"],
                   d["duration"], d["money"], d["year"])


class FantacalcioManager:
    CONTRATTO_ANNI = 4
    ANNO_CORRENTE = 2026

    def __init__(self):
        self.players: Dict[str, Giocatore] = {}
        self.teams: Dict[int, Squadra] = {}
        self.loans: List[Prestito] = []
        self._load_data()

    def _load_data(self):
        if os.path.exists(DATA_FILE):
            try:
                with open(DATA_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                for p in data.get("players", DEFAULT_PLAYERS):
                    g = Giocatore(p)
                    self.players[g.id] = g
                for t in data.get("teams", []):
                    s = Squadra.from_dict(t)
                    self.teams[s.id] = s
                for l in data.get("loans", []):
                    self.loans.append(Prestito.from_dict(l))
                return
            except Exception:
                pass
        # default
        for p in DEFAULT_PLAYERS:
            g = Giocatore(p)
            self.players[g.id] = g

    def save(self):
        data = {
            "players": [p.to_dict() for p in self.players.values()],
            "teams": [t.to_dict() for t in self.teams.values()],
            "loans": [l.to_dict() for l in self.loans]
        }
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print("\n💾 Dati salvati su", DATA_FILE)

    # ---------- SQUADRE ----------
    def add_team(self, name: str, budget: int = 500):
        tid = max(self.teams.keys(), default=0) + 1
        self.teams[tid] = Squadra(tid, name, budget)
        print(f"✅ Squadra '{name}' creata con budget {budget}cr (ID: {tid})")

    def remove_team(self, tid: int):
        if tid in self.teams:
            name = self.teams[tid].name
            del self.teams[tid]
            print(f"🗑️ Squadra '{name}' eliminata")
        else:
            print("❌ Squadra non trovata")

    def list_teams(self):
        if not self.teams:
            print("Nessuna squadra. Aggiungine una dal menu.")
            return
        print(f"\n{'ID':<4} {'Nome':<20} {'Budget':<8} {'Rosa':<6}")
        print("-" * 45)
        for t in self.teams.values():
            print(f"{t.id:<4} {t.name:<20} {t.budget:<8} {len(t.rosa):<6}")

    def show_team(self, tid: int):
        t = self.teams.get(tid)
        if not t:
            print("❌ Squadra non trovata")
            return
        stats = t.stats(self.players)
        print(f"\n📋 {t.name} — Budget: {t.budget}cr")
        print(f"   Portieri: {stats['P']} | Difensori: {stats['D']} | Centrocampisti: {stats['C']} | Attaccanti: {stats['A']}")
        if not t.rosa:
            print("   Rosa vuota")
            return
        print(f"   {'Nome':<20} {'R':<3} {'Squadra':<12} {'Prezzo':<8} {'Contratto':<12} {'Prestito':<10}")
        print("   " + "-" * 70)
        for r in t.rosa:
            p = self.players.get(r.player_id)
            if not p:
                continue
            contratto = f"{r.year}-{r.year + self.CONTRATTO_ANNI}"
            prestito = ""
            if r.loan:
                to = self.teams.get(r.loan["to_team_id"])
                prestito = f"→ {to.name if to else '?'} ({r.loan['duration']}m)"
            print(f"   {p.nome:<20} {p.ruolo:<3} {p.squadra:<12} {r.price:<8} {contratto:<12} {prestito:<10}")

    # ---------- LISTONE ----------
    def list_players(self, ruolo: str = "", squadra: str = "", consiglio: str = "", nome: str = ""):
        results = []
        for p in self.players.values():
            if ruolo and p.ruolo != ruolo:
                continue
            if squadra and p.squadra != squadra:
                continue
            if consiglio and p.consiglio != consiglio:
                continue
            if nome and nome.lower() not in p.nome.lower():
                continue
            results.append(p)
        if not results:
            print("Nessun giocatore trovato")
            return
        print(f"\n{'ID':<6} {'Nome':<20} {'R':<3} {'Squadra':<12} {'Prezzo':<8} {'Consiglio':<12} {'Note'}")
        print("-" * 90)
        for p in sorted(results, key=lambda x: (x.ruolo, -x.prezzo)):
            owned = any(t.has_player(p.id) for t in self.teams.values())
            flag = " [ACQ]" if owned else ""
            print(f"{p.id:<6} {p.nome:<20} {p.ruolo:<3} {p.squadra:<12} {p.prezzo:<8} {p.consiglio:<12} {p.note}{flag}")

    # ---------- ACQUISTI ----------
    def buy_player(self, team_id: int, player_id: str, price: int):
        t = self.teams.get(team_id)
        p = self.players.get(player_id)
        if not t or not p:
            print("❌ Squadra o giocatore non trovato")
            return
        if t.has_player(player_id):
            print("❌ Giocatore già in rosa")
            return
        if t.budget < price:
            print(f"❌ Budget insufficiente ({t.budget}cr disponibili)")
            return
        t.add_player(player_id, price, self.ANNO_CORRENTE)
        print(f"✅ {p.nome} acquistato da {t.name} per {price}cr! Contratto fino al {self.ANNO_CORRENTE + self.CONTRATTO_ANNI}")

    def release_player(self, team_id: int, player_id: str):
        t = self.teams.get(team_id)
        if not t:
            print("❌ Squadra non trovata")
            return
        entry = t.remove_player(player_id)
        if entry:
            p = self.players.get(player_id)
            print(f"🗑️ {p.nome if p else player_id} liberato. {entry.price}cr restituiti a {t.name}")
        else:
            print("❌ Giocatore non trovato in rosa")

    # ---------- SCAMBI ----------
    def trade(self, team_a_id: int, team_b_id: int,
              players_a: List[str], players_b: List[str],
              money_a: int = 0, money_b: int = 0):
        if team_a_id == team_b_id:
            print("❌ Le squadre devono essere diverse")
            return
        ta = self.teams.get(team_a_id)
        tb = self.teams.get(team_b_id)
        if not ta or not tb:
            print("❌ Squadra non trovata")
            return
        if ta.budget < money_a:
            print(f"❌ {ta.name} non ha budget per {money_a}cr")
            return
        if tb.budget < money_b:
            print(f"❌ {tb.name} non ha budget per {money_b}cr")
            return
        # Verifica possesso
        for pid in players_a:
            if not ta.has_player(pid):
                print(f"❌ {ta.name} non ha {self.players.get(pid, Giocatore({'id':pid,'nome':pid,'ruolo':'?','squadra':'?','prezzo':0})).nome}")
                return
        for pid in players_b:
            if not tb.has_player(pid):
                print(f"❌ {tb.name} non ha {self.players.get(pid, Giocatore({'id':pid,'nome':pid,'ruolo':'?','squadra':'?','prezzo':0})).nome}")
                return
        # Esegui scambio
        moved_a = []
        for pid in players_a:
            for i, r in enumerate(ta.rosa):
                if r.player_id == pid:
                    moved_a.append(ta.rosa.pop(i))
                    break
        moved_b = []
        for pid in players_b:
            for i, r in enumerate(tb.rosa):
                if r.player_id == pid:
                    moved_b.append(tb.rosa.pop(i))
                    break
        ta.rosa.extend(moved_b)
        tb.rosa.extend(moved_a)
        ta.budget -= money_a
        ta.budget += money_b
        tb.budget -= money_b
        tb.budget += money_a
        print(f"✅ Scambio effettuato!")
        if money_a or money_b:
            print(f"   💰 {ta.name} → {tb.name}: {money_a}cr | {tb.name} → {ta.name}: {money_b}cr")

    # ---------- PRESTITI ----------
    def loan_player(self, from_team_id: int, to_team_id: int, player_id: str,
                    duration: int, money: int = 0):
        if from_team_id == to_team_id:
            print("❌ Le squadre devono essere diverse")
            return
        from_t = self.teams.get(from_team_id)
        to_t = self.teams.get(to_team_id)
        p = self.players.get(player_id)
        if not from_t or not to_t or not p:
            print("❌ Dati non validi")
            return
        if not from_t.has_player(player_id):
            print(f"❌ {from_t.name} non ha {p.nome}")
            return
        if to_t.budget < money:
            print(f"❌ {to_t.name} non ha budget per {money}cr")
            return
        # Trova entry e segna come prestato
        for r in from_t.rosa:
            if r.player_id == player_id:
                r.loan = {"to_team_id": to_team_id, "duration": duration,
                          "money": money, "start_year": self.ANNO_CORRENTE}
                break
        to_t.budget -= money
        from_t.budget += money
        self.loans.append(Prestito(player_id, from_team_id, to_team_id,
                                   duration, money, self.ANNO_CORRENTE))
        print(f"✅ {p.nome} prestato da {from_t.name} a {to_t.name} per {duration} mesi" +
              (f" ({money}cr)" if money else ""))

    def end_loan(self, loan_index: int):
        if loan_index < 0 or loan_index >= len(self.loans):
            print("❌ Prestito non trovato")
            return
        l = self.loans.pop(loan_index)
        from_t = self.teams.get(l.from_team_id)
        p = self.players.get(l.player_id)
        if from_t:
            for r in from_t.rosa:
                if r.player_id == l.player_id:
                    r.loan = None
                    break
        print(f"✅ Prestito di {p.nome if p else l.player_id} terminato. Torna a {from_t.name if from_t else '?'}")

    def list_loans(self):
        if not self.loans:
            print("Nessun prestito attivo")
            return
        print(f"\n{'#':<4} {'Giocatore':<20} {'Da':<15} {'A':<15} {'Durata':<8} {'Denaro':<8}")
        print("-" * 75)
        for i, l in enumerate(self.loans):
            p = self.players.get(l.player_id)
            from_t = self.teams.get(l.from_team_id)
            to_t = self.teams.get(l.to_team_id)
            print(f"{i:<4} {p.nome if p else l.player_id:<20} "
                  f"{from_t.name if from_t else '?':<15} {to_t.name if to_t else '?':<15} "
                  f"{l.duration}m{'':<5} {l.money}cr")

    # ---------- CONSIGLI ----------
    def show_tips(self):
        print("\n" + "=" * 60)
        print("   🏆 CONSIGLI FANTACALCIO 2026/2027")
        print("=" * 60)
        for ruolo, data in CONSIGLI_DATA.items():
            print(f"\n📌 {ruolo.upper()}")
            print("   ⭐ TOP:")
            for t in data["top"]:
                print(f"      • {t}")
            print("   👍 CONSIGLIATI:")
            for t in data["consigliati"]:
                print(f"      • {t}")
            print("   🎲 SCOMMESSE:")
            for t in data["scommesse"]:
                print(f"      • {t}")


# ============================================================
# INTERFACCIA CLI
# ============================================================

def print_menu():
    print("\n" + "=" * 50)
    print("   🏟️  FANTAMANAGER 2026/2027")
    print("=" * 50)
    print("""
  [1]  Gestione squadre (crea/elimina/visualizza)
  [2]  Listone giocatori (filtra/acquista)
  [3]  Acquisto dal listone
  [4]  Scambio tra squadre
  [5]  Prestito giocatore
  [6]  Visualizza prestiti attivi
  [7]  Libera giocatore
  [8]  Consigli per l'asta
  [9]  Salva dati
  [0]  Esci
""")


def main():
    fm = FantacalcioManager()
    print("\n🎉 Benvenuto in FantaManager 2026/2027!")
    print(f"   Giocatori caricati: {len(fm.players)}")
    print(f"   Squadre presenti: {len(fm.teams)}")

    while True:
        print_menu()
        scelta = input("Scegli un'opzione: ").strip()

        if scelta == "1":
            print("\n--- Gestione squadre ---")
            print("  a) Crea squadra")
            print("  b) Elimina squadra")
            print("  c) Visualizza tutte le squadre")
            print("  d) Visualizza dettaglio squadra")
            sub = input("Scegli: ").strip().lower()
            if sub == "a":
                name = input("Nome squadra: ").strip()
                budget = input("Budget (default 500): ").strip()
                fm.add_team(name, int(budget) if budget else 500)
            elif sub == "b":
                fm.list_teams()
                tid = input("ID squadra da eliminare: ").strip()
                fm.remove_team(int(tid))
            elif sub == "c":
                fm.list_teams()
            elif sub == "d":
                fm.list_teams()
                tid = input("ID squadra: ").strip()
                fm.show_team(int(tid))

        elif scelta == "2":
            print("\n--- Listone giocatori ---")
            ruolo = input("Filtra ruolo (P/D/C/A, invio=tutti): ").strip().upper()
            squadra = input("Filtra squadra (invio=tutte): ").strip()
            consiglio = input("Filtra consiglio (top/consigliato/scommessa, invio=tutti): ").strip()
            nome = input("Cerca nome (invio=nessuno): ").strip()
            fm.list_players(ruolo=ruolo, squadra=squadra, consiglio=consiglio, nome=nome)

        elif scelta == "3":
            print("\n--- Acquisto dal listone ---")
            fm.list_teams()
            tid = input("ID squadra acquirente: ").strip()
            fm.list_players()
            pid = input("ID giocatore da acquistare: ").strip()
            price = input("Prezzo pagato: ").strip()
            fm.buy_player(int(tid), pid, int(price))

        elif scelta == "4":
            print("\n--- Scambio tra squadre ---")
            fm.list_teams()
            aid = input("ID Squadra A: ").strip()
            bid = input("ID Squadra B: ").strip()
            ta = fm.teams.get(int(aid))
            tb = fm.teams.get(int(bid))
            if ta and tb:
                print(f"\nGiocatori {ta.name}:")
                for r in ta.rosa:
                    p = fm.players.get(r.player_id)
                    if p:
                        print(f"  {p.id}: {p.nome} ({p.ruolo})")
                pa = input("ID giocatori A (separati da virgola): ").strip().split(",")
                pa = [x.strip() for x in pa if x.strip()]

                print(f"\nGiocatori {tb.name}:")
                for r in tb.rosa:
                    p = fm.players.get(r.player_id)
                    if p:
                        print(f"  {p.id}: {p.nome} ({p.ruolo})")
                pb = input("ID giocatori B (separati da virgola): ").strip().split(",")
                pb = [x.strip() for x in pb if x.strip()]

                ma = input(f"Denaro da {ta.name} a {tb.name} (default 0): ").strip()
                mb = input(f"Denaro da {tb.name} a {ta.name} (default 0): ").strip()
                fm.trade(int(aid), int(bid), pa, pb, int(ma) if ma else 0, int(mb) if mb else 0)

        elif scelta == "5":
            print("\n--- Prestito ---")
            fm.list_teams()
            fid = input("ID squadra che presta: ").strip()
            tid = input("ID squadra che riceve: ").strip()
            ft = fm.teams.get(int(fid))
            if ft:
                print(f"\nGiocatori disponibili in {ft.name}:")
                for r in ft.rosa:
                    if not r.loan:
                        p = fm.players.get(r.player_id)
                        if p:
                            print(f"  {p.id}: {p.nome} ({p.ruolo})")
            pid = input("ID giocatore da prestare: ").strip()
            dur = input("Durata (6 = 6 mesi, 12 = 1 anno): ").strip()
            money = input("Denaro incluso (default 0): ").strip()
            fm.loan_player(int(fid), int(tid), pid, int(dur), int(money) if money else 0)

        elif scelta == "6":
            fm.list_loans()
            if fm.loans:
                end = input("Terminare un prestito? (n/#prestito): ").strip()
                if end.isdigit():
                    fm.end_loan(int(end))

        elif scelta == "7":
            print("\n--- Libera giocatore ---")
            fm.list_teams()
            tid = input("ID squadra: ").strip()
            t = fm.teams.get(int(tid))
            if t:
                for r in t.rosa:
                    p = fm.players.get(r.player_id)
                    if p:
                        print(f"  {p.id}: {p.nome} ({p.ruolo}) — {r.price}cr")
            pid = input("ID giocatore da liberare: ").strip()
            fm.release_player(int(tid), pid)

        elif scelta == "8":
            fm.show_tips()

        elif scelta == "9":
            fm.save()

        elif scelta == "0":
            fm.save()
            print("👋 Arrivederci!")
            break

        else:
            print("❌ Opzione non valida")


if __name__ == "__main__":
    main()
