# Usa uma imagem oficial e leve do Python
FROM python:3.10-slim

# Define o diretório de trabalho dentro do contentor
WORKDIR /app

# Instala dependências do sistema necessárias para o ChromaDB compilar
RUN apt-get update && apt-get install -y build-essential

# Copia o ficheiro de dependências
COPY requirements.txt .

# Instala as bibliotecas
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o resto do código da sua máquina para o contentor
COPY . .

# Expõe a porta que o Streamlit utiliza
EXPOSE 8501

# Comando para executar a aplicação quando o contentor iniciar
CMD ["streamlit", "run", "app.py", "--server.address=0.0.0.0"]