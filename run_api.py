#!/usr/bin/env python3
"""
Script de ejecución del API DATAR
==================================
Inicia el servidor FastAPI con root_agent configurado correctamente.
"""

import os
import sys
import uvicorn

# Agregar el directorio raíz al path para importaciones correctas
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

if __name__ == "__main__":
    print("=" * 70)
    print("🌱 INICIANDO DATAR - Sistema Agéntico Ambiental")
    print("=" * 70)
    
    # Verificar que root_agent está configurado
    try:
        from datar_prueba.api import app, root_agent
        
        print(f"✅ API importado correctamente")
        print(f"✅ root_agent: {root_agent.name}")
        print(f"✅ Descripción: {root_agent.description}")
        print(f"✅ Sub-agentes: {len(root_agent.sub_agents) if hasattr(root_agent, 'sub_agents') else 0}")
        
    except Exception as e:
        print(f"❌ Error al importar API: {e}")
        sys.exit(1)
    
    print("\n" + "=" * 70)
    print("🔗 Iniciando servidor...")
    print("=" * 70)
    print(f"📍 Escuchando en: http://0.0.0.0:8000")
    print(f"📚 Documentación: http://localhost:8000/docs")
    print(f"🤖 root_agent status: http://localhost:8000/root_agent/status")
    print("=" * 70 + "\n")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        reload=False,
        log_level="info"
    )
