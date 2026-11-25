"""Flujo completo (noite / madrugada / alertas) con API falsa y sin enviar nada."""
from datetime import date

import estado as est
import main

NOITE = ["noite", "--hoje", "2026-11-18"]
MADRUGADA = ["madrugada", "--hoje", "2026-11-19"]


def test_console_no_rompe(api_falsa, capsys):
    main.main(["console"])
    assert "19/11/2026" in capsys.readouterr().out


def test_relatorio_noite(api_falsa, estado_temp, enviados):
    main.main(NOITE)
    texto = enviados[0]
    assert texto.startswith("🌊 *Previsão de surf — quinta, 19/11*")
    assert "🥇" in texto and "📅 *Próximos dias*" in texto
    assert "." not in texto.split("nota ")[1][:3], "nota con coma decimal"
    assert any("ALERTA DE SWELL" in t for t in enviados)


def test_alerta_no_se_repite(api_falsa, estado_temp, enviados):
    main.main(NOITE)
    enviados.clear()
    main.main(NOITE)
    assert not any("ALERTA DE SWELL" in t for t in enviados)


def test_madrugada_sin_cambios_no_avisa(api_falsa, estado_temp, enviados):
    main.main(NOITE)
    enviados.clear()
    main.main(MADRUGADA)
    assert not any("Atualização" in t for t in enviados)


def test_madrugada_con_cambio_avisa(api_falsa, estado_temp, enviados):
    main.main(NOITE)
    e = est.carregar()
    e["ultimo_relatorio"]["nota"] -= 3
    est.salvar(e, date(2026, 11, 19))
    enviados.clear()
    main.main(MADRUGADA)
    assert any("Atualização" in t for t in enviados)


def test_modo_teste_no_guarda_estado(api_falsa, estado_temp, enviados):
    main.main(["noite", "--teste", "--hoje", "2026-11-18"])
    assert not estado_temp.exists()
