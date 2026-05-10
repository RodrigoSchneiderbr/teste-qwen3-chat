# 🚀 Guia de Configuração: Modelo Local com Ollama (Qwen)

Este repositório contém as instruções e o script necessário (`conversar.py`) para interagir com um modelo de inteligência artificial rodando localmente na sua máquina, utilizando o **Ollama**.

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
