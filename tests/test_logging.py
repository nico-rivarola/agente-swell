"""Logging: qué se registra, con qué nivel, y que nunca se filtren secretos."""
import logging

import pytest
import requests

import coleta
import envio
import main
from conftest import _api_falsa

APIKEY = "1234567"
TELEFONE = "+5571999998888"


def test_pico_sin_datos_es_warning_y_los_demas_siguen(monkeypatch, caplog, capsys):
    def api_que_falla_en_un_pico(lat, lon):
        if lat == main.PRAIAS["jaguaribe"]["lat"]:
            raise requests.ConnectionError("timeout simulado")
        return _api_falsa(lat, lon)

    monkeypatch.setattr(coleta, "buscar_dados", api_que_falla_en_un_pico)
    main.main(["console"])

    avisos = [r for r in caplog.records if r.levelno == logging.WARNING]
    assert len(avisos) == 1 and "Jaguaribe" in avisos[0].getMessage()
    assert "Piatã" in capsys.readouterr().out   # el resto del ranking salió igual


def test_sin_datos_para_manana_es_error(monkeypatch, caplog, estado_temp, enviados):
    monkeypatch.setattr(coleta, "buscar_dados", lambda lat, lon: [])
    with pytest.raises(SystemExit) as salida:
        main.main(["noite", "--hoje", "2026-11-18"])
    assert salida.value.code == 1          # código ≠ 0 → el workflow queda en rojo
    assert any(r.levelno == logging.ERROR for r in caplog.records)
    assert enviados == []


def test_madrugada_sin_cambios_queda_en_el_log(api_falsa, estado_temp, enviados, caplog):
    main.main(["noite", "--hoje", "2026-11-18"])
    caplog.clear()
    with caplog.at_level(logging.INFO):
        main.main(["madrugada", "--hoje", "2026-11-19"])
    assert "nenhuma confirmação enviada" in caplog.text


def test_urllib3_nunca_loguea_urls_en_debug():
    """En DEBUG, urllib3 escribiría la URL de CallMeBot (con apikey y teléfono)."""
    main.configurar_logging("DEBUG")
    assert logging.getLogger("urllib3").getEffectiveLevel() >= logging.WARNING


def test_rechazo_de_callmebot_no_filtra_secretos(monkeypatch, caplog):
    monkeypatch.setenv("CALLMEBOT_APIKEY", APIKEY)
    monkeypatch.setenv("WHATSAPP_PHONE", TELEFONE)

    class RespostaFalsa:
        # CallMeBot responde 200 pero con un error que repite tus datos
        text = f"<p>APIKey {APIKEY} is invalid for phone {TELEFONE}</p>"

        def raise_for_status(self):
            pass

    monkeypatch.setattr(envio.requests, "get", lambda *a, **k: RespostaFalsa())
    with caplog.at_level(logging.DEBUG), pytest.raises(RuntimeError):
        envio.enviar("Teste")

    assert "invalid" in caplog.text                  # el motivo sí aparece...
    assert APIKEY not in caplog.text                 # ...pero los secretos no
    assert TELEFONE.lstrip("+") not in caplog.text
