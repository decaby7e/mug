from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from mug.settings import config
from mug.models import Base


def _get_db_engine():
    dbconf = config["sqlite"]
    dbdsn = f"sqlite:///{dbconf['path']}"
    return create_engine(dbdsn)


def init_db():
    engine = _get_db_engine()
    return Base.metadata.create_all(engine)


def get_db_session():
    Session = sessionmaker(bind=_get_db_engine())
    return Session()
