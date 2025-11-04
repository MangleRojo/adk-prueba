#!/usr/bin/env python3
"""
Script de Debug - Investigar el modelo de root_agent
====================================================
"""

import os
import sys
from pprint import pprint

print("=" * 70)
print("🔍 DEBUGGING MODEL DE ROOT_AGENT")
print("=" * 70)

try:
    from datar_prueba.agent import root_agent
    
    print(f"\n✅ root_agent importado correctamente")
    print(f"   Nombre: {root_agent.name}")
    print(f"   Descripción: {root_agent.description}")
    
    # Verificar si tiene modelo
    if hasattr(root_agent, 'model'):
        model = root_agent.model
        print(f"\n✅ root_agent tiene atributo 'model'")
        print(f"   Tipo: {type(model)}")
        print(f"   Valor: {model}")
        print(f"   Str: {str(model)}")
        
        # Listar todos los atributos del modelo
        print(f"\n📋 Atributos del modelo:")
        attributes = dir(model)
        
        # Filtrar atributos relevantes (no privados, no métodos dunder)
        relevant = [attr for attr in attributes if not attr.startswith('_')]
        
        for attr in sorted(relevant):
            try:
                value = getattr(model, attr)
                # No mostrar métodos, solo atributos
                if not callable(value):
                    print(f"   - {attr}: {value}")
            except Exception as e:
                print(f"   - {attr}: [Error: {e}]")
        
        # Buscar específicamente palabras clave
        print(f"\n🔑 Búsqueda de palabras clave:")
        keywords = ['model', 'model_name', 'model_id', '_model', 'name', 'api_key', 'api_base']
        
        for keyword in keywords:
            if hasattr(model, keyword):
                value = getattr(model, keyword)
                print(f"   ✅ {keyword}: {value}")
        
        # Verificar si es LiteLlm
        print(f"\n🤖 Tipo de modelo:")
        print(f"   Clase: {model.__class__.__name__}")
        print(f"   Módulo: {model.__class__.__module__}")
        
    else:
        print(f"\n❌ root_agent NO tiene atributo 'model'")
        
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()

print("\n" + "=" * 70)
