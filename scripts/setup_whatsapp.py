import requests
import time
import os
import base64

# Configurações da Evolution API v1.8.2
BASE_URL = "http://localhost:8080"
GLOBAL_API_KEY = "42247710-6003-490b-936b-67a6d8d65451"
INSTANCE_NAME = "BoletimIA"

def setup():
    headers = {"apikey": GLOBAL_API_KEY, "Content-Type": "application/json"}
    print(f"--- Configurando Instancia v1.8.2: {INSTANCE_NAME} ---")

    # 1. Verificar se ja esta conectado
    try:
        state_res = requests.get(f"{BASE_URL}/instance/connectionState/{INSTANCE_NAME}", headers=headers)
        if state_res.status_code == 200 and state_res.json().get("instance", {}).get("state") == "open":
            print("Seu WhatsApp ja esta CONECTADO!")
            return
    except:
        pass

    # 2. Criar a instancia (Payload simplificado v1)
    create_payload = {
        "instanceName": INSTANCE_NAME,
        "token": "token_secreto_ia"
    }
    requests.post(f"{BASE_URL}/instance/create", json=create_payload, headers=headers)

    # 3. Obter QR Code
    print("Aguardando geracao do QR Code...")
    for i in range(1, 10):
        print(f"Tentativa {i}/10...")
        qr_response = requests.get(f"{BASE_URL}/instance/connect/{INSTANCE_NAME}", headers=headers)
        if qr_response.status_code == 200:
            data = qr_response.json()
            # Na v1.8 o base64 pode vir direto ou dentro de um objeto
            b64 = data.get("base64") or data.get("qrcode", {}).get("base64")
            if b64:
                base64_data = b64.split(",")[1] if "," in b64 else b64
                with open("qrcode_whatsapp.png", "wb") as f:
                    f.write(base64.b64decode(base64_data))
                print("\nQR CODE GERADO COM SUCESSO!")
                print("Abra 'qrcode_whatsapp.png' e escaneie no seu WhatsApp.")
                return
        time.sleep(5)

    print("\nNao foi possivel obter o QR Code. Tente abrir http://localhost:8080/manager no navegador.")

if __name__ == "__main__":
    setup()
