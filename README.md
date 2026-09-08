# ToggleMaster — Tech Challenge Fase 3 (IaC, CI/CD e DevSecOps)

Automacao da infraestrutura e do ciclo de vida dos 5 microsservicos do
ToggleMaster (`auth`, `flag`, `targeting`, `evaluation`, `analytics`),
evoluindo o monolito da Fase 1 para uma arquitetura de microsservicos
operada com Terraform, GitHub Actions (DevSecOps) e GitOps (ArgoCD).

## Estrutura do repositorio

```
.
services/           # codigo-fonte dos 5 microsservicos (um app Flask por servico)
  auth/
  flag/
  targeting/
  evaluation/
  analytics/
infra/               # Terraform (Infraestrutura como Codigo)
  bootstrap/         # cria o bucket S3 do backend remoto (roda uma unica vez)
  modules/           # modulos reutilizaveis (networking, eks, rds, elasticache, dynamodb, sqs, ecr)
  envs/dev/          # ambiente "dev": compoe os modulos acima
.github/workflows/   # pipelines de CI/DevSecOps (um workflow por microsservico)
gitops/              # manifests Kubernetes que o ArgoCD sincroniza no EKS
  apps/<servico>/    # Deployment/Service de cada microsservico
  argocd/            # Application(s) do ArgoCD
docs/                # relatorio de entrega, diagramas, evidencias
```

## Mapeamento microsservico -> recurso AWS

| Microsservico | Responsabilidade                                          | Recurso AWS principal                  |
|---------------|-------------------------------------------------------------|------------------------------------------|
| auth          | Autenticacao / emissao de API key                           | RDS PostgreSQL                          |
| flag          | CRUD das feature flags                                       | RDS PostgreSQL                          |
| targeting     | Regras de segmentacao (quem recebe qual flag)                | RDS PostgreSQL                          |
| evaluation    | Avaliacao em tempo real da flag para um contexto/usuario      | ElastiCache (Redis) + publica no SQS    |
| analytics     | Consome eventos de avaliacao e persiste o historico           | SQS (consumidor) + DynamoDB (ToggleMasterAnalytics) |

## Status

Projeto em construcao, passo a passo, como parte do Tech Challenge da
Fase 3 da pos-graduacao em Arquitetura Cloud e DevOps (FIAP/POSTECH).
