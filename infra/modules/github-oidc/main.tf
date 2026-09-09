# O GitHub publica um endpoint OIDC (OpenID Connect) que emite um token de
# identidade assinado a cada execucao de um workflow do Actions. A AWS
# confia nesse token (via este "Identity Provider") sem precisar de nenhuma
# access key fixa guardada como secret do repositorio.
#
# So pode existir 1 provider por URL em cada conta AWS - se este modulo for
# usado mais de uma vez na mesma conta, o segundo aws_iam_openid_connect_provider
# vai falhar com "EntityAlreadyExists". Nesse projeto so instanciamos 1 vez
# (no ambiente dev), entao nao e um problema aqui.
data "tls_certificate" "github" {
  url = "https://token.actions.githubusercontent.com"
}

resource "aws_iam_openid_connect_provider" "github" {
  url             = "https://token.actions.githubusercontent.com"
  client_id_list  = ["sts.amazonaws.com"]
  thumbprint_list = [data.tls_certificate.github.certificates[0].sha1_fingerprint]
}

# Trust policy: so aceita o token se ele vier do REPOSITORIO especifico
# (nao de qualquer conta do GitHub) e se o "audience" do token for
# "sts.amazonaws.com" (o publico que o Actions usa quando pede um token
# pra se autenticar em um provedor de nuvem).
#
# "StringLike" com "repo:${var.github_repo}:*" libera qualquer branch, tag,
# pull request ou environment DENTRO desse repositorio - suficiente pra um
# projeto academico com um unico repo. Para restringir so a branch "main"
# (impedindo que um push em uma branch de feature tambem consiga a role),
# bastaria trocar o "*" por "ref:refs/heads/main".
data "aws_iam_policy_document" "assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [aws_iam_openid_connect_provider.github.arn]
    }

    condition {
      test     = "StringEquals"
      variable = "token.actions.githubusercontent.com:aud"
      values   = ["sts.amazonaws.com"]
    }

    condition {
      test     = "StringLike"
      variable = "token.actions.githubusercontent.com:sub"
      values   = ["repo:${var.github_repo}:*"]
    }
  }
}

resource "aws_iam_role" "github_actions" {
  name               = "${var.project_name}-github-actions-ecr"
  assume_role_policy = data.aws_iam_policy_document.assume_role.json
}

# Permissao minima pra: autenticar no ECR (GetAuthorizationToken - essa acao
# da API do ECR nao aceita restricao por recurso, so "*", e' uma limitacao
# da propria AWS) e fazer push/pull SO nos repositorios ECR deste projeto
# (nunca em outros repositorios ECR da conta).
data "aws_iam_policy_document" "ecr_push" {
  statement {
    sid       = "ECRAuth"
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  statement {
    sid = "ECRPushPull"
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:GetDownloadUrlForLayer",
      "ecr:BatchGetImage",
      "ecr:PutImage",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
    ]
    resources = var.ecr_repository_arns
  }
}

resource "aws_iam_role_policy" "ecr_push" {
  name   = "${var.project_name}-github-actions-ecr-push"
  role   = aws_iam_role.github_actions.id
  policy = data.aws_iam_policy_document.ecr_push.json
}
