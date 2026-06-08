import os
import time
import requests
import base64
import webbrowser

API_URL = "http://localhost:8080"
API_KEY = "42247710-6003-490b-936b-67a6d8d65451"
INSTANCE_NAME = "BoletimIA"
HEADERS = {"apikey": API_KEY, "Content-Type": "application/json"}

print("=======================================")
print("  RECONECTANDO SESSÃO DO WHATSAPP...   ")
print("=======================================")

# 1. Tenta deslogar a sessão antiga presa
try:
    requests.delete(f"{API_URL}/instance/logout/{INSTANCE_NAME}", headers=HEADERS, timeout=5)
    print("- Sessão antiga deslogada.")
except:
    pass

# 2. Deleta a instância para limpar o cache
try:
    requests.delete(f"{API_URL}/instance/delete/{INSTANCE_NAME}", headers=HEADERS, timeout=5)
    print("- Instância limpa do sistema.")
except:
    pass

time.sleep(2)

# 3. Recria a instância do zero
payload = {
    "instanceName": INSTANCE_NAME,
    "token": API_KEY,
    "qrcode": True
}
try:
    requests.post(f"{API_URL}/instance/create", json=payload, headers=HEADERS, timeout=10)
    print("- Nova instância 'BoletimIA' criada.")
except Exception as e:
    print(f"Erro ao criar instância: {e}")

time.sleep(1)

# 4. Baixa o QR Code nativo e salva como imagem
try:
    response = requests.get(f"{API_URL}/instance/connect/{INSTANCE_NAME}", headers=HEADERS, timeout=10)
    data = response.json()
    if "base64" in data:
        base64_str = data["base64"]
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
        
        img_data = base64.b64decode(base64_str)
        with open("qrcode.png", "wb") as f:
            f.write(img_data)
            
        html = """<!DOCTYPE html>
<html>
<head><title>QR Code WhatsApp</title></head>
<body style="text-align: center; padding-top: 50px; font-family: sans-serif;">
    <h2>Leia o QR Code abaixo no WhatsApp</h2>
    <img src="qrcode.png" alt="QR Code" style="border: 2px solid #ccc; padding: 10px; border-radius: 10px;"/>
    <br><br>
    <button onclick="location.reload()" style="padding: 10px 20px; font-size: 16px; cursor: pointer;">Atualizar QR Code</button>
</body>
</html>"""
        with open("qrcode.html", "w", encoding="utf-8") as f:
            f.write(html)
            
        print("- Novo QR Code gerado com sucesso!")
        
        # Abre automaticamente no navegador padrão
        filepath = os.path.abspath("qrcode.html")
        webbrowser.open(f"file:///{filepath}")
        
    else:
        print("Não foi possível gerar o QR Code. A resposta da API foi:", data)
except Exception as e:
    print("Erro ao obter o QR Code:", e)

print("\nConcluído! Uma página com o novo QR Code deve abrir no seu navegador.")
