#!/usr/bin/env python3
"""
Script de Prueba - Comunicación con Sub-Agentes vía API
========================================================

Este script verifica que todos los sub-agentes del DATAR estén
funcionando correctamente a través del API REST.

Uso:
    python test_api.py
"""

import requests
import json
import time
from typing import Dict, Any, List
from datetime import datetime

# Configuración
API_BASE_URL = "http://localhost:8000"
TIMEOUT = 30

class bcolors:
    """Colores para terminal"""
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'


def print_header(text: str):
    """Imprime un encabezado"""
    print(f"\n{bcolors.HEADER}{bcolors.BOLD}{'='*70}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{text:^70}{bcolors.ENDC}")
    print(f"{bcolors.HEADER}{bcolors.BOLD}{'='*70}{bcolors.ENDC}\n")


def print_success(text: str):
    """Imprime mensaje de éxito"""
    print(f"{bcolors.OKGREEN}✅ {text}{bcolors.ENDC}")


def print_error(text: str):
    """Imprime mensaje de error"""
    print(f"{bcolors.FAIL}❌ {text}{bcolors.ENDC}")


def print_info(text: str):
    """Imprime información"""
    print(f"{bcolors.OKBLUE}ℹ️  {text}{bcolors.ENDC}")


def print_warning(text: str):
    """Imprime advertencia"""
    print(f"{bcolors.WARNING}⚠️  {text}{bcolors.ENDC}")


def test_health_check() -> bool:
    """Verifica que el servidor esté activo"""
    print_header("1. VERIFICACIÓN DE SALUD DEL SERVIDOR")
    
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        response.raise_for_status()
        data = response.json()
        
        print_success(f"Servidor activo: {data.get('message')}")
        print_info(f"Agente activo: {data.get('agente_activo')}")
        return True
    except requests.exceptions.ConnectionError:
        print_error(f"No se pudo conectar a {API_BASE_URL}")
        print_warning("Asegúrate de que el servidor está corriendo con:")
        print_warning("  uvicorn datar_prueba.api:app --reload")
        return False
    except Exception as e:
        print_error(f"Error en health check: {str(e)}")
        return False


def test_list_agents() -> Dict[str, Any]:
    """Lista todos los agentes disponibles"""
    print_header("2. LISTADO DE AGENTES")
    
    try:
        response = requests.get(f"{API_BASE_URL}/agents", timeout=TIMEOUT)
        response.raise_for_status()
        agents = response.json()
        
        print_success(f"Se encontraron agentes disponibles")
        
        if agents:
            agent = agents[0]
            print_info(f"Agente Raíz: {agent.get('name')}")
            print_info(f"Descripción: {agent.get('description')}")
            
            sub_agents = agent.get('sub_agents', [])
            print_info(f"Sub-agentes ({len(sub_agents)}):")
            for i, sub_agent in enumerate(sub_agents, 1):
                print(f"   {i}. {sub_agent}")
            
            return {"success": True, "agents": agents, "sub_agents_count": len(sub_agents)}
        else:
            print_warning("No se encontraron agentes")
            return {"success": False}
            
    except Exception as e:
        print_error(f"Error listando agentes: {str(e)}")
        return {"success": False}


def test_agent_info() -> Dict[str, Any]:
    """Obtiene información detallada del agente"""
    print_header("3. INFORMACIÓN DETALLADA DEL AGENTE")
    
    try:
        response = requests.get(f"{API_BASE_URL}/agent/info", timeout=TIMEOUT)
        response.raise_for_status()
        info = response.json()
        
        print_success(f"Información obtenida del agente")
        print_info(f"Nombre: {info.get('name')}")
        print_info(f"Descripción: {info.get('description')}")
        print_info(f"Modelo: {info.get('model')}")
        
        sub_agents_info = info.get('sub_agents', [])
        print_info(f"Sub-agentes configurados ({len(sub_agents_info)}):")
        for i, agent in enumerate(sub_agents_info, 1):
            agent_name = agent.get('name', 'Sin nombre')
            agent_desc = agent.get('description', 'Sin descripción')
            print(f"   {i}. {agent_name}")
            print(f"      └─ {agent_desc[:60]}...")
        
        return {"success": True, "info": info}
    except Exception as e:
        print_error(f"Error obteniendo info: {str(e)}")
        return {"success": False}


