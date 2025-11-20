# AccessTokenDropbox

Microservicio para gestionar tokens de acceso de Dropbox en Google Cloud Run.  
Este servicio soluciona el problema de tokens de Dropbox que caducan rápidamente, proporcionando un sistema centralizado que valida, refresca y distribuye tokens válidos automáticamente.

---

## Características

- **Arquitectura por capas**: Separación clara de responsabilidades (API, Servicios, Repositorios, Modelos).
- **Gestión automática de tokens**: Valida y refresca tokens de Dropbox automáticamente.
- **Google Cloud Secret Manager**: Almacenamiento seguro de tokens (`access_token` + `refresh_token`).
- **Autenticación por firma**: Protege el acceso al servicio mediante una firma compartida.
- **FastAPI**: Framework moderno y rápido para APIs.
- **Listo para Cloud Run**: Configuración completa para deployment en Google Cloud (Artifact Registry + Cloud Run + Secret Manager).

---

## Arquitectura

```text
accesstokendropbox/
├── app/
│   ├── api/                     # Capa de presentación (endpoints)
│   │   ├── __init__.py
│   │   └── routes.py            # Rutas y endpoints de la API
│   ├── core/                    # Configuración y utilidades
│   │   ├── __init__.py
│   │   ├── config.py            # Configuración de la aplicación (Settings)
│   │   └── logging_config.py    # Configuración de logging
│   ├── middlewares/             # Middlewares de la aplicación
│   │   ├── __init__.py
│   │   └── error_handler.py     # Manejo estándar de errores
│   ├── models/                  # Capa de dominio (entidades)
│   │   ├── __init__.py
│   │   └── token.py             # Modelos de datos (DropboxToken, TokenResponse)
│   ├── repositories/            # Capa de acceso a datos
│   │   ├── __init__.py
│   │   ├── dropbox_repository.py        # Interacción con API de Dropbox
│   │   └── secret_manager_repository.py # Interacción con Secret Manager
│   ├── services/                # Capa de lógica de negocio
│   │   ├── __init__.py
│   │   ├── auth_service.py      # Autenticación y autorización
│   │   └── token_service.py     # Lógica de gestión de tokens
│   ├── __init__.py
│   └── main.py                  # Punto de entrada de la aplicación (FastAPI)
├── tests/                       # Tests unitarios y de integración
├── .dockerignore
├── .env.example                 # Ejemplo de variables de entorno
├── .gitignore
├── cloudbuild.yaml              # Configuración de Cloud Build (opcional)
├── Dockerfile                   # Configuración de contenedor
├── README.md
└── requirements.txt             # Dependencias de Python
````

---

## Flujo de Trabajo

1. **Solicitud de token**

   * El cliente envía una solicitud con una firma (`signature`) y un `service`.
   * El servicio valida la firma mediante `AuthService`.

2. **Validación del token**

   * Recupera el token almacenado en **Secret Manager**.
   * Verifica si el token está expirado o próximo a expirar.
   * Valida el token con la API de Dropbox.

3. **Actualización automática**

   * Si el token no es válido o está expirado, se refresca usando el `refresh_token`.
   * Actualiza el token en Secret Manager (nueva versión).
   * Devuelve un token válido al cliente.

---

## Configuración

### 1. Prerequisitos

* Python 3.11+
* Cuenta de Google Cloud con proyecto activo.
* Aplicación de Dropbox registrada (App key + App secret).
* `gcloud` CLI instalado y configurado.
* Artifact Registry habilitado.
* Secret Manager habilitado.

---

### 2. Variables de Entorno

#### 2.1. Entorno local (`.env`)

Copia `.env.example` a `.env` y configura las variables:

```env
# Application
APP_NAME=AccessTokenDropbox
DEBUG=True
LOG_LEVEL=INFO

# Authentication
API_SECRET_KEY=tu-clave-secreta-aqui
AUTH_MODE=simple  # o 'hmac'

# Google Cloud
GCP_PROJECT_ID=tu-proyecto-gcp
SECRET_NAME=dropbox-access-token

# Dropbox
DROPBOX_APP_KEY=tu-app-key-dropbox
DROPBOX_APP_SECRET=tu-app-secret-dropbox
DROPBOX_REDIRECT_URI=http://localhost:8080/oauth2/callback

