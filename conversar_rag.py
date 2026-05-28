import os
import ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings 
from langchain_community.vectorstores import Chroma

# Configurações dos modelos
MODELO_CHAT = 'qwen3:0.6b' 
MODELO_EMBEDDING = 'nomic-embed-text' 
CAMINHO_PDF = 'preview.pdf' 

def preparar_banco_de_dados_pdf():
    print(f"Encontrado o arquivo '{CAMINHO_PDF}'. Processando o PDF...")
    
    loader = PyPDFLoader(CAMINHO_PDF)
    documentos = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    textos_fatiados = text_splitter.split_documents(documentos)

    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
    vectorstore = Chroma.from_documents(documents=textos_fatiados, embedding=embeddings)
    
    print("PDF processado com sucesso! Modo RAG ativado.\n")
    return vectorstore

def iniciar_chat():
    nome_usuario = input("Qual é o seu nome? ")
    print(f"\nOlá, {nome_usuario}! --- Chat com {MODELO_CHAT} iniciado ---")
    
    banco_vetorial = None

    if os.path.exists(CAMINHO_PDF):
        try:
            banco_vetorial = preparar_banco_de_dados_pdf()
        except Exception as e:
            print(f"Erro ao processar o PDF. Detalhe: {e}")
            print("O sistema continuará no modo de Chat Normal.\n")
    else:
        print(f"Arquivo '{CAMINHO_PDF}' não encontrado. Iniciando modo de Chat Normal.\n")

    print("(Digite 'sair' para encerrar o programa)\n")

    while True:
        entrada = input(f"{nome_usuario}: ")

        if entrada.lower() in ['sair', 'exit', 'parar']:
            print(f"Encerrando chat... Até logo, {nome_usuario}!")
            break

        try:
            if banco_vetorial is not None:
                docs_relevantes = banco_vetorial.similarity_search(entrada, k=3)
                contexto = "\n\n".join([doc.page_content for doc in docs_relevantes])
                
                conteudo_mensagem = f"""
                Você é um assistente útil. Use o contexto abaixo, extraído de um documento, para responder à pergunta. 
                Se não souber a resposta com base no contexto, diga que não sabe.

                CONTEXTO:
                {contexto}

                PERGUNTA DO USUÁRIO: 
                {entrada}
                """
            else:
                conteudo_mensagem = entrada

            stream = ollama.chat(
                model=MODELO_CHAT,
                messages=[{'role': 'user', 'content': conteudo_mensagem}],
                stream=True,
            )

            print("IA: ", end='', flush=True)
            for chunk in stream:
                print(chunk['message']['content'], end='', flush=True)
            
            print("\n" + "-"*30)

        except Exception as e:
            print(f"\nErro durante a geração ou busca: {e}")
            break

if __name__ == "__main__":
    iniciar_chat()