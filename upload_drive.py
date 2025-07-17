import os
import json
import time
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request

# Caminhos fixos dos arquivos secretos
CREDENTIALS_FILE = '/etc/secrets/credentials.json'
TOKEN_FILE = '/etc/secrets/token.json'
METADADOS_FILE = '/etc/secrets/metadados_shapefile.json'

# ID da pasta no Google Drive (ou leia de variável de ambiente)
PASTA_DESTINO_ID = '1rpazJv21rg7lCJHknjxqSFu8XewYSTRQ'

SCOPES = ['https://www.googleapis.com/auth/drive.file']

def autenticar_drive():
    try:
        creds = None
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        return build('drive', 'v3', credentials=creds)
    
    except Exception as e:
        print(f"[ERRO] Autenticação falhou: {e}")
        return None

def carregar_metadados():
    try:
        with open(METADADOS_FILE) as f:
            metadados = json.load(f)
        
        for caminho in metadados['caminhos_completos']:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        return metadados
    except Exception as e:
        print(f"[ERRO] Falha ao carregar metadados: {e}")
        return None

def upload_arquivo(service, caminho_arquivo, tentativa=1, max_tentativas=3):
    nome_arquivo = os.path.basename(caminho_arquivo)
    
    mime_types = {
        '.shp': 'application/octet-stream',
        '.shx': 'application/octet-stream',
        '.dbf': 'application/x-dbf',
        '.prj': 'text/plain',
        '.cpg': 'text/plain',
        '.sbn': 'application/octet-stream',
        '.sbx': 'application/octet-stream',
        '.xml': 'application/xml'
    }
    
    ext = os.path.splitext(nome_arquivo)[1].lower()
    mime_type = mime_types.get(ext, 'application/octet-stream')
    
    file_metadata = {
        'name': nome_arquivo,
        'parents': [PASTA_DESTINO_ID] if PASTA_DESTINO_ID else []
    }

    try:
        media = MediaFileUpload(caminho_arquivo, mimetype=mime_type, resumable=True)
        request = service.files().create(body=file_metadata, media_body=media, fields='id,name,size')

        response = None
        while response is None:
            status, response = request.next_chunk()
            if status:
                print(f"[UPLOAD] {nome_arquivo}: {int(status.progress() * 100)}%")

        print(f"[SUCESSO] {response['name']} enviado! ID: {response['id']}")
        return True
    
    except Exception as e:
        if tentativa < max_tentativas:
            print(f"[TENTATIVA {tentativa}] Falha. Retentando em 5s...")
            time.sleep(5)
            return upload_arquivo(service, caminho_arquivo, tentativa + 1)
        print(f"[ERRO] Falha no upload {nome_arquivo}: {e}")
        return False
        
def main():
    print("Iniciando processo de upload para o Google Drive...")
    
    metadados = carregar_metadados()
    if not metadados:
        return
    
    drive_service = autenticar_drive()
    if not drive_service:
        return
    
    resultados = []
    for caminho in metadados['caminhos_completos']:
        resultados.append(upload_arquivo(drive_service, caminho))
    
    sucessos = sum(1 for r in resultados if r)
    print(f"\nUpload: {sucessos} de {len(resultados)} arquivos enviados com sucesso")

if __name__ == "__main__":
    main()
