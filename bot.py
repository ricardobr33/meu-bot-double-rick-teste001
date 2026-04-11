from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
import re
import traceback
import os
import requests
import builtins
import os
from dotenv import load_dotenv

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

    # print normal no terminal
    print_original(*args, **kwargs)

    # envia pro telegram
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
            texto = botao.text.strip()

            if texto in ["Começar o jogo", "Esperando"]:
                print(f"✅ Botão encontrado: {texto}")
                return texto

        except:
            pass

        print("⏳ Botão não encontrado, tentando novamente...")
        time.sleep(3)


def pegar_ultimo_numero(driver):
    try:
        elemento = driver.find_element(
            By.XPATH,
            '//*[@id="roulette-recent"]/div/div[1]/div[1]/div/div/div'
        )
        return extrair_numero(elemento.text.strip())
    except:
        return None


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

        # 🔥 Modo invisível
        options.add_argument("--headless=new")

        # 🔧 Configurações importantes
        options.add_argument("--disable-gpu")
        options.add_argument("--window-size=1920,1080")

        # 👀 Anti-detecção
        options.add_argument("--disable-blink-features=AutomationControlled")
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option("useAutomationExtension", False)

        driver = webdriver.Chrome(options=options)

        # Remove flag de automação
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    except Exception:
        traceback.print_exc()
        input("Erro ao iniciar Chrome")
        exit()


def iniciar_automacao():
    driver = iniciar_driver()
    driver.get("https://blaze.bet.br/pt/games/double")
    print(f"__________▶️ INICIALIZAÇÃO__________\n")
    # 🍪 aceitar cookies
    clicar_se_existir(
        driver,
        '//*[@id="policy-regulation-popup"]/div/div[2]/div/button',
        "Aceitar cookies"
    )

    time.sleep(5)

    # ▶️ botão inicial
    clicar_se_existir(
        driver,
        '//*[@id="blaze-provider"]/main/div[2]/div/div/div/div/div[4]/button[1]',
        "Entrar no jogo"
    )

    print("⏱ Aguardando carregamento...")
    time.sleep(10)

    estado_inicial = aguardar_botao(driver)

    saldo_casa = 0.0
    primeira_rodada = True

    # 🔁 RESPEITA O CICLO INICIAL
    if estado_inicial == "Esperando":
        esperar_estado(driver, "Começar o jogo")
        esperar_estado(driver, "Esperando")

    elif estado_inicial == "Começar o jogo":
        esperar_estado(driver, "Esperando")

    time.sleep(5)

    base_vermelho = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[1]'
    base_branco = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[2]'
    base_preto = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[3]'

    valor_vermelho = 0.0
    valor_branco = 0.0
    valor_preto = 0.0
    numrodada = 0
    ultimo_foi_branco = False
    win = 0
    loss = 0

    while True:
        numrodada += 1
        try:
            # 🔄 ESPERA ABRIR A RODADA
            esperar_estado(driver, "Esperando")
            time.sleep(5)

            # 💰 COLETA APOSTAS
            valor_vermelho = pegar_valor_com_espera(driver, base_vermelho)
            valor_branco = pegar_valor_com_espera(driver, base_branco)
            valor_preto = pegar_valor_com_espera(driver, base_preto)

            # definido a maior aposta
            vermelhormaior = ""
            brancomaior = ""
            pretomaior = ""
            menorvalorcor = ""

            # pegando maior valor
            if valor_vermelho > valor_branco and valor_vermelho > valor_preto:
                vermelhormaior = '🚨'
            elif valor_branco > valor_vermelho and valor_branco > valor_preto:
                brancomaior = '🚨'
            else:
                pretomaior = '🚨'

            # pegando menor valor
            if valor_vermelho < valor_branco and valor_vermelho < valor_preto:
                menorvalorcor = "🔴"
            elif valor_branco < valor_vermelho and valor_branco < valor_preto:
                menorvalorcor = "⚪"
            elif valor_preto < valor_vermelho and valor_preto < valor_branco:
                menorvalorcor = "⚫"

            menorvalorvalor = min(valor_vermelho, valor_branco, valor_preto)

            if primeira_rodada:
                primeira_rodada = True
            else:
                limpar_tela()
                print(f"______📊 RESUMO DA RODADA {numrodada}_______ \n")
                print(f"🔴 Vermelho: {valor_vermelho} {vermelhormaior}")
                print(f"⚪ Branco: {valor_branco} {brancomaior}")
                print(f"⚫ Preto: {valor_preto} {pretomaior}")
                print("\nAguardando último sorteio...\n")

            esperar_estado(driver, "Começar o jogo")
            time.sleep(5)

            if primeira_rodada:
                print("⏳ Primeira rodada ignorada (sincronização)")
                numrodada = 0
                primeira_rodada = False
            else:
                ultimo_numero = pegar_ultimo_numero(driver)
                cor = classificar_cor(ultimo_numero)

                if cor == "🔴":
                    saldo_casa += (valor_preto + valor_branco)
                    saldo_casa -= (valor_vermelho * 2)

                elif cor == "⚫":
                    saldo_casa += (valor_vermelho + valor_branco)
                    saldo_casa -= (valor_preto * 2)

                elif cor == "⚪":
                    saldo_casa += (valor_vermelho + valor_preto)
                    saldo_casa -= (valor_branco * 14)


                # verificando se o penúltimo foi branco
                if ultimo_foi_branco:
                    if menorvalorvalor == valor_vermelho:
                        if menorvalorvalor <= 0.7 * valor_preto and menorvalorvalor <= 0.7 * valor_branco:
                            print("\n🎯 Penúltimo sorteio: ⚪")
                            if cor == menorvalorcor:
                                print("\n🎯 Deu Win ✅")
                                win += 1
                            else:
                                loss += 1
                            ultimo_foi_branco = False

                    elif menorvalorvalor == valor_preto:
                        if menorvalorvalor <= 0.7 * valor_vermelho and menorvalorvalor <= 0.7 * valor_branco:
                            print("\n🎯 Penúltimo sorteio: ⚪")
                            if cor == menorvalorcor:
                                print("\n🎯 Deu Win ✅")
                                win += 1
                            else:
                                loss += 1
                            ultimo_foi_branco = False

                    elif menorvalorvalor == valor_branco:
                        print("\n### Branco foi o menor valor. Cancelar entrada ###")
                        print(f"\n⚪ {valor_branco}")
                    else:
                        print("\n### Entrada cancelada, mínimos muito próximos ###")
                        print(f"\n🔴 {valor_vermelho} | ⚫ {valor_preto}")

                print(f"\n🎯 Último sorteio: {cor} ({ultimo_numero})")
                print(f"💰 Saldo da Casa: {round(saldo_casa, 2)}")
                print(f"\n✅ Total de Wins: {win}")
                print(f"❌ Total de Loss: {loss}")

                if cor == "⚪":
                    ultimo_foi_branco = True

            valor_vermelho = 0.0
            valor_preto = 0.0
            valor_branco = 0.0

        except Exception as e:
            print("❌ Erro:", e)
            time.sleep(2)


if __name__ == "__main__":
    iniciar_automacao()