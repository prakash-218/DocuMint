"""
Database access (PostgreSQL via SQLAlchemy).

DATABASE_URL picks the database (Railway's Postgres sets it). Operations live in
store/procs.py as named functions; db.execute_proc('sp_name', args) runs one in
its own transaction and returns rows the way callers expect:
    no rows -> None, one result set -> list of dicts, several -> list of lists.
"""

import logging
import os
import pathlib
import time
import uuid
from decimal import Decimal
from typing import Any, Dict, List, Optional

from dotenv import load_dotenv
from sqlalchemy import create_engine, event
from sqlalchemy.exc import DataError, DBAPIError, IntegrityError, OperationalError

load_dotenv(dotenv_path=pathlib.Path(__file__).parent / '.env')
logger = logging.getLogger(__name__)

DEFAULT_URL = 'postgresql+psycopg://postgres:dev@127.0.0.1:5434/documint'


class DatabaseError(Exception):
    """A database operation failed; the message is safe to show (business rules) or log."""


def database_url() -> str:
    url = os.getenv('DATABASE_URL') or DEFAULT_URL
    # Railway / Heroku style URLs -> the psycopg 3 driver
    if url.startswith('postgres://'):
        url = 'postgresql://' + url[len('postgres://'):]
    if url.startswith('postgresql://'):
        url = 'postgresql+psycopg://' + url[len('postgresql://'):]
    return url


def _plain(value):
    if isinstance(value, uuid.UUID):
        return str(value)
    return value


class Database:
    def __init__(self):
        self._engine = None
        self._observers = []

    @property
    def engine(self):
        if self._engine is None:
            self._engine = create_engine(database_url(), pool_pre_ping=True, pool_size=5, max_overflow=5,
                                         pool_recycle=1800, future=True)
            if os.getenv('SLOW_QUERY_MS'):
                _log_slow_queries(self._engine, int(os.getenv('SLOW_QUERY_MS')))
        return self._engine

    def reset(self):
        """Forget the engine (tests switch databases)."""
        if self._engine is not None:
            self._engine.dispose()
        self._engine = None

    def add_row_observer(self, fn):
        """fn(results) is called with every operation's rows (e.g. to remember document types)."""
        self._observers.append(fn)

    def execute_proc(self, proc_name: str, args: tuple = None, fetch: bool = True) -> Optional[List[Any]]:
        from store.procs import PROCS, ProcError
        fn = PROCS.get(proc_name)
        if fn is None:
            raise DatabaseError(f'Unknown operation {proc_name}')
        args = tuple(args or ())
        try:
            with self.engine.begin() as conn:
                sets = fn(conn, *args) or []
        except ProcError as e:
            raise DatabaseError(str(e)) from e
        except IntegrityError as e:
            constraint = getattr(getattr(e.orig, 'diag', None), 'constraint_name', '') or ''
            if getattr(e.orig, 'sqlstate', '') == '23505':     # unique violation
                raise DatabaseError(f'Duplicate entry ({constraint})') from e
            raise DatabaseError(f'Constraint failed ({constraint})') from e
        except DataError as e:
            # e.g. an id from the URL that isn't a UUID: behaves like "not found", no stack trace
            logger.info('Bad input to %s: %s', proc_name, str(e.orig).splitlines()[0])
            raise DatabaseError(f'Invalid value for {proc_name}') from e
        except OperationalError as e:
            logger.exception('Database unavailable in %s', proc_name)
            raise DatabaseError(f'Database connection error: {e.orig}') from e
        except DBAPIError as e:
            logger.exception('Database error in %s', proc_name)
            raise DatabaseError(f'Database error in {proc_name}: {e.orig}') from e

        results = [[{k: _plain(v) for k, v in row.items()} for row in rows] for rows in sets]
        results = [rows for rows in results if rows]
        for observe in self._observers:
            try:
                observe(results)
            except Exception:
                pass
        if not fetch or not results:
            return None
        return results[0] if len(results) == 1 else results

    def execute_proc_single(self, proc_name: str, args: tuple = None) -> Optional[Dict[str, Any]]:
        results = self.execute_proc(proc_name, args, fetch=True)
        return results[0] if results else None

    def ping(self) -> bool:
        from sqlalchemy import text
        with self.engine.connect() as conn:
            conn.execute(text('SELECT 1'))
        return True


def _log_slow_queries(engine, threshold_ms):
    @event.listens_for(engine, 'before_cursor_execute')
    def _start(conn, cursor, statement, params, context, executemany):
        conn.info.setdefault('t0', []).append(time.perf_counter())

    @event.listens_for(engine, 'after_cursor_execute')
    def _end(conn, cursor, statement, params, context, executemany):
        ms = (time.perf_counter() - conn.info['t0'].pop()) * 1000
        if ms >= threshold_ms:
            logger.warning('slow query %.0f ms: %s', ms, ' '.join(statement.split())[:300])


db = Database()