# Server
HOST=0.0.0.0
PORT=8080

# Solo para entorno local (no se usa en Cloud Run)
GOOGLE_APPLICATION_CREDENTIALS=/ruta/a/tu/sa_key.json
```

En **Cloud Run**, no se usa `GOOGLE_APPLICATION_CREDENTIALS`: la app se autentica usando la Service Account asignada al servicio.

---

### 3. Configuración de Google Cloud

#### 3.1. Crear Service Account para el servicio

```bash
gcloud iam service-accounts create secret-manager-sa \
    --display-name="AccessTokenDropbox Service Account"
```

Asignar permisos mínimos necesarios (Secret Manager):

```bash
gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:secret-manager-sa@[PROJECT_ID].iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"

gcloud projects add-iam-policy-binding [PROJECT_ID] \
  --member="serviceAccount:secret-manager-sa@[PROJECT_ID].iam.gserviceaccount.com" \
  --role="roles/secretmanager.secretVersionAdder"
```

#### 3.2. Secrets para llaves de la app/API

Recomendado: guardar las claves sensibles en Secret Manager:

```bash
# API secret del servicio (firma)
echo -n "tu-api-secret-key" | gcloud secrets create api-secret-key --data-file=-

# App key de Dropbox
echo -n "tu-dropbox-app-key" | gcloud secrets create dropbox-app-key --data-file=-

# App secret de Dropbox
echo -n "tu-dropbox-app-secret" | gcloud secrets create dropbox-app-secret --data-file=-
```

El secreto que almacenará el token se llama (por ejemplo):

```text
dropbox-access-token
```

> Este secreto es gestionado por el servicio: guarda `access_token`, `refresh_token` y fechas.
> Lo inicializas una sola vez con `/api/v1/token/initialize`.

---

### 4. Configuración de Dropbox

1. Ve a [Dropbox App Console](https://www.dropbox.com/developers/apps).
2. Crea una nueva app (Scoped App) o usa una existente.
3. En la configuración de la app:

   * Copia el **App key** y **App secret**.

   * Configura el **Redirect URI** (en modo local):

     ```text
     http://localhost:8080/oauth2/callback
     ```

   * Selecciona los scopes/permisos necesarios (por ejemplo, lectura/escritura de archivos según uso).
4. Para el flujo OAuth 2.0:

   * Generarás un `authorization_code` usando la URL de autorización.
   * Ese `authorization_code` se usará una sola vez para inicializar el token en Secret Manager.

---

## Instalación y Ejecución Local

### 1. Instalación

```bash
# Clonar el repositorio
cd accesstokendropbox

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# En Windows:
venv\Scripts\activate
# En Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

### 2. Ejecutar la aplicación

```bash
# Si usas Service Account en local:
# (Solo si no estás usando ADC de gcloud)
export GOOGLE_APPLICATION_CREDENTIALS="path/to/sa_key.json"

# Ejecutar la aplicación
uvicorn app.main:app --reload --host 0.0.0.0 --port 8080
```

La aplicación estará disponible en `http://localhost:8080` y la documentación en `http://localhost:8080/docs`.

---

## Inicializar el Token (Primera vez)

Este paso se hace una sola vez por proyecto/cuenta de Dropbox para guardar el `access_token` + `refresh_token` en Secret Manager.

### 1. Obtener `authorization_code` desde Dropbox

1. Construye la URL de autorización (ejemplo):

   ```text
   https://www.dropbox.com/oauth2/authorize?client_id=TU_APP_KEY&response_type=code&token_access_type=offline&redirect_uri=http%3A%2F%2Flocalhost%3A8080%2Foauth2%2Fcallback
   ```

2. Abre esa URL en el navegador.

3. Inicia sesión y acepta los permisos.

4. Dropbox te redirigirá a algo como:

   ```text
   http://localhost:8080/oauth2/callback?code=AAAAA_BBBBB_CCCCC&state=...
   ```

5. Copia el valor de `code=...` → **ese es el `authorization_code`** (solo sirve una vez y expira rápido).

