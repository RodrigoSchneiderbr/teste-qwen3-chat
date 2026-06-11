import ollama
from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings 
from langchain_community.vectorstores import Chroma

# ==========================================
# CONFIGURAÇÕES DOS MODELOS
# ==========================================
MODELO_CHAT = 'qwen3:0.6b' 
MODELO_EMBEDDING = 'nomic-embed-text' 

def preparar_banco_de_dados_pdf(caminho_pdf):
    """
    Lê o PDF, divide em pedaços e cria o banco vetorial.
    Recebe o caminho físico do arquivo como parâmetro.
    """
    loader = PyPDFLoader(caminho_pdf)
    documentos = loader.load()

    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    textos_fatiados = text_splitter.split_documents(documentos)

    embeddings = OllamaEmbeddings(model=MODELO_EMBEDDING)
    vectorstore = Chroma.from_documents(documents=textos_fatiados, embedding=embeddings)
    
    return vectorstore

def gerar_resposta_stream(prompt, vectorstore=None):
    """
    Gera a resposta do Ollama com base na pergunta e no banco vetorial.
    Retorna um gerador (yield) para o efeito de digitação.
    """
    conteudo_mensagem = prompt

    # Se houver um PDF processado, busca o contexto
    if vectorstore is not None:
        docs_relevantes = vectorstore.similarity_search(prompt, k=3)
        contexto = "\n\n".join([doc.page_content for doc in docs_relevantes])
        
        conteudo_mensagem = f"""
        Você é um assistente útil. Use o contexto abaixo, extraído de um documento, para responder à pergunta. 
        Se não souber a resposta com base no contexto, diga que não sabe.

        CONTEXTO:
        {contexto}

        PERGUNTA DO USUÁRIO: 
        {prompt}
        """

    # Chama o modelo Ollama
    stream = ollama.chat(
        model=MODELO_CHAT,
        messages=[{'role': 'user', 'content': conteudo_mensagem}],
        stream=True,
    )
    
    # Envia os pedaços da resposta um por um
    for chunk in stream:
        yield chunk['message']['content']