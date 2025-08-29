from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from sqlalchemy import func,distinct
from app import db

# Caratteristiche dei nodi in rete
class Modes(db.Model):
    node_id: so.Mapped[str] = so.mapped_column(sa.String(9), primary_key=True)
    nome: so.Mapped[str] = so.mapped_column(sa.String(28))
    freq: so.Mapped[int] = so.mapped_column(sa.Integer)
    mode: so.Mapped[str] = so.mapped_column(sa.String(14))

    @staticmethod
    def getMode(nodeid):
        modi = db.session.query(Modes.freq, Modes.mode).filter(Modes.node_id == nodeid).limit(1).first()
        return modi

    @staticmethod
    def insert_mode(node_id: str, nome: str, freq: int, mode: str):
        try:
            new_mode = Modes(
                node_id=node_id,
                nome=nome,
                freq=freq,
                mode=mode
            )
            db.session.add(new_mode)
            db.session.commit()
            return True
        except Exception as e:
            db.session.rollback()
            print(f"Errore durante l'inserimento: {e}")
            return False

    @staticmethod
    def update_mode(node_id: str, nome: str, freq: int, mode: str):
        try:
            mode_entry = db.session.query(Modes).filter_by(node_id=node_id).first()
            if mode_entry:
                mode_entry.nome = nome
                mode_entry.freq = freq
                mode_entry.mode = mode
                db.session.commit()
                return True
            else:
                print(f"Nessuna entry trovata con node_id {node_id}")
                return False
        except Exception as e:
            db.session.rollback()
            print(f"Errore durante l'aggiornamento: {e}")
            return False

    def __repr__(self):
        return f"<Modes node_id={self.node_id}>"


# Definizione nodi in rete con posizione gps
class Meshnodes(db.Model):
    __tablename__ = 'meshnodes'

    data: so.Mapped[str] = so.mapped_column(sa.String(8))
    ora: so.Mapped[str] = so.mapped_column(sa.String(8))
    nodenum: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True)
    node_id: so.Mapped[str] = so.mapped_column(sa.String(9))
    longname: so.Mapped[str] = so.mapped_column(sa.String(28))
    alt: so.Mapped[int] = so.mapped_column(sa.Integer)
    lat: so.Mapped[float] = so.mapped_column(sa.Float)
    lon: so.Mapped[float] = so.mapped_column(sa.Float)
    batt: so.Mapped[int] = so.mapped_column(sa.Integer)
    snr: so.Mapped[float] = so.mapped_column(sa.Float)
    pressione: so.Mapped[float] = so.mapped_column(sa.Float)
    temperat: so.Mapped[float] = so.mapped_column(sa.Float)
    umidita: so.Mapped[float] = so.mapped_column(sa.Float)

    def selNodo(node_id):
        target = db.session.query(Meshnodes.node_id,Meshnodes.longname).filter(
            Meshnodes.node_id == node_id).all()
        return target
    
    def chiamaNodi():
        nodi_validi = db.session.query(Meshnodes).filter(
            Meshnodes.lat.isnot(None),
            Meshnodes.lon.isnot(None),
            Meshnodes.longname.isnot(None)
        ).all()
        return nodi_validi
    

    @staticmethod
    def get_ndcnt():
        try:
            count = db.session.query(func.count(Meshnodes.node_id)).scalar()
            return count
        except Exception as e:
            print(f"Errore in get_ndcnt: {e}")
            return 0 

    def __repr__(self):
        return '<Meshnodes {}>'


class Tracking(db.Model):
    node_id: so.Mapped[str] = so.mapped_column(sa.String(9))
    longname: so.Mapped[str] = so.mapped_column(sa.String(28))
    data: so.Mapped[str] = so.mapped_column(sa.String(8))
    ora: so.Mapped[str] = so.mapped_column(sa.String(8))
    lon: so.Mapped[float] = so.mapped_column(sa.Float)
    lat: so.Mapped[float] = so.mapped_column(sa.Float)
    alt: so.Mapped[int] = so.mapped_column(sa.Integer)
    batt: so.Mapped[int] = so.mapped_column(sa.Integer)
    temperat: so.Mapped[float] = so.mapped_column(sa.Float)
    pressione: so.Mapped[float] = so.mapped_column(sa.Float)
    umidita: so.Mapped[float] = so.mapped_column(sa.Float)
    _id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True)


    def get_nodi():
        nodes = db.session.query(Tracking.longname,Tracking.node_id).distinct().order_by(Tracking.longname.asc()).all()
        nodi = []
        for nodo in nodes:
            if Modes.getMode(nodo[1]):
                nodi.append(nodo[0])
                print(nodi)
        return nodi

    def getTrack(data,nome):
        nodi = db.session.query(Tracking).filter(Tracking.data >= data,Tracking.longname==nome).order_by(Tracking.data.asc(),Tracking.ora.asc()).all()
        return nodi

    def __repr__(self):
        return '<Tracking {}>'

class Messaggi(db.Model):

    _id: so.Mapped[int] = so.mapped_column(sa.Integer,primary_key=True)
    data: so.Mapped[str] = so.mapped_column(sa.String(8))
    ora: so.Mapped[str] = so.mapped_column(sa.String(8))
    msg: so.Mapped[str] = so.mapped_column(sa.String(200))

    # @classmethod: è meglio usare questo decoratore perché getMsgs() non ha bisogno 
    # di un'istanza (self) ma agisce sull'intera tabella.
    @classmethod
    def getMsgs(cls):
        oggi = datetime.now().strftime("%y/%m/%d")
        db.session.query(cls).filter(cls.data < oggi).delete()
        db.session.commit()
        messg = db.session.query(cls.ora,cls.msg).filter(cls.data == oggi).all()
        return messg

    @classmethod
    def sendMsg(cls, testo):
        try:
            now = datetime.now()
            nuovo_messaggio = cls(
                data=now.strftime("%y/%m/%d"),
                ora=now.strftime("%H:%M:%S"),
                msg='^' + testo
            )
            db.session.add(nuovo_messaggio)
            db.session.commit()
            return True
        except Exception as e:
            print(f"Errore in sendMsg: {e}")
            db.session.rollback()
            return False

    def __repr__(self):
        return f'<Messaggi {self.data} {self.ora}: {self.msg}>'
   
