"""Pool de conexiones pyodbc.

No se usa ORM ni SQLAlchemy. Cada conexión se reutiliza y las operaciones
se ejecutan con autocommit, porque los procedimientos de entrada y salida
abren y cierran su propia transacción explícita. Así ninguna lectura deja
transacciones abiertas reteniendo bloqueos.
"""

from __future__ import annotations

import logging
import queue
import threading
from collections.abc import Iterator
from contextlib import contextmanager

import pyodbc

from backend.core.config import Settings

logger = logging.getLogger(__name__)


class ConnectionPool:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings
        self._max_size = settings.db_pool_size
        self._queue: queue.LifoQueue[pyodbc.Connection] = queue.LifoQueue(
            maxsize=self._max_size
        )
        self._created = 0
        self._lock = threading.Lock()

    # ------------------------------------------------------------------
    # Construcción de conexiones
    # ------------------------------------------------------------------
    def _new_connection(self) -> pyodbc.Connection:
        connection = pyodbc.connect(
            self._settings.connection_string,
            autocommit=True,
            timeout=self._settings.db_timeout,
        )
        return connection

    def _acquire(self) -> pyodbc.Connection:
        try:
            connection = self._queue.get_nowait()
        except queue.Empty:
            with self._lock:
                if self._created < self._max_size:
                    self._created += 1
                    try:
                        return self._new_connection()
                    except Exception:
                        self._created -= 1
                        raise
            # Pool agotado: esperar a que se libere una conexión.
            connection = self._queue.get(timeout=self._settings.db_timeout * 2)

        try:
            connection.cursor().execute("SELECT 1").fetchone()
        except Exception:
            logger.warning("Conexión pyodbc inválida; se reemplaza.")
            try:
                connection.close()
            except Exception:
                pass
            with self._lock:
                self._created -= 1
            return self._acquire()

        return connection

    def _release(self, connection: pyodbc.Connection) -> None:
        try:
            self._queue.put_nowait(connection)
        except queue.Full:
            connection.close()

    @contextmanager
    def connection(self) -> Iterator[pyodbc.Connection]:
        connection = self._acquire()
        try:
            yield connection
        finally:
            self._release(connection)

    # ------------------------------------------------------------------
    def healthcheck(self) -> bool:
        with self.connection() as connection:
            cursor = connection.cursor()
            cursor.execute("SELECT 1")
            return cursor.fetchone()[0] == 1

    def close_all(self) -> None:
        while True:
            try:
                connection = self._queue.get_nowait()
            except queue.Empty:
                break
            try:
                connection.close()
            except Exception:
                pass
        with self._lock:
            self._created = 0


_pool: ConnectionPool | None = None
_pool_lock = threading.Lock()


def init_pool(settings: Settings) -> ConnectionPool:
    global _pool
    with _pool_lock:
        if _pool is None:
            _pool = ConnectionPool(settings)
        return _pool


def get_pool() -> ConnectionPool:
    if _pool is None:
        raise RuntimeError("El pool de conexiones no fue inicializado.")
    return _pool


def close_pool() -> None:
    global _pool
    with _pool_lock:
        if _pool is not None:
            _pool.close_all()
            _pool = None
