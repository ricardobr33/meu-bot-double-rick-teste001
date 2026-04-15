from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re
import traceback
import os
import requests
import builtins
from dotenv import load_dotenv

print_original = print
load_dotenv()

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
        valor = match.group()
        valor = valor.replace(".", "").replace(",", ".")
        return float(valor)
    return 0.0


def extrair_numero(texto):
    match = re.search(r"\d+", texto)
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
                    valor = extrair_valor(texto)
                    if valor >= 0:
                        return valor
        except:
            pass

        time.sleep(1)

    return 0.0


def aguardar_timer_zerar(driver):
    while True:
        try:
            timer = driver.find_element(
                By.XPATH,
                '//*[@id="roulette-timer"]/div[2]/div[2]/span'
            ).get_attribute("textContent").strip()

            if timer.startswith("0:00"):
                return
        except:
            pass

        time.sleep(0.2)


def aguardar_timer_sair_de_zero(driver):
    while True:
        try:
            timer = driver.find_element(
                By.XPATH,
                '//*[@id="roulette-timer"]/div[2]/div[2]/span'
            ).get_attribute("textContent").strip()

            if not timer.startswith("0:0"):
                return
        except:
            pass

        time.sleep(0.2)


def pegar_lista_resultados(driver, limite=5):
    lista = []
    try:
        for i in range(1, limite + 1):
            xpath = f'//*[@id="roulette-recent"]/div/div[1]/div[{i}]/div/div/div'
            texto = driver.find_element(By.XPATH, xpath).text.strip()
            numero = extrair_numero(texto)
            lista.append(numero)
    except:
        pass

    return lista


def aguardar_novo_resultado(driver, lista_anterior):
    while True:
        lista_atual = pegar_lista_resultados(driver)

        if lista_atual and lista_atual != lista_anterior:
            return lista_atual

        time.sleep(0.2)


def classificar_cor(numero):
    if numero is None:
        return "⚪"
    elif 1 <= numero <= 7:
        return "🔴"
    elif 8 <= numero <= 14:
        return "⚫"
    else:
        return "⚪"


def iniciar_driver():
    try:
        options = Options()

        options.add_argument("--headless=new")

        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        options.add_argument("--start-maximized")
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    except Exception:
        traceback.print_exc()
        input("Erro ao iniciar Chrome")
        exit()


def iniciar_automacao():
    driver = iniciar_driver()
    driver.get("https://blaze.bet.br/pt/games/double")

    clicar_se_existir(
        driver,
        '//*[@id="policy-regulation-popup"]/div/div[2]/div/button',
        "Aceitar cookies"
    )

    time.sleep(5)

    clicar_se_existir(
        driver,
        '//*[@id="blaze-provider"]/main/div[2]/div/div/div/div/div[4]/button[1]',
        "Entrar no jogo"
    )

    print("⏱ Aguardando carregamento...")
    time.sleep(10)

    primeira_rodada = True
    modo_verificacao = False
    tentativas_restantes = 0

    base_vermelho = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[1]'
    base_branco = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[2]'
    base_preto = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[3]'

    valor_vermelho = 0.0
    valor_branco = 0.0
    valor_preto = 0.0

    numrodada = 0
    win = 0
    loss = 0

    lista_resultados = pegar_lista_resultados(driver)

    cor_maior_salva = None
    cor_menor_salva = None

    while True:
        numrodada += 1

        try:
            aguardar_timer_zerar(driver)

            valor_vermelho = pegar_valor_com_espera(driver, base_vermelho)
            valor_branco = pegar_valor_com_espera(driver, base_branco)
            valor_preto = pegar_valor_com_espera(driver, base_preto)

            seta_vermelho = ""
            seta_branco = ""
            seta_preto = ""

            if valor_vermelho > valor_branco and valor_vermelho > valor_preto:
                cor_maior = "🔴"
                seta_vermelho = "🏆"
            elif valor_branco > valor_vermelho and valor_branco > valor_preto:
                cor_maior = "⚪"
                seta_branco = "🏆"
            else:
                cor_maior = "⚫"
                seta_preto = "🏆"

            if valor_vermelho < valor_branco and valor_vermelho < valor_preto:
                cor_menor = "🔴"
                seta_vermelho += "⬇️"
            elif valor_branco < valor_vermelho and valor_branco < valor_preto:
                cor_menor = "⚪"
                seta_branco += "⬇️"
            else:
                cor_menor = "⚫"
                seta_preto += "⬇️"

            if not primeira_rodada:
                limpar_tela()
                print(f"________ 📊 RESUMO DA RODADA {numrodada} ________\n"
                f"\n🔴 Vermelho: {valor_vermelho} {seta_vermelho}"
                f"\n⚪ Branco: {valor_branco} {seta_branco}"
                f"\n⚫ Preto: {valor_preto} {seta_preto}"
                "\n\nAguardando resultado...")

            aguardar_timer_sair_de_zero(driver)

            time.sleep(3)
            lista_resultados = aguardar_novo_resultado(driver, lista_resultados)

            ultimo_numero = lista_resultados[0]
            cor = classificar_cor(ultimo_numero)

            print(f"\n🎯 Último sorteio: {cor} ({ultimo_numero})")

            # =========================
            # 🔥 LÓGICA NOVA (3 TENTATIVAS)
            # =========================

            if primeira_rodada:
                primeira_rodada = False
                print("⏳ Primeira rodada ignorada (sincronizando)")
                numrodada = 0
                continue

            if not modo_verificacao:
                if cor == cor_maior:
                    print("✅ Maior bateu → iniciando 3 tentativas")
                    cor_maior_salva = cor_maior
                    cor_menor_salva = cor_menor
                    tentativas_restantes = 3
                    modo_verificacao = True
                else:
                    print("❌ Maior não bateu")

            else:
                if cor == cor_menor_salva:
                    print("🎯 MENOR bateu dentro das tentativas → WIN +1")
                    win += 1
                    modo_verificacao = False
                    tentativas_restantes = 0

                else:
                    tentativas_restantes -= 1
                    print(f"⏳ Tentativa restante: {tentativas_restantes}")

                    if tentativas_restantes <= 0:
                        print("💀 Nenhuma tentativa acertou → LOSS +1")
                        loss += 1
                        modo_verificacao = False

            print(f"\n✅ Wins: {win}"
            f"❌ Loss: {loss}")

            valor_vermelho = 0.0
            valor_branco = 0.0
            valor_preto = 0.0

        except Exception as e:
            print("❌ Erro:", e)
            time.sleep(2)


if __name__ == "__main__":
    iniciar_automacao()
