"""
Ejemplo de uso de la API DATAR
Demuestra cómo interactuar con los diferentes endpoints
"""

import httpx
import asyncio
import json
from typing import Optional


class DATARClient:
    """Cliente para interactuar con la API DATAR"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.session_id: Optional[str] = None
    
    async def health_check(self) -> dict:
        """Verificar que el servidor está funcionando"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/health")
            response.raise_for_status()
            return response.json()
    
    async def get_info(self) -> dict:
        """Obtener información general del API"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/")
            response.raise_for_status()
            return response.json()
    
    async def get_agent_info(self) -> dict:
        """Obtener información del agente principal"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/agent/info")
            response.raise_for_status()
            return response.json()
    
    async def send_message(self, message: str) -> dict:
        """Enviar un mensaje al agente"""
        async with httpx.AsyncClient() as client:
            payload = {
                "message": message,
                "session_id": self.session_id
            }
            response = await client.post(
                f"{self.base_url}/chat",
                json=payload
            )
            response.raise_for_status()
            data = response.json()
            # Guardar el session_id para próximos mensajes
            if not self.session_id:
                self.session_id = data.get("session_id")
            return data
    
    async def get_sessions(self) -> list:
        """Listar todas las sesiones activas"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/sessions")
            response.raise_for_status()
            return response.json()
    
    async def get_session_history(self, session_id: str) -> dict:
        """Obtener el historial de una sesión específica"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.base_url}/sessions/{session_id}")
            response.raise_for_status()
            return response.json()
    
    async def delete_session(self, session_id: str) -> dict:
        """Eliminar una sesión"""
        async with httpx.AsyncClient() as client:
            response = await client.delete(f"{self.base_url}/sessions/{session_id}")
            response.raise_for_status()
            return response.json()


async def main():
    """Función principal demostrando el uso de la API"""
    
    client = DATARClient()
    
    try:
        print("=" * 60)
        print("🤖 DATAR API - Cliente de Ejemplo")
        print("=" * 60)
        
        # 1. Verificar salud del servidor
        print("\n1️⃣  Verificando salud del servidor...")
        health = await client.health_check()
        print(f"   ✅ Estado: {health.get('status')}")
        print(f"   📊 Agente activo: {health.get('agente_activo')}")
        
        # 2. Obtener información del API
        print("\n2️⃣  Obteniendo información del API...")
        info = await client.get_info()
        print(f"   📝 Nombre: {info.get('nombre')}")
        print(f"   📍 Versión: {info.get('version')}")
        
        # 3. Obtener información del agente
        print("\n3️⃣  Obteniendo información del agente...")
        agent_info = await client.get_agent_info()
        print(f"   🤖 Nombre: {agent_info.get('name')}")
        print(f"   📖 Descripción: {agent_info.get('description')}")
        print(f"   🧠 Modelo: {agent_info.get('model')}")
        
        # 4. Enviar primer mensaje
        print("\n4️⃣  Enviando primer mensaje al agente...")
        message1 = "Hola, ¿cuál es tu nombre?"
        response1 = await client.send_message(message1)
        print(f"   👤 Usuario: {message1}")
        print(f"   🤖 Agente: {response1.get('response')}")
        print(f"   💾 Session ID: {response1.get('session_id')}")
        
        # 5. Enviar segundo mensaje (mantiene contexto)
        print("\n5️⃣  Enviando segundo mensaje (con contexto de sesión)...")
        message2 = "¿Cuáles son tus funciones principales?"
        response2 = await client.send_message(message2)
        print(f"   👤 Usuario: {message2}")
        print(f"   🤖 Agente: {response2.get('response')}")
        
        # 6. Listar sesiones activas
        print("\n6️⃣  Listando sesiones activas...")
        sessions = await client.get_sessions()
        print(f"   📊 Total de sesiones: {len(sessions)}")
        for session in sessions:
            print(f"     - ID: {session.get('session_id')}")
            print(f"       Mensajes: {session.get('message_count')}")
        
        # 7. Ver historial de sesión
        print("\n7️⃣  Ver historial de la sesión actual...")
        if client.session_id:
            history = await client.get_session_history(client.session_id)
            print(f"   📜 Total de mensajes: {history.get('message_count')}")
            for i, msg in enumerate(history.get('messages', []), 1):
                print(f"     {i}. [{msg.get('role')}]: {msg.get('content')[:80]}...")
        
        print("\n" + "=" * 60)
        print("✨ Ejemplo completado exitosamente!")
        print("=" * 60)
        
    except httpx.ConnectError:
        print("❌ Error: No se pudo conectar al servidor")
        print("   Asegúrate de que el servidor está ejecutándose en http://localhost:8000")
    except Exception as e:
        print(f"❌ Error: {str(e)}")


if __name__ == "__main__":
    print("\n🚀 Iniciando cliente DATAR...\n")
    asyncio.run(main())
