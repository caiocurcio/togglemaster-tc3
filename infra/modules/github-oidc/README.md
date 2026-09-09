# Modulo: github-oidc

Cria a ponte de confianca entre o GitHub Actions e a AWS via OIDC, sem
nenhuma access key fixa:

- `aws_iam_openid_connect_provider` — registra o emissor de tokens do
  GitHub (`token.actions.githubusercontent.com`) como um provedor de
  identidade confiavel pela conta AWS.
- `aws_iam_role` — role que so pode ser assumida por um token OIDC emitido
  para o repositorio especifico (`var.github_repo`), com permissao restrita
  a fazer push/pull nos repositorios ECR deste projeto.

## Por que OIDC em vez de access key?

Uma access key de IAM guardada como secret do GitHub e' uma credencial de
longa duracao: se vazar (log, fork malicioso, etc.) continua valida ate' ser
revogada manualmente. Com OIDC, a cada execucao do workflow a AWS emite uma
credencial temporaria (dura minutos) so pra aquela execucao - nao ha nada
de longa duracao pra vazar.
