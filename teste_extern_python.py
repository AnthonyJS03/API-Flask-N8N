from flask import Flask, request, jsonify
import os
import zipfile
import requests
import urllib3
import subprocess
import sys

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
    url = item["url"]
    filename = item["filename"]
    caminho_arquivo = os.path.join(DOWNLOADS_DIR, filename)
    
    try:
        print (f"🔄 Processando: {url}")
        resposta = requests.get(url, stream=True, timeout=300, verify=False)
        if resposta.status_code == 200:
            with open(caminho_arquivo, 'wb') as f:
                for chunk in resposta.iter_content(chunk_size=8192):
                    f.write(chunk)
            print(f"✔️ Baixado: {filename}")
        else:
            print(f"❌ Erro ao baixar {filename}: {resposta.status_code}")
            return

        # Extração se for ZIP
        if filename.endswith(".zip"):
            with zipfile.ZipFile(caminho_arquivo, 'r') as zip_ref:
                zip_ref.extractall(os.path.join(DOWNLOADS_DIR, filename.replace(".zip", "")))
            print(f"📦 Extraído: {filename}")
    except Exception as e:
        print(f"⚠️ Erro com {filename}: {e}")

@app.route('/download', methods=['GET'])
def process_data():
    links = get_downloads()
    for item in links:
        get_extract_urls(item)

    extraidos = []
    for root, dirs, files in os.walk(DOWNLOADS_DIR):
        for file in files:
            caminho = os.path.join(root, file)
            extraidos.append(caminho)

    # Executa o upload
    try:
        print("🔄 Iniciando upload para o Drive...")
        resultado = subprocess.run(
            [sys.executable, "upload_drive.py"],
            input=json.dumps({'caminhos_completos': lista_de_arquivos}),
            text=True,
            check=True
        )
        if resultado.returncode != 0:
            print("❌ Erro no upload:", resultado.stderr)
            return jsonify({"error": "Falha no upload"}), 500
        print("✔️ Upload concluído!")
    except Exception as e:
        print("⚠️ Falha ao executar upload:", e)
        return jsonify({"error": str(e)}), 500

    return jsonify({
        "message": "Download e extração concluídos.",
        "arquivos": extraidos
    }), 200

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)

