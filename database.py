from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, declarative_base


DATABASE_URL = "sqlite:////home/NalivAuto/logistics_bot/logistics.db"

engine = create_engine(
    DATABASE_URL, echo=False,
    connect_args={"check_same_thread": False, "timeout": 30}
)


@event.listens_for(engine, "connect")
def _set_pragma(dbapi_conn, record):
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=30000")
    cursor.close()

Session = sessionmaker(bind=engine)
Base = declarative_base()

def get_session():
    return Session()


def init_db():
    import models  # noqa: F401
    Base.metadata.create_all(engine)