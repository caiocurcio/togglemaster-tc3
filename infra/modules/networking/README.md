# Modulo: networking

Cria a VPC, subnets publicas e privadas (uma de cada por AZ), Internet
Gateway, 1 NAT Gateway (compartilhado) e as Route Tables associadas.

## Decisoes

- **1 NAT Gateway só** (não um por AZ): num ambiente de estudo/portfólio,
  cada NAT Gateway custa por hora rodando + tráfego processado. Um único
  NAT já satisfaz o requisito (subnets privadas com saída à internet) sem
  multiplicar esse custo. Em produção real, valeria 1 por AZ para alta
  disponibilidade.
- As tags `kubernetes.io/role/elb` e `kubernetes.io/role/internal-elb` já
  saem prontas nas subnets: são exigidas pelo AWS Load Balancer Controller
  do EKS para descobrir sozinho onde criar Load Balancers.
- O módulo **não** conhece o nome do cluster EKS (evita dependência
  circular entre os módulos `networking` e `eks`); quem usa o módulo pode
  injetar tags extras via `public_subnet_extra_tags` /
  `private_subnet_extra_tags`, incluindo a tag `kubernetes.io/cluster/<nome>`.
