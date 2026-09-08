# Modulo: ecr

Um repositorio ECR por microsservico (`toggle-master/auth`,
`toggle-master/flag`, etc.), usados pelo pipeline de CI (task 9) pra
publicar as imagens Docker.

## Decisoes

- **`IMMUTABLE`**: uma vez publicada, a tag `v1.0.0-a1b2c3d` (hash do
  commit) nao pode ser sobrescrita com outro conteudo — condiz com o
  requisito do desafio de taguear a imagem pelo hash do commit, e evita
  o classico bug de "reimplantei a mesma tag e o conteudo mudou sem eu
  perceber".
- **`scan_on_push = true`**: o proprio ECR escaneia a imagem ao
  receber o push, como uma camada extra alem do scan do Trivy que vai
  rodar dentro do pipeline de CI (defesa em profundidade).
- **Lifecycle policy** expirando imagens além das 10 mais recentes por
  repositorio, pra nao acumular custo de armazenamento indefinidamente.