### 2. Llamar al endpoint `/api/v1/token/initialize`

El endpoint actual recibe los parámetros como **query params**:

```bash
curl -X POST "http://localhost:8080/api/v1/token/initialize?authorization_code=CODIGO_DE_AUTORIZACION&signature=tu-api-secret-key"
```

* `authorization_code`: el `code` obtenido en el paso anterior.
* `signature`: debe coincidir con `API_SECRET_KEY`.

También puedes hacerlo desde Swagger UI:

1. Ir a `http://localhost:8080/docs`.
2. Buscar `POST /api/v1/token/initialize`.
3. Dar click en **Try it out**.
4. Llenar:

   * `authorization_code`: el código de Dropbox.
   * `signature`: tu `API_SECRET_KEY`.
5. Ejecutar.

Si todo sale bien:

* El servicio obtendrá `access_token` + `refresh_token` desde Dropbox.
* Guardará el token en Secret Manager (`dropbox-access-token`).
* Responderá con un `TokenResponse` y `refreshed: false`.

> A partir de aquí, **no necesitas volver a inicializar** mientras no borres el secreto ni revoques la app en Dropbox.

---

## Uso de la API

### 1. Health Check

```bash
curl "http://localhost:8080/health"
```

Respuesta:

```json
{
  "status": "healthy",
  "service": "AccessTokenDropbox",
  "version": "1.0.0"
}
```

### 2. Obtener Token Válido

```bash
curl -X POST "http://localhost:8080/api/v1/token" \
  -H "Content-Type: application/json" \
  -d '{
    "signature": "tu-api-secret-key",
    "service": "mi_servicio"
  }'
```

Ejemplo de respuesta:

```json
{
  "access_token": "sl.xxxxxxxxxxxxx",
  "expires_at": "2025-11-18T23:58:37.051159",
  "token_type": "bearer",
  "refreshed": false
}
```

### 3. Forzar Actualización de Token

```bash
curl -X POST "http://localhost:8080/api/v1/token/refresh?signature=tu-api-secret-key"
```

* Fuerza el uso del `refresh_token` para obtener un nuevo `access_token`.
* Actualiza el secreto en Secret Manager (nueva versión).
* Devuelve un `TokenResponse` con `refreshed: true`.

### 4. Obtener Información del Token

```bash
curl "http://localhost:8080/api/v1/token/info?signature=tu-api-secret-key"
```

Ejemplo de respuesta:

```json
{
  "exists": true,
  "created_at": "2025-11-18T19:58:37.051159",
  "updated_at": "2025-11-18T19:58:37.051159",
  "expires_at": "2025-11-18T23:58:37.051159",
  "is_expired": false,
  "is_about_to_expire": false,
  "status": "valid"
}
```

---

## Deployment en Google Cloud Run (Artifact Registry)

### 1. Crear repositorio en Artifact Registry (una sola vez)

```bash
gcloud artifacts repositories create ai \
  --repository-format=docker \
  --location=us-central1 \
  --description="Docker repo for AccessTokenDropbox and related services"
```

### 2. Build + Deploy (ejemplo en Bash)

```bash
PROJECT_ID="tu-proyecto-gcp"
REGION="us-central1"
SERVICE="accesstokendropbox"
REPO="ai"
TAG=$(date +%Y%m%d-%H%M%S)
IMAGE="us-central1-docker.pkg.dev/$PROJECT_ID/$REPO/$SERVICE:$TAG"

# 1) Build + push
gcloud config set project "$PROJECT_ID"
gcloud builds submit --tag "$IMAGE"

# 2) Deploy a Cloud Run
gcloud run deploy "$SERVICE" \
  --image "$IMAGE" \
  --platform managed \
  --region "$REGION" \
  --allow-unauthenticated \
  --service-account "secret-manager-sa@$PROJECT_ID.iam.gserviceaccount.com" \
  --memory 512Mi \
  --cpu 1 \
  --timeout 60s \
  --set-env-vars "APP_NAME=AccessTokenDropbox,DEBUG=False,LOG_LEVEL=INFO,AUTH_MODE=simple,GCP_PROJECT_ID=$PROJECT_ID,SECRET_NAME=dropbox-access-token" \
  --set-secrets "API_SECRET_KEY=api-secret-key:latest,DROPBOX_APP_KEY=dropbox-app-key:latest,DROPBOX_APP_SECRET=dropbox-app-secret:latest"
```

