# Modulo: dynamodb

Tabela `ToggleMasterAnalytics` que o microsservico `analytics` usa para
gravar cada evento de avaliacao consumido da fila SQS.

## Decisoes

- **`PAY_PER_REQUEST`** em vez de capacidade provisionada: o volume de
  eventos e imprevisivel (depende de quanto trafego o `evaluation`
  gerar) e pequeno para este projeto — pagar por requisicao evita
  configurar/chutar unidades de capacidade.
- **Chave composta `flag_name` + `event_id`**: permite consultar
  "os ultimos eventos de uma flag especifica" com uma Query eficiente,
  em vez de um Scan na tabela inteira.
