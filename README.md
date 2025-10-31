# 🤖 Datar API - Google ADK + FastAPI

API REST construida con **FastAPI** y **Google ADK** para interactuar con agentes IA basados en Gemini.

## 📋 Requisitos Previos

- Python 3.8+
- pip (gestor de paquetes)
- Clave de API de Google Gemini (opcional pero recomendado)

## 🚀 Instalación y Configuración

### 1. Crear un entorno virtual (recomendado)

```bash
python -m venv venv
source venv/bin/activate  # En Mac/Linux
# o en Windows:
# venv\Scripts\activate
```

### 2. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 3. Configurar variables de entorno (opcional)

```bash
# Crear un archivo .env en la raíz del proyecto
export GOOGLE_API_KEY="tu-clave-api-aqui"
```

## 🎯 Ejecutar la API

```bash
# Desde el directorio raíz del proyecto
python datar_prueba/main.py
```

La API estará disponible en: `http://localhost:8000`

### Documentación interactiva

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📡 Endpoints Disponibles

### 1. Health Check
Verificar que la API está funcionando:

```bash
curl -X GET "http://localhost:8000/health"
```

**Respuesta:**
```json
{
  "status": "healthy",
  "message": "API funcionando correctamente"
}
```

### 2. Chat con Agente
Enviar un mensaje al agente IA:

```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "¿Cuál es la capital de Francia?",
    "conversation_id": "conv_123"
  }'
```

**Respuesta:**
```json
{
  "response": "La capital de Francia es París.",
  "conversation_id": "conv_123",
  "status": "success"
}
```

### 3. Información de la API
Obtener información general:

```bash
curl -X GET "http://localhost:8000/"
```

## 📚 Estructura del Proyecto

```
adk-prueba/
├── datar_prueba/
│   ├── __init__.py          # Inicializador del módulo
│   ├── agent.py             # Configuración del agente (root_agent)
│   ├── api.py               # Definición de la API FastAPI
│   └── main.py              # Punto de entrada (ejecutar con uvicorn)
├── requirements.txt         # Dependencias del proyecto
└── README.md               # Este archivo
```

## 🔧 Estructura de la API

### Modelos de Datos

#### ChatRequest
```json
{
  "message": "string (1-2000 caracteres)",
  "conversation_id": "string (opcional)"
}
```

#### ChatResponse
```json
{
  "response": "string",
  "conversation_id": "string",
  "status": "string"
}
```

## 🛠️ Próximos Pasos (Mejoras)

- [ ] Agregar autenticación con API Key
- [ ] Implementar persistencia de conversaciones en BD
- [ ] Agregar manejo de múltiples agentes
- [ ] Agregar rate limiting
- [ ] Implementar logging y monitoreo
- [ ] Agregar pruebas unitarias
- [ ] Dockerizar la aplicación

## 📝 Ejemplo de Uso Completo

```python
import httpx
import asyncio

async def test_api():
    async with httpx.AsyncClient() as client:
        # Test health check
        response = await client.get("http://localhost:8000/health")
        print("Health:", response.json())
        
        # Test chat
        response = await client.post(
            "http://localhost:8000/chat",
            json={"message": "Hola, ¿cómo estás?"}
        )
        print("Chat:", response.json())

# Ejecutar
asyncio.run(test_api())
```

## ❓ Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'google.adk'"

**Solución:** Asegúrate de instalar las dependencias:
```bash
pip install -r requirements.txt
```

### Error: "GOOGLE_API_KEY not found"

**Solución:** Configura tu clave API de Google:
```bash
export GOOGLE_API_KEY="tu-clave-aqui"
```

### Puerto 8000 ya en uso

**Solución:** Modifica el puerto en `datar_prueba/main.py`:
```python
uvicorn.run(app, host="0.0.0.0", port=8001)  # Cambiar a otro puerto
```

## 📞 Soporte

Para reportar problemas o hacer sugerencias, crea un issue en el repositorio.

## 📄 Licencia

Ver archivo LICENSE en el directorio raíz.

