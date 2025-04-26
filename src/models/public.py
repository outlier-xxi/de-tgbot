from enum import Enum

from sqlalchemy import (
    Column,
    Index,
)
from sqlalchemy.dialects.postgresql import (
    UUID, TIMESTAMP, TEXT, INTEGER
)
from sqlalchemy.orm import declarative_base

Base = declarative_base()


class Action(Base):
    """
    Действия пользователей
    """
    __tablename__ = 't_action'
    __table_args__ = (
        {
            'schema': 'public',
            'comment': 'Действия пользователей',
        },
    )
    action_id = Column(UUID, primary_key=True, comment='ID действия')
    timestamp = Column(TIMESTAMP, comment='Timestamp действия')
    user_id   = Column(INTEGER, comment='ID пользователя')
    query_id  = Column(UUID, comment='ID запроса')
    action    = Column(TEXT, comment='Действие')


Index(None, Action.timestamp.desc(), unique=False)
Index(None, Action.user_id, unique=False)


class Query(Base):
    """
    Запросы
    """
    __tablename__ = 't_query'
    __table_args__ = (
        {
            'schema': 'public',
            'comment': 'Запросы',
        },
    )
    query_id          = Column(UUID, primary_key=True, comment='ID запроса')
    user_id           = Column(INTEGER, comment='ID пользователя')
    timestamp         = Column(TIMESTAMP, comment='Timestamp действия')
    status            = Column(TEXT, comment='Статус запроса')
    query_text        = Column(TEXT, comment='Текст запроса')
    response_text     = Column(TEXT, comment='Текст ответа')
    input_text_tokens = Column(INTEGER, comment='Использование токенов, inputTextTokens')
    completion_tokens = Column(INTEGER, comment='Использование токенов, completionTokens')
    total_tokens      = Column(INTEGER, comment='Использование токенов, totalTokens')


Index(None, Query.timestamp.desc(), unique=False)


class QueryStatus(Enum):
    new       = "new"
    responded = "responded"
    error     = "error"


class ActionType(Enum):
    start       = "start"
    question    = "question"
    cancel      = "cancel"
