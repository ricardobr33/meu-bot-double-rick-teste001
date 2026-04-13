from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager

import time
import requests
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={
            "chat_id": CHAT_ID,
            "text": msg,
            "parse_mode": "HTML"
        })
    except Exception as e:
        print("Erro ao enviar mensagem:", e)

# 🔥 CONFIG DO NAVEGADOR (OTIMIZADO PRA SERVIDOR)
options = Options()
options.add_argument("--headless=new")
options.add_argument("--no-sandbox")
options.add_argument("--disable-dev-shm-usage")
options.add_argument("--disable-gpu")
options.add_argument("--window-size=1920,1080")
options.add_argument("--disable-blink-features=AutomationControlled")

# 👇 DRIVER CORRIGIDO (ESSENCIAL PRA RAILWAY)
driver = webdriver.Chrome(
    service=Service(ChromeDriverManager().install()),
    options=options
)

driver.get("https://blaze.com/pt/games/double")

time.sleep(10)  # tempo pra carregar

ultimo_resultado = None

def definir_cor(numero):
    if numero == 0:
        return "⚪ BRANCO", "⚪"
    elif 1 <= numero <= 7:
        return "🔴 VERMELHO", "🔴"
    else:
        return "⚫ PRETO", "⚫"

def montar_mensagem(numero, cor, emoji):
    horario = datetime.now().strftime("%H:%M:%S")

    return f"""
<b>🎰 RESULTADO BLAZE DOUBLE</b>

{emoji} <b>Cor:</b> {cor}
🔢 <b>Número:</b> {numero}

⏰ <b>Horário:</b> {horario}

━━━━━━━━━━━━━━━
🔥 <b>Novo giro detectado!</b>
"""

while True:
    try:
        elementos = driver.find_elements(By.CLASS_NAME, "entry")

        if elementos:
            texto = elementos[0].text.strip()

            # 🔥 evita erro se vier vazio
            if texto.isdigit():
                numero = int(texto)

                if numero != ultimo_resultado:
                    ultimo_resultado = numero

                    cor, emoji = definir_cor(numero)

                    msg = montar_mensagem(numero, cor, emoji)
                    print(msg)

                    enviar_telegram(msg)

    except Exception as e:
        print("Erro:", e)

    time.sleep(3)