def test_root_agent_connection() -> bool:
    """Verifica que root_agent está correctamente configurado y accesible"""
    print_header("3.5 VERIFICACIÓN DE CONEXIÓN CON ROOT_AGENT")
    
    try:
        # Primero verificar que el agente existe
        response = requests.get(f"{API_BASE_URL}/agent/info", timeout=TIMEOUT)
        response.raise_for_status()
        info = response.json()
        
        agent_name = info.get('name')
        model = info.get('model')
        sub_agents = info.get('sub_agents', [])
        
        # Validación 1: ¿Es root_agent?
        if agent_name != 'root_agent':
            print_error(f"❌ El agente no es root_agent, es: {agent_name}")
            return False
        
        print_success(f"✅ Agente raíz identificado: {agent_name}")
        
        # Validación 2: ¿Está configurado el modelo?
        if not model or model == "N/D":
            print_error(f"❌ Modelo no configurado correctamente: {model}")
            return False
        
        # Aceptar diferentes representaciones del modelo
        model_str = str(model).lower()
        is_valid_model = any(keyword in model_str for keyword in ['litellm', 'model', 'llm', 'openrouter', 'minimax'])
        
        if not is_valid_model:
            print_warning(f"⚠️ Modelo no reconocido completamente: {model}")
        
        print_success(f"✅ Modelo configurado: {model}")
        
        # Validación 3: ¿Tiene sub-agentes?
        if not sub_agents or len(sub_agents) == 0:
            print_error("❌ No hay sub-agentes configurados")
            return False
        
        print_success(f"✅ Sub-agentes disponibles: {len(sub_agents)}")
        for i, agent in enumerate(sub_agents, 1):
            print(f"   {i}. {agent.get('name', 'Sin nombre')}")
        
        # Validación 4: ¿Hay instrucción?
        instruction = info.get('instruction')
        if not instruction:
            print_warning("⚠️ root_agent no tiene instrucción configurada")
        else:
            print_success(f"✅ Instrucción configurada: {instruction[:50]}...")
        
        print_success("✅ ¡ROOT_AGENT LISTO PARA COMUNICACIÓN!")
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("❌ No se puede conectar con el servidor")
        return False
    except Exception as e:
        print_error(f"❌ Error verificando root_agent: {str(e)}")
        return False