Una vez desplegado, el comando mostrará la URL pública, por ejemplo:

```text
https://accesstokendropbox-xxxxx-uc.a.run.app
```

Puedes usar esa URL en lugar de `http://localhost:8080`:

```bash
curl -X POST "https://accesstokendropbox-xxxxx-uc.a.run.app/api/v1/token" \
  -H "Content-Type: application/json" \
  -d '{
    "signature": "tu-api-secret-key",
    "service": "mi_servicio"
  }'
```

> ⚠️ Mientras no borres el secreto `dropbox-access-token` ni revoques la app en Dropbox, **no necesitas volver a llamar `/api/v1/token/initialize`**.
> El servicio usará el `refresh_token` para mantener el token siempre válido.

---

## Testing

```bash
# Instalar dependencias de testing
pip install pytest pytest-cov pytest-asyncio httpx

# Ejecutar tests
pytest tests/ -v

# Con coverage
pytest tests/ --cov=app --cov-report=html
```

---

## Monitoreo y Logs

### Ver logs en Cloud Run

```bash
gcloud run services logs read accesstokendropbox --region us-central1
```

### Métricas en Cloud Console

* Cloud Console → Cloud Run → `accesstokendropbox` → **Métricas**.

---

## Seguridad

* **Autenticación**: Todas las solicitudes a `/api/v1/*` requieren una firma válida.
* **Secrets**: Credenciales y tokens almacenados en Secret Manager.
* **Service Account**: Principio de menor privilegio (solo permisos necesarios).
* **HTTPS**: Todo el tráfico en Cloud Run se sirve sobre HTTPS.
* **Non-root user**: El contenedor puede ejecutarse con usuario no privilegiado (según Dockerfile).

---

## Modos de Autenticación

### Simple Mode (recomendado para empezar)

```env
AUTH_MODE=simple
API_SECRET_KEY=tu-clave-secreta
```

El cliente envía directamente la clave secreta como `signature`.

### HMAC Mode (para producción más estricta)

```env
AUTH_MODE=hmac
ALLOWED_SIGNATURES=signature1,signature2,signature3
```

El cliente genera una firma HMAC-SHA256 basada en datos y clave secreta.
(La implementación concreta de HMAC depende de tu `AuthService`.)

---

## Troubleshooting

### Error: `"No token found in Secret Manager"`

* Verifica que el secreto `dropbox-access-token` existe.
* Verifica que la Service Account tiene `secretAccessor` y `secretVersionAdder`.
* Inicializa el token usando `/api/v1/token/initialize` (local).

### Error: `"Invalid signature"` / `401 Unauthorized`

* Verifica que `API_SECRET_KEY` en el cliente coincide con la del servidor.
* Verifica que `AUTH_MODE` está en `simple` (o que estás construyendo bien la firma en modo HMAC).

### Error: `"invalid_grant"` al inicializar

* El `authorization_code` se usó dos veces o expiró.
* El `redirect_uri` usado en `get_initial_token` debe coincidir EXACTAMENTE con el configurado en Dropbox y usado en la URL de autorización.

---

## Contribución

1. Haz fork del repositorio.
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`).
3. Haz commit de tus cambios (`git commit -m 'Add some AmazingFeature'`).
4. Haz push de la rama (`git push origin feature/AmazingFeature`).
5. Abre un Pull Request.

---

## Licencia

Este proyecto es privado y de uso interno.

---

## Contacto

Para preguntas o soporte, contacta al equipo de desarrollo / eficiencia operativa.

---

## Próximas Mejoras

* [ ] Implementar caché en memoria para reducir llamadas a Secret Manager.
* [ ] Agregar métricas personalizadas en Cloud Monitoring.
* [ ] Implementar rate limiting.
* [ ] Agregar soporte para múltiples proveedores (no solo Dropbox).
* [ ] Implementar audit logging detallado.
* [ ] Agregar tests de integración end-to-end.
* [ ] Implementar circuit breaker para APIs externas.
