"""
Envío de mensajes. Todo el "canal" (CallMeBot hoy, Meta/Telegram mañana)
vive acá: para cambiar de canal se toca SOLO este archivo.

Credenciales: vienen de variables de entorno (GitHub Secrets), nunca del código.
Con --teste el mensaje se imprime en vez de enviarse; sin credenciales, falla.
"""
import os
import re
import time

import requests

URL_CALLMEBOT = "https://api.callmebot.com/whatsapp.php"
INTERVALO_ENTRE_ENVIOS_S = 5   # no saturar el bot gratuito con mensajes seguidos

_ultimo_envio = 0.0


def resposta_sanitizada(html, *segredos, limite=400):
    """Texto de la respuesta, legible y SIN datos sensibles (el log es público).

    1. Quita etiquetas HTML y espacios de más.
    2. Borra los secretos literales (apikey, teléfono).
    3. Por las dudas, tapa cualquier secuencia de 6+ dígitos (otro formato del número).
    """
    texto = re.sub(r"<script.*?</script>|<style.*?</style>", " ", html, flags=re.S | re.I)
    texto = re.sub(r"<[^>]+>", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip()
    for segredo in segredos:
        if segredo:
            texto = texto.replace(segredo, "***").replace(segredo.lstrip("+"), "***")
    texto = re.sub(r"\d{6,}", "***", texto)
    return texto if limite is None else texto[:limite]


def enviar(texto, modo_teste=False):
    """Devuelve True si envió de verdad, False si fue modo teste."""
    global _ultimo_envio
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    telefone = os.environ.get("WHATSAPP_PHONE")

    if modo_teste:
        print("📝 MODO TESTE — mensagem NÃO enviada:")
        print(texto)
        print("-" * 40)
        return False

    # Sin secrets y sin --teste: FALLAR en vez de simular en silencio.
    # Si no, el workflow sale "✅ Éxito", guarda el estado como si hubiera
    # enviado y vos nunca te enterás de que no llegó nada.
    faltando = [n for n, v in [("CALLMEBOT_APIKEY", apikey),
                               ("WHATSAPP_PHONE", telefone)] if not v]
    if faltando:
        raise RuntimeError("Secret não configurado: " + ", ".join(faltando)
                           + " (Settings → Secrets and variables → Actions)")

    espera = INTERVALO_ENTRE_ENVIOS_S - (time.monotonic() - _ultimo_envio)
    if espera > 0:
        time.sleep(espera)

    try:
        # params=: requests codifica el texto (espacios, acentos, emojis) en la URL
        r = requests.get(URL_CALLMEBOT,
                         params={"phone": telefone, "text": texto, "apikey": apikey},
                         timeout=30)
        r.raise_for_status()
    except requests.RequestException as erro:
        # ⚠️ SEGURIDAD: NO imprimimos `erro`. Su texto incluye la URL completa,
        # con tu apikey y tu teléfono. Como el repo es público, los logs de
        # Actions también lo son. "from None" corta la cadena del error original.
        raise RuntimeError(f"Falha ao enviar WhatsApp ({type(erro).__name__})") from None

    # CallMeBot responde 200 incluso cuando rechaza: hay que leer la página.
    # La página de éxito repite TU mensaje ("Text to send: ..."), así que lo
    # sacamos antes de buscar palabras de error (evita falsos positivos).
    pagina = resposta_sanitizada(r.text, apikey, telefone, limite=None)
    eco = resposta_sanitizada(texto, limite=None)
    for variante in (eco, eco.replace(" ", "%0A")):
        pagina = pagina.replace(variante, "[mensagem]")
    achado = re.search(r"error|invalid", pagina, flags=re.I)
    if achado:
        trecho = pagina[max(0, achado.start() - 150): achado.end() + 150]
        print("Resposta do CallMeBot (trecho sanitizado):", trecho)
        raise RuntimeError("CallMeBot recusou a mensagem (verifique apikey e telefone)")

    _ultimo_envio = time.monotonic()
    print("✅ WhatsApp enviado")
    return True
