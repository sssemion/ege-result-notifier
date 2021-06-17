import os
from typing import Iterator
from contextlib import contextmanager

import sqlalchemy as sa
import sqlalchemy.orm as orm
from sqlalchemy.ext import declarative
from sqlalchemy.orm import Session

db = declarative.declarative_base()

__factory = None


def global_init():
    global __factory

    if __factory:
        return

    db_filename = os.environ.get("DB_FILENAME")

    conn_str = f"sqlite:///{db_filename}"

    engine = sa.create_engine(conn_str, echo=False)
    __factory = orm.sessionmaker(bind=engine)

    import app.data.models

    db.metadata.create_all(engine)
    return db


@contextmanager
def create_session() -> Iterator[Session]:
    global __factory
    session = None

    try:
        session = __factory()
        yield session
    except Exception:
        if session:
            session.rollback()
        raise
    else:
        session.commit()
    finally:
        if session:
            session.close()
