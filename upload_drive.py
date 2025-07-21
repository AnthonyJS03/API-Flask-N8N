import os
import json
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_JSON = os.getenv('GCP_SERVICE_ACCOUNT_JSON')
DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')

def autenticar_drive():
    try:
        cred_dict = json.loads(SERVICE_ACCOUNT_JSON)
        # Corrige a private_key para ter quebras de linha reais
        cred_dict['private_key'] = cred_dict['private_key'].replace('\\n', '\n')
        
        creds = Credentials.from_service_account_info(
            cred_dict,
            scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    except Exception as e:
        print(f"❌ Erro de autenticação: {str(e)}")
        return None


def upload_arquivo(service, caminho_arquivo):
    try:
        file_metadata = {
            'name': os.path.basename(caminho_arquivo),
            'parents': [DRIVE_FOLDER_ID] if DRIVE_FOLDER_ID else []
        }
        
        media = MediaFileUpload(caminho_arquivo)
        file = service.files().create(
            body=file_metadata,
            media_body=media,
            fields='id'
        ).execute()
        
        print(f"✅ {file.get('name')} enviado (ID: {file.get('id')})")
        return True
    except Exception as e:
        print(f"❌ Falha no upload: {str(e)}")
        return False

def main():
    if not SERVICE_ACCOUNT_JSON:
        print("❌ Variáveis de ambiente não configuradas")
        return

    try:
        arquivos = json.load(sys.stdin).get('caminhos_completos', [])
    except:
        arquivos = []

    service = autenticar_drive()
    if not service:
        return

    for arquivo in arquivos:
        upload_arquivo(service, arquivo)

if __name__ == "__main__":
    main()
