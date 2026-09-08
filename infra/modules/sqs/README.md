# Modulo: sqs

A fila que o `evaluation` publica (evento: flag avaliada para um
usuario) e o `analytics` consome, com uma Dead Letter Queue (DLQ) para
mensagens que falham repetidamente.

## Decisoes

- **DLQ com `maxReceiveCount = 5`**: se o `analytics` tentar processar
  a mesma mensagem 5 vezes e falhar, ela sai da fila principal e vai
  pra DLQ, em vez de ficar bloqueando/repetindo pra sempre. Isso evita
  que um bug no consumidor derrube a fila inteira silenciosamente.
- **Retencao de 4 dias** na fila principal: tempo suficiente pro
  `analytics` se recuperar de uma indisponibilidade temporaria (ex:
  deploy, throttling do DynamoDB) sem perder eventos.
