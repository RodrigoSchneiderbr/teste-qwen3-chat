import ollama
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
import os

# ==========================================
# CONFIGURAÇÕES DOS MODELOS
# ==========================================
MODELO_CHAT = 'qwen3:0.6b' 
MODELO_EMBEDDING = 'nomic-embed-text' 
URL_OLLAMA = os.getenv("OLLAMA_HOST", "http://localhost:11434")

def preparar_banco_de_dados(caminho_arquivo):
    """
    Lê o PDF ou DOCX, divide em pedaços e cria a Busca Híbrida.
    Compatível com execução local e via Docker.
    """
    print(f"Lendo o documento: {caminho_arquivo}...")
    
    # Extrai a extensão do arquivo (ex: 'pdf' ou 'docx')
    extensao = caminho_arquivo.split('.')[-1].lower()
    
    # Detecta automaticamente e escolhe o Leitor correto
    if extensao == 'pdf':
        loader = PyPDFLoader(caminho_arquivo)
    elif extensao == 'docx':
        loader = Docx2txtLoader(caminho_arquivo)
    else:
        raise ValueError("Formato de arquivo não suportado!")

    # O resto continua exatamente igual
    documentos = loader.load()

    print("Fatiando o texto...")
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)
    textos_fatiados = text_splitter.split_documents(documentos)

    print("Criando índice vetorial (Chroma)...")
    embeddings = OllamaEmbeddings(
        model=MODELO_EMBEDDING,
        base_url=URL_OLLAMA 
    )
    vectorstore = Chroma.from_documents(documents=textos_fatiados, embedding=embeddings)
    retriever_denso = vectorstore.as_retriever(search_kwargs={"k": 3})

    print("Criando índice de palavras-chave (BM25)...")
    retriever_esparso = BM25Retriever.from_documents(textos_fatiados)
    retriever_esparso.k = 3
    
    print("Banco de dados pronto!\n")
    return retriever_denso, retriever_esparso

def gerar_resposta_stream(prompt, retrievers=None, peso_denso=0.5, peso_esparso=0.5):
    """
    Gera a resposta do Ollama fazendo a Busca Híbrida.
    Pesos são opcionais e, por padrão, valem 50% (0.5) cada.
    """
    conteudo_mensagem = prompt

    if retrievers is not None:
        retriever_denso, retriever_esparso = retrievers
        
        # 1. Faz as buscas nos dois bibliotecários
        docs_semantica = retriever_denso.invoke(prompt)
        docs_palavras = retriever_esparso.invoke(prompt)
        
        # 2. Dicionário para guardar as notas de cada texto
        pontuacoes = {}

        # Função auxiliar para dar notas aos textos (Rank Fusion)
        def pontuar_docs(docs, peso_da_busca):
            for ranking, doc in enumerate(docs):
                texto = doc.page_content
                nota = peso_da_busca / (ranking + 1)
                
                if texto in pontuacoes:
                    pontuacoes[texto] += nota
                else:
                    pontuacoes[texto] = nota

        # 3. Aplica o sistema de notas usando os pesos recebidos na função
        pontuar_docs(docs_semantica, peso_denso)
        pontuar_docs(docs_palavras, peso_esparso)
        
        # 4. Ordena e extrai os 4 melhores textos
        textos_vencedores = sorted(pontuacoes.items(), key=lambda item: item[1], reverse=True)
        melhores_textos = [texto for texto, nota in textos_vencedores[:4]]
        
        contexto = "\n\n---\n\n".join(melhores_textos)
        
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
# ==========================================
# ÁREA DE TESTE  mais para debuga mesmo
# ==========================================
if __name__ == "__main__":
    # Substitua pelo nome do seu arquivo PDF real
    caminho_do_meu_pdf = "meu_documento_teste.pdf" 
    
    if not os.path.exists(caminho_do_meu_pdf):
        print(f"ERRO: Coloque um arquivo PDF chamado '{caminho_do_meu_pdf}' na mesma pasta do script.")
    else:
        # 1. Prepara o RAG (agora recebe dois retrievers)
        meus_retrievers = preparar_banco_de_dados(caminho_do_meu_pdf)
        
        # 2. Faz uma pergunta
        pergunta = "Qual é o assunto principal deste documento?"
        print(f"\nUsuário: {pergunta}")
        print("Assistente: ", end="")
        
        # 3. Imprime a resposta
        for pedaco in gerar_resposta_stream(pergunta, retrievers=meus_retrievers):
            print(pedaco, end="", flush=True)
        print("\n")