"""
Orquestador del agente.

Modos:
    python main.py console              # ranking en la terminal (como antes)
    python main.py noite [--teste]      # 20h: reporte de mañana + 2 días + alertas
    python main.py madrugada [--teste]  # 4h30: confirmación solo si cambió algo + alertas

--teste  → muestra los mensajes sin enviarlos y NO guarda el estado.
--hoje AAAA-MM-DD → simula otra fecha (útil para pruebas).
"""
import argparse
from collections import defaultdict
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

import requests

import coleta
import envio
import estado as est
import relatorio
from mare import analisar_mare, extremos_mare
from nota import calcular_nota, graus_para_cardinal
from praias import PRAIAS, JANELA_HORAS, NOTA_ALERTA

# El runner de GitHub está en UTC: "hoy" tiene que calcularse en hora de Bahia,
# si no, a las 22h de Salvador (01h UTC) el agente pensaría que ya es mañana.
FUSO = ZoneInfo("America/Bahia")


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
            melhores[dia] = {**resultado, "registro": r,
                             "praia": praia["nome"], "regiao": praia["regiao"]}
    return melhores, extremos_mare(registros)


def calcular_previsao():
    por_dia = defaultdict(list)
    mares = {}
    for praia in PRAIAS.values():
        try:
            melhores, extremos = avaliar_praia(praia)
        except requests.RequestException as erro:
            print(f"❌ {praia['nome']}: erro ao buscar dados → {erro}")
            continue
        for dia, item in melhores.items():
            por_dia[dia].append(item)
        mares.setdefault(praia["regiao"], extremos)
    for ranking in por_dia.values():
        ranking.sort(key=lambda x: x["nota"], reverse=True)
    return dict(por_dia), mares


# ---------------- Modos ----------------

def modo_console(por_dia, mares):
    for dia in sorted(por_dia):
        print(f"\n===== {dia:%d/%m/%Y} =====")
        for pos, item in enumerate(por_dia[dia], 1):
            r = item["registro"]
            alerta = "  🚨 ALERTA" if item["nota"] >= NOTA_ALERTA else ""
            print(f"{pos}. {item['praia']:<13} {item['nota']:>4}/10  {r['hora']:%Hh}  "
                  f"swell {r['swell_altura']:.1f} m {graus_para_cardinal(r['swell_direcao'])} "
                  f"{r['swell_periodo']:.0f} s · vento {r['vento_vel']:.0f} kn "
                  f"{graus_para_cardinal(r['vento_direcao'])} ({item['tipo_vento']}) · "
                  f"maré {item['classe_mare']} {r['mare_tendencia']}{alerta}")
        extremos = [e for e in mares.get("salvador", []) if e[0].date() == dia]
        print("   Marés (Salvador): " +
              " · ".join(f"{t} {h:%H:%M} ({n} m)" for h, t, n in extremos))


def enviar_alertas(por_dia, estado, desde, teste):
    for dia in sorted(por_dia):
        melhor = por_dia[dia][0]
        if dia < desde or melhor["nota"] < NOTA_ALERTA or est.alerta_ja_enviado(estado, dia):
            continue
        envio.enviar(relatorio.alerta(melhor, dia), modo_teste=teste)
        est.registrar_alerta(estado, dia)


def modo_noite(por_dia, mares, estado, hoje, teste):
    amanha = hoje + timedelta(days=1)
    if amanha not in por_dia:
        raise SystemExit("❌ Sem dados para amanhã — nada enviado.")
    dias = [amanha + timedelta(days=i) for i in range(3)]
    envio.enviar(relatorio.relatorio_noite(por_dia, mares, dias), modo_teste=teste)
    est.registrar_relatorio(estado, amanha, por_dia[amanha][0])
    enviar_alertas(por_dia, estado, desde=amanha, teste=teste)


def modo_madrugada(por_dia, mares, estado, hoje, teste):
    if hoje not in por_dia:
        raise SystemExit("❌ Sem dados para hoje — nada enviado.")
    melhor = por_dia[hoje][0]
    if est.mudou(estado, hoje, melhor):
        anterior = estado.get("ultimo_relatorio")
        envio.enviar(relatorio.confirmacao(melhor, hoje, mares, anterior), modo_teste=teste)
    else:
        print("✔️ Previsão igual à da noite: nenhuma confirmação enviada.")
    est.registrar_relatorio(estado, hoje, melhor)
    enviar_alertas(por_dia, estado, desde=hoje, teste=teste)


def main(argv=None):
    parser = argparse.ArgumentParser(description="Agente de swell")
    parser.add_argument("modo", choices=["console", "noite", "madrugada"], nargs="?",
                        default="console")
    parser.add_argument("--teste", action="store_true",
                        help="mostra as mensagens sem enviar e não salva o estado")
    parser.add_argument("--hoje", type=date.fromisoformat,
                        help="simula outra data (AAAA-MM-DD)")
    args = parser.parse_args(argv)

    hoje = args.hoje or datetime.now(FUSO).date()
    por_dia, mares = calcular_previsao()

    if args.modo == "console":
        modo_console(por_dia, mares)
        return

    estado = est.carregar()
    if args.modo == "noite":
        modo_noite(por_dia, mares, estado, hoje, args.teste)
    else:
        modo_madrugada(por_dia, mares, estado, hoje, args.teste)

    # En modo teste no guardamos: si no, una prueba "gastaría" una alerta real.
    if not args.teste:
        est.salvar(estado, hoje)


if __name__ == "__main__":
    main()
