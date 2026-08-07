from fastapi import FastAPI, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import create_engine, Column, Integer, String, Float, Boolean, ForeignKey, TIMESTAMP, func
from sqlalchemy.orm import declarative_base, sessionmaker, Session
from typing import List, Optional
import datetime

# 1. CONFIGURAZIONE DATABASE (In-memory SQLite per test, convertibile in PostgreSQL)
DATABASE_URL = "sqlite:///./fantacalcio.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

app = FastAPI(title="FantaApp API", version="1.0.0")

# Dependency per ottenere la sessione del database
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# 2. MODELLI DATABASE (SQLAlchemy)
class CalciatoreDB(Base):
    __tablename__ = "calciatori"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String, index=True)
    ruolo = Column(String(2))  # P, D, C, A
    squadra_reale = Column(String)
    quotazione = Column(Integer)
    fanta_media = Column(Float, default=0.0)
    media_voto = Column(Float, default=0.0)
    gol = Column(Integer, default=0)
    assist = Column(Integer, default=0)
    minuti_giocati = Column(Integer, default=0)

class FantasquadraDB(Base):
    __tablename__ = "fantasquadre"
    id = Column(Integer, primary_key=True, index=True)
    nome_squadra = Column(String, unique=True)
    budget_crediti = Column(Integer, default=500)

class RosaDB(Base):
    __tablename__ = "rose"
    id_squadra = Column(Integer, ForeignKey("fantasquadre.id", ondelete="CASCADE"), primary_key=True)
    id_calciatore = Column(Integer, ForeignKey("calciatori.id", ondelete="CASCADE"), primary_key=True)

class PrestitoDB(Base):
    __tablename__ = "prestiti"
    id = Column(Integer, primary_key=True, index=True)
    id_calciatore = Column(Integer, ForeignKey("calciatori.id"))
    squadra_origine = Column(Integer, ForeignKey("fantasquadre.id"))
    squadra_destinazione = Column(Integer, ForeignKey("fantasquadre.id"))
    giornata_inizio = Column(Integer)
    giornata_fine = Column(Integer)
    crediti_pagati = Column(Integer, default=0)
    stato = Column(String, default="ATTIVO")  # ATTIVO, CONCLUSO

# Crea le tabelle nel database
Base.metadata.create_all(bind=engine)


# 3. SCHEMI DI VALIDAZIONE DATI (Pydantic)
class PropostaScambio(BaseModel):
    squadra_proprietaria_id: int
    squadra_acquirente_id: int
    calciatore_offerto_id: int
    calciatore_richiesto_id: int
    conguaglio_crediti: int = Field(..., description="Crediti che la squadra proprietaria dà in aggiunta")

class PropostaPrestito(BaseModel):
    squadra_origine_id: int
    squadra_destinazione_id: int
    id_calciatore: int
    giornata_inizio: int
    giornata_fine: int
    crediti_pagati: int


# 4. ENDPOINT 1: ALGORITMO DI SCOUTING AVANZATO (Intreccio Dati)
@app.get("/scouting/", response_model=List[dict])
def scouting_giocatori(
    ruolo: Optional[str] = None, 
    max_prezzo: Optional[int] = None, 
    min_partite: Optional[int] = 5, 
    db: Session = Depends(get_db)
):
    """
    Calcola l'Indice di Valore Reale (IVR) incrociando fanta-media, 
    presenze (minuti) e bonus per scovare i migliori talenti.
    """
    query = db.query(CalciatoreDB)
    if ruolo:
        query = query.filter(CalciatoreDB.ruolo == ruolo.upper())
    if max_prezzo:
        query = query.filter(CalciatoreDB.quotazione <= max_prezzo)
        
    calciatori = query.all()
    risultati = []

    for c in calciatori:
        partite_giocate = c.minuti_giocati / 90
        if partite_giocate < min_partite:
            continue
            
        # Algoritmo IVR: Pesa la fanta-media (50%), la costanza (30%) e i bonus puri (20%)
        score_presenze = min(partite_giocate / 38, 1.0) * 10
        score_bonus = (c.gol * 3) + c.assist
        ivr = (c.fanta_media * 0.5) + (score_presenze * 0.3) + (score_bonus * 0.2)
        
        risultati.append({
            "id": c.id,
            "nome": c.nome,
            "ruolo": c.ruolo,
            "quotazione": c.quotazione,
            "fanta_media": c.fanta_media,
            "ivr_scouting": round(ivr, 2)
        })
        
    # Ordina i giocatori dal più appetibile al meno appetibile
    return sorted(risultati, key=lambda x: x["ivr_scouting"], reverse=True)


