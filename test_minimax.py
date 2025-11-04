#!/usr/bin/env python3
"""
Test de Minimax - Diagnóstico
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("🧪 TEST DE RESPUESTA DEL MODELO MINIMAX")
print("=" * 70)

try:
    print("\n1️⃣ Enviando mensaje al modelo...")
    response = requests.post(
        f"{API_BASE_URL}/chat",
        json={"message": "Hola, ¿cuál es tu nombre?"},
        timeout=30
    )
    response.raise_for_status()
    
    data = response.json()
    
    print("\n📝 RESPUESTA DEL API:")
    print("-" * 70)
    print(json.dumps(data, indent=2, ensure_ascii=False))
    print("-" * 70)
    
    print("\n🔎 ANÁLISIS:")
    print(f"✅ agent_name: {data.get('agent_name')}")
    print(f"✅ session_id: {data.get('session_id')}")
    print(f"📝 response: {data.get('response')}")
    
    response_text = data.get('response', '')
    
    if not response_text or response_text.startswith("[Sistema]"):
        print("\n⚠️ PROBLEMA DETECTADO:")
        print(f"   La respuesta está vacía o es un mensaje de fallback")
        print(f"   Esto significa que el modelo de Minimax está retornando respuestas vacías")
    else:
        print("\n✅ RESPUESTA NORMAL")
        print(f"   Longitud: {len(response_text)} caracteres")
    
except requests.exceptions.ConnectionError:
    print("❌ No se puede conectar al servidor")
    print("   Asegúrate que está corriendo: python run_api.py")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
