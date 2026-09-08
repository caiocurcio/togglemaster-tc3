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

## Como testar localmente (sem AWS)

Com Docker Desktop instalado na sua máquina (fora deste ambiente), na raiz do projeto:

```bash
docker compose up --build
```

Isso sobe os 5 microsserviços, 3 bancos Postgres (um por serviço com estado) e um Redis.
Sem credenciais AWS, o `evaluation` some sem publicar no SQS e o `analytics` não inicia o
consumidor da fila — mas dá pra validar toda a lógica de negócio, incluindo a chamada
HTTP entre `evaluation`, `flag` e `targeting`.

```bash
# 1. cria a flag "novo-checkout" desligada
curl -X POST -H "Content-Type: application/json" \
  -d '{"name": "novo-checkout", "is_enabled": true}' \
  http://localhost:5002/flags

# 2. define que 50% dos usuários (por hash do user_id) recebem a flag
curl -X PUT -H "Content-Type: application/json" \
  -d '{"rollout_percentage": 50, "user_whitelist": ["vip-1"], "user_blacklist": []}' \
  http://localhost:5003/targeting/novo-checkout

# 3. avalia a flag pra um usuário específico (evaluation chama flag + targeting e cacheia no Redis)
curl "http://localhost:5004/evaluate/novo-checkout?user_id=vip-1"

# 4. cria um client de auth e emite um token JWT
curl -X POST -H "Content-Type: application/json" -d '{"name": "postman"}' http://localhost:5001/clients
curl -X POST -H "Content-Type: application/json" -d '{"api_key": "<api_key retornada acima>"}' http://localhost:5001/token
```

Para encerrar: `docker compose down -v` (o `-v` também apaga os volumes dos bancos).
