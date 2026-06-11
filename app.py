import os
import tempfile
import streamlit as st
from conversar_rag import preparar_banco_de_dados_pdf, gerar_resposta_stream

# ==========================================
# CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="Chat IA com PDF", page_icon="🤖", layout="wide")

# ==========================================
# GERENCIAMENTO DE ESTADO (SESSION STATE)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
if "vectorstore" not in st.session_state:
    st.session_state.vectorstore = None

# ==========================================
# INTERFACE DO USUÁRIO (BARRA LATERAL)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações")
    nome_usuario = st.text_input("Qual é o seu nome?", value="Usuário")
    
    st.divider()
    
    st.subheader("📄 Modo RAG (Contexto)")
    arquivo_pdf = st.file_uploader("Envie um PDF para basear as respostas", type=["pdf"])
    
    # Processa o PDF apenas se foi enviado e ainda não está no session_state
    if arquivo_pdf is not None and st.session_state.vectorstore is None:
        with st.spinner("Processando o PDF e gerando embeddings..."):
            try:
                # Cria um arquivo temporário físico para o PyPDFLoader conseguir ler
                with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as temp_file:
                    temp_file.write(arquivo_pdf.read())
                    temp_path = temp_file.name

                # Chama a função do conversar_rag.py
                st.session_state.vectorstore = preparar_banco_de_dados_pdf(temp_path)
                
                # Exclui o arquivo temporário após o uso
                os.remove(temp_path)
                
                st.success("PDF processado! Modo RAG ativado.")
            except Exception as e:
                st.error(f"Erro ao processar o PDF: {e}")
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path) # Garante que o temporário seja apagado em caso de erro
                
    elif arquivo_pdf is None and st.session_state.vectorstore is not None:
        st.session_state.vectorstore = None
        st.warning("PDF removido. Chat normal ativado.")

    st.divider()
    if st.button("🗑️ Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# INTERFACE DO USUÁRIO (CHAT PRINCIPAL)
# ==========================================
st.title(f"Olá, {nome_usuario}! 👋")

if st.session_state.vectorstore is not None:
    st.caption("🟢 **Modo RAG Ativado:** A IA usará o PDF fornecido como base de conhecimento.")
else:
    st.caption("⚪ **Chat Normal:** A IA usará apenas seu conhecimento pré-treinado.")

# Exibe o histórico de mensagens
for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])

# ==========================================
# LÓGICA DE INTERAÇÃO DO CHAT
# ==========================================
if prompt := st.chat_input("Digite sua mensagem..."):
    
    # 1. Adiciona a pergunta na tela
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # 2. Chama o Ollama (via conversar_rag.py) e exibe a resposta escrevendo na tela
    with st.chat_message("assistant"):
        try:
            # Obtém o gerador da nossa função modularizada
            fluxo_resposta = gerar_resposta_stream(prompt, st.session_state.vectorstore)
            
            # st.write_stream lida automaticamente com o gerador e cria o efeito máquina de escrever
            resposta_completa = st.write_stream(fluxo_resposta)
            
            # Salva a resposta no histórico
            st.session_state.messages.append({"role": "assistant", "content": resposta_completa})
            
        except Exception as e:
            st.error(f"Erro durante a comunicação com a IA: {e}")