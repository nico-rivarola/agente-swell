"""
Envío de mensajes. Todo el "canal" (CallMeBot hoy, Meta/Telegram mañana)
vive acá: para cambiar de canal se toca SOLO este archivo.

Credenciales: vienen de variables de entorno (GitHub Secrets), nunca del código.
Sin credenciales → MODO TESTE: el mensaje se imprime en vez de enviarse.
"""
import os
import time

import requests

URL_CALLMEBOT = "https://api.callmebot.com/whatsapp.php"
INTERVALO_ENTRE_ENVIOS_S = 5   # no saturar el bot gratuito con mensajes seguidos

_ultimo_envio = 0.0


def enviar(texto, modo_teste=False):
    """Devuelve True si envió de verdad, False si fue modo teste."""
    global _ultimo_envio
    apikey = os.environ.get("CALLMEBOT_APIKEY")
    telefone = os.environ.get("WHATSAPP_PHONE")

    if modo_teste or not apikey or not telefone:
        # Decimos el MOTIVO (sin mostrar valores): si no, "falta el secret" y
        # "marcaste teste" se ven iguales en el log.
        if modo_teste:
            motivo = "opção --teste ativada"
        else:
            faltando = [n for n, v in [("CALLMEBOT_APIKEY", apikey),
                                       ("WHATSAPP_PHONE", telefone)] if not v]
            motivo = "secret não configurado: " + ", ".join(faltando)
        print(f"📝 MODO TESTE ({motivo}) — mensagem NÃO enviada:")
        print(texto)
        print("-" * 40)
        return False

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

    # CallMeBot a veces responde 200 aunque haya un error: revisamos el texto,
    # pero sin imprimirlo (podría contener tu número).
    if "error" in r.text.lower() or "invalid" in r.text.lower():
        raise RuntimeError("CallMeBot recusou a mensagem (verifique apikey e telefone)")

    _ultimo_envio = time.monotonic()
    print("✅ WhatsApp enviado")
    return True
