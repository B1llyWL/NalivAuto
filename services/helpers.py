from config import LOGIST_IDS
from database import get_session
from models import User

def get_or_create_user(telegram_id, username=None):
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if not user:
            user = User(telegram_id=telegram_id, username=username, state="idle")
            session.add(user)
            session.commit()
        else:
            if username and user.username != username:
                user.username = username
                session.commit()
        return user
    finally:
        session.close()

def set_user_state(telegram_id, state):
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        if user:
            user.state = state
            session.commit()
    finally:
        session.close()


def get_user_state(telegram_id):
    session = get_session()
    try:
        user = session.query(User).filter_by(telegram_id=telegram_id).first()
        return user.state if user else "idle"
    finally:
        session.close()


def find_user_by_username(username):
    session = get_session()
    try:
        uname = username.lstrip("@").lower()
        users = session.query(User).filter(User.username != None).all()
        for u in users:
            if u.username and u.username.lower() == uname:
                return u.telegram_id
        return None
    finally:
        session.close()

def is_logist(telegram_id):
    """Логист - из config.py"""
    return telegram_id in LOGIST_IDS
