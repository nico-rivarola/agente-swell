"""
Prueba SIN internet: reemplaza la API por datos inventados.

¿Por qué? Para probar la lógica de la nota sin depender de la red y con
casos que conocemos de antemano (sabemos qué nota DEBERÍA salir).
Esta técnica se llama "mock". Correlo con:  python teste_simulado.py
"""
import math
from datetime import datetime, timedelta

import coleta
import main
from nota import calcular_nota, tipo_vento, distancia_angular
from praias import PRAIAS

# ---- 1. Pruebas unitarias de casos conocidos ----
assert distancia_angular(350, 10) == 20
assert tipo_vento(315, ["NO"]) == "terral"
assert tipo_vento(135, ["NO"]) == "maral"      # SE en Jaguaribe = onshore
assert tipo_vento(45, ["NO"]) == "lateral"     # NE = cross-shore

jag = PRAIAS["jaguaribe"]
dia_perfeito = {"swell_altura": 1.2, "swell_direcao": 135, "swell_periodo": 11,
                "vento_vel": 8, "vento_direcao": 315,
                "mare_pos": 0.5, "mare_tendencia": "descendo"}
assert calcular_nota(dia_perfeito, jag)["nota"] == 10.0

dia_plano = {**dia_perfeito, "swell_altura": 0.3}
assert calcular_nota(dia_plano, jag)["nota"] <= 3.0, "el veto tiene que actuar"

maral_forte = {**dia_perfeito, "vento_vel": 14, "vento_direcao": 120}
n_jag = calcular_nota(maral_forte, jag)["nota"]
n_pia = calcular_nota(maral_forte, PRAIAS["piata"])["nota"]
assert n_pia > n_jag, "Piatã tiene que salir mejor con viento SE"
# Calibración 23/11: caso real del 19/11 (1 m E 5 s) → máximo 6
mar_de_vento = {**dia_perfeito, "swell_direcao": 90, "swell_periodo": 5}
assert calcular_nota(mar_de_vento, jag)["nota"] <= 6.0, "teto por período"

# Viento < 5 kn: espejo, aunque sea maral
espelho = {**dia_perfeito, "vento_vel": 3, "vento_direcao": 135}
res = calcular_nota(espelho, jag)
assert res["tipo_vento"] == "espelho" and res["subnotas"]["vento"] == 1.0

# Reglas confirmadas por Nicolás (no cambian el código, quedan protegidas)
assert tipo_vento(0, ["NO"]) == "terral"            # N en Salvador
assert tipo_vento(22.5, ["NO"]) == "lateral"        # NNE en Salvador
assert tipo_vento(45, ["ONO", "NO"]) == "lateral"   # NE en Linha Verde

print(f"✅ Pruebas unitarias OK  (SE 14 kn → Jaguaribe {n_jag} · Piatã {n_pia})")


# ---- 2. Simulación completa con una API falsa ----
def api_falsa(lat, lon):
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

coleta.buscar_dados = api_falsa
main.main()
