from datetime import datetime, timezone
from typing import Optional
import sqlalchemy as sa
import sqlalchemy.orm as so
from app import db

# Caratteristiche dei nodi in rete
class Modes(db.Model):
    node_id: so.Mapped[str] = so.mapped_column(sa.String(9), primary_key=True)
    nome: so.Mapped[str] = so.mapped_column(sa.String(28))
    freq: so.Mapped[int] = so.mapped_column(sa.Integer)
    mode: so.Mapped[str] = so.mapped_column(sa.String(14))


# Definizione nodi in rete con posizione gps
class Meshnodes(db.Model):
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



    