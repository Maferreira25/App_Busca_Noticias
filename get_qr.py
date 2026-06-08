import requests
import base64
import os

url = "http://localhost:8080/instance/connect/BoletimIA"
headers = {"apikey": "42247710-6003-490b-936b-67a6d8d65451"}

try:
    response = requests.get(url, headers=headers)
    data = response.json()
    
    if "base64" in data:
        base64_str = data["base64"]
        
        # O base64 retornado as vezes vem com o prefixo 'data:image/png;base64,'
        if "," in base64_str:
            base64_str = base64_str.split(",")[1]
            
        img_data = base64.b64decode(base64_str)
        
        with open("qrcode.png", "wb") as f:
            f.write(img_data)
            
        print("QR Code salvo como qrcode.png!")
        
        # Atualizar o HTML para apontar para a imagem png
        html = """<!DOCTYPE html>
<html>
<head>
    <title>QR Code WhatsApp</title>
</head>
<body style="text-align: center; padding-top: 50px;">
    <h2>Leia o QR Code abaixo no WhatsApp</h2>
    <img src="qrcode.png" alt="QR Code" />
    <br><br>
    <button onclick="location.reload()">Atualizar QR Code</button>
</body>
</html>"""
        with open("qrcode.html", "w", encoding="utf-8") as f:
            f.write(html)
            
    else:
        print("A resposta não contém base64:", data)
except Exception as e:
    print("Erro:", e)
