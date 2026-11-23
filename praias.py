"""
Configuración de los picos y de las reglas de puntuación.

¿Por qué un archivo separado? Porque las REGLAS (tu conocimiento de surfista)
cambian seguido y no deberían mezclarse con el CÓDIGO. Para calibrar el agente
vas a editar casi siempre solo este archivo.

Direcciones: siempre "de dónde VIENE" (convención de meteorología).
  Swell SE = la ola viene del sudeste.  Viento NO = sopla desde el noroeste.

⚠️ Coordenadas APROXIMADAS: confirmalas en Google Maps (clic derecho en el
mar, frente al pico → copiar coordenadas). Usá un punto ~300-500 m mar adentro:
si el punto cae en tierra, la API marina devuelve null.
"""

PRAIAS = {
    "jaguaribe": {
        "nome": "Jaguaribe",
        "lat": -12.955, "lon": -38.400,
        "swell_ideal": ["E", "SE", "S"],
        "vento_ideal": ["NO"],
        "fundo": "areia",
        "mare_ideal": "media_descendo",
        "fator_vento": 1.0,   # 1.0 = expuesta al viento normalmente
    },
    "piata": {
        "nome": "Piatã",
        "lat": -12.957, "lon": -38.380,
        "swell_ideal": ["E", "SE", "S"],
        "vento_ideal": ["NO"],
        "fundo": "areia",
        "mare_ideal": "media_descendo",
        # Más protegida: el viento maral/lateral "pega" como si fuera 30 %
        # más débil. Es un número inicial: calibralo comparando con el agua.
        "fator_vento": 0.7,
    },
    "stella_maris": {
        "nome": "Stella Maris",
        "lat": -12.945, "lon": -38.330,
        "swell_ideal": ["S", "SE"],
        "vento_ideal": ["ONO", "NO"],
        "fundo": "areia e pedra",
        "mare_ideal": "media_subindo",
        "fator_vento": 1.0,
    },
    "itacimirim": {
        "nome": "Itacimirim",
        "lat": -12.630, "lon": -38.035,
        "swell_ideal": ["S", "SE", "E"],
        "vento_ideal": ["ONO", "NO"],
        "fundo": "coral e areia",
        "mare_ideal": "media_cheia",
        "fator_vento": 1.0,
    },
    "guarajuba": {
        "nome": "Guarajuba",
        "lat": -12.655, "lon": -38.058,
        "swell_ideal": ["S", "SE", "E"],
        "vento_ideal": ["ONO", "NO"],
        "fundo": "coral e areia",
        "mare_ideal": "media_cheia",
        "fator_vento": 1.0,
    },
}

# ---------------- Reglas generales ----------------
JANELA_HORAS = [5, 6, 7]       # tu horario preferido
DIAS_PREVISAO = 3              # hoy + 2 días

PERIODO_BOM_S = 8              # "a partir de 8 s ya es bueno"
TAMANHO_IDEAL_M = (1.0, 1.5)   # tu rango preferido de swell

# Peso de cada criterio en la nota final (suman 1.0).
# El viento pesa más porque es lo que más rápido arruina un día con buen swell.
PESOS = {
    "vento": 0.30,
    "direcao": 0.20,
    "tamanho": 0.20,
    "periodo": 0.15,
    "mare": 0.15,
}

NOTA_ALERTA = 8.0   # desde esta nota se manda el "alerta especial"

# Calibración 23/11/2026 (ver CALIBRACAO.md)
# Con menos de 5 kn el mar queda espejo: la dirección del viento no importa.
VENTO_ESPELHO_KN = 5
# Techo de la nota según el período: (período por debajo de X s, nota máxima).
# Con menos de 6 s es mar de viento: "sirve para entrenar", máximo 6.
TETOS_PERIODO = [(6, 6.0)]
