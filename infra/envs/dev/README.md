# Ambiente: dev

Junta todos os modulos (`networking`, `eks`, `rds`, `elasticache`,
`dynamodb`, `sqs`, `ecr`) num unico ambiente e cria as roles IRSA dos
microsservicos `evaluation` e `analytics`.

## Como aplicar

O `backend.hcl` deste diretorio ja está preenchido com o bucket que
você criou no bootstrap (`togglemaster-tfstate-383996694340`) — não é
versionado no git (só o `.example`), porque é específico da sua conta.

```bash
cd infra/envs/dev
terraform init -backend-config=backend.hcl
terraform plan    # revise o que vai ser criado antes de aplicar
terraform apply
```

**Isso demora.** O cluster EKS sozinho leva uns 10-15 minutos pra ficar
pronto, o Node Group mais uns 3-5, e os 3 RDS sobem em paralelo mas
também não são instantâneos. Não é a sessão travada — espere o
`apply` terminar (ou apareça um erro).

Ao final, olhe os outputs — em especial:

```bash
terraform output configure_kubectl
```

Copia e cola o comando que aparecer (algo como
`aws eks update-kubeconfig --region us-east-1 --name togglemaster-eks`)
pra apontar seu `kubectl` local pro cluster novo, e confirme com:

```bash
kubectl get nodes
```

## Custo (estimativa, não confiável — confira no Cost Explorer)

Pra ordem de grandeza: 1 cluster EKS (~US$0,10/hora) + 2 nodes
`t3.medium` + 1 NAT Gateway (~US$0,045/hora + tráfego) + 3 RDS
`db.t3.micro` + 1 ElastiCache `cache.t3.micro`. Rodando o dia todo,
isso fica na casa de alguns dólares por dia — **desligue os recursos
(`terraform destroy`) quando não estiver usando**, especialmente antes
de qualquer intervalo maior sem mexer no projeto. O relatório final
pede um print da estimativa de custo real da AWS (Cost Explorer /
Billing), não uma conta de padaria feita aqui.
