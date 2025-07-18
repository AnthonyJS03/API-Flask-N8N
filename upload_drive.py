# upload_drive.py (versão simplificada e segura)
import os
import json
import sys
from google.oauth2.service_account import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

# Configurações via variáveis de ambiente
SCOPES = ['https://www.googleapis.com/auth/drive.file']
SERVICE_ACCOUNT_JSON = os.getenv('GCP_SERVICE_ACCOUNT_JSON')  # JSON completo em 1 linha
DRIVE_FOLDER_ID = os.getenv('DRIVE_FOLDER_ID')  # ID da pasta de destino

def autenticar_drive():
    """Conecta ao Google Drive usando Service Account"""
    try:
        creds = Credentials.from_service_account_info(
            json.loads(SERVICE_ACCOUNT_JSON),
            scopes=SCOPES
        )
        return build('drive', 'v3', credentials=creds)
    except json.JSONDecodeError:
        print("❌ Erro: JSON da Service Account inválido")
    except Exception as e:
        print(f"❌ Falha na autenticação: {str(e)}")
    return None

def upload_arquivo(service, caminho_arquivo):
    """Faz upload de um único arquivo"""
    try:
        nome_arquivo = os.path.basename(caminho_arquivo)
        
        metadata = {
            'name': nome_arquivo,
            'parents': [DRIVE_FOLDER_ID] if DRIVE_FOLDER_ID else []
        }
        
        media = MediaFileUpload(caminho_arquivo, resumable=True)
        request = service.files().create(
            body=metadata,
            media_body=media,
            fields='id,name'
        )
        
        response = request.execute()
        print(f"✅ {response['name']} enviado (ID: {response['id']})")
        return True
        
    except Exception as e:
        print(f"❌ Falha no upload de {os.path.basename(caminho_arquivo)}: {str(e)}")
        return False

def main():
    # Verifica variáveis essenciais
    if not SERVICE_ACCOUNT_JSON:
        print("❌ Variável GCP_SERVICE_ACCOUNT_JSON não encontrada")
        return
        
    # Carrega lista de arquivos (via stdin ou vazia)
    try:
        arquivos = json.load(sys.stdin).get('caminhos_completos', []) if not sys.stdin.isatty() else []
    except:
        arquivos = []
    
    # Autentica
    drive_service = autenticar_drive()
    if not drive_service or not arquivos:
        return
        
    # Processa uploads
    resultados = [upload_arquivo(drive_service, arq) for arq in arquivos]
    print(f"\n📊 Resultado: {sum(resultados)}/{len(arquivos)} arquivos enviados")

if __name__ == "__main__":
    main()
