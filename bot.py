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
import threading
import keyboard


controle = 0
controle2 = 0
controle3 = 0
print_original = print
load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")

# =========================
# 🛑 CONTROLE DE ENCERRAMENTO
# =========================
rodando = True

def monitorar_tecla():
    global rodando
    print("🛑 Pressione ESC para encerrar o bot")
    keyboard.wait("esc")
    print("🛑 ENCERRANDO BOT...")
    rodando = False

threading.Thread(target=monitorar_tecla, daemon=True).start()

# =========================
# 🔥 CONTROLE TELEGRAM
# =========================
mensagem_id = None
mensagem_texto = ""
modo = "init"  # init ou rodada
total_martingale = 1
metexib = 0
menu = ""

def enviar_telegram(mensagem, nova=False):
    global mensagem_id, mensagem_texto

    mensagem_texto += mensagem + "\n"

    try:
        if nova or mensagem_id is None:
            url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
            r = requests.post(url, data={
                "chat_id": CHAT_ID,
                "text": mensagem_texto
            })
            mensagem_id = r.json()["result"]["message_id"]
        else:
            url = f"https://api.telegram.org/bot{TOKEN}/editMessageText"
            requests.post(url, data={
                "chat_id": CHAT_ID,
                "message_id": mensagem_id,
                "text": mensagem_texto
            })
    except Exception as e:
        print("❌ ERRO TELEGRAM:", e)
        traceback.print_exc()


def print(*args, **kwargs):
    mensagem = " ".join(str(a) for a in args)
    print_original(*args, **kwargs)
    enviar_telegram(mensagem)


def nova_mensagem():
    global mensagem_id, mensagem_texto
    mensagem_id = None
    mensagem_texto = ""


# =========================
# 🔧 RESTANTE DO SEU CÓDIGO
# =========================
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

        time.sleep(0.1)

    return 0.0

# AGUARDAR O TIMER CHEGAR EM 5
chegou_cinco = False

def monitorar_timer_cinco(driver, base_vermelho, base_branco, base_preto):
    global porc_min2
    global porc_montante
    chegou_cinco = False
    global entrada_segura
    global cor_segura
    global rodada_premiada
    global tentativas_restantes
    global controle_aguardando_rodada

    while chegou_cinco == False:
        try:
            timer = driver.find_element(
                By.XPATH,
                '//*[@id="roulette-timer"]//span'
            ).text.strip()

            if not timer or ":" not in timer:
                continue

            minuto_str = timer.split(":")[0]

            if not minuto_str.isdigit():
                continue

            minuto = int(minuto_str)
            
            if chegou_cinco == False and 2 <= minuto <= 5:
                valor_vermelho = pegar_valor_com_espera(driver, base_vermelho)
                valor_branco = pegar_valor_com_espera(driver, base_branco)
                valor_preto = pegar_valor_com_espera(driver, base_preto)

                # verificnado valor menor
                if valor_vermelho < valor_branco and valor_vermelho < valor_preto:
                    cor_menor = "🔴"
                    valormenor1 = valor_vermelho
                    if valor_branco < valor_preto:
                        valormenor2 = valor_branco
                    else:
                        valormenor2 = valor_preto
                elif valor_branco < valor_vermelho and valor_branco < valor_preto:
                    cor_menor = "⚪"
                    valormenor1 = valor_branco
                    if valor_vermelho < valor_preto:
                        valormenor2 = valor_vermelho
                    else:
                        valormenor2 = valor_preto
                else:
                    cor_menor = "⚫"
                    valormenor1 = valor_preto
                    if valor_branco < valor_vermelho:
                        valormenor2 = valor_branco
                    else:
                        valormenor2 = valor_vermelho
                montante_total = valor_vermelho + valor_branco + valor_preto

                # avaliando se deve entrar ou não 
                diferenca_percentual = ((valormenor2 - valormenor1) / valormenor2) * 100
                porcentagem_total = (valormenor1 / montante_total) * 100
                limpar_tela()
                if diferenca_percentual >= porc_min2 and porcentagem_total <= porc_montante:
                    entrada_segura = True
                    cor_segura = cor_menor
                    print(f"✅ Entrada FORTE no {cor_menor}"
                    "\n-  -  -  -  -  -  -  -  -  -  -  -  -  -")
                
                else:
                    entrada_segura = False
                    rodada_premiada = 0
                    tentativas_restantes = 0
                    if controle_aguardando_rodada == 1:
                        print("❌ Entrada fraca - melhor ignorar"
                        "\n-  -  -  -  -  -  -  -  -  -  -  -  -  -")

            

                chegou_cinco = True
                # return  # 🔥 aqui encerra de verdade

        except:
            pass

        time.sleep(0.1)

