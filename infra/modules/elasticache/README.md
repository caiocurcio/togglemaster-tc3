# Modulo: elasticache

Um cluster Redis de 1 no, usado pelo microsservico `evaluation` como
cache-aside (guarda por alguns segundos o resultado de flag+targeting
combinados, pra nao bater no `flag`/`targeting` a cada avaliacao).

## Decisoes

- **1 no, sem replicacao**: e um cache, nao uma fonte de verdade — se o
  Redis reiniciar, o `evaluation` simplesmente recalcula a partir do
  `flag` e do `targeting` no proximo pedido. Nao justifica o custo de
  replicas para este projeto.
- Security Group segue o mesmo padrao do modulo `rds`: so libera 6379
  para SGs explicitamente autorizados.
