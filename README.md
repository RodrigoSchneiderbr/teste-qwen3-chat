# 🚀 Guia de Configuração: Modelo Local com Ollama (Qwen)

Este repositório contém as instruções e o script necessário (`conversar_rag.py`) para interagir com um modelo de inteligência artificial rodando localmente na sua máquina, utilizando o **Ollama**.

Podendo colocar um arquivo em pdf para ele buscar dados dentro deste arquivo
Acesse o site oficial de download: ollama.com/download

**Ollama** instalado para rodar os modelos locais de IA:
   * Acesse o site oficial de download: [ollama.com/download](https://ollama.com/download)
---

## 📋 Pré-requisitos
Antes de começar, certifique-se de ter as seguintes ferramentas instaladas no seu sistema:

* **[Python 3.8+](https://www.python.org/downloads/)**: Para gerenciar o ambiente virtual e executar o script.
* **[Ollama](https://ollama.com/)**: O motor responsável por baixar e rodar o modelo de IA localmente.

---

## 🛠️ Passo a Passo da Instalação e Execução

### 1. Baixar o Modelo no Ollama

Com o Ollama instalado e rodando em segundo plano, abra o seu terminal e faça o download do modelo Qwen:

```bash
ollama pull qwen3:0.6b

ollama pull nomic-embed-text
```

### 2. Criar o Venv Ambiente virtual

``` text
python -m venv venv
```
### 3. Instalar os requirements

```text
pip install -r requirements.txt
```

### 4. Rodar o streamlit

```
streamlit run conversas_rag.py
```


Para usar digite seu nome no nome de usuario.
Obs: caso coloque um documento em pdf o chat irá buscar respostas usando o RAG, caso não coloque irá usar a base treinada do qwen 3.6b

# 🚀 Guia de Configuração: Modelo Local com Ollama (Qwen) com DOCKER

### 1. Construir o container

``` text
docker-compose up -d --build
```
Depois somente acessar http://localhost:8501