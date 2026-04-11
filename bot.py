from playwright.sync_api import sync_playwright
import time
import re
import os
import requests
from dotenv import load_dotenv

load_dotenv()

TOKEN = os.getenv("TOKEN")
CHAT_ID = os.getenv("CHAT_ID")


def enviar_telegram(msg):
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": CHAT_ID, "text": msg})
    except:
        pass


def print(*args):
    msg = " ".join(str(a) for a in args)
    __builtins__.print(msg)
    enviar_telegram(msg)


def extrair_valor(texto):
    match = re.search(r"[\d.,]+", texto)
    if match:
        return float(match.group().replace(".", "").replace(",", "."))
    return 0.0


def extrair_numero(texto):
    match = re.search(r"\d+", texto)
    return int(match.group()) if match else None


def classificar_cor(numero):
    if numero is None:
        return "⚪"
    if 1 <= numero <= 7:
        return "🔴"
    if 8 <= numero <= 14:
        return "⚫"
    return "⚪"


# =========================
# PLAYWRIGHT STABLE RAILWAY
# =========================
def iniciar_browser():
    p = sync_playwright().start()

    browser = p.chromium.launch(
        headless=True,
        args=[
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--disable-gpu"
        ]
    )

    context = browser.new_context()
    page = context.new_page()

    return p, browser, context, page


# =========================
# BOT
# =========================
def iniciar_automacao():
    p, browser, context, page = iniciar_browser()

    try:
        page.goto("https://blaze.bet.br/pt/games/double", timeout=60000)

        print("🚀 INICIADO")

        # cookies
        try:
            page.click('xpath=//*[@id="policy-regulation-popup"]/div/div[2]/div/button', timeout=5000)
        except:
            pass

        time.sleep(5)

        # entrar jogo
        try:
            page.click('xpath=//*[@id="blaze-provider"]/main/div[2]/div/div/div/div/div[4]/button[1]', timeout=5000)
        except:
            pass

        time.sleep(10)

        print("⏳ carregado")

        saldo = 0.0

        while True:
            try:
                time.sleep(5)

                # apostas
                v = extrair_valor(page.locator('xpath=//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[1]').inner_text())
                b = extrair_valor(page.locator('xpath=//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[2]').inner_text())
                p = extrair_valor(page.locator('xpath=//*[@id="roulette"]/div/div[2]/div[2]/div/div/div/div[3]').inner_text())

                print(f"🔴 {v} ⚪ {b} ⚫ {p}")

                time.sleep(5)

                ultimo = page.locator('xpath=//*[@id="roulette-recent"]/div/div[1]/div[1]/div/div/div').inner_text()
                numero = extrair_numero(ultimo)
                cor = classificar_cor(numero)

                print(f"🎯 {cor} ({numero})")

                if cor == "🔴":
                    saldo += (b + p) - (v * 2)
                elif cor == "⚫":
                    saldo += (v + b) - (p * 2)
                elif cor == "⚪":
                    saldo += (v + p) - (b * 14)

                print(f"💰 saldo: {saldo}")

            except Exception as e:
                print("erro loop:", e)

                # 🔥 RESTART AUTOMÁTICO DO BROWSER (IMPORTANTE NO RAILWAY)
                try:
                    browser.close()
                    context.close()
                    p.stop()
                except:
                    pass

                time.sleep(5)

                p, browser, context, page = iniciar_browser()

    except Exception as e:
        print("ERRO FATAL:", e)

    finally:
        try:
            browser.close()
            context.close()
            p.stop()
        except:
            pass


if __name__ == "__main__":
    iniciar_automacao()
