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
        nodi = db.session.query(Tracking.longname,Tracking.node_id).distinct().order_by(Tracking.longname.asc()).all()
        return nodi

    def getTrack(data,nome):
        nodi = db.session.query(Tracking).filter(Tracking.data >= data,Tracking.longname==nome).order_by(Tracking.data.asc(),Tracking.ora.asc()).all()
        return nodi


    def __repr__(self):
        return '<Tracking {}>'