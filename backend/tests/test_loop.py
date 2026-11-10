"""Pruebas del bucle de eventos usado por uvicorn en Windows."""

from __future__ import annotations

import asyncio
import sys

import backend.main as main
from backend.core.loop import event_loop_factory


def test_factory_devuelve_una_instancia_de_loop() -> None:
    loop = event_loop_factory()
    try:
        assert isinstance(loop, asyncio.AbstractEventLoop)
        if sys.platform == "win32":
            # ProactorEventLoop cierra el listener ante WinError 64.
            assert isinstance(loop, asyncio.SelectorEventLoop)
            assert not isinstance(loop, asyncio.ProactorEventLoop)
    finally:
        loop.close()


def test_run_pasa_la_fabrica_de_loop_a_uvicorn(monkeypatch) -> None:
    capturado: dict[str, object] = {}

    def falso_run(app: str, **kwargs: object) -> None:
        capturado["app"] = app
        capturado.update(kwargs)

    monkeypatch.setattr(main.uvicorn, "run", falso_run)

    main.run()

    assert capturado["app"] == "backend.main:app"
    assert capturado["loop"] == "backend.core.loop:event_loop_factory"
