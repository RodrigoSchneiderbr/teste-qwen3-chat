import ollama

MODELO = 'qwen3:0.6b' 


def iniciar_chat():
    nome_usuario = input("Qual é o seu nome? ")
    print(f"\nOlá, {nome_usuario}! --- Chat com {MODELO} iniciado ---")
    print("(Digite 'sair' para encerrar o programa)\n")

    while True:
        entrada = input(f"{nome_usuario}: ")

        if entrada.lower() in ['sair', 'exit', 'parar']:
            print(f"Encerrando chat... Até logo, {nome_usuario}!")
            break

        try:
            stream = ollama.chat(
                model=MODELO,
                messages=[{'role': 'user', 'content': entrada}],
                stream=True,
            )

            print("IA: ", end='', flush=True)
            for chunk in stream:
                print(chunk['message']['content'], end='', flush=True)
            
            print("\n" + "-"*30)

        except Exception as e:
            print(f"\nErro de conexão: {e}")
            break

if __name__ == "__main__":
    iniciar_chat()