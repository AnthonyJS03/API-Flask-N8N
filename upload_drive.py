import os
import json
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google.auth.transport.requests import Request
from google_auth_oauthlib.flow import InstalledAppFlow
import time

# Configurações
SCOPES = ['https://www.googleapis.com/auth/drive.file']
CREDENTIALS_FILE = 'credentials.json'
TOKEN_FILE = 'token.json'
PASTA_DESTINO_ID = '1rpazJv21rg7lCJHknjxqSFu8XewYSTRQ'  # ID da pasta no Drive

def carregar_metadados():
    try:
        with open('metadados_shapefile.json') as f:
            metadados = json.load(f)
        
        for caminho in metadados['caminhos_completos']:
            if not os.path.exists(caminho):
                raise FileNotFoundError(f"Arquivo não encontrado: {caminho}")
        
        return metadados
    except Exception as e:
        print(f"Erro ao carregar metadados: {e}")
        return None

def autenticar_drive():
    try:
        creds = None
        
        if os.path.exists(TOKEN_FILE):
            creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
                creds = flow.run_local_server(port=0)
            
            with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())
        
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"Falha na autenticação: {e}")
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
                print(f"Progresso {nome_arquivo}: {int(status.progress() * 100)}%")
        
        print(f"Upload concluído: {response['name']} (ID: {response['id']})")
        return True
        
    except Exception as e:
        if tentativa < max_tentativas:
            print(f"Tentativa {tentativa} falhou. Tentando novamente em 5 segundos...")
            time.sleep(5)
            return upload_arquivo(service, caminho_arquivo, tentativa + 1)
        print(f"Falha no upload de {nome_arquivo} após {max_tentativas} tentativas: {e}")
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