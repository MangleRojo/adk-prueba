"""
Servidor FastAPI para DATAR - Sistema Agéntico Ambiental
Estructura Ecológica Principal de Bogotá
"""

import os
import uvicorn
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime
import uuid

# PASO 1: Importar el agente raíz
from .agent import root_agent
from . import config

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
    
    return {
        "name": root_agent.name,
        "description": root_agent.description,
        "instruction": root_agent.instruction,
        "model": root_agent.model,
        "sub_agents": sub_agents_info
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
        # Construir el contexto con el historial de la sesión
        messages = []
        
        # Agregar la instrucción del agente como mensaje del sistema
        if hasattr(root_agent, 'instruction') and root_agent.instruction:
            messages.append({
                "role": "system",
                "content": root_agent.instruction
            })
        
        # Agregar historial de la sesión si existe
        if session_id in sessions_store and sessions_store[session_id]["messages"]:
            for msg in sessions_store[session_id]["messages"]:
                # Solo agregar mensajes de usuario y asistente, no errores
                if msg["role"] in ["user", "assistant"]:
                    messages.append({
                        "role": msg["role"],
                        "content": msg["content"]
                    })
        
        # Usar el método de generate del agente si está disponible
        # De lo contrario, devolver un mensaje de ejemplo
        try:
            if hasattr(root_agent, 'generate'):
                response_text = root_agent.generate(
                    request.message,
                    system_instruction=root_agent.instruction if hasattr(root_agent, 'instruction') else None
                )
            elif hasattr(root_agent, '__call__'):
                response_text = root_agent(request.message)
            else:
                # Respuesta de fallback si el agente no tiene métodos esperados
                response_text = f"Echo: {request.message}"
        except Exception as agent_error:
            # Si falla la generación, devolver error descriptivo
            raise agent_error
        
        # Guardar respuesta del agente en la sesión
        sessions_store[session_id]["messages"].append({
            "role": "assistant",
            "content": response_text,
            "timestamp": datetime.now().isoformat()
        })
        sessions_store[session_id]["last_activity"] = datetime.now().isoformat()
        
        return ChatResponse(
            response=response_text,
            agent_name=root_agent.name,
            session_id=session_id,
            timestamp=timestamp
        )
    except Exception as e:
        error_message = f"Error al procesar el mensaje: {str(e)}"
        
        # Guardar error en la sesión
        sessions_store[session_id]["messages"].append({
            "role": "error",
            "content": error_message,
            "timestamp": datetime.now().isoformat()
        })
        
        return ChatResponse(
            response=error_message,
            agent_name=root_agent.name,
            session_id=session_id,
            timestamp=timestamp
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