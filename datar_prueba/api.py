"""
Servidor FastAPI para DATAR - Sistema Agéntico Ambiental
Estructura Ecológica Principal de Bogotá
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from litellm import completion
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# PASO 1: Importar el agente raíz
from .agent import root_agent
from . import config

# Validar que root_agent está correctamente inicializado
if not root_agent:
    raise RuntimeError("❌ root_agent no pudo ser inicializado. Verifica datar_prueba/agent.py")

if root_agent.name != 'root_agent':
    print(f"⚠️  ADVERTENCIA: El nombre del agente es '{root_agent.name}', esperado 'root_agent'")
else:
    print(f"✅ root_agent inicializado correctamente: {root_agent.name}")

# PASO 2: Sistema de gestión de sesiones en memoria
# En producción, esto debería estar en una base de datos
sessions_store: Dict[str, Dict[str, Any]] = {}

# PASO 3: Configuración del servidor
AGENT_DIR = os.path.dirname(os.path.abspath(__file__))
SESSION_DB_URL = "sqlite:///memory.db"  # Base de datos para sesiones
ALLOWED_ORIGINS = [
    "http://localhost:5500",      # Frontend en desarrollo
    "http://127.0.0.1:5500",      # Alternativa localhost
    "http://localhost:3000",      # React/Next.js común
    "http://localhost:8000",      # Servidor de desarrollo
    "*"                           # Permitir todos los orígenes (en desarrollo)
]

# PASO 4: Crear la aplicación FastAPI
app = FastAPI(
    title="DATAR API",
    description="Sistema Agéntico para la Estructura Ecológica Principal de Bogotá",
    version="1.0.0"
)

# Configurar CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# PASO 5: Modelos Pydantic para requests/responses
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    
class ChatResponse(BaseModel):
    response: str
    agent_name: str
    session_id: str
    timestamp: str

class AgentInfo(BaseModel):
    name: str
    description: str
    sub_agents: List[str]

class SessionInfo(BaseModel):
    session_id: str
    created_at: str
    last_activity: str
    message_count: int
    
class SessionHistoryResponse(BaseModel):
    session_id: str
    messages: List[Dict[str, Any]]
    created_at: str
    message_count: int


def _as_serializable_dict(obj: Any) -> Any:
    """Convierte objetos con métodos de serialización en dicts simples."""
    if isinstance(obj, dict):
        return obj
    if hasattr(obj, "model_dump"):
        try:
            return obj.model_dump()
        except Exception:
            pass
    if hasattr(obj, "dict"):
        try:
            return obj.dict()
        except Exception:
            pass
    if hasattr(obj, "__dict__"):
        return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}
    return obj


def _flatten_content(content: Any) -> str:
    """Normaliza contenido potencialmente estructurado a texto plano."""
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts: List[str] = []
        for item in content:
            if isinstance(item, dict):
                text = item.get("text") or item.get("content") or ""
                parts.append(str(text))
            else:
                parts.append(str(item))
        return "".join(parts)
    return str(content)


def _resolve_litellm_params() -> Dict[str, Any]:
    """Obtiene la configuración del modelo LiteLLM a partir del agente o del entorno."""
    params: Dict[str, Any] = {}

    agent_model = getattr(root_agent, "model", None)
    if agent_model is not None:
        for attr in ("model", "api_key", "api_base", "temperature", "max_tokens" ):
            value = getattr(agent_model, attr, None)
            if value is not None:
                key = "model" if attr == "model" else attr
                params[key] = value

    if "model" not in params:
        params["model"] = getattr(config, "AGENT_MODEL", "gpt-3.5-turbo")

    if "api_key" not in params:
        params["api_key"] = (
            os.getenv("OPENROUTER_API_KEY")
            or os.getenv("LITELLM_API_KEY")
            or os.getenv("GOOGLE_API_KEY")
        )

    if "api_base" not in params:
        api_base_env = (
            os.getenv("LITELLM_API_BASE")
            or os.getenv("OPENROUTER_API_BASE")
            or os.getenv("LITELLM_API_URL")
        )
        if api_base_env:
            params["api_base"] = api_base_env

    return {k: v for k, v in params.items() if v is not None}


def _build_conversation(session_id: str) -> List[Dict[str, str]]:
    """Construye el historial de mensajes en formato compatible con LiteLLM."""
    conversation: List[Dict[str, str]] = []

    system_instruction = (
        getattr(root_agent, "instruction", None)
        or getattr(config, "AGENT_INSTRUCTION", None)
    )
    if system_instruction:
        conversation.append({"role": "system", "content": system_instruction})

    session_data = sessions_store.get(session_id)
    if session_data and session_data.get("messages"):
        for msg in session_data["messages"]:
            if msg.get("role") in ("user", "assistant"):
                conversation.append({
                    "role": msg["role"],
                    "content": msg["content"],
                })

    return conversation


def _extract_text_from_response(model_response: Any) -> str:
    """Extrae el texto de la primera respuesta del modelo LiteLLM."""
    if model_response is None:
        return "Sin respuesta del modelo"

    if isinstance(model_response, str):
        text = model_response.strip()
        return text if text else "Sin respuesta del modelo"

    # Intentar extraer como dict primero
    response_obj = _as_serializable_dict(model_response)
    choices = []

    if isinstance(response_obj, dict):
        choices = response_obj.get("choices") or []
    else:
        choices = getattr(model_response, "choices", []) or []

    if not choices and hasattr(model_response, "model_dump"):
        try:
            dumped = model_response.model_dump()
            choices = dumped.get("choices", []) if isinstance(dumped, dict) else []
        except Exception:
            pass

    if not choices:
        # Si no hay choices, intentar extraer el contenido directamente
        if hasattr(model_response, "content"):
            content = getattr(model_response, "content", "")
            if content:
                return _flatten_content(content).strip()
        return str(model_response).strip()

    first_choice = choices[0]
    first_choice = _as_serializable_dict(first_choice)

    if isinstance(first_choice, dict):
        message = first_choice.get("message")
        message = _as_serializable_dict(message)
        if isinstance(message, dict):
            content = message.get("content")
            if content:
                return _flatten_content(content).strip()

        fallback_text = first_choice.get("text") or first_choice.get("content")
        if fallback_text:
            return _flatten_content(fallback_text).strip()

    # Último intento: buscar en el objeto original
    if hasattr(model_response, "content") and model_response.content:
        return _flatten_content(model_response.content).strip()
    
    if hasattr(model_response, "text") and model_response.text:
        return _flatten_content(model_response.text).strip()

    return "Sin respuesta del modelo"


async def _generate_agent_reply(session_id: str) -> str:
    """Invoca LiteLLM de forma no bloqueante y retorna el texto de respuesta."""
    params = _resolve_litellm_params()

    if not params.get("model"):
        raise RuntimeError("Modelo de LiteLLM no configurado.")

    if not params.get("api_key"):
        raise RuntimeError(
            "No se encontró una API key válida para LiteLLM. Define OPENROUTER_API_KEY o LITELLM_API_KEY."
        )

    messages = _build_conversation(session_id)

    raw_response = await run_in_threadpool(
        completion,
        messages=messages,
        **params,
    )

    response_text = _extract_text_from_response(raw_response)
    return response_text.strip()


def _fallback_agent_reply(user_message: str) -> str:
    """Intento secundario usando las capacidades nativas del agente ADK."""
    system_instruction = getattr(root_agent, "instruction", None)
    try:
        if hasattr(root_agent, "generate"):
            raw = root_agent.generate(
                user_message,
                system_instruction=system_instruction,
            )
            return _extract_text_from_response(raw)
        if hasattr(root_agent, "__call__"):
            raw = root_agent(user_message)
            return _extract_text_from_response(raw)
    except Exception as e:
        pass
    
    # Si todo falla, retornar un mensaje informativo
    return f"[Sistema] El agente procesó tu mensaje pero la respuesta está vacía. Modelo: {getattr(root_agent, 'model', 'desconocido')}. Por favor, intenta de nuevo."

# PASO 6: Definir los endpoints del API

@app.get("/")
async def root():
    """Endpoint raíz - Información del API"""
    return {
        "nombre": "DATAR API",
        "descripcion": "Sistema Agéntico para la Estructura Ecológica Principal de Bogotá",
        "version": "1.0.0",
        "agente_principal": root_agent.name,
        "endpoints": {
            "raiz": "/",
            "salud": "/health",
            "root_agent_status": "/root_agent/status",
            "agentes": "/agents",
            "chat": "/chat",
            "info_agente": "/agent/info",
            "sesiones": "/sessions",
            "sesion_especifica": "/sessions/{session_id}",
            "eliminar_sesion": "DELETE /sessions/{session_id}",
            "docs": "/docs",
            "ejemplo": "/hello"
        }
    }

@app.get("/health")
async def health_check():
    """Endpoint de salud - Verificar que el servidor está funcionando"""
    return {
        "status": "healthy",
        "message": "DATAR está operativo",
        "agente_activo": root_agent.name,
        "database": SESSION_DB_URL
    }

@app.get("/agents", response_model=List[AgentInfo])
async def list_agents():
    """Lista todos los agentes disponibles"""
    sub_agent_names = []
    if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
        sub_agent_names = [agent.name for agent in root_agent.sub_agents]
    
    return [
        AgentInfo(
            name=root_agent.name,
            description=root_agent.description,
            sub_agents=sub_agent_names
        )
    ]

@app.get("/agent/info")
async def agent_info():
    """Información detallada del agente principal"""
    sub_agents_info = []
    if hasattr(root_agent, 'sub_agents') and root_agent.sub_agents:
        for agent in root_agent.sub_agents:
            sub_agents_info.append({
                "name": agent.name,
                "description": getattr(agent, 'description', 'Sin descripción')
            })
    
    # Obtener información del modelo
    model_info = getattr(root_agent, "model", None)
    model_str = str(model_info) if model_info else "N/D"
    model_name = "N/D"
    
    # Si el modelo existe, intentar extraer el nombre
    if model_info:
        # Buscar en los atributos del objeto
        possible_attrs = ['model', 'model_name', 'model_id', '_model', 'name']
        for attr in possible_attrs:
            if hasattr(model_info, attr):
                value = getattr(model_info, attr, None)
                if value and isinstance(value, str) and value != "N/D":
                    model_name = value
                    break
        
        # Si no encontró en atributos, intentar parsear del string
        if model_name == "N/D" and "model=" in model_str:
            try:
                # Parsear: model='openrouter/minimax/minimax-m2:free' ...
                start = model_str.find("model='") + len("model='")
                end = model_str.find("'", start)
                if start > len("model='") - 1 and end > start:
                    model_name = model_str[start:end]
            except Exception:
                pass
    
    return {
        "name": root_agent.name,
        "description": root_agent.description,
        "instruction": root_agent.instruction,
        "model": model_str,
        "model_name": model_name,
        "has_model": model_info is not None,
        "sub_agents": sub_agents_info,
    }

@app.post("/chat", response_model=ChatResponse)
async def chat_with_agent(request: ChatRequest):
    """
    Envía un mensaje al agente y recibe una respuesta.
    
    - **message**: El mensaje que quieres enviar al agente
    - **session_id**: (Opcional) ID de sesión para mantener contexto. Si no se proporciona, se crea uno nuevo.
    """
    # Validar que el mensaje no esté vacío
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="El mensaje no puede estar vacío")
    
    # Validar longitud del mensaje
    if len(request.message) > config.MAX_MESSAGE_LENGTH:
        raise HTTPException(
            status_code=400, 
            detail=f"El mensaje no puede exceder {config.MAX_MESSAGE_LENGTH} caracteres"
        )
    
    # Generar o usar session_id existente
    session_id = request.session_id or str(uuid.uuid4())
    timestamp = datetime.now().isoformat()
    
    # Inicializar sesión si no existe
    if session_id not in sessions_store:
        sessions_store[session_id] = {
            "created_at": timestamp,
            "messages": [],
            "last_activity": timestamp
        }
    
    # Guardar mensaje del usuario en la sesión
    sessions_store[session_id]["messages"].append({
        "role": "user",
        "content": request.message,
        "timestamp": timestamp
    })
    
    try:
        response_text = await _generate_agent_reply(session_id)
        if not response_text:
            raise ValueError("La respuesta del agente llegó vacía.")
    except Exception as agent_error:
        response_text = _fallback_agent_reply(request.message)
        error_details = str(agent_error).strip()
        if error_details and len(error_details) > 200:
            error_details = f"{error_details[:200]}..."
        fallback_note = "[fallback] LiteLLM no respondió, se usó una respuesta alternativa."
        if error_details:
            fallback_note = f"{fallback_note} Detalle: {error_details}"
        sessions_store[session_id]["messages"].append({
            "role": "system",
            "content": fallback_note,
            "timestamp": datetime.now().isoformat()
        })
    
    assistant_timestamp = datetime.now().isoformat()

    try:
        # Guardar respuesta del agente en la sesión
        sessions_store[session_id]["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": assistant_timestamp
        })
        sessions_store[session_id]["last_activity"] = datetime.now().isoformat()
    except Exception as e:
        error_message = f"Error al almacenar la respuesta del agente: {str(e)}"
        sessions_store[session_id]["messages"].append({
            "role": "error",
            "content": error_message,
            "timestamp": datetime.now().isoformat()
        })
        raise HTTPException(status_code=500, detail=error_message)

    response_text = response_text[:config.MAX_RESPONSE_LENGTH]

    return ChatResponse(
        response=response_text,
        agent_name=root_agent.name,
        session_id=session_id,
        timestamp=assistant_timestamp
    )

@app.get("/sessions", response_model=List[SessionInfo])
async def list_sessions():
    """Lista todas las sesiones activas"""
    sessions = []
    for session_id, data in sessions_store.items():
        sessions.append(SessionInfo(
            session_id=session_id,
            created_at=data["created_at"],
            last_activity=data["last_activity"],
            message_count=len(data["messages"])
        ))
    return sessions

@app.get("/sessions/{session_id}", response_model=SessionHistoryResponse)
async def get_session_history(session_id: str):
    """Obtiene el historial completo de una sesión"""
    if session_id not in sessions_store:
        return {
            "session_id": session_id,
            "messages": [],
            "created_at": "",
            "message_count": 0
        }
    
    session_data = sessions_store[session_id]
    return SessionHistoryResponse(
        session_id=session_id,
        messages=session_data["messages"],
        created_at=session_data["created_at"],
        message_count=len(session_data["messages"])
    )

@app.delete("/sessions/{session_id}")
async def delete_session(session_id: str):
    """Elimina una sesión específica"""
    if session_id in sessions_store:
        del sessions_store[session_id]
        return {"message": f"Sesión {session_id} eliminada exitosamente"}
    return {"message": f"Sesión {session_id} no encontrada"}

@app.get("/hello")
async def say_hello():
    """Endpoint de ejemplo - Saludo simple"""
    return {
        "hello": "world",
        "proyecto": "DATAR",
        "agente": root_agent.name
    }

@app.get("/root_agent/status")
async def root_agent_status():
    """Endpoint de diagnóstico - Verifica el estado de root_agent"""
    model_info = getattr(root_agent, "model", None)
    model_str = str(model_info) if model_info else "N/D"
    model_name = "N/D"
    
    if model_info:
        # Buscar en los atributos del objeto
        possible_attrs = ['model', 'model_name', 'model_id', '_model', 'name']
        for attr in possible_attrs:
            if hasattr(model_info, attr):
                value = getattr(model_info, attr, None)
                if value and isinstance(value, str) and value != "N/D":
                    model_name = value
                    break
        
        # Si no encontró en atributos, intentar parsear del string
        if model_name == "N/D" and "model=" in model_str:
            try:
                # Parsear: model='openrouter/minimax/minimax-m2:free' ...
                start = model_str.find("model='") + len("model='")
                end = model_str.find("'", start)
                if start > len("model='") - 1 and end > start:
                    model_name = model_str[start:end]
            except Exception:
                pass
    
    return {
        "status": "active",
        "agent_name": root_agent.name,
        "description": root_agent.description,
        "instruction": root_agent.instruction[:100] + "..." if root_agent.instruction and len(root_agent.instruction) > 100 else root_agent.instruction,
        "has_model": model_info is not None,
        "model": model_str,
        "model_name": model_name,
        "has_sub_agents": hasattr(root_agent, "sub_agents") and bool(root_agent.sub_agents),
        "sub_agents_count": len(root_agent.sub_agents) if hasattr(root_agent, "sub_agents") and root_agent.sub_agents else 0,
        "is_root_agent": root_agent.name == 'root_agent'
    }

# PASO 7: Punto de entrada (para ejecución directa)
if __name__ == "__main__":
    print("🌱 Iniciando DATAR - Sistema Agéntico Ambiental")
    print(f"📍 Agente Principal: {root_agent.name}")
    print(f"💾 Base de datos de sesiones: {SESSION_DB_URL}")
    print(f"🌐 Servidor escuchando en: http://0.0.0.0:8000")
    print(f"📚 Documentación disponible en: http://localhost:8000/docs")
    print(f"\n🔗 Endpoints disponibles:")
    print(f"   - GET    /                     (Información del API)")
    print(f"   - GET    /health               (Estado del servidor)")
    print(f"   - GET    /agents               (Lista de agentes)")
    print(f"   - GET    /agent/info           (Info detallada del agente)")
    print(f"   - POST   /chat                 (Chatear con el agente)")
    print(f"   - GET    /sessions             (Listar todas las sesiones)")
    print(f"   - GET    /sessions/{{id}}        (Ver historial de sesión)")
    print(f"   - DELETE /sessions/{{id}}        (Eliminar sesión)")
    print(f"   - GET    /hello                (Ejemplo)")
    
    uvicorn.run(
        app,
        host="0.0.0.0",      # Accesible desde cualquier interfaz de red
        port=8000,           # Puerto consistente con main.py
        log_level="info",    # Nivel de logging
        reload=False         # Auto-reload en desarrollo
    )