"""
Memoria del agente entre ejecuciones (estado.json, versionado en el repo).

¿Por qué hace falta? Cada ejecución de GitHub Actions arranca en una máquina
nueva, sin recuerdos. Para (1) no repetir alertas y (2) comparar la madrugada
con lo que se mandó a la noche, el agente necesita guardar qué hizo.

¿Por qué un JSON en el repo y no una base de datos? Para 2 datos alcanza,
es gratis y cada cambio queda en el historial de git (auditable).
"""
import json
from pathlib import Path

from praias import MUDANCA_NOTA

ARQUIVO = Path(__file__).with_name("estado.json")


def carregar(caminho=None):
    caminho = caminho or ARQUIVO
    if not caminho.exists():
        return {"alertas_enviados": [], "ultimo_relatorio": None}
    return json.loads(caminho.read_text(encoding="utf-8"))


def salvar(estado, hoje, caminho=None):
    caminho = caminho or ARQUIVO
    # Limpieza: alertas de días pasados ya no sirven (el archivo no crece infinito)
    estado["alertas_enviados"] = sorted(
        d for d in estado["alertas_enviados"] if d >= hoje.isoformat())
    caminho.write_text(json.dumps(estado, indent=2, ensure_ascii=False) + "\n",
                       encoding="utf-8")


def alerta_ja_enviado(estado, dia):
    return dia.isoformat() in estado["alertas_enviados"]


def registrar_alerta(estado, dia):
    estado["alertas_enviados"].append(dia.isoformat())


def registrar_relatorio(estado, dia, melhor):
    estado["ultimo_relatorio"] = {
        "data": dia.isoformat(), "melhor": melhor["praia"], "nota": melhor["nota"]}


def mudou(estado, dia, melhor_agora):
    """¿La previsión de la madrugada cambió respecto de la de la noche?"""
    anterior = estado.get("ultimo_relatorio")
    if not anterior or anterior["data"] != dia.isoformat():
        return True   # no hubo reporte a la noche (¿falló?): mejor avisar
    return (anterior["melhor"] != melhor_agora["praia"]
            or abs(anterior["nota"] - melhor_agora["nota"]) >= MUDANCA_NOTA)
