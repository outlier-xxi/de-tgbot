import uuid
from datetime import datetime, UTC
from uuid import uuid4

import asyncpg
from sqlalchemy import insert, update
from sqlalchemy.dialects import postgresql

from src.common.log import logger
from src.common.settings import settings
from src.models.public import Action, Query, QueryStatus


async def init_pool():
    pool: asyncpg.Pool = await asyncpg.create_pool(
        settings.db_conn_str, min_size=1
    )
    return pool


def compile_query(stmt) -> str:
    """
    Generate SQL query from SQLAlchemy statement.
    """
    result = stmt.compile(
        dialect=postgresql.dialect(),
        compile_kwargs={"literal_binds": True},
    ).string
    return result


async def log_action(
        pool: asyncpg.Pool,
        user_id: int,
        action: str,
        query_id: uuid.UUID = None,
):
    """
    Inserts user action into Action table.
    """
    logger.info(f"Action: user_id: {user_id}, action: {action}, query_id: {query_id}")
    stmt = insert(Action).values(
        action_id=uuid4(),
        timestamp=datetime.now(UTC),
        user_id=user_id,
        query_id=query_id,
        action=action,
    )
    res = await pool.execute(compile_query(stmt))


async def log_query(
        pool: asyncpg.Pool,
        user_id: int,
        query_text: str = None,
) -> uuid.UUID:
    """
    Inserts a user query into Query table.
    """
    query_id: uuid.UUID = uuid4()  # Generate random UUID for query_id
    logger.info(
        f"Query: user_id: {user_id}, query_id: {query_id}, query_text len: {len(query_text)}"
    )
    stmt = insert(Query).values(
        query_id=query_id,
        user_id=user_id,
        timestamp=datetime.now(UTC),
        status=QueryStatus.new.value,
        query_text=query_text,
    )
    res = await pool.execute(compile_query(stmt))
    return query_id


async def update_query(
        pool: asyncpg.Pool,
        query_id: uuid.UUID,
        user_id: int = None,
        query_text: str = None,
        status: QueryStatus = QueryStatus.responded,
        response_text: str = None,
        input_text_tokens: int = None,
        completion_tokens: int = None,
        total_tokens: int = None,
):
    """
    Inserts a user query into Query table.
    """
    logger.info(
        f"Query: user_id: {user_id}, query_id: {query_id}"
        f", query_text len: {len(query_text) if query_text else 0}"
    )
    stmt = update(Query).where(
        Query.query_id == query_id,
    ).values(
        status=status,
        response_text=response_text,
        input_text_tokens=input_text_tokens,
        completion_tokens=completion_tokens,
        total_tokens=total_tokens,
    )
    res = await pool.execute(compile_query(stmt))
