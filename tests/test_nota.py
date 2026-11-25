"""Reglas de la nota: casos conocidos y calibraciones reales (CALIBRACAO.md)."""
import pytest

from nota import calcular_nota, distancia_angular, tipo_vento
from praias import PRAIAS


def test_distancia_angular_cruza_el_norte():
    assert distancia_angular(350, 10) == 20


# parametrize: una sola función, un test por fila (si falla, dice cuál)
@pytest.mark.parametrize("grados, terrais, esperado", [
    (315, ["NO"], "terral"),
    (135, ["NO"], "maral"),          # SE en Jaguaribe = onshore
    (45, ["NO"], "lateral"),         # NE = cross-shore
    # Reglas confirmadas por Nicolás el 23/11
    (0, ["NO"], "terral"),           # N en Salvador
    (22.5, ["NO"], "lateral"),       # NNE en Salvador
    (45, ["ONO", "NO"], "lateral"),  # NE en Linha Verde
])
def test_tipo_vento(grados, terrais, esperado):
    assert tipo_vento(grados, terrais) == esperado


def test_dia_perfeito_da_10(dia_perfeito, jaguaribe):
    assert calcular_nota(dia_perfeito, jaguaribe)["nota"] == 10.0


def test_veto_dia_plano(dia_perfeito, jaguaribe):
    plano = {**dia_perfeito, "swell_altura": 0.3}
    assert calcular_nota(plano, jaguaribe)["nota"] <= 3.0


def test_piata_protegida_del_maral(dia_perfeito, jaguaribe):
    maral = {**dia_perfeito, "vento_vel": 14, "vento_direcao": 120}
    n_jag = calcular_nota(maral, jaguaribe)["nota"]
    n_pia = calcular_nota(maral, PRAIAS["piata"])["nota"]
    assert n_pia > n_jag


def test_teto_periodo_curto(dia_perfeito, jaguaribe):
    """Calibración 19/11: 1 m E 5 s es mar de viento → máximo 6."""
    mar_de_vento = {**dia_perfeito, "swell_direcao": 90, "swell_periodo": 5}
    assert calcular_nota(mar_de_vento, jaguaribe)["nota"] <= 6.0


def test_vento_espelho(dia_perfeito, jaguaribe):
    """Calibración 20/11: < 5 kn es espejo, aunque venga del mar."""
    res = calcular_nota({**dia_perfeito, "vento_vel": 3, "vento_direcao": 135}, jaguaribe)
    assert res["tipo_vento"] == "espelho"
    assert res["subnotas"]["vento"] == 1.0


def test_desempate_por_nota_bruta(dia_perfeito, jaguaribe):
    """Cuando todos quedan en el techo, la nota bruta ordena el ranking."""
    mar_de_vento = {**dia_perfeito, "swell_direcao": 90, "swell_periodo": 5}
    com_maral = calcular_nota({**mar_de_vento, "vento_vel": 12, "vento_direcao": 135}, jaguaribe)
    limpo = calcular_nota(mar_de_vento, jaguaribe)
    assert com_maral["nota"] == limpo["nota"] == 6.0
    assert limpo["nota_bruta"] > com_maral["nota_bruta"]