def aguardar_timer_zerar(driver, base_vermelho, base_branco, base_preto):
    # buscando diga aos 5 segundos
    if modo_verificacao == True:
        monitorar_timer_cinco(driver, base_vermelho, base_branco, base_preto)
    while rodando:
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
    while rodando:
        try:
            timer = driver.find_element(
                By.XPATH,
                '//*[@id="roulette-timer"]/div[2]/div[2]/span'
            ).get_attribute("textContent").strip()

            if not timer.startswith("0:00"):
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
    while rodando:
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
oquemostrar = 0
nomeexibição = "todas"
# configurações iniciais
def menu_inicial(controle, controle2, controle3):
    global oquemostrar
    global menu
    global metexib
    global total_martingale
    global nomeexibição
    global porc_min2
    global porc_montante

    porc_min2 = 30
    porc_montante = 15

    while controle == 0:
        
        # AJUSTANDO TEXTO DA EXIBIÇÃO
        if metexib == 0:
            nomeexibição = "todas"
        elif metexib == 1:
            nomeexibição = "somente rodadas premiadas"
        # MENU PRINCIPAL
        limpar_tela()
        nova_mensagem()
        print("### ⚙️ Configurações iniciais ###\n"
        "\n----------------------------------------"
        f"\nExibição de entradas: {nomeexibição}"
        f"\nMartingale atual: {total_martingale}"
        f"\nDiferença entre menores: {porc_min2}"
        f"\nReferência ao montante: {porc_montante}"
        "\n----------------------------------------\n")
        print("\n> Selecione o número da opção desejada:"
        "\n 0. Iniciar bot"
        "\n 1. Configurar exibição do bot"
        "\n 2. Configurar martingale"
        "\n 3. Ajustes de entrada segura"
        )
        
        menu = input("Resposta: ")

        # MENU MÉTODO DE EXIBIÇÃO
        if menu == "1":
            controle2 = 0    
            while controle2 == 0:
                limpar_tela()
                print("### ⚙️ Configurações iniciais ###\n")
                print("\n> Qual será o metódo de exibição?\n"
                "\n 0. Mostrar todas as entradas"
                "\n 1. Mostrar apenas entradas premiadas"
                )
                oquemostrar = input("Resposta: ")
                if oquemostrar == "0":
                    metexib = 0
                    controle2 = 1
                    print(f"\n✨ Salvo com sucesso! 💾")
                    time.sleep(1)
                elif oquemostrar == "1":
                    metexib = 1
                    controle2 = 1
                    print(f"\n✨ Salvo com sucesso! 💾")
                    time.sleep(1)
                else:
                    controle2 = 0
                    print("Opção inválida, tente novamente...")
                    time.sleep(2)

        # MENU DEFINIÇÃO DE MARTINGALE
        elif menu == "2":
            controle3 = 0    
            while controle3 == 0:
                limpar_tela()
                print("### ⚙️ Configurações iniciais ###\n")
                print("\n> Qual será a quantidade de martingale?\n")
                total_martingale = input("Resposta: ")
                if total_martingale.isdigit():
                    total_martingale = int(total_martingale)
                    print(f"\n✨ Salvo com sucesso! 💾")
                    time.sleep(1)
                    controle3 = 1
                else:
                    controle3 = 0
                    print("Opção inválida, tente novamente...")
                    time.sleep(2)

        # MENU AJUSTES ENTRADA SEGURA
        elif menu == "3":
            controle3 = 0    
            while controle3 == 0:
                limpar_tela()
                print("### ⚙️ Configurações iniciais ###\n")
                print("\n> Quanto menor (%) deve ser o menor valor em relação ao 2 menor?\n")
                porc_min2 = input("Resposta: ")
                if porc_min2.isdigit():
                    porc_min2 = int(porc_min2)
                    print(f"R: min {porc_min2} % menor que o segundo menor")
                    time.sleep(1)
                    print("\n> Qual a diferença (%) em relação ao montante?\n")
                    porc_montante = input("Resposta: ")

                    if porc_montante.isdigit():
                        porc_montante = int(porc_montante)
                        print(f"R: min {porc_montante} % menor que o montante\n"
                        f"\n✨ Salvo com sucesso! 💾")
                        time.sleep(1)
                        controle3 = 1
                    else:
                        controle3 = 0
                        print("Opção inválida, tente novamente...")
                        time.sleep(2)        
                else:
                    controle3 = 0
                    print("Opção inválida, tente novamente...")
                    time.sleep(2)
        
        # iniciar o bot
        elif menu == "0":
            controle = 1
            total_martingale += 1
        
        #opção inválida
        else:
            controle = 0
            print("Opção inválida, tente novamente...")
            time.sleep(2)

        

