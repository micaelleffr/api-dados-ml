variable "project" {
    type = string
    default = "graphite-byte-472516-n8"
  
}

variable "region" {
    type = string
    default = "us-central1"
  
}

variable "dataset_id" {
    type = string
    default = "ml_dataset"
  
}

variable "table_id" {
    type = string
    default = "ml_table"
  
}

variable "image" {
     type = string
     default = "micaelleffr/nome-da-imagem:latest"   
}
