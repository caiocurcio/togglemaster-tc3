# Bootstrap do backend remoto

Este é o único módulo Terraform do projeto que roda com **state local**
(fica um `terraform.tfstate` na sua máquina, ignorado pelo git). É um
problema clássico de "ovo e galinha": o backend remoto (bucket S3) não
pode guardar o próprio state que o cria.

Rode isso **uma única vez**, antes de tocar em qualquer outro módulo.

```bash
cd infra/bootstrap
terraform init
terraform apply
```

Anote o valor de `state_bucket_name` da saída — ele será usado no
backend do ambiente `dev` (`infra/envs/dev`).
