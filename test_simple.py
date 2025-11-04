#!/usr/bin/env python3
"""
Test Simple - Verificar qué está retornando /agent/info
"""

import requests
import json

API_BASE_URL = "http://localhost:8000"

print("=" * 70)
print("🔍 VERIFICANDO ENDPOINT /agent/info")
print("=" * 70)

try:
    print("\n1️⃣ Conectando al API...")
    response = requests.get(f"{API_BASE_URL}/health", timeout=5)
    response.raise_for_status()
    print("✅ Servidor respondiendo")
    
    print("\n2️⃣ Obteniendo información del agente...")
    response = requests.get(f"{API_BASE_URL}/agent/info", timeout=5)
    response.raise_for_status()
    
    info = response.json()
    
    print("\n📝 RESPUESTA COMPLETA DE /agent/info:")
    print("-" * 70)
    print(json.dumps(info, indent=2, ensure_ascii=False))
    print("-" * 70)
    
    print("\n🔎 ANÁLISIS:")
    print(f"✅ name: {info.get('name')}")
    print(f"✅ model: {info.get('model')}")
    print(f"✅ model_name: {info.get('model_name')}")
    print(f"✅ has_model: {info.get('has_model')}")
    print(f"✅ instruction: {info.get('instruction')[:50]}...")
    
    # Verificar si el modelo existe
    has_model = info.get('has_model', False)
    model_str = info.get('model', 'N/D')
    model_name = info.get('model_name', 'N/D')
    
    print("\n📊 VALIDACIONES:")
    if has_model:
        print(f"✅ has_model=True")
    else:
        print(f"❌ has_model=False ← PROBLEMA")
    
    if model_str != 'N/D' and model_str:
        print(f"✅ model_str tiene valor: {model_str[:50]}...")
    else:
        print(f"❌ model_str='N/D' o vacío ← PROBLEMA")
    
    if model_name != 'N/D' and model_name:
        print(f"✅ model_name tiene valor: {model_name}")
    else:
        print(f"⚠️ model_name='N/D' o vacío")
    
except requests.exceptions.ConnectionError:
    print("❌ No se puede conectar al servidor")
    print("   Asegúrate que está corriendo: python run_api.py")
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
