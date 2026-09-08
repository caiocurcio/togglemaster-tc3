# Modulo: rds

Cria N instancias RDS PostgreSQL (uma por item do mapa `databases`) na
mesma VPC, cada uma com seu proprio Secrets Manager secret contendo
usuario/senha/host/porta/nome do banco.

## Decisoes

- **`for_each` sobre um mapa, nao 3 blocos de recurso copiados e colados**:
  o desafio pede "3 instancias RDS"; usamos `for_each` justamente para
  não repetir o mesmo bloco de `aws_db_instance` tres vezes — o ambiente
  `dev` (task 8) so passa um mapa com as chaves `auth`, `flag`, `targeting`.
- **Senha gerada com `random_password` e guardada no Secrets Manager**,
  nunca em `.tfvars` ou hardcoded no codigo: isso resolve diretamente um
  dos problemas descritos no enunciado do desafio ("credenciais do banco
  de dados sendo passadas em arquivos de texto sem seguranca").
- **`multi_az = false`** por padrao: Multi-AZ dobra o custo da instancia.
  Fica como variavel para ligar facilmente se quiser demonstrar HA.
- **Security Group so libera 5432 pros SGs explicitamente autorizados**
  (o SG dos nodes do EKS, por exemplo) — nunca `0.0.0.0/0`.
