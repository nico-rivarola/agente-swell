"""
Marea: a partir de la curva horaria del nivel del mar calcula
  1. la POSICIÓN de la marea en cada hora (0 = bajamar, 1 = pleamar)
  2. la TENDENCIA (subindo / descendo)
  3. los horarios de pleamar y bajamar (extremos)
"""
from datetime import timedelta

# En Salvador la marea es semidiurna: ~2 pleamares y 2 bajamares por día,
# un ciclo cada ~12h25. Una ventana de ±7 h siempre contiene un ciclo completo.
JANELA_CICLO_H = 7


def analisar_mare(registros):
    """Agrega 'mare_pos' y 'mare_tendencia' a cada registro (lo modifica)."""
    niveis = [r["nivel_mar"] for r in registros]
    for i, r in enumerate(registros):
        janela = [n for n in niveis[max(0, i - JANELA_CICLO_H): i + JANELA_CICLO_H + 1]
                  if n is not None]
        if r["nivel_mar"] is None or len(janela) < 2 or max(janela) == min(janela):
            r["mare_pos"], r["mare_tendencia"] = None, None
            continue
        # Normalizamos: la amplitud cambia entre marea de sicigia (luna
        # llena/nueva) y de cuadratura. Así "media" significa lo mismo siempre.
        r["mare_pos"] = (r["nivel_mar"] - min(janela)) / (max(janela) - min(janela))

        anterior = niveis[i - 1] if i > 0 else None
        seguinte = niveis[i + 1] if i + 1 < len(niveis) else None
        if anterior is not None:
            r["mare_tendencia"] = "subindo" if r["nivel_mar"] > anterior else "descendo"
        elif seguinte is not None:
            r["mare_tendencia"] = "subindo" if seguinte > r["nivel_mar"] else "descendo"
        else:
            r["mare_tendencia"] = None
    return registros


def classificar_mare(pos):
    if pos is None:
        return None
    if pos < 0.3:
        return "baixa"
    if pos > 0.7:
        return "cheia"
    return "media"


def extremos_mare(registros):
    """Devuelve [(datetime, 'preamar'|'baixa-mar', nivel)].

    Los datos son horarios, pero la pleamar real puede ser 6:40. Con
    interpolación parabólica (pasamos una parábola por los 3 puntos alrededor
    del pico) estimamos el minuto, con error típico de ~10-15 min.
    """
    extremos = []
    for i in range(1, len(registros) - 1):
        y0, y1, y2 = (registros[i - 1]["nivel_mar"], registros[i]["nivel_mar"],
                      registros[i + 1]["nivel_mar"])
        if None in (y0, y1, y2):
            continue
        if y1 > y0 and y1 >= y2:
            tipo = "preamar"
        elif y1 < y0 and y1 <= y2:
            tipo = "baixa-mar"
        else:
            continue
        denom = y0 - 2 * y1 + y2
        desvio_h = 0.5 * (y0 - y2) / denom if denom != 0 else 0.0
        nivel = y1 - 0.25 * (y0 - y2) * desvio_h
        hora = registros[i]["hora"] + timedelta(hours=desvio_h)
        extremos.append((hora, tipo, round(nivel, 2)))
    return extremos
