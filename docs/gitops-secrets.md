# Secrets do Kubernetes (não ficam no Git)

As senhas dos 3 bancos Postgres (`auth`, `flag`, `targeting`) e o `JWT_SECRET` do
serviço `auth` **nunca são comitados no repositório** — o repo vai ficar público antes
da entrega, e mesmo privado isso seria má prática. Os `Deployment` em
`gitops/apps/<serviço>/deployment.yaml` referenciam esses valores por nome
(`secretKeyRef`), mas o `Secret` em si é criado uma vez, manualmente, direto na conta
AWS do Caio.

Por isso mesmo esses `Secret`s não moram dentro de `gitops/apps/`: qualquer arquivo
ali dentro é sincronizado automaticamente pelo ArgoCD (Task 11) a partir do que está
no Git — se um `Secret` com senha placeholder estivesse commitado ali, o ArgoCD
sobrescreveria a senha real do cluster com o placeholder a cada sync.

> **Como colar estes comandos:** cada bloco abaixo é UMA linha só de comando (sem
> `` ` `` de continuação) - copie só o conteúdo de dentro do bloco cinza, nunca as
> três crases (\`\`\`) que marcam o início/fim do bloco. Depois de cada linha que
> busca um valor (`$authDb = ...`), tem uma linha de conferência (`$authDb.password.Length`)
> - rode ela e confirme o número antes de seguir pra próxima linha. Se der `0` ou
> vier em branco, o valor não foi buscado direito - não crie o secret ainda, me
> manda a saída de volta.

## Pré-requisito

`kubectl` configurado apontando pro cluster (`aws eks update-kubeconfig --region
us-east-1 --name togglemaster-eks`, já feito antes) e o namespace criado:

```powershell
kubectl apply -f gitops/namespace.yaml
```

## auth (senha do banco + JWT_SECRET)

A senha do banco já existe no AWS Secrets Manager (criada pelo Terraform, módulo
`rds`, sempre com 24 caracteres). O `JWT_SECRET` não é gerenciado pelo Terraform -
é gerado agora, uma vez (32 bytes em hexadecimal = 64 caracteres), e guardado só no
Secret do Kubernetes.

```powershell
$authDb = aws secretsmanager get-secret-value --secret-id togglemaster/auth/db --region us-east-1 --query SecretString --output text | ConvertFrom-Json
```
```powershell
$authDb.password.Length
```
*(tem que aparecer `24`)*
```powershell
$jwtSecret = python -c "import secrets; print(secrets.token_hex(32))"
```
```powershell
$jwtSecret.Length
```
*(tem que aparecer `64`)*
```powershell
kubectl create secret generic auth-secrets --namespace togglemaster --from-literal=db-password=$($authDb.password) --from-literal=jwt-secret=$jwtSecret --dry-run=client -o yaml | kubectl apply -f -
```

## flag (senha do banco)

```powershell
$flagDb = aws secretsmanager get-secret-value --secret-id togglemaster/flag/db --region us-east-1 --query SecretString --output text | ConvertFrom-Json
```
```powershell
$flagDb.password.Length
```
*(tem que aparecer `24`)*
```powershell
kubectl create secret generic flag-secrets --namespace togglemaster --from-literal=db-password=$($flagDb.password) --dry-run=client -o yaml | kubectl apply -f -
```

## targeting (senha do banco)

```powershell
$targetingDb = aws secretsmanager get-secret-value --secret-id togglemaster/targeting/db --region us-east-1 --query SecretString --output text | ConvertFrom-Json
```
```powershell
$targetingDb.password.Length
```
*(tem que aparecer `24`)*
```powershell
kubectl create secret generic targeting-secrets --namespace togglemaster --from-literal=db-password=$($targetingDb.password) --dry-run=client -o yaml | kubectl apply -f -
```

## Forçar os pods a pegar o secret certo agora

Usar `--dry-run=client -o yaml | kubectl apply -f -` (em vez de `kubectl create secret`
puro) já deixa o comando seguro pra rodar de novo se algo tiver dado errado da
primeira vez - ele **substitui** o secret existente em vez de dar erro "already
exists". Mas um Pod que já está em `CreateContainerConfigError` não relê o Secret
sozinho na hora - force a recriação:

```powershell
kubectl delete pod -n togglemaster -l app=auth
kubectl delete pod -n togglemaster -l app=flag
kubectl delete pod -n togglemaster -l app=targeting
```

(o `Deployment` sobe um Pod novo automaticamente assim que o antigo é apagado - não
tem risco de ficar sem nada rodando.)

## Atualizar um secret depois (se a senha rotacionar)

Mesmo comando de criação acima (com `--dry-run=client -o yaml | kubectl apply -f -`)
funciona pra atualizar - só rodar de novo com o valor novo. O Pod só pega o valor
novo depois de recriado: `kubectl rollout restart deployment/<serviço> -n
togglemaster`.

## evaluation e analytics — sem Secret nenhum

Esses dois não usam senha pra falar com a AWS: autenticam via **IRSA** (a
`ServiceAccount` de cada um já vem com a anotação `eks.amazonaws.com/role-arn`
apontando pra role que o Terraform criou). Nada a fazer aqui.
