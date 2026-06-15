# Definindo o provedor de Nuvem (AWS)
provider "aws" {
  region = "us-east-1" # pelo preço kkkk
}

# Buscando a imagem mais recente do Ubuntu automaticamente
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # ID oficial da Canonical

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd/ubuntu-jammy-22.04-amd64-server-*"]
  }
}

# Criando o Firewall (Security Group)
resource "aws_security_group" "rag_sg" {
  name        = "rag-app-sg"
  description = "Permitir porta do Streamlit e SSH"

  # Libera a porta 8501 para o mundo acessar o seu site
  ingress {
    from_port   = 8501
    to_port     = 8501
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Libera o SSH (Acesso ao terminal da máquina, MAS TRAVAR DEPOIS PARA NÃO DAR MERDA)
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Permite que a máquina baixe coisas da internet
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. Criando o Servidor (EC2)
resource "aws_instance" "rag_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.medium"  # 2CPUs e 4GB RAM
  vpc_security_group_ids = [aws_security_group.rag_sg.id]

  # =================================================================
  # O SCRIPT para rodar na maquina
  # =================================================================
  user_data = <<-EOF
              #!/bin/bash
              # Atualiza a máquina e instala Docker e Git
              apt-get update -y
              apt-get install -y docker.io git curl

              # Instala o Docker Compose
              curl -L "https://github.com/docker/compose/releases/download/v2.24.5/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
              chmod +x /usr/local/bin/docker-compose

              # Inicia o Docker
              systemctl start docker
              systemctl enable docker

              git clone https://github.com/RodrigoSchneiderbr/teste-qwen3-chat /home/ubuntu/app
              
              cd /home/ubuntu/app

              # Sobe a aplicação silenciosamente no fundo
              docker-compose up --build -d
              EOF

  tags = {
    Name = "Servidor-RAG-Producao"
  }
}

# 5. Mostra o link pronto no final da instalação!
output "link_do_app" {
  value       = "http://${aws_instance.rag_server.public_ip}:8501"
  description = "Clique aqui para acessar a sua Inteligência Artificial"
}