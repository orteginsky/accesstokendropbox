import requests
import json

# Configuración
SERVICE_URL = "https://accesstokendropbox-223080314602.us-central1.run.app"
API_SIGNATURE = "930xY0dJ0pD"

def check_token_and_scopes():
    print(f"--- Iniciando validación de Team Space en: {SERVICE_URL} ---")
    
    # 1. Obtener token
    token_url = f"{SERVICE_URL}/api/v1/token"
    payload = {"signature": API_SIGNATURE, "service": "test_script"}
    
    try:
        response = requests.post(token_url, json=payload)
        response.raise_for_status()
        access_token = response.json().get("access_token")
        
        headers = {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }

        # 2. Obtener Root Info (Namespace empresarial)
        print("\n2. Identificando Namespace del Team Space...")
        user_url = "https://api.dropboxapi.com/2/users/get_current_account"
        user_response = requests.post(user_url, headers=headers, data="null")
        
        root_ns_id = None
        if user_response.status_code == 200:
            u = user_response.json()
            root_ns_id = u.get('root_info', {}).get('root_namespace_id')
            print(f"   [OK] Usuario: {u.get('email')}")
            print(f"   [OK] Root Namespace ID: {root_ns_id}")
        else:
            print(f"   [ERROR] No se pudo obtener información de cuenta: {user_response.text}")
            return

        # 3. Listar archivos usando el Namespace Empresarial
        print("\n3. Listando carpetas en el TEAM SPACE...")
        # Header crítico para cuentas Business:
        headers["Dropbox-API-Path-Root"] = json.dumps({".tag": "root", "root": root_ns_id})
        
        list_url = "https://api.dropboxapi.com/2/files/list_folder"
        list_payload = {"path": "", "recursive": False}
        
        list_response = requests.post(list_url, headers=headers, json=list_payload)
        
        if list_response.status_code == 200:
            entries = list_response.json().get('entries', [])
            print(f"   [OK] ¡Éxito! Se encontraron {len(entries)} elementos en el espacio de equipo:")
            for e in entries:
                print(f"      - [{e['.tag']}] {e['name']} (ID: {e.get('id')})")
        else:
            print(f"   [ERROR] No se pudo acceder al Team Space: {list_response.status_code}")
            print(f"   Detalle: {list_response.text}")

    except Exception as e:
        print(f"\n[ERROR] {e}")

if __name__ == "__main__":
    check_token_and_scopes()
