"""
Script de prueba para la API Datar
Ejecutar con: python test_api.py
"""

import httpx
import asyncio
import json


async def test_api():
    """Ejecutar pruebas en los endpoints de la API"""
    
    base_url = "http://localhost:8000"
    
    print("=" * 60)
    print("🧪 PRUEBA DE API - Datar")
    print("=" * 60)
    
    async with httpx.AsyncClient() as client:
        
        # Test 1: Health Check
        print("\n📍 TEST 1: Health Check")
        print("-" * 60)
        try:
            response = await client.get(f"{base_url}/health")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 2: Root Endpoint
        print("\n📍 TEST 2: Root Endpoint")
        print("-" * 60)
        try:
            response = await client.get(f"{base_url}/")
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 3: Chat Endpoint
        print("\n📍 TEST 3: Chat Endpoint")
        print("-" * 60)
        try:
            payload = {
                "message": "¿Cuál es la capital de Francia?",
                "conversation_id": "test_conv_001"
            }
            print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            response = await client.post(f"{base_url}/chat", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Test 4: Chat sin conversation_id
        print("\n📍 TEST 4: Chat sin conversation_id")
        print("-" * 60)
        try:
            payload = {"message": "Hola, ¿cómo funciona esta API?"}
            print(f"Request: {json.dumps(payload, indent=2, ensure_ascii=False)}")
            response = await client.post(f"{base_url}/chat", json=payload)
            print(f"Status: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        except Exception as e:
            print(f"❌ Error: {e}")
    
    print("\n" + "=" * 60)
    print("✅ Pruebas completadas")
    print("=" * 60)


if __name__ == "__main__":
    print("⚠️  Asegúrate de que la API esté ejecutándose en http://localhost:8000")
    print("Ejecuta: python datar_prueba/main.py\n")
    
    asyncio.run(test_api())

