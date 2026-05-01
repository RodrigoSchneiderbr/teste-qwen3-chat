import pywhatkit as kit
import ollama
import requests
from datetime import datetime

# --- CONFIGURAÇÕES ---
NUMERO_DESTINO = "+5551997851980" 
# Coordenadas exatas de Santa Maria - RS
LAT = "-29.68"
LON = "-53.80"

# 1. Busca o clima real (Temperatura + Chuva)
def pegar_clima():
    url = f"https://api.open-meteo.com/v1/forecast?latitude={LAT}&longitude={LON}&current_weather=true&hourly=precipitation_probability"
    
    try:
        response = requests.get(url)
        dados = response.json()
        
        temp = dados['current_weather']['temperature']
        # Pega a probabilidade de chuva da hora atual
        chance_chuva = dados['hourly']['precipitation_probability'][0] 
        
        status_chuva = "com chance de chuva" if chance_chuva > 30 else "sem previsão de chuva"
        
        return f"Agora em Santa Maria faz {temp}°C e está {status_chuva} ({chance_chuva}% de probabilidade)."
    except Exception as e:
        return "Erro ao buscar clima, mas tenha um bom dia!"

# 2. IA gera a mensagem personalizada
def gerar_mensagem_ia(clima_info):
    # Ajustei o prompt para a IA focar na chuva também
    prompt = (f"Contexto: {clima_info}. Escreva uma mensagem de bom dia curta e amigável. ")
    
    response = ollama.generate(model='qwen3:0.6b', prompt=prompt)
    return response['response']

# 3. Enviar via WhatsApp
def enviar_whatsapp(texto):
    print(f"Enviando: {texto}")
    # sendwhatmsg_instantly abre o navegador e envia via WhatsApp Web
    kit.sendwhatmsg_instantly(NUMERO_DESTINO, texto, wait_time=15, tab_close=True)

if __name__ == "__main__":
    info_clima = pegar_clima()
    mensagem_final = gerar_mensagem_ia(info_clima)
    enviar_whatsapp(mensagem_final)