locals {
  cluster_name = "${var.project_name}-eks"
}

module "networking" {
  source = "../../modules/networking"

  project_name         = var.project_name
  vpc_cidr             = var.vpc_cidr
  azs                  = var.azs
  public_subnet_cidrs  = var.public_subnet_cidrs
  private_subnet_cidrs = var.private_subnet_cidrs

  # Tag que o AWS Load Balancer Controller do EKS usa pra saber quais
  # subnets pertencem a este cluster. E aqui, no ambiente que conhece os
  # dois modulos, que fechamos essa dependencia - nao dentro de "networking".
  public_subnet_extra_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
  private_subnet_extra_tags = {
    "kubernetes.io/cluster/${local.cluster_name}" = "shared"
  }
}

module "eks" {
  source = "../../modules/eks"

  project_name = var.project_name

  # Control plane: publicas + privadas (permite endpoint publico).
  # Nodes: so privadas.
  cluster_subnet_ids = concat(module.networking.public_subnet_ids, module.networking.private_subnet_ids)
  node_subnet_ids    = module.networking.private_subnet_ids
}

module "ecr" {
  source = "../../modules/ecr"

  project_name = var.project_name
}

module "rds" {
  source = "../../modules/rds"

  project_name = var.project_name
  vpc_id       = module.networking.vpc_id
  subnet_ids   = module.networking.private_subnet_ids

  # O EKS anexa esse Security Group tanto ao control plane quanto aos
  # nodes do Node Group gerenciado - por isso ele basta aqui.
  allowed_security_group_ids = [module.eks.cluster_security_group_id]

  databases = {
    auth = {
      db_name  = "auth"
      username = "auth_app"
    }
    flag = {
      # "flag" e palavra reservada pela API do RDS para o parametro DBName
      # (nao e do Postgres em si, e uma regra da propria AWS) - usamos "flagdb".
      db_name  = "flagdb"
      username = "flag_app"
    }
    targeting = {
      db_name  = "targeting"
      username = "targeting_app"
    }
  }
}

module "elasticache" {
  source = "../../modules/elasticache"

  project_name               = var.project_name
  vpc_id                     = module.networking.vpc_id
  subnet_ids                 = module.networking.private_subnet_ids
  allowed_security_group_ids = [module.eks.cluster_security_group_id]
}

module "dynamodb" {
  source = "../../modules/dynamodb"
}

module "sqs" {
  source = "../../modules/sqs"
}

# ---------------------------------------------------------------------------
# IRSA: o Pod do "evaluation" só pode enviar mensagem pra ESSA fila.
# O Pod do "analytics" só pode ler/apagar dessa fila e escrever/consultar
# NESSA tabela. Nenhum dos dois herda a permissao ampla da role do node.
# ---------------------------------------------------------------------------
data "aws_iam_policy_document" "evaluation_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:${var.k8s_namespace}:evaluation"]
    }

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "evaluation" {
  name               = "${var.project_name}-evaluation-irsa"
  assume_role_policy = data.aws_iam_policy_document.evaluation_assume_role.json
}

data "aws_iam_policy_document" "evaluation_permissions" {
  statement {
    actions   = ["sqs:SendMessage"]
    resources = [module.sqs.queue_arn]
  }
}

resource "aws_iam_role_policy" "evaluation" {
  name   = "${var.project_name}-evaluation-sqs-send"
  role   = aws_iam_role.evaluation.id
  policy = data.aws_iam_policy_document.evaluation_permissions.json
}

data "aws_iam_policy_document" "analytics_assume_role" {
  statement {
    actions = ["sts:AssumeRoleWithWebIdentity"]

    principals {
      type        = "Federated"
      identifiers = [module.eks.oidc_provider_arn]
    }

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider_url}:sub"
      values   = ["system:serviceaccount:${var.k8s_namespace}:analytics"]
    }

    condition {
      test     = "StringEquals"
      variable = "${module.eks.oidc_provider_url}:aud"
      values   = ["sts.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "analytics" {
  name               = "${var.project_name}-analytics-irsa"
  assume_role_policy = data.aws_iam_policy_document.analytics_assume_role.json
}

data "aws_iam_policy_document" "analytics_permissions" {
  statement {
    actions   = ["sqs:ReceiveMessage", "sqs:DeleteMessage", "sqs:GetQueueAttributes"]
    resources = [module.sqs.queue_arn]
  }

  statement {
    actions   = ["dynamodb:PutItem", "dynamodb:Query", "dynamodb:GetItem"]
    resources = [module.dynamodb.table_arn]
  }
}

resource "aws_iam_role_policy" "analytics" {
  name   = "${var.project_name}-analytics-permissions"
  role   = aws_iam_role.analytics.id
  policy = data.aws_iam_policy_document.analytics_permissions.json
}