def iniciar_driver():
    try:
        options = Options()

        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")

        driver = webdriver.Chrome(options=options)
        driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")

        return driver

    except Exception:
        traceback.print_exc()
        input("Erro ao iniciar Chrome")
        exit()


def iniciar_automacao():
    global modo
    global total_martingale
    menu_inicial(controle, controle2, controle3)
    driver = iniciar_driver()
    driver.get("https://blaze.bet.br/pt/games/double")
    
    # novo grupo de msg
    nova_mensagem()
    enviar_telegram("### 🚀 INICIANDO O BOT ###", nova=True)

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
    global rodada_premiada
    rodada_premiada = 0
    primeira_rodada = True
    global modo_verificacao
    modo_verificacao = False
    global tentativas_restantes
    tentativas_restantes = 0
    primeira_rodada_valida = True
    global entrada_segura
    entrada_segura = False
    cor_segura = ""
    win_seguro = 0
    global controle_aguardando_rodada
    controle_aguardando_rodada = 0

    base_vermelho = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[1]'
    base_branco = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[2]'
    base_preto = '//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[3]'

    numrodada = 0
    win = 0
    loss = 0
    
    lista_resultados = pegar_lista_resultados(driver)
    limpar_tela()
    while rodando:
        numrodada += 1

        # opcao: mostrando todas as rodadas
        if metexib == 0:
            try:
                # VERIFICANDO SE É PRIMEIRA RODADA
                if primeira_rodada == True:
                    print("⏳ Primeira rodada ignorada")
                    numrodada = 0
                    primeira_rodada = False
                    aguardar_timer_sair_de_zero(driver)
                    print("(Calibrando entradas...)")
                    aguardar_timer_zerar(driver, base_vermelho, base_branco, base_preto)
                # 🔥 Constatada de que não é a primeira rodada
                elif primeira_rodada == False:
                    
                    # Aguardando 1 rodada valida
                    if primeira_rodada_valida == True:    
                        aguardar_timer_sair_de_zero(driver)
                        primeira_rodada_valida = False
                    
                    # Iniciando nova rodada          
                    limpar_tela()
                    nova_mensagem()
                    enviar_telegram(f"#############################", nova=True)
                    print(f"------------ 📊 RODADA {numrodada} ------------")
                    
                    # Aguardando o 5
                    aguardar_timer_zerar(driver, base_vermelho, base_branco, base_preto)
                
                    valor_vermelho = pegar_valor_com_espera(driver, base_vermelho)
                    valor_branco = pegar_valor_com_espera(driver, base_branco)
                    valor_preto = pegar_valor_com_espera(driver, base_preto)

                    # 🔥 SUA LÓGICA ORIGINAL MANTIDA
                    seta_vermelho = ""
                    seta_branco = ""
                    seta_preto = ""
                
                    # verificando valor maior
                    if valor_vermelho > valor_branco and valor_vermelho > valor_preto:
                        cor_maior = "🔴"; seta_vermelho = "🏆"
                    elif valor_branco > valor_vermelho and valor_branco > valor_preto:
                        cor_maior = "⚪"; seta_branco = "🏆"
                    else:
                        cor_maior = "⚫"; seta_preto = "🏆"

                    # verificnado valor menor
                    if valor_vermelho < valor_branco and valor_vermelho < valor_preto:
                        cor_menor = "🔴"; seta_vermelho += "⬇️"
                        valormenor1 = valor_vermelho
                        if valor_branco < valor_preto:
                            valormenor2 = valor_branco
                        else:
                            valormenor2 = valor_preto
                    elif valor_branco < valor_vermelho and valor_branco < valor_preto:
                        cor_menor = "⚪"; seta_branco += "⬇️"
                        valormenor1 = valor_branco
                        if valor_vermelho < valor_preto:
                            valormenor2 = valor_vermelho
                        else:
                            valormenor2 = valor_preto
                    else:
                        cor_menor = "⚫"; seta_preto += "⬇️"
                        valormenor1 = valor_preto
                        if valor_branco < valor_vermelho:
                            valormenor2 = valor_branco
                        else:
                            valormenor2 = valor_vermelho
                    montante_total = valor_vermelho + valor_branco + valor_preto

                    print(f"\n🔴 {valor_vermelho} {seta_vermelho}"
                    f"\n⚪ {valor_branco} {seta_branco}"
                    f"\n⚫ {valor_preto} {seta_preto}"
                    "\n----------------------------------------"
                    f"\n🕛Aguardando resultado...\n")

                    # avaliando se é rodada premiada (estou fazendo essa validação no segundo 5)
                    #if modo_verificacao == True:
                        # avaliando se deve entrar ou não 
                        #diferenca_percentual = ((valormenor2 - valormenor1) / valormenor2) * 100
                        #porcentagem_total = (valormenor1 / montante_total) * 100

                        #if diferenca_percentual >= 30 and porcentagem_total <= 15:
                        #    print("✅ Entrada FORTE - pode entrar")
                        #else:
                        #    print("❌ Entrada fraca - melhor ignorar")


                    aguardar_timer_sair_de_zero(driver)
                    time.sleep(3)
                    lista_resultados = aguardar_novo_resultado(driver, lista_resultados)
                    numero = lista_resultados[0]
                    cor = classificar_cor(numero)

                    print("----------------------------------------"
                    f"\nResultado: {cor} ({numero})")
                    
                    if not modo_verificacao:
                        
                        if cor == cor_maior: # cor_maior
                            print("----------------------------------------"
                            "\n✅ Maior bateu → entrar no menor")
                            modo_verificacao = True
                            tentativas_restantes = total_martingale
                        else:
                            print("----------------------------------------"
                            "\n🔄 Maior não bateu")
                    else:
                        if entrada_segura == True:
                            if cor == cor_segura:
                                win_seguro += 1

                        if entrada_segura == True:
                            
                                
                            if cor == cor_menor:
                                print("----------------------------------------"
                                "\n🎯 WIN")
                                entrada_segura = False
                                win += 1
                                modo_verificacao = False

                            else:
                                tentativas_restantes -= 1
                                print("----------------------------------------"
                                f"\n⏳ Tentativas: {tentativas_restantes}")
                                if tentativas_restantes == 0:
                                    print("💀 LOSS")
                                    entrada_segura = False
                                    loss += 1
                                    modo_verificacao = False

                        elif entrada_segura == False:
                            print("Entrada não segura, aguardando a próxima...")
                    
                    print(f"🤑 WIN: {win} |😭 LOSS: {loss}"
                          f"\n🤑 Win seguro: {win_seguro}")
                    

            except Exception as e:
                print("❌ Erro:", e)
                time.sleep(2)


        # opcao: mostrando apenas as rodadas premiadas
        elif metexib == 1:
            try:
                # VERIFICANDO SE É PRIMEIRA RODADA
                if primeira_rodada == True:
                    print("⏳ Primeira rodada ignorada")
                    numrodada = 0
                    primeira_rodada = False
                    aguardar_timer_sair_de_zero(driver)
                    print("(Calibrando entradas...)")
                    aguardar_timer_zerar(driver, base_vermelho, base_branco, base_preto)
                # 🔥 Constatada de que não é a primeira rodada
                elif primeira_rodada == False:
                    
                    # Aguardando 1 rodada valida
                    if primeira_rodada_valida == True:    
                        aguardar_timer_sair_de_zero(driver)
                        primeira_rodada_valida = False
                    
                    # Iniciando nova rodada          
                    # verificando se é rodada premiada para poder printar
                    if rodada_premiada == 1:
                        limpar_tela()
                        nova_mensagem()
                        enviar_telegram(f"#############################", nova=True)
                        print(f"------------ 📊 RODADA {numrodada} ------------")
                    else:
                        if controle_aguardando_rodada == 0:
                            limpar_tela()
                            controle_aguardando_rodada = 1
                            nova_mensagem()
                            enviar_telegram(f"----------------------------------------", nova=True)
                            print("⏳ Aguardando rodada premiada\n")
                    # Aguardando o 5
                    aguardar_timer_zerar(driver, base_vermelho, base_branco, base_preto)
                
                    valor_vermelho = pegar_valor_com_espera(driver, base_vermelho)
                    valor_branco = pegar_valor_com_espera(driver, base_branco)
                    valor_preto = pegar_valor_com_espera(driver, base_preto)

                    # 🔥 SUA LÓGICA ORIGINAL MANTIDA
                    seta_vermelho = ""
                    seta_branco = ""
                    seta_preto = ""
                
                    # verificando valor maior
                    if valor_vermelho > valor_branco and valor_vermelho > valor_preto:
                        cor_maior = "🔴"; seta_vermelho = "🏆"
                    elif valor_branco > valor_vermelho and valor_branco > valor_preto:
                        cor_maior = "⚪"; seta_branco = "🏆"
                    else:
                        cor_maior = "⚫"; seta_preto = "🏆"

                    # verificnado valor menor
                    if valor_vermelho < valor_branco and valor_vermelho < valor_preto:
                        cor_menor = "🔴"; seta_vermelho += "⬇️"
                        valormenor1 = valor_vermelho
                        if valor_branco < valor_preto:
                            valormenor2 = valor_branco
                        else:
                            valormenor2 = valor_preto
                    elif valor_branco < valor_vermelho and valor_branco < valor_preto:
                        cor_menor = "⚪"; seta_branco += "⬇️"
                        valormenor1 = valor_branco
                        if valor_vermelho < valor_preto:
                            valormenor2 = valor_vermelho
                        else:
                            valormenor2 = valor_preto
                    else:
                        cor_menor = "⚫"; seta_preto += "⬇️"
                        valormenor1 = valor_preto
                        if valor_branco < valor_vermelho:
                            valormenor2 = valor_branco
                        else:
                            valormenor2 = valor_vermelho
                    montante_total = valor_vermelho + valor_branco + valor_preto

                    # mostarar se for rodada premiada
                    if rodada_premiada == 1:
                        print(f"\n🔴 {valor_vermelho} {seta_vermelho}"
                        f"\n⚪ {valor_branco} {seta_branco}"
                        f"\n⚫ {valor_preto} {seta_preto}"
                        "\n----------------------------------------"
                        f"\n🕛Aguardando resultado...\n")

                    aguardar_timer_sair_de_zero(driver)
                    time.sleep(3)
                    lista_resultados = aguardar_novo_resultado(driver, lista_resultados)
                    numero = lista_resultados[0]
                    cor = classificar_cor(numero)

                    # mostarar se for rodada premiada
                    if rodada_premiada == 1:
                        print("----------------------------------------"
                        f"\nResultado: {cor} ({numero})")
                        
                    if not modo_verificacao:
                        # verificando se é rodada premiada
                        if cor == cor_maior: # cor_maior
                            rodada_premiada = 1
                            print("----------------------------------------"
                            "\n✅ Maior bateu → entrar no menor")
                            modo_verificacao = True
                            tentativas_restantes = total_martingale
                        #else:
                        #    print("----------------------------------------"
                        #    "\n↻ Maior não bateu, próxima...")
                    else:
                        if entrada_segura == True:
                            if cor == cor_segura:
                                win_seguro += 1

                        if entrada_segura == True:
                            if cor == cor_menor: #cor_menor
                                entrada_segura = False
                                win += 1
                                modo_verificacao = False
                                # mostarar se for rodada premiada
                                if rodada_premiada == 1:
                                    print("----------------------------------------"
                                    "\n🎯 WIN"
                                    "\n-  -  -  -  -  -  -  -  -  -  -  -  -  -"
                                    f"\n🤑 WIN: {win}"
                                    f"\n🤑 Win seguro: {win_seguro}"
                                    f"\n😭 LOSS: {loss}")
                                    #finalizou a roada premiada
                                    controle_aguardando_rodada = 0
                                    rodada_premiada = 0

                            else:
                                tentativas_restantes -= 1
                                # mostarar se for rodada premiada
                                if rodada_premiada == 1 and tentativas_restantes != 0:
                                    print("----------------------------------------"
                                    f"\n⏳ Tentativas: {tentativas_restantes}")
                                if tentativas_restantes == 0:
                                    entrada_segura = False
                                    loss += 1
                                    modo_verificacao = False
                                    # mostarar se for rodada premiada
                                    if rodada_premiada == 1:
                                        print("----------------------------------------"
                                        "\n💀 LOSS"
                                        "\n-  -  -  -  -  -  -  -  -  -  -  -  -  -"
                                        f"\n🤑 WIN: {win}"
                                        f"\n🤑 Win seguro: {win_seguro}"
                                        f"\n😭 LOSS: {loss}")
                                        #finalizou a roada premiada
                                        controle_aguardando_rodada = 0
                                        rodada_premiada = 0

                        elif entrada_segura == False:
                            # mostarar se for rodada premiada
                            if rodada_premiada == 1:
                                print("Entrada não segura, aguardando a próxima...")
                    
                    

            except Exception as e:
                print("❌ Erro:", e)
                time.sleep(2)


if __name__ == "__main__":
    iniciar_automacao()


# Instruções para gerar executável com novo nome:
# python -m PyInstaller
#python -m PyInstaller --onefile -n bot_v2 bot.py
# python -m PyInstaller --onefile --icon=icone.ico bot.py  (alterando icone)

# estava dando erro, só deu certo quando fiz assim: python -m PyInstaller --onefile --clean --noconfirm --icon=iconebot.ico --hidden-import=selenium.webdriver.chrome.webdriver -n bot_v6 bot.py
