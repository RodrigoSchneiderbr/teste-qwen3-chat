import ollama
from langchain_community.document_loaders import PyPDFLoader, Docx2txtLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_ollama import OllamaEmbeddings 
from langchain_community.vectorstores import Chroma
from langchain_community.retrievers import BM25Retriever
import os
from ollama import Client

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

from ollama import Client # Certifique-se de que isso está no topo do arquivo!

def gerar_resposta_stream(prompt, retrievers=None, peso_denso=0.5, peso_esparso=0.5, historico_chat=[]):
    """
    Gera a resposta com Busca Híbrida, Memória de Conversação e suporte ao Docker.
    """
    contexto = ""

    # 1. Faz a busca no PDF (se o RAG estiver ativado)
    if retrievers is not None:
        retriever_denso, retriever_esparso = retrievers
        
        docs_semantica = retriever_denso.invoke(prompt)
        docs_palavras = retriever_esparso.invoke(prompt)
        
        pontuacoes = {}

        def pontuar_docs(docs, peso_da_busca):
            for ranking, doc in enumerate(docs):
                texto = doc.page_content
                nota = peso_da_busca / (ranking + 1)
                
                if texto in pontuacoes:
                    pontuacoes[texto] += nota
                else:
                    pontuacoes[texto] = nota

        pontuar_docs(docs_semantica, peso_denso)
        pontuar_docs(docs_palavras, peso_esparso)
        
        textos_vencedores = sorted(pontuacoes.items(), key=lambda item: item[1], reverse=True)
        melhores_textos = [texto for texto, nota in textos_vencedores[:4]]
        
        contexto = "\n\n---\n\n".join(melhores_textos)

    # ==========================================
    # 2. CONSTRUÇÃO DA MEMÓRIA E CONTEXTO
    # ==========================================
    mensagens_para_ia = []
    
    # A) Cria a "Voz da Consciência" da IA (System Prompt)
    instrucao_sistema = "Você é um assistente útil e amigável. Responda de forma clara no idioma do usuário."
    
    # Se achou algo no PDF, injeta nas regras do sistema
    if contexto:
         instrucao_sistema += f"\n\nUse EXCLUSIVAMENTE o CONTEXTO abaixo para basear sua resposta. Se a resposta não estiver no contexto, diga que não sabe.\n\nCONTEXTO:\n{contexto}"
         
    mensagens_para_ia.append({'role': 'system', 'content': instrucao_sistema})

    # B) Injeta todo o histórico da conversa (O Streamlit já manda a nova pergunta junto aqui)
    for mensagem in historico_chat:
        mensagens_para_ia.append({'role': mensagem['role'], 'content': mensagem['content']})

    # ==========================================
    # 3. CHAMA O OLLAMA (Compatível com Docker)
    # ==========================================
    # Lembre-se que URL_OLLAMA foi definido lá em cima no seu arquivo
    cliente_docker = Client(host=URL_OLLAMA)
    
    stream = cliente_docker.chat(
        model=MODELO_CHAT,
        messages=mensagens_para_ia, # Enviamos a lista de mensagens inteira!
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