# Recursos AWS provisionados

Registro dos recursos criados na conta pessoal AWS via Terraform
(`infra/envs/dev`), utile para o relatorio de entrega final.

| Recurso                     | Nome / Identificador                                                        | Regiao    |
|-------------------------------|------------------------------------------------------------------------------|-----------|
| Bucket S3 (state remoto)      | `togglemaster-tfstate-383996694340`                                          | us-east-1 |
| Cluster EKS                   | `togglemaster-eks`                                                            | us-east-1 |
| RDS `auth`                    | `togglemaster-auth.cgj4a2auutt3.us-east-1.rds.amazonaws.com`                  | us-east-1 |
| RDS `flag`                    | `togglemaster-flag.cgj4a2auutt3.us-east-1.rds.amazonaws.com`                  | us-east-1 |
| RDS `targeting`               | `togglemaster-targeting.cgj4a2auutt3.us-east-1.rds.amazonaws.com`             | us-east-1 |
| ElastiCache Redis             | `togglemaster-redis.yer9pn.0001.use1.cache.amazonaws.com`                     | us-east-1 |
| Tabela DynamoDB               | `ToggleMasterAnalytics`                                                       | us-east-1 |
| Fila SQS                      | `toggle-master-evaluation-events` (+ DLQ `-dlq`)                              | us-east-1 |
| Repositorios ECR              | `togglemaster/{auth,flag,targeting,evaluation,analytics}`                     | us-east-1 |
| Secrets Manager (credenciais) | `togglemaster/{auth,flag,targeting}/db`                                       | us-east-1 |
| Role IRSA evaluation          | `togglemaster-evaluation-irsa`                                                | -         |
| Role IRSA analytics           | `togglemaster-analytics-irsa`                                                 | -         |

## Nota sobre o plano da conta AWS

A conta pessoal comecou no "Free Plan" da AWS (restringe tipos de
instancia a apenas elegiveis para o nivel gratuito e limita a
quantidade de instancias RDS). Foi necessario fazer upgrade para o
"Paid Plan" (console AWS -> Billing -> Upgrade account) para conseguir
provisionar o node group (`t3.medium`) e a 3a instancia RDS.
