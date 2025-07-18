from flask import Flask, request, jsonify
import os
import zipfile
import requests
import urllib3
import subprocess
import sys
import json  # Adicionado

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

app = Flask(__name__)

DOWNLOADS_DIR = 'downloads'
os.makedirs(DOWNLOADS_DIR, exist_ok=True)

def get_downloads():
    return [
        {
            "url": "https://ftp-pamgia.ibama.gov.br/dados/adm_embargos_ibama_a.zip",
            "filename": "adm_embargos_ibama_a.zip"
        }
    ]

def get_extract_urls(item):
    try:
        url = item["url"]
        filename = item["filename"]
        caminho_arquivo = os.path.join(DOWNLOADS_DIR, filename)
        
        print(f"🔄 Baixando: {url}")
        resposta = requests.get(url, stream=True, timeout=300, verify=False)
        
        if resposta.status_code == 200:
            with open(caminho_arquivo, 'wb') as f:
                for chunk in resposta.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✔️ Arquivo baixado: {filename}")
            
            if filename.endswith(".zip"):
                with zipfile.ZipFile(caminho_arquivo, 'r') as zip_ref:
                    zip_ref.extractall(os.path.join(DOWNLOADS_DIR, filename.replace(".zip", "")))
                print(f"📦 Arquivo extraído: {filename}")
        else:
            print(f"❌ Falha no download: {resposta.status_code}")
    except Exception as e:
        print(f"⚠️ Erro no processamento: {str(e)}")

@app.route('/download', methods=['GET'])
def process_data():
    try:
        # Download e extração
        links = get_downloads()
        for item in links:
            get_extract_urls(item)

        # Lista arquivos baixados
        arquivos_baixados = []
        for root, _, files in os.walk(DOWNLOADS_DIR):
            for file in files:
                caminho = os.path.join(root, file)
                arquivos_baixados.append(caminho)

        # Upload para o Drive
        print("🔄 Iniciando upload...")
        resultado = subprocess.run(
            [sys.executable, "upload_drive.py"],
            input=json.dumps({'caminhos_completos': arquivos_baixados}),
            text=True,
            capture_output=True
        )
        
        if resultado.returncode != 0:
            raise Exception(resultado.stderr)
            
        print("✔️ Processo concluído!")
        return jsonify({
            "message": "Sucesso",
            "arquivos": arquivos_baixados,
            "upload_log": resultado.stdout
        }), 200

    except Exception as e:
        print(f"❌ Erro no processo: {str(e)}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
