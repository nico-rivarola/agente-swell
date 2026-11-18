"""
PASO 2 — Ranking de picos por día (todavía en consola, sin WhatsApp).

Cómo probar:
    pip install -r requirements.txt
    python main.py
"""
from collections import defaultdict

import requests

import coleta
from mare import analisar_mare, extremos_mare
from nota import calcular_nota, graus_para_cardinal
from praias import PRAIAS, JANELA_HORAS, NOTA_ALERTA


def avaliar_praia(praia):
    """Devuelve {fecha: mejor_hora_del_dia} y los extremos de marea."""
    registros = analisar_mare(coleta.buscar_dados(praia["lat"], praia["lon"]))
    melhores = {}
    for r in registros:
        if r["hora"].hour not in JANELA_HORAS:
            continue
        resultado = calcular_nota(r, praia)
        if resultado is None:
            continue
        dia = r["hora"].date()
        if dia not in melhores or resultado["nota"] > melhores[dia]["nota"]:
            melhores[dia] = {**resultado, "registro": r, "praia": praia["nome"]}
    return melhores, extremos_mare(registros)


def descrever(item):
    r = item["registro"]
    return (f"{item['praia']:<13} {item['nota']:>4}/10  {r['hora']:%Hh}  "
            f"swell {r['swell_altura']:.1f} m {graus_para_cardinal(r['swell_direcao'])} "
            f"{r['swell_periodo']:.0f} s · vento {r['vento_vel']:.0f} kn "
            f"{graus_para_cardinal(r['vento_direcao'])} ({item['tipo_vento']}) · "
            f"maré {item['classe_mare']} {r['mare_tendencia']}")


def main():
    por_dia = defaultdict(list)
    mares = {}
    for chave, praia in PRAIAS.items():
        try:
            melhores, extremos = avaliar_praia(praia)
        except requests.RequestException as erro:
            print(f"❌ {praia['nome']}: erro ao buscar dados → {erro}")
            continue
        for dia, item in melhores.items():
            por_dia[dia].append(item)
        mares.setdefault("salvador" if praia["lat"] < -12.8 else "linha_verde", extremos)

    for dia in sorted(por_dia):
        ranking = sorted(por_dia[dia], key=lambda x: x["nota"], reverse=True)
        print(f"\n===== {dia:%d/%m/%Y} =====")
        for pos, item in enumerate(ranking, 1):
            alerta = "  🚨 ALERTA" if item["nota"] >= NOTA_ALERTA else ""
            print(f"{pos}. {descrever(item)}{alerta}")
        extremos_dia = [e for e in mares.get("salvador", []) if e[0].date() == dia]
        print("   Marés (Salvador): " +
              " · ".join(f"{t} {h:%H:%M} ({n} m)" for h, t, n in extremos_dia))


if __name__ == "__main__":
    main()
