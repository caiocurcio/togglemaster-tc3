# Uma senha aleatoria por banco - nunca hardcoded, nunca em arquivo de texto
# (que era exatamente um dos problemas descritos no desafio).
resource "random_password" "db" {
  for_each = var.databases
  length   = 24
  special  = false
}

resource "aws_db_subnet_group" "this" {
  name       = "${var.project_name}-rds"
  subnet_ids = var.subnet_ids

  tags = {
    Name = "${var.project_name}-rds-subnet-group"
  }
}

resource "aws_security_group" "rds" {
  name        = "${var.project_name}-rds-sg"
  description = "Postgres (5432) apenas dos security groups autorizados"
  vpc_id      = var.vpc_id

  tags = {
    Name = "${var.project_name}-rds-sg"
  }
}

resource "aws_security_group_rule" "allow_postgres" {
  # count, nao for_each: o valor de allowed_security_group_ids (o SG do
  # EKS) so fica conhecido depois do apply do modulo eks, e for_each
  # exige que as CHAVES sejam conhecidas no plan. O tamanho da lista
  # (quantos SGs) e conhecido mesmo sem saber o valor de cada um.
  count                    = length(var.allowed_security_group_ids)
  type                     = "ingress"
  from_port                = 5432
  to_port                  = 5432
  protocol                 = "tcp"
  security_group_id        = aws_security_group.rds.id
  source_security_group_id = var.allowed_security_group_ids[count.index]
}

resource "aws_security_group_rule" "allow_egress_all" {
  type              = "egress"
  from_port         = 0
  to_port           = 0
  protocol          = "-1"
  security_group_id = aws_security_group.rds.id
  cidr_blocks       = ["0.0.0.0/0"]
}

resource "aws_db_instance" "this" {
  for_each = var.databases

  identifier     = "${var.project_name}-${each.key}"
  engine         = "postgres"
  engine_version = var.engine_version
  instance_class = var.instance_class

  allocated_storage = var.allocated_storage
  storage_encrypted = true

  db_name  = each.value.db_name
  username = each.value.username
  password = random_password.db[each.key].result

  db_subnet_group_name   = aws_db_subnet_group.this.name
  vpc_security_group_ids = [aws_security_group.rds.id]

  multi_az            = var.multi_az
  publicly_accessible = false

  backup_retention_period = 1
  skip_final_snapshot     = var.skip_final_snapshot
  deletion_protection     = false

  tags = {
    Name    = "${var.project_name}-${each.key}"
    Service = each.key
  }
}

# Credenciais NUNCA em texto plano: cada banco tem um secret proprio no
# Secrets Manager com usuario, senha e endpoint ja prontos pro pod consumir.
resource "aws_secretsmanager_secret" "db" {
  for_each    = var.databases
  name        = "${var.project_name}/${each.key}/db"
  description = "Credenciais do banco Postgres do servico ${each.key}"
}

resource "aws_secretsmanager_secret_version" "db" {
  for_each  = var.databases
  secret_id = aws_secretsmanager_secret.db[each.key].id
  secret_string = jsonencode({
    username = each.value.username
    password = random_password.db[each.key].result
    host     = aws_db_instance.this[each.key].address
    port     = aws_db_instance.this[each.key].port
    dbname   = each.value.db_name
  })
}
