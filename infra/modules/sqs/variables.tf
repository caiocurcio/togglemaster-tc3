variable "queue_name" {
  type    = string
  default = "toggle-master-evaluation-events"
}

variable "visibility_timeout_seconds" {
  description = "Tempo que uma mensagem fica invisivel apos ser lida, antes de poder ser reentregue"
  type        = number
  default     = 30
}

variable "message_retention_seconds" {
  description = "Por quanto tempo uma mensagem nao processada fica na fila (padrao: 4 dias)"
  type        = number
  default     = 345600
}

variable "max_receive_count" {
  description = "Quantas vezes uma mensagem pode falhar antes de ir pra Dead Letter Queue"
  type        = number
  default     = 5
}
