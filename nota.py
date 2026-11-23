"""
Nota de 0 a 10 por hora y por pico.

Cada criterio da una subnota de 0.0 a 1.0; la nota final es el promedio
ponderado (PESOS en praias.py) × 10.

Problema de un promedio puro: un día PLANO con viento perfecto sacaría ~6/10.
Por eso hay un "veto": si tamaño, dirección o viento dan 0, la nota queda
limitada a 3, porque cualquiera de esos tres solo ya arruina la sesión.
"""
from mare import classificar_mare
from praias import (PERIODO_BOM_S, TAMANHO_IDEAL_M, PESOS,
                    VENTO_ESPELHO_KN, TETOS_PERIODO)

PONTOS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
          "S", "SSO", "SO", "OSO", "O", "ONO", "NO", "NNO"]
CARDINAL_GRAUS = {p: i * 22.5 for i, p in enumerate(PONTOS)}


def graus_para_cardinal(graus):
    """0-360° → rosa de 16 puntos (sectores de 22,5°)."""
    if graus is None:
        return "?"
    return PONTOS[int(((graus + 11.25) % 360) // 22.5)]


def distancia_angular(a, b):
    """Menor ángulo entre dos direcciones. Ej.: 350° y 10° → 20°, no 340°."""
    d = abs(a - b) % 360
    return min(d, 360 - d)


def menor_distancia(graus, cardinais):
    return min(distancia_angular(graus, CARDINAL_GRAUS[c]) for c in cardinais)


# ---------------- Subnotas ----------------

def nota_direcao_swell(graus, ideais):
    d = menor_distancia(graus, ideais)
    if d <= 11.25:      # dentro de un sector ideal
        return 1.0
    if d <= 33.75:      # sector vecino
        return 0.6
    if d <= 56.25:
        return 0.25
    return 0.0          # el swell no entra en el pico


def nota_periodo(p):
    if p < 6:
        return 0.0      # mar de viento, sin fuerza
    if p < PERIODO_BOM_S:
        return 0.4
    if p < 10:
        return 0.8
    return 1.0


def nota_tamanho(h):
    minimo, maximo = TAMANHO_IDEAL_M
    if minimo <= h <= maximo:
        return 1.0
    if 0.8 <= h < minimo or maximo < h <= 2.0:
        return 0.6
    if 0.5 <= h < 0.8 or 2.0 < h <= 2.5:
        return 0.3
    return 0.0          # plano (<0,5 m) o demasiado grande (>2,5 m)


def tipo_vento(graus, vento_ideal):
    """Clasifica el viento respecto del terral ideal del pico."""
    d = menor_distancia(graus, vento_ideal)
    if d <= 45:
        return "terral"
    if d >= 112.5:
        return "maral"     # onshore
    return "lateral"       # cross-shore


def nota_vento(vel, graus, praia, periodo):
    # Viento muy flojo: mar espejo, sin importar de dónde sopla (regla de Nicolás)
    if vel < VENTO_ESPELHO_KN:
        return 1.0, "espelho"

    tipo = tipo_vento(graus, praia["vento_ideal"])

    if tipo == "terral":
        # Tus rangos: 5-12 ideal · 13-18 muy bueno · 19-22 límite · >25 no funciona
        if vel <= 12:
            return 1.0, tipo
        if vel <= 18:
            return 0.85, tipo
        if vel <= 22:
            return 0.5, tipo
        if vel <= 25:
            return 0.25, tipo
        return 0.0, tipo

    # Maral o lateral: la protección del pico reduce la velocidad "efectiva"
    vel_ef = vel * praia.get("fator_vento", 1.0)
    # Tu regla: con período alto (>14 s) el mar aguanta más el onshore
    if periodo is not None and periodo >= 14:
        vel_ef -= 3

    if tipo == "maral":
        # Tus rangos: 0-7 mínimo · 8-12 chop · 13-15 desordenado · >15 arruinado
        if vel_ef <= 7:
            return 0.8, tipo
        if vel_ef <= 12:
            return 0.5, tipo
        if vel_ef <= 15:
            return 0.2, tipo
        return 0.0, tipo

    # Lateral: a mitad de camino entre terral y maral
    if vel_ef <= 7:
        return 0.85, tipo
    if vel_ef <= 12:
        return 0.6, tipo
    if vel_ef <= 15:
        return 0.35, tipo
    if vel_ef <= 20:
        return 0.15, tipo
    return 0.0, tipo


# Tabla: regla del pico → {(clase de marea, tendencia): subnota}
TABELA_MARE = {
    "media_descendo": {("media", "descendo"): 1.0, ("media", "subindo"): 0.7,
                       ("cheia", "descendo"): 0.6, ("cheia", "subindo"): 0.4,
                       ("baixa", "descendo"): 0.4, ("baixa", "subindo"): 0.5},
    "media_subindo":  {("media", "subindo"): 1.0, ("media", "descendo"): 0.7,
                       ("baixa", "subindo"): 0.6, ("baixa", "descendo"): 0.4,
                       ("cheia", "subindo"): 0.5, ("cheia", "descendo"): 0.4},
    "media_cheia":    {("media", "subindo"): 1.0, ("media", "descendo"): 0.9,
                       ("cheia", "subindo"): 1.0, ("cheia", "descendo"): 0.9,
                       ("baixa", "subindo"): 0.4, ("baixa", "descendo"): 0.2},
}


def nota_mare(pos, tendencia, regra):
    classe = classificar_mare(pos)
    return TABELA_MARE[regra].get((classe, tendencia), 0.5), classe


# ---------------- Nota final ----------------

def calcular_nota(r, praia):
    """Devuelve un dict con la nota y el detalle, o None si faltan datos."""
    necessarios = ["swell_altura", "swell_direcao", "swell_periodo",
                   "vento_vel", "vento_direcao"]
    if any(r.get(c) is None for c in necessarios):
        return None

    s_vento, tipo = nota_vento(r["vento_vel"], r["vento_direcao"], praia, r["swell_periodo"])
    if r.get("mare_pos") is not None:
        s_mare, classe_mare = nota_mare(r["mare_pos"], r["mare_tendencia"], praia["mare_ideal"])
    else:
        s_mare, classe_mare = 0.5, None   # sin dato de marea: neutro

    sub = {
        "vento": s_vento,
        "direcao": nota_direcao_swell(r["swell_direcao"], praia["swell_ideal"]),
        "tamanho": nota_tamanho(r["swell_altura"]),
        "periodo": nota_periodo(r["swell_periodo"]),
        "mare": s_mare,
    }
    nota = 10 * sum(PESOS[k] * v for k, v in sub.items())
    if min(sub["tamanho"], sub["direcao"], sub["vento"]) == 0:
        nota = min(nota, 3.0)
    # Techo por período corto: el promedio solo no alcanza para castigar
    # el mar de viento (el período pesa 15 %).
    for limite_s, teto in TETOS_PERIODO:
        if r["swell_periodo"] < limite_s:
            nota = min(nota, teto)

    return {
        "nota": round(nota, 1),
        "subnotas": sub,
        "tipo_vento": tipo,
        "classe_mare": classe_mare,
    }