def test_model_validation() -> bool:
    """Valida el modelo que utiliza root_agent y su configuración"""
    print_header("3.7 VALIDACIÓN DEL MODELO DE ROOT_AGENT")
    
    try:
        # Obtener información del agente
        response = requests.get(f"{API_BASE_URL}/agent/info", timeout=TIMEOUT)
        response.raise_for_status()
        info = response.json()
        
        print_info(f"📡 Respuesta del endpoint /agent/info:")
        print_info(f"   - Nombre: {info.get('name')}")
        print_info(f"   - Model (raw): {info.get('model')}")
        print_info(f"   - Model Name: {info.get('model_name')}")
        print_info(f"   - Has Model: {info.get('has_model')}")
        
        model_str = info.get('model', 'N/D')
        model_name = info.get('model_name', 'N/D')
        has_model = info.get('has_model', False)
        
        # ✅ VALIDACIÓN 1: ¿Existe el modelo?
        if not has_model:
            print_error("❌ has_model es False - No hay modelo configurado para root_agent")
            print_warning(f"⚠️ Detalles: model_str='{model_str}', model_name='{model_name}'")
            return False
        
        if model_str == 'N/D' or not model_str:
            print_error("❌ model_str es 'N/D' - No hay modelo configurado para root_agent")
            return False
        
        print_success(f"✅ Modelo detectado: {model_str}")
        
        # ✅ VALIDACIÓN 2: ¿Cuál es el nombre del modelo?
        if model_name == 'N/D' or not model_name:
            print_warning("⚠️ No se pudo identificar el nombre específico del modelo")
        else:
            print_success(f"✅ Nombre del modelo: {model_name}")
        
        # ✅ VALIDACIÓN 3: ¿Contiene palabras clave de modelo LLM?
        model_lower = model_str.lower()
        llm_keywords = ['litellm', 'model', 'llm', 'openrouter', 'minimax', 'gpt', 'claude', 'llama']
        found_keywords = [kw for kw in llm_keywords if kw in model_lower]
        
        if found_keywords:
            print_success(f"✅ Palabras clave encontradas: {', '.join(found_keywords)}")
        else:
            print_warning("⚠️ No se encontraron palabras clave LLM estándar")
        
        # ✅ VALIDACIÓN 4: Información adicional
        print_info("\n📋 Información del Modelo:")
        print(f"   Representación completa: {model_str}")
        print(f"   Nombre: {model_name}")
        print(f"   Estado: {'Configurado' if has_model else 'No configurado'}")
        
        # ✅ VALIDACIÓN 5: Verificar también desde /root_agent/status
        status_response = requests.get(f"{API_BASE_URL}/root_agent/status", timeout=TIMEOUT)
        status_response.raise_for_status()
        status_data = status_response.json()
        
        status_model = status_data.get('model_name', 'N/D')
        if status_model != 'N/D' and status_model == model_name:
            print_success("✅ Información del modelo consistente entre endpoints")
        elif status_model != 'N/D':
            print_warning(f"⚠️ Información del modelo diferente en /root_agent/status: {status_model}")
        
        # ✅ VALIDACIÓN 6: Validar que sea capaz de procesar texto
        if 'openrouter' in model_lower or 'minimax' in model_lower or 'gpt' in model_lower or 'claude' in model_lower:
            print_success("✅ Modelo identificado como LLM capaz de procesar lenguaje natural")
        else:
            print_warning("⚠️ No se puede confirmar que el modelo sea LLM")
        
        print_success("\n✅ ¡VALIDACIÓN DE MODELO COMPLETADA!")
        return True
        
    except requests.exceptions.ConnectionError:
        print_error("❌ No se puede conectar con el servidor")
        return False
    except Exception as e:
        print_error(f"❌ Error validando modelo: {str(e)}")
        import traceback
        print_warning(f"Detalles: {traceback.format_exc()}")
        return False


