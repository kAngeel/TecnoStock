"""Selección del event loop de asyncio.

En Windows, uvicorn usa ``ProactorEventLoop`` (IOCP) cuando corre en un solo
proceso. Su ``accept`` puede fallar con ``WinError 64`` ("El nombre de red
especificado ya no está disponible") cuando un cliente aborta la conexión
justo antes de que IOCP la acepte. En ese caso asyncio registra el error y
**cierra el socket de escucha**, por lo que el servidor deja de aceptar
conexiones nuevas aunque el proceso siga vivo.

``SelectorEventLoop`` usa ``select()`` y, ante el mismo error, solo registra
la excepción y mantiene el listener abierto: la siguiente conexión se acepta
con normalidad.

Esta fábrica se pasa a uvicorn con
``loop="backend.core.loop:event_loop_factory"``. No se parchean módulos de la
biblioteca estándar ni se silencian excepciones: el error se sigue viendo en
los registros, pero deja de tumbar el listener.
"""

from __future__ import annotations

import asyncio
import sys


def event_loop_factory() -> asyncio.AbstractEventLoop:
    """Crea el event loop que usará uvicorn.

    Uvicorn importa esta función y la llama sin argumentos, por lo que debe
    devolver una instancia de loop (no una clase).
    """
    if sys.platform == "win32":
        return asyncio.SelectorEventLoop()
    return asyncio.new_event_loop()
