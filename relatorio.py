"""
Arma los textos de WhatsApp en portugués de Brasil.

Formato brasileño: coma decimal (1,2 m), fecha dd/mm, horas 05h / 12h36.
WhatsApp: *texto* = negrita.
"""
from nota import graus_para_cardinal
from praias import NOTA_ALERTA, NOTA_MINIMA_BOA

DIAS = ["segunda", "terça", "quarta", "quinta", "sexta", "sábado", "domingo"]
DIAS_CURTOS = ["Seg", "Ter", "Qua", "Qui", "Sex", "Sáb", "Dom"]
MEDALHAS = ["🥇", "🥈", "🥉"]


# ---------------- Formato ----------------

def num(valor, casas=1):
    """1.25 → '1,3' (formato brasileño)."""
    return f"{valor:.{casas}f}".replace(".", ",")


def hora(dt):
    return f"{dt:%H}h" if dt.minute == 0 else f"{dt:%H}h{dt:%M}"


def data_curta(dia):
    return f"{dia:%d/%m}"


# ---------------- Piezas del mensaje ----------------

def descrever_swell(item):
    r = item["registro"]
    return (f"Swell {num(r['swell_altura'])} m de {graus_para_cardinal(r['swell_direcao'])}"
            f" · período {int(r['swell_periodo'])} s")
    # int() trunca (5,8 → 5) en vez de redondear (5,8 → 6): así el número
    # mostrado es coherente con la regla "menos de 6 s = mar de viento".


def descrever_vento(item):
    r = item["registro"]
    vel = r["vento_vel"]
    if item["tipo_vento"] == "espelho":
        return f"{num(vel, 0)} kn — mar espelho"
    forca = "fraco" if vel < 8 else "moderado" if vel <= 15 else "forte"
    return f"{num(vel, 0)} kn de {graus_para_cardinal(r['vento_direcao'])} ({item['tipo_vento']} {forca})"


def descrever_mare(item, extremos):
    r = item["registro"]
    classe = {"baixa": "baixa", "media": "média", "cheia": "cheia"}.get(item["classe_mare"])
    if classe is None:
        return "Maré: sem dados"
    tendencia = {"subindo": "enchendo", "descendo": "vazando"}.get(r.get("mare_tendencia"), "")
    texto = f"Maré {classe}" + (f", {tendencia}" if tendencia else "")
    proximo = next((e for e in extremos if e[0] > r["hora"]), None)
    if proximo:
        texto += f" ({proximo[1]} {hora(proximo[0])})"
    return texto


def comentario(item):
    """Una frase amigable según el punto más fuerte o más débil del día."""
    r, sub, nota = item["registro"], item["subnotas"], item["nota"]
    if nota >= NOTA_ALERTA:
        return "Dia muito bom, vale acordar cedo! 🤙"
    if r["swell_periodo"] < 8:
        return "Período curto: ondas com pouca força, bom pra treinar."
    if sub["vento"] <= 0.5:
        return "O vento vai deixar o mar mexido."
    if r["swell_altura"] < 0.8:
        return "Ondas pequenas hoje."
    if r["swell_altura"] > 1.8:
        return "Mar grande, cuidado na entrada! ⚠️"
    return "Dá pra surfar bem. Boas ondas! 🏄"


def bloco_detalhe(item, extremos):
    return [
        f"⏰ Melhor horário: {hora(item['registro']['hora'])}",
        f"🌊 {descrever_swell(item)}",
        f"💨 Vento {descrever_vento(item)}",
        f"🌙 {descrever_mare(item, extremos)}",
    ]


# ---------------- Mensajes ----------------

def relatorio_noite(por_dia, mares, dias):
    amanha = dias[0]
    ranking = por_dia[amanha]
    melhor = ranking[0]
    linhas = [f"🌊 *Previsão de surf — {DIAS[amanha.weekday()]}, {data_curta(amanha)}*", ""]

    if melhor["nota"] < NOTA_MINIMA_BOA:
        linhas += [f"😴 Amanhã sem ondas boas (melhor: {melhor['praia']}, "
                   f"nota {num(melhor['nota'])}).", "Aproveita pra descansar!"]
    else:
        linhas.append(f"🥇 *{melhor['praia']}* — nota {num(melhor['nota'])}/10")
        linhas += bloco_detalhe(melhor, mares.get(melhor["regiao"], []))
        linhas.append("")
        for medalha, item in zip(MEDALHAS[1:], ranking[1:3]):
            linhas.append(f"{medalha} {item['praia']} — {num(item['nota'])}"
                          f" · {hora(item['registro']['hora'])}")

    proximos = [d for d in dias[1:] if d in por_dia]
    if proximos:
        linhas += ["", "📅 *Próximos dias*"]
        for dia in proximos:
            top = por_dia[dia][0]
            marca = " 🚨" if top["nota"] >= NOTA_ALERTA else ""
            linhas.append(f"{DIAS_CURTOS[dia.weekday()]} {data_curta(dia)} → "
                          f"{top['praia']} {num(top['nota'])}{marca}")

    if melhor["nota"] >= NOTA_MINIMA_BOA:
        linhas += ["", f"💬 {comentario(melhor)}"]
    return "\n".join(linhas)


def alerta(item, dia):
    r = item["registro"]
    return "\n".join([
        "🚨 *ALERTA DE SWELL!* 🚨",
        f"{DIAS[dia.weekday()].capitalize()} {data_curta(dia)} → "
        f"*{item['praia']} nota {num(item['nota'])}*",
        f"{descrever_swell(item)} · vento {descrever_vento(item)}",
        f"Melhor horário: {hora(r['hora'])}. Prepara a prancha! 🏄",
    ])


def confirmacao(item, dia, mares, anterior=None):
    linhas = [f"🔄 *Atualização da previsão — hoje, {data_curta(dia)}*"]
    if anterior and anterior.get("data") == dia.isoformat():
        linhas.append(f"Ontem à noite: {anterior['melhor']} {num(anterior['nota'])} → agora:")
    linhas += ["", f"🥇 *{item['praia']}* — nota {num(item['nota'])}/10"]
    linhas += bloco_detalhe(item, mares.get(item["regiao"], []))
    return "\n".join(linhas)
