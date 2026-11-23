# Diário de calibração

Registre aqui cada vez que a nota prevista não bateu com o mar real.
Assim os ajustes em `praias.py` ficam justificados e com histórico.

| Data | Pico | Nota prevista | Como estava de verdade | Critério que falhou | Ajuste feito |
|---|---|---|---|---|---|
| 19/11/2026 | Todos | 5,9–6,5 (Jaguaribe 6,5) | Swell E 1 m com período de 5 s = mar de vento; "serve para treinar" | Período (peso 15 % não bastava) | Teto: período < 6 s → nota máx. 6 (`TETOS_PERIODO`) |
| 20/11/2026 | Jaguaribe | 7,3 com vento 3 kn N | Abaixo de 5 kn o mar fica espelho, a direção não importa | Vento | `VENTO_ESPELHO_KN = 5` → subnota de vento 1,0 |
| 23/11/2026 | Salvador / Linha Verde | — | Confirmado: N = terral, NNE = lateral (Salvador); NE = lateral aceitável (Linha Verde) | — | Sem mudança; regras protegidas com testes |
