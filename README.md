# 🌊 Agente de Swell — Salvador & Linha Verde

Agente em Python que consulta previsões de ondas, vento e maré, dá uma **nota de 0 a 10** para cada pico de surf e indica **onde surfar amanhã cedo** (5h–7h). Em breve: relatório amigável por WhatsApp, enviado automaticamente pelo GitHub Actions.

**Picos:** Jaguaribe · Piatã · Stella Maris · Itacimirim · Guarajuba

## Por que este projeto?

Analisar Windguru/Surfguru manualmente toma tempo e pode ser confuso. Este agente transforma os dados brutos em uma decisão: *qual pico, em que horário e por quê*, usando as regras de quem surfa esses picos.

## Como funciona

```
Open-Meteo Marine API ─┐
                       ├─► coleta.py ─► mare.py ─► nota.py ─► ranking por dia
Open-Meteo Weather API ┘                              ▲
                                                      │
                                    praias.py (regras de cada pico)
```

| Critério | Peso | Regra |
|---|---|---|
| Vento | 30 % | Terral (NO/ONO) ideal até 12 kn; maral (E/SE/S) arruína acima de 15 kn |
| Direção do swell | 20 % | Direções ideais de cada pico |
| Tamanho | 20 % | Faixa preferida 1,0–1,5 m |
| Período | 15 % | A partir de 8 s é bom; 10 s ou mais, ótimo |
| Maré | 15 % | Média/vazante, média/enchente ou média/cheia, conforme o pico |

**Veto:** se tamanho, direção ou vento derem nota zero, a nota final fica limitada a 3 (um dia flat com vento perfeito não é um dia bom).

As marés (preamar/baixa-mar) são estimadas ao minuto por interpolação parabólica sobre a série horária do nível do mar.

## Como rodar

```bash
pip install -r requirements.txt
python teste_simulado.py   # testa a lógica com dados simulados (sem internet)
python main.py             # previsão real dos próximos 3 dias
```

## Estrutura

| Arquivo | Responsabilidade |
|---|---|
| `praias.py` | Regras, coordenadas, pesos e limites (único lugar para calibrar) |
| `coleta.py` | Chamadas HTTP às APIs → registros por hora |
| `mare.py` | Posição, tendência e horários de maré |
| `nota.py` | Subnotas, média ponderada e veto |
| `main.py` | Orquestra tudo e imprime o ranking |
| `teste_simulado.py` | Mock da API + testes de casos conhecidos |

## Roadmap

- [x] Coleta de dados (Open-Meteo)
- [x] Nota 0–10, maré e ranking por dia
- [ ] Mensagem amigável + envio por WhatsApp (CallMeBot)
- [ ] Execução diária com GitHub Actions + Secrets
- [ ] Alerta especial sem repetição (nota ≥ 8)
- [ ] Migração para WhatsApp Cloud API (Meta)
- [ ] Histórico em SQLite + dashboard de calibração
- [ ] pytest, CI e logging

## Limitações

- Os modelos são globais (~5–25 km): não enxergam bancos de areia nem recifes. As regras de cada pico compensam parte disso e são calibradas com sessões reais (`CALIBRACAO.md`).
- O nível do mar do Open-Meteo **não serve para navegação**; para confirmar as marés, compare com a tábua da Marinha (Porto de Salvador).

## Dados

Previsões: [Open-Meteo](https://open-meteo.com/) (gratuito para uso não comercial, licença CC BY 4.0).

---
Projeto de aprendizado de APIs e automação por **Nicolás Rivarola** — Análise e Desenvolvimento de Sistemas (UCSal).