# 5. ENDPOINT 2: SCAMBIO DIRETTO TRA UTENTI CON SCAMBIO DI DENARO
@app.post("/mercato/scambio/")
def esegui_scambio(proposta: PropostaScambio, db: Session = Depends(get_db)):
    """
    Esegue uno scambio atomico tra due fantasquadre con transazione monetaria in crediti.
    """
    # 1. Recupera le squadre
    squadra_prop = db.query(FantasquadraDB).filter(FantasquadraDB.id == proposta.squadra_proprietaria_id).first()
    squadra_acq = db.query(FantasquadraDB).filter(FantasquadraDB.id == proposta.squadra_acquirente_id).first()
    
    if not squadra_prop or not squadra_acq:
        raise HTTPException(status_code=404, detail="Una o entrambe le fantasquadre non esistono")
        
    # 2. Verifica copertura finanziaria per il conguaglio
    if squadra_prop.budget_crediti < proposta.conguaglio_crediti:
        raise HTTPException(status_code=400, detail="Budget crediti insufficiente per coprire il conguaglio")

    # 3. Verifica l'effettivo possesso dei giocatori nelle rose
    possesso_offerto = db.query(RosaDB).filter(RosaDB.id_squadra == squadra_prop.id, RosaDB.id_calciatore == proposta.calciatore_offerto_id).first()
    possesso_richiesto = db.query(RosaDB).filter(RosaDB.id_squadra == squadra_acq.id, RosaDB.id_calciatore == proposta.calciatore_richiesto_id).first()
    
    if not possesso_offerto or not possesso_richiesto:
        raise HTTPException(status_code=400, detail="I giocatori non appartengono ai rispettivi proprietari dichiarati")

    try:
        # 4. Spostamento Economico
        squadra_prop.budget_crediti -= proposta.conguaglio_crediti
        squadra_acq.budget_crediti += proposta.conguaglio_crediti
        
        # 5. Spostamento Fisico dei Calciatori nelle Rose
        db.delete(possesso_offerto)
        db.delete(possesso_richiesto)
        db.flush() # Svuota i vecchi record prima di inserire i nuovi per evitare conflitti di chiave primaria
        
        nuovo_possesso_1 = RosaDB(id_squadra=squadra_acq.id, id_calciatore=proposta.calciatore_offerto_id)
        nuovo_possesso_2 = RosaDB(id_squadra=squadra_prop.id, id_calciatore=proposta.calciatore_richiesto_id)
        
        db.add(nuovo_possesso_1)
        db.add(nuovo_possesso_2)
        
        # Salva tutto nel database definitivamente
        db.commit()
        return {"status": "Successo", "detail": "Scambio e transazione monetaria completati con successo"}
        
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Errore transazione annullata: {str(e)}")


# 6. ENDPOINT 3: CEDERE IN PRESTITO CON SCAMBIO DI DENARO
@app.post("/mercato/prestito/")
def cedi_in_prestito(prestito: PropostaPrestito, db: Session = Depends(get_db)):
    """
    Trasferisce temporaneamente un giocatore da una squadra all'altra in cambio di crediti.
    """
    squadra_orig = db.query(FantasquadraDB).filter(FantasquadraDB.id == prestito.squadra_origine_id).first()
    squadra_dest = db.query(FantasquadraDB).filter(FantasquadraDB.id == prestito.squadra_destinazione_id).first()
    
    if squadra_dest.budget_crediti < prestito.crediti_pagati:
        raise HTTPException(status_code=400, detail="La squadra destinataria non ha abbastanza crediti per il prestito")
        
    rosa_orig = db.query(RosaDB).filter(RosaDB.id_squadra == squadra_orig.id, RosaDB.id_calciatore == prestito.id_calciatore).first()
    if not rosa_orig:
        raise HTTPException(status_code=400, detail="Il calciatore non è presente nella rosa della squadra di origine")

    try:
        # Transazione finanziaria
        squadra_dest.budget_crediti -= prestito.crediti_pagati
        squadra_orig.budget_crediti += prestito.crediti_pagati
        
        # Spostamento rosa
        db.delete(rosa_orig)
        nuova_rosa = RosaDB(id_squadra=squadra_dest.id, id_calciatore=prestito.id_calciatore)
        db.add(nuova_rosa)
        
        # Registro del prestito temporaneo
        nuovo_prestito_registro = PrestitoDB(
            id_calciatore=prestito.id_calciatore,
            squadra_origine=squadra_orig.id,
            squadra_destinazione=squadra_dest.id,
            giornata_inizio=prestito.giornata_inizio,
            giornata_fine=prestito.giornata_fine,
            crediti_pagati=prestito.crediti_pagati
        )
        db.add(nuovo_prestito_registro)
        
        db.commit()
        return {"status": "Successo", "detail": f"Giocatore concesso in prestito fino alla giornata {prestito.giornata_fine}"}
    except Exception as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=str(e))


# 7. SCRIPT AUTOMATICO (CRONJOB) PER IL RIENTRO DEI PRESTITI A FINE GIORNATA
@app.post("/sistema/risolvi-prestiti/{giornata_conclusa}")
def cronjob_rientro_prestiti(giornata_conclusa: int, db: Session = Depends(get_db)):
    """
    Questo endpoint va chiamato automaticamente dal server alla fine di ogni giornata.
    Riprende i giocatori in prestito scaduto e li rimette nella rosa originale.
    """
    prestiti_scaduti = db.query(PrestitoDB).filter(
        PrestitoDB.giornata_fine == giornata_conclusa, 
        PrestitoDB.stato == "ATTIVO"
    ).all()
    
    contatore = 0
    for p in prestiti_scaduti:
        # Rimuovi dalla squadra temporanea
        db.query(RosaDB).filter(RosaDB.id_squadra == p.squadra_destinazione, RosaDB.id_calciatore == p.id_calciatore).delete()
        # Ritorna alla squadra originaria
        rientro = RosaDB(id_squadra=p.squadra_origine, id_calciatore=p.id_calciatore)
        db.add(rientro)
