import os
import tempfile
import streamlit as st
from conversar_rag import preparar_banco_de_dados, gerar_resposta_stream

# ==========================================
# CONFIGURAÇÕES DA PÁGINA
# ==========================================
st.set_page_config(page_title="Chat IA com PDF", page_icon="🤖", layout="wide")

# ==========================================
# GERENCIAMENTO DE ESTADO (SESSION STATE)
# ==========================================
if "messages" not in st.session_state:
    st.session_state.messages = []
    
# Atualizado: de 'vectorstore' para 'retrievers' para suportar a Busca Híbrida
if "retrievers" not in st.session_state:
    st.session_state.retrievers = None

# ==========================================
# INTERFACE DO USUÁRIO (BARRA LATERAL)
# ==========================================
with st.sidebar:
    st.header("⚙️ Configurações")
    nome_usuario = st.text_input("Qual é o seu nome?", value="Usuário")
    
    st.subheader("📄 Modo RAG (Contexto)")
    # 1. Permite pdf E docx
    arquivo_up = st.file_uploader("Envie um PDF ou DOCX", type=["pdf", "docx"])
    
    if arquivo_up is not None and st.session_state.retrievers is None:
        with st.spinner("Processando o documento e gerando a Busca Híbrida..."):
            try:
                # 2. Descobre a extensão do arquivo que o usuário subiu (ex: .docx)
                extensao_original = f".{arquivo_up.name.split('.')[-1]}"
                
                # 3. Cria o arquivo temporário usando a extensão correta
                with tempfile.NamedTemporaryFile(delete=False, suffix=extensao_original) as temp_file:
                    temp_file.write(arquivo_up.read())
                    temp_path = temp_file.name

                # Chama a função que agora detecta automaticamente
                st.session_state.retrievers = preparar_banco_de_dados(temp_path)
                
                os.remove(temp_path)
                st.success("Documento processado! Modo RAG ativado.")
                
            except Exception as e:
                st.error(f"Erro ao processar: {e}")
                if 'temp_path' in locals() and os.path.exists(temp_path):
                    os.remove(temp_path)
                
    elif arquivo_up is None and st.session_state.retrievers is not None:
        st.session_state.retrievers = None
        st.warning("Documento removido. Chat normal ativado.")

    st.divider()
    
    # ==========================================
    # NOVOS CONTROLES DE PESO (SLIDERS)
    # ==========================================
    st.subheader("⚖️ Pesos da Busca Híbrida")
    st.caption("Ajuste como a IA deve procurar as informações no PDF.")
    
    peso_denso = st.slider(
        "🧠 Significado e Contexto", 
        min_value=0.0, max_value=1.0, value=0.5, step=0.1,
        help="Aumente para focar em ideias parecidas (Semântica)."
    )
    
    peso_esparso = st.slider(
        "🔤 Palavras Exatas", 
        min_value=0.0, max_value=1.0, value=0.5, step=0.1,
        help="Aumente para procurar por nomes, siglas e números exatos (BM25)."
    )

    st.divider()
    
    if st.button("🗑️ Limpar Chat"):
        st.session_state.messages = []
        st.rerun()

# ==========================================
# INTERFACE DO USUÁRIO (CHAT PRINCIPAL)
# ==========================================
st.title(f"Olá, {nome_usuario}! 👋")

if st.session_state.retrievers is not None:
    st.caption("🟢 **Modo RAG Ativado:** A IA usará o PDF fornecido com a Busca Híbrida.")
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

    # 2. Chama o Ollama e exibe a resposta escrevendo na tela
    with st.chat_message("assistant"):
        try:
            # Obtém o gerador da nossa função, AGORA PASSANDO OS PESOS DO SLIDER
            fluxo_resposta = gerar_resposta_stream(
                prompt=prompt, 
                retrievers=st.session_state.retrievers,
                peso_denso=peso_denso,
                peso_esparso=peso_esparso,
                historico_chat=st.session_state.messages
            )
            
            # st.write_stream lida automaticamente com o gerador
            resposta_completa = st.write_stream(fluxo_resposta)
            
            # Salva a resposta no histórico
            st.session_state.messages.append({"role": "assistant", "content": resposta_completa})
            
        except Exception as e:
            st.error(f"Erro durante a comunicação com a IA: {e}")