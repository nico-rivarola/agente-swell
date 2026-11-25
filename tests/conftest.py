"""
Fixtures compartidas por todos los tests.

¿Qué es una fixture? Una función que prepara el "escenario" de un test
(API falsa, estado temporal...) y pytest la inyecta en cada test que la pide
por nombre. Con `monkeypatch`, todo lo que se reemplaza vuelve a la
normalidad al terminar el test: un test nunca contamina al siguiente.
"""
import math
from datetime import datetime, timedelta

import pytest

import coleta
import envio
import estado as est
from praias import PRAIAS


@pytest.fixture
def jaguaribe():
    return PRAIAS["jaguaribe"]


@pytest.fixture
def dia_perfeito():
    return {"swell_altura": 1.2, "swell_direcao": 135, "swell_periodo": 11,
            "vento_vel": 8, "vento_direcao": 315,
            "mare_pos": 0.5, "mare_tendencia": "descendo"}


def _api_falsa(lat, lon):
    """72 h de mar bueno a partir del 19/11/2026 (mock de Open-Meteo)."""
    inicio = datetime(2026, 11, 19, 0, 0)
    regs = []
    for h in range(72):
        t = inicio + timedelta(hours=h)
        regs.append({
            "hora": t,
            "swell_altura": 1.0 + 0.3 * math.sin(h / 10),
            "swell_direcao": 140 + (lat * 10 % 40),
            "swell_periodo": 9 + (h % 24) / 12,
            "onda_total": 1.3,
            # marea semidiurna: período 12,42 h, amplitud ~1,1 m
            "nivel_mar": 1.1 * math.sin(2 * math.pi * h / 12.42),
            # terral NO a la madrugada, gira a SE/E de día (típico de Salvador)
            "vento_vel": 7 if t.hour < 9 else 14,
            "vento_direcao": 315 if t.hour < 9 else 110,
            "vento_rajada": 12,
        })
    return regs


@pytest.fixture
def api_falsa(monkeypatch):
    """Ningún test sale a internet: la API se reemplaza por datos conocidos."""
    monkeypatch.setattr(coleta, "buscar_dados", _api_falsa)


@pytest.fixture
def estado_temp(monkeypatch, tmp_path):
    """El estado va a una carpeta temporal: nunca se toca el estado.json real."""
    arquivo = tmp_path / "estado.json"
    monkeypatch.setattr(est, "ARQUIVO", arquivo)
    return arquivo


@pytest.fixture
def enviados(monkeypatch):
    """Captura los mensajes en una lista en vez de mandarlos por WhatsApp."""
    caixa = []
    monkeypatch.setattr(envio, "enviar",
                        lambda texto, modo_teste=False: caixa.append(texto) or False)
    return caixa