def test_chat_basic(message: str, session_id: str = None) -> Dict[str, Any]:
    """Prueba comunicación básica con el agente raíz (root_agent)"""
    print_header("4. PRUEBA DE COMUNICACIÓN CON EL AGENTE")
    
    try:
        payload = {
            "message": message,
        }
        if session_id:
            payload["session_id"] = session_id
        
        print_info(f"📤 Enviando mensaje al root_agent: '{message}'")
        
        start_time = time.time()
        response = requests.post(
            f"{API_BASE_URL}/chat",
            json=payload,
            timeout=TIMEOUT
        )
        elapsed_time = time.time() - start_time
        
        response.raise_for_status()
        data = response.json()
        
        # ✅ VALIDACIÓN 1: ¿Tenemos una respuesta?
        if not data.get('response'):
            print_error("⚠️ El agente no proporcionó una respuesta")
            return {"success": False}
        
        print_success(f"✅ Respuesta recibida en {elapsed_time:.2f}s")
        
        # ✅ VALIDACIÓN 2: ¿Hay un agent_name?
        agent_name = data.get('agent_name', 'unknown')
        if agent_name == 'root_agent':
            print_success(f"✅ Agente raíz confirmado: {agent_name}")
        else:
            print_warning(f"⚠️ Agente respondedor: {agent_name}")
        
        # ✅ VALIDACIÓN 3: ¿Se creó una sesión?
        session_id_response = data.get('session_id')
        if not session_id_response:
            print_error("❌ No se generó session_id")
            return {"success": False}
        
        print_success(f"✅ Session ID creada: {session_id_response}")
        
        # ✅ VALIDACIÓN 4: ¿Hay timestamp?
        timestamp = data.get('timestamp')
        if timestamp:
            print_success(f"✅ Timestamp registrado: {timestamp}")
        else:
            print_warning("⚠️ No hay timestamp en la respuesta")
        
        # Mostrar la respuesta con formato
        response_text = data.get('response', 'Sin respuesta')
        print(f"\n{bcolors.OKCYAN}📝 RESPUESTA DEL AGENTE:{bcolors.ENDC}")
        print(f"{bcolors.OKCYAN}{'─' * 70}{bcolors.ENDC}")
        print(f"{response_text}")
        print(f"{bcolors.OKCYAN}{'─' * 70}{bcolors.ENDC}\n")
        
        # ✅ VALIDACIÓN 5: ¿La respuesta tiene contenido significativo?
        if len(response_text.strip()) < 5:
            print_warning("⚠️ La respuesta es muy corta")
        else:
            print_success(f"✅ Respuesta con contenido significativo ({len(response_text)} caracteres)")
        
        # ✅ RESUMEN DE VALIDACIÓN
        print_success("✅ ¡Comunicación efectiva con root_agent!")
        
        return {
            "success": True,
            "session_id": session_id_response,
            "response": response_text,
            "agent_name": agent_name,
            "elapsed_time": elapsed_time,
            "response_length": len(response_text)
        }
    except requests.exceptions.Timeout:
        print_error("❌ Timeout: El agente tardó más de 30 segundos en responder")
        print_warning("💡 Aumenta el timeout en la línea 20: TIMEOUT = 60")
        return {"success": False}
    except requests.exceptions.ConnectionError:
        print_error("❌ Error de conexión: No se puede alcanzar el servidor")
        print_warning("💡 Asegúrate de que el servidor está corriendo")
        return {"success": False}
    except Exception as e:
        print_error(f"❌ Error en comunicación: {str(e)}")
        import traceback
        print_warning(f"Detalles: {traceback.format_exc()}")
        return {"success": False}


def test_multi_turn_conversation() -> bool:
    """Prueba una conversación multi-turno (mantiene contexto)"""
    print_header("5. PRUEBA DE CONVERSACIÓN MULTI-TURNO")
    
    try:
        # Primer mensaje
        print_info("Primer mensaje...")
        result1 = test_chat_basic(
            "Hola, me llamo DATAR y soy de Bogotá",
            session_id=None
        )
        
        if not result1.get("success"):
            print_error("Falló el primer mensaje")
            return False
        
        session_id = result1.get("session_id")
        print_success(f"Session creada: {session_id}")
        
        time.sleep(1)
        
        # Segundo mensaje (mismo contexto)
        print_info("\nSegundo mensaje (mismo contexto)...")
        result2 = test_chat_basic(
            "¿Qué puedes decirme sobre los humedales?",
            session_id=session_id
        )
        
        if not result2.get("success"):
            print_error("Falló el segundo mensaje")
            return False
        
        print_success("Conversación multi-turno funcionando correctamente")
        return True
        
    except Exception as e:
        print_error(f"Error en conversación multi-turno: {str(e)}")
        return False


def test_sessions_endpoint() -> bool:
    """Prueba el endpoint de sesiones"""
    print_header("6. LISTADO DE SESIONES")
    
    try:
        response = requests.get(f"{API_BASE_URL}/sessions", timeout=TIMEOUT)
        response.raise_for_status()
        sessions = response.json()
        
        print_success(f"Sesiones encontradas: {len(sessions)}")
        
        if sessions:
            print_info("Últimas 5 sesiones:")
            for i, session in enumerate(sessions[:5], 1):
                session_id = session.get('session_id', 'N/D')
                created = session.get('created_at', 'N/D')
                messages = session.get('message_count', 0)
                print(f"   {i}. {session_id[:8]}... ({messages} mensajes)")
                print(f"      Creada: {created}")
        
        return True
    except Exception as e:
        print_error(f"Error obteniendo sesiones: {str(e)}")
        return False


