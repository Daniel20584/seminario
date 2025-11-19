from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.responses import Response
from fastapi.middleware.cors import CORSMiddleware
import requests
import logging
logging.basicConfig(level=logging.WARNING)
import os

# Define la instancia de la aplicación FastAPI.
app = FastAPI(title="API Gateway Taller Microservicios")

# Configura CORS (Cross-Origin Resource Sharing).
# Esto es esencial para permitir que el frontend se comunique con el gateway.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen (ajustar en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crea un enrutador para las peticiones de los microservicios.
router = APIRouter(prefix="/api/v1")

# Define los microservicios y sus URLs.
# La URL debe coincidir con el nombre del servicio definido en docker-compose.yml.
# El puerto debe ser el del contenedor (ej. auth-service:8001).
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
    # TODO: Agrega los URLs de los otros microservicios de tu tema.
    # "service1_name": os.getenv("NAME1_SERVICE_URL", "http://service1-service:8002"),
    # "service2_name": os.getenv("NAME2_SERVICE_URL", "http://service2-service:8003"),
    # "service3_name": os.getenv("NAME3_SERVICE_URL", "http://service3-service:8004"),
}

# Timeout (seconds) para las llamadas HTTP entre servicios
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "3"))

# Add the remaining services to the SERVICES dictionary
SERVICES.update({
    "experiences": os.getenv("EXPERIENCES_SERVICE_URL", "http://service1-service:8002"),
    "reservations": os.getenv("RESERVATIONS_SERVICE_URL", "http://reservations-service:8004"),
    "ratings": os.getenv("RATINGS_SERVICE_URL", "http://ratings-service:8005"),
})

# Add the remaining services to the SERVICES dictionary
@router.get("/{service_name}/{path:path}")
async def forward_get(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found.")
    
    service_url = f"{SERVICES[service_name]}/{path}"
    
    try:
        response = requests.get(service_url, params=request.query_params, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to {service_name}: {e}")

# TODO: Implementa una ruta genérica para redirigir peticiones POST.
from fastapi import FastAPI, APIRouter, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import requests
import os

# Define la instancia de la aplicación FastAPI.
app = FastAPI(title="API Gateway Taller Microservicios")

# Configura CORS (Cross-Origin Resource Sharing).
# Esto es esencial para permitir que el frontend se comunique con el gateway.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Permite peticiones desde cualquier origen (ajustar en producción)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Crea un enrutador para las peticiones de los microservicios.
router = APIRouter(prefix="/api/v1")

# Define los microservicios y sus URLs.
# La URL debe coincidir con el nombre del servicio definido en docker-compose.yml.
# El puerto debe ser el del contenedor (ej. auth-service:8001).
SERVICES = {
    "auth": os.getenv("AUTH_SERVICE_URL", "http://auth-service:8001"),
}

# Timeout (seconds) para las llamadas HTTP entre servicios
REQUEST_TIMEOUT = float(os.getenv("REQUEST_TIMEOUT", "3"))

# Add the remaining services to the SERVICES dictionary
SERVICES.update({
    # experiences service container name is `experiences-service` in docker-compose
    "experiences": os.getenv("EXPERIENCES_SERVICE_URL", "http://experiences-service:8002"),
    "reservations": os.getenv("RESERVATIONS_SERVICE_URL", "http://reservations-service:8004"),
    "ratings": os.getenv("RATINGS_SERVICE_URL", "http://ratings-service:8005"),
})


@router.get("/{service_name}/{path:path}")
async def forward_get(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found.")
    
    service_url = f"{SERVICES[service_name]}/{path}"
    
    try:
        response = requests.get(service_url, params=request.query_params, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to {service_name}: {e}")


@router.post("/{service_name}/{path:path}")
async def forward_post(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found.")
    
    service_url = f"{SERVICES[service_name]}/{path}"
    
    try:
        # Intenta obtener JSON del body; si no es JSON (form data or empty), reenvía raw body or no body.
        try:
            body_json = await request.json()
            response = requests.post(service_url, json=body_json, timeout=REQUEST_TIMEOUT)
        except Exception:
            raw_body = await request.body()
            if raw_body:
                headers = {k: v for k, v in request.headers.items()}
                # Forward raw body preserving content-type header
                response = requests.post(service_url, data=raw_body, headers={"content-type": headers.get("content-type")}, timeout=REQUEST_TIMEOUT)
            else:
                response = requests.post(service_url, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to {service_name}: {e}")


@router.get("/experiences/{path:path}")
async def forward_experiences(path: str, request: Request):
    service_url = f"{SERVICES['experiences']}/{path}"
    try:
        response = requests.get(service_url, params=request.query_params, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to experiences: {e}")


@router.get("/reservations/{path:path}")
async def forward_reservations(path: str, request: Request):
    service_url = f"{SERVICES['reservations']}/{path}"
    try:
        response = requests.get(service_url, params=request.query_params, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to reservations: {e}")


@router.get("/ratings/{path:path}")
async def forward_ratings(path: str, request: Request):
    service_url = f"{SERVICES['ratings']}/{path}"
    try:
        response = requests.get(service_url, params=request.query_params, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to ratings: {e}")


@router.post("/experiences/{path:path}")
async def forward_experiences_post(path: str, request: Request):
    service_url = f"{SERVICES['experiences']}/{path}"
    try:
        body_json = await request.json()
        response = requests.post(service_url, json=body_json, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding request to experiences: {e}")


@router.put("/{service_name}/{path:path}")
async def forward_put(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found.")
    service_url = f"{SERVICES[service_name]}/{path}"
    try:
        body = await request.json()
        response = requests.put(service_url, json=body, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding PUT to {service_name}: {e}")


@router.delete("/{service_name}/{path:path}")
async def forward_delete(service_name: str, path: str, request: Request):
    if service_name not in SERVICES:
        raise HTTPException(status_code=404, detail=f"Service '{service_name}' not found.")
    service_url = f"{SERVICES[service_name]}/{path}"
    try:
        response = requests.delete(service_url, timeout=REQUEST_TIMEOUT)
        content = response.content
        content_type = response.headers.get("content-type", "application/json")
        return Response(content=content, status_code=response.status_code, media_type=content_type)
    except requests.exceptions.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Error forwarding DELETE to {service_name}: {e}")


# Incluye el router en la aplicación principal.
app.include_router(router)

# Endpoint de salud para verificar el estado del gateway.
@app.get("/health")
def health_check():
    return {"status": "ok", "message": "API Gateway is running."}


