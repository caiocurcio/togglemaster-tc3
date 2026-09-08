# Chave composta: flag_name (partition key) + event_id (sort key).
# Isso bate exatamente com o que o servico "analytics" grava
# (services/analytics/app.py) e permite consultar "todos os eventos
# de uma flag, do mais recente pro mais antigo" (Query, nao Scan).
resource "aws_dynamodb_table" "analytics" {
  name         = var.table_name
  billing_mode = "PAY_PER_REQUEST" # sem capacidade fixa pra gerenciar; cobra so pelo uso real

  hash_key  = "flag_name"
  range_key = "event_id"

  attribute {
    name = "flag_name"
    type = "S"
  }

  attribute {
    name = "event_id"
    type = "S"
  }

  tags = {
    Name = var.table_name
  }
}