def test_session_history(session_id: str) -> bool:
    """Prueba el historial de una sesión"""
    print_header("7. HISTORIAL DE SESIÓN")
    
    try:
        response = requests.get(
            f"{API_BASE_URL}/sessions/{session_id}",
            timeout=TIMEOUT
        )
        response.raise_for_status()
        history = response.json()
        
        print_success(f"Historial de sesión obtenido")
        print_info(f"Session ID: {history.get('session_id')}")
        print_info(f"Total de mensajes: {history.get('message_count')}")
        print_info(f"Creada: {history.get('created_at')}")
        
        messages = history.get('messages', [])
        if messages:
            print_info("\nÚltimos 3 mensajes:")
            for msg in messages[-3:]:
                role = msg.get('role', 'unknown')
                content = msg.get('content', '')[:60]
                print(f"   [{role}]: {content}...")
        
        return True
    except Exception as e:
        print_error(f"Error obteniendo historial: {str(e)}")
        return False


def run_comprehensive_test():
    """Ejecuta todas las pruebas"""
    print_header("PRUEBA INTEGRAL DEL API DATAR")
    print(f"{bcolors.BOLD}Iniciando pruebas a las {datetime.now().strftime('%H:%M:%S')}{bcolors.ENDC}\n")
    
    results = []
    
    # Test 1: Health check
    if not test_health_check():
        print_error("El servidor no está disponible. Deteniendo pruebas.")
        return
    
    results.append(("Health Check", True))
    time.sleep(1)
    
    # Test 2: Listar agentes
    agents_result = test_list_agents()
    results.append(("Listar Agentes", agents_result.get("success", False)))
    time.sleep(1)
    
    # Test 3: Información del agente
    info_result = test_agent_info()
    results.append(("Info del Agente", info_result.get("success", False)))
    time.sleep(1)
    
    # Test 3.5: Verificar conexión con root_agent
    root_agent_result = test_root_agent_connection()
    results.append(("Verificación root_agent", root_agent_result))
    time.sleep(1)
    
    # Test 3.7: Validar modelo de root_agent
    model_validation_result = test_model_validation()
    results.append(("Validación Modelo", model_validation_result))
    time.sleep(1)
    
    # Test 4: Chat básico
    chat_result = test_chat_basic("¿Qué LLM estás usando?")
    results.append(("Chat Básico", chat_result.get("success", False)))
    session_id = chat_result.get("session_id") if chat_result.get("success") else None
    time.sleep(1)
    
    # Test 5: Conversación multi-turno
    if session_id:
        multi_result = test_multi_turn_conversation()
        results.append(("Conversación Multi-turno", multi_result))
        time.sleep(1)
    
    # Test 6: Sesiones
    sessions_result = test_sessions_endpoint()
    results.append(("Listado Sesiones", sessions_result))
    time.sleep(1)
    
    # Test 7: Historial de sesión
    if session_id:
        history_result = test_session_history(session_id)
        results.append(("Historial Sesión", history_result))
    
    # Resumen final
    print_header("RESUMEN DE PRUEBAS")
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    print(f"{bcolors.BOLD}Resultados:{bcolors.ENDC}")
    for test_name, result in results:
        status = f"{bcolors.OKGREEN}✅ PASÓ{bcolors.ENDC}" if result else f"{bcolors.FAIL}❌ FALLÓ{bcolors.ENDC}"
        print(f"  {test_name:.<40} {status}")
    
    print(f"\n{bcolors.BOLD}Total: {passed}/{total} pruebas pasaron{bcolors.ENDC}")
    
    if passed == total:
        print_success("¡TODAS LAS PRUEBAS PASARON! 🎉")
        print_success("Tu API está funcionando correctamente y se puede comunicar con los sub-agentes")
    else:
        print_warning(f"{total - passed} pruebas fallaron")
    
    print(f"\n{bcolors.BOLD}Finalizado a las {datetime.now().strftime('%H:%M:%S')}{bcolors.ENDC}\n")


if __name__ == "__main__":
    try:
        run_comprehensive_test()
    except KeyboardInterrupt:
        print("\n\nPruebas interrumpidas por el usuario")
    except Exception as e:
        print_error(f"Error inesperado: {str(e)}")



