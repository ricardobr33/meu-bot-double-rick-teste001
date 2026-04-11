from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
import time
import re
import traceback
import os
import requests
import builtins
from dotenv import load_dotenv
import shutil
import glob

load_dotenv()
print_original = print

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def enviar_telegram(mensagem):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        payload = {
            "chat_id": CHAT_ID,
            "text": mensagem
        }
        requests.post(url, data=payload)
    except:
        pass


def print(*args, **kwargs):
    mensagem = " ".join(str(a) for a in args)
    print_original(*args, **kwargs)
    enviar_telegram(mensagem)


def limpar_tela():
    os.system('cls' if os.name == 'nt' else 'clear')


def clicar_se_existir(driver, xpath, descricao, tentativas=5, espera=2):
    for _ in range(tentativas):
        try:
            elemento = driver.find_element(By.XPATH, xpath)
            elemento.click()
            print(f"✅ {descricao} clicado")
            return True
        except:
            time.sleep(espera)

    print(f"⚠️ {descricao} não encontrado (seguindo fluxo)")
    return False


def extrair_valor(texto):
    match = re.search(r"[\d.,]+", texto)
    if match:
        valor = match.group().replace(".", "").replace(",", ".")
        return float(valor)
    return 0.0


def extrair_numero(texto):
    match = re.search(r"\d+")
    if match:
        return int(match.group())
    return None


def pegar_valor_com_espera(driver, xpath_base, tentativas=10):
    for _ in range(tentativas):
        try:
            elementos = driver.find_elements(By.XPATH, xpath_base + '//span')
            for el in elementos:
                texto = el.text.strip()
                if "R$" in texto:
                    return extrair_valor(texto)
        except:
            pass
        time.sleep(1)

    return 0.0


def esperar_estado(driver, texto_esperado):
    while True:
        try:
            botao = driver.find_element(By.XPATH, '//*[@id="roulette-controller"]/div[1]/div[3]/button')
            if botao.text.strip() == texto_esperado:
                return
        except:
            pass
        time.sleep(1)


def aguardar_botao(driver):
    print("🔎 Procurando botão do jogo...")
    while True:
        try:
            botao = driver.find_element(By.XPATH, '//*[@id="roulette-controller"]/div[1]/div[3]/button')
            if botao.text.strip() in ["Começar o jogo", "Esperando"]:
                return botao.text.strip()
        except:
            pass
        time.sleep(2)


def pegar_ultimo_numero(driver):
    try:
        el = driver.find_element(By.XPATH, '//*[@id="roulette-recent"]/div/div[1]/div[1]/div/div/div')
        return extrair_numero(el.text.strip())
    except:
        return None


def classificar_cor(numero):
    if numero is None:
        return "⚪"
    if 1 <= numero <= 7:
        return "🔴"
    if 8 <= numero <= 14:
        return "⚫"
    return "⚪"


# =========================
# 🔥 DRIVER RAILWAY BLINDADO
# =========================
def iniciar_driver():
    try:
        options = Options()

        # obrigatório Railway
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")
        options.add_argument("--disable-extensions")
        options.add_argument("--remote-debugging-port=9222")

        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        # 🔥 tenta achar Chromium automaticamente no Railway
        chromium_path = (
            shutil.which("chromium") or
            shutil.which("chromium-browser") or
            next(iter(glob.glob("/nix/store/*/bin/chromium")), None)
        )

        chromedriver_path = (
            shutil.which("chromedriver") or
            next(iter(glob.glob("/nix/store/*/bin/chromedriver")), None)
        )

        print("🔎 Chromium:", chromium_path)
        print("🔎 Driver:", chromedriver_path)

        if not chromium_path or not chromedriver_path:
            print("❌ Chrome não encontrado no ambiente")
            return None

        options.binary_location = chromium_path
        service = Service(chromedriver_path)

        driver = webdriver.Chrome(service=service, options=options)

        driver.execute_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        print("✅ Chrome iniciado com sucesso")
        return driver

    except Exception:
        traceback.print_exc()
        return None


# =========================
# 🔥 SUA LÓGICA ORIGINAL
# =========================
def iniciar_automacao():
    while True:
        driver = iniciar_driver()
        if driver:
            break
        print("⏳ Tentando novamente driver...")
        time.sleep(10)

    driver.get("https://blaze.bet.br/pt/games/double")

    print("__________▶️ INICIALIZAÇÃO__________")

    clicar_se_existir(driver,
        '//*[@id="policy-regulation-popup"]/div/div[2]/div/button',
        "Aceitar cookies"
    )

    time.sleep(5)

    clicar_se_existir(driver,
        '//*[@id="blaze-provider"]/main/div[2]/div/div/div/div/div[4]/button[1]',
        "Entrar no jogo"
    )

    time.sleep(10)

    aguardar_botao(driver)

    print("🚀 BOT INICIADO")

    while True:
        try:
            esperar_estado(driver, "Esperando")
            time.sleep(3)

            vermelho = pegar_valor_com_espera(driver, '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[1]')
            branco = pegar_valor_com_espera(driver, '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[2]')
            preto = pegar_valor_com_espera(driver, '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[3]')

            print(f"🔴 {vermelho} ⚪ {branco} ⚫ {preto}")

            esperar_estado(driver, "Começar o jogo")

            ultimo = pegar_ultimo_numero(driver)
            cor = classificar_cor(ultimo)

            print(f"🎯 Resultado: {cor} ({ultimo})")

        except Exception as e:
            print("❌ erro loop:", e)
            time.sleep(2)


if __name__ == "__main__":
    iniciar_automacao()
