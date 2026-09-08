# Modulo: eks

Cria o cluster EKS, seu Node Group gerenciado e a infraestrutura de IAM
necessaria — tudo via Terraform, porque o projeto usa uma conta pessoal
(Opcao B do desafio: liberdade total pra criar Roles/Policies).

## Decisoes

- **Duas IAM roles**, cada uma com o minimo de policies gerenciadas pela
  AWS para o proposito dela: uma para o control plane (`cluster`) e outra
  para as instancias EC2 do Node Group (`node`). Nada de reusar uma unica
  role "faz tudo".
- **`endpoint_public_access = true` e `endpoint_private_access = true`**:
  o endpoint publico permite que voce (da sua maquina) e o ArgoCD/kubectl
  administrem o cluster; o privado garante que o trafego node -> control
  plane nao saia da VPC. Endurecimento possivel no futuro: restringir
  `endpoint_public_access_cidrs` ao seu IP.
- **OIDC provider do cluster**: pre-requisito tecnico para IRSA (IAM Roles
  for Service Accounts). Ainda nao criamos nenhuma role IRSA aqui — isso
  vem depois, quando os microsservicos `evaluation` e `analytics`
  precisarem de permissao (SQS/DynamoDB) sem dar essa permissao pra
  role do node inteiro (que serviria pra qualquer Pod do cluster).
- **Add-ons gerenciados explicitos** (`vpc-cni`, `kube-proxy`, `coredns`):
  declarados via Terraform em vez de depender do que o EKS instala por
  padrao, para manter tudo versionado como codigo.
- **`capacity_type = ON_DEMAND`** por padrao: SPOT é mais barato, mas os
  nodes podem ser reclamados pela AWS a qualquer momento — arriscado bem
  na hora de gravar o video de demonstracao. Fica como variavel caso
  queira trocar depois de validar tudo.
