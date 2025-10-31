# 🚀 Guía de Inicio Rápido - DATAR API

## ⚡ En 5 Minutos

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar el servidor
```bash
python datar_prueba/main.py
```

Deberías ver algo como:
```
🌱 Iniciando DATAR - Sistema Agéntico Ambiental
📍 Agente Principal: root_agent
💾 Base de datos de sesiones: sqlite:///memory.db
🌐 Servidor escuchando en: http://0.0.0.0:8000
📚 Documentación disponible en: http://localhost:8000/docs
```

### 3. Probar que funciona
```bash
curl http://localhost:8000/health
```

### 4. Usar la interfaz web interactiva
Abre en tu navegador: **http://localhost:8000/docs**

## 💬 Ejemplos de Uso

### Enviar un mensaje
```bash
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{"message": "Hola, ¿cómo estás?"}'
```

### Ver información del agente
```bash
curl http://localhost:8000/agent/info
```

### Listar sesiones activas
```bash
curl http://localhost:8000/sessions
```

## 🐍 Usar el Cliente Python

```bash
python ejemplo_uso.py
```

Esto ejecutará un ejemplo completo que demuestra todos los endpoints.

## 📚 Documentación Completa

- **CAMBIOS_REALIZADOS.md** - Detalle de todos los ajustes realizados
- **RESUMEN_AJUSTES.txt** - Resumen visual con todos los cambios
- **README.md** - Documentación general del proyecto
- **http://localhost:8000/docs** - Documentación interactiva (Swagger UI)

## ⚙️ Configuración Rápida

### Cambiar Puerto
```bash
export API_PORT=8001
python datar_prueba/main.py
```

### Modo Producción
```bash
export API_ENV=production
python datar_prueba/main.py
```

### Cambiar Modelo
```bash
export AGENT_MODEL="gemini-1.5-pro"
python datar_prueba/main.py
```

## 🆘 Problemas Comunes

### Puerto 8000 ya en uso
```bash
# Usar otro puerto
export API_PORT=8001
python datar_prueba/main.py
```

### ModuleNotFoundError
```bash
# Reinstalar dependencias
pip install --upgrade -r requirements.txt
```

### API Key de Google
```bash
# Configurar la API key si es necesaria
export GOOGLE_API_KEY="tu-clave-aqui"
python datar_prueba/main.py
```

## 📝 Endpoints Principales

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información del API |
| GET | `/health` | Health check |
| GET | `/agent/info` | Info del agente |
| POST | `/chat` | Enviar mensaje |
| GET | `/sessions` | Listar sesiones |
| GET | `/docs` | Swagger UI |

## 🎯 Próximos Pasos

1. Personalizar instrucciones del agente en `datar_prueba/agent.py`
2. Integrar con tu frontend
3. Añadir autenticación (ver CAMBIOS_REALIZADOS.md)
4. Configurar base de datos para persistencia
5. Desplegar en producción

## 🔗 Enlaces Útiles

- [FastAPI Documentación](https://fastapi.tiangolo.com/)
- [Google ADK Documentación](https://github.com/google-cloud-tools/agent-development-kit)
- [Pydantic Documentación](https://pydantic-settings.readthedocs.io/)

---

**¡Listo para comenzar! 🎉**

Si tienes problemas, consulta CAMBIOS_REALIZADOS.md para más detalles.
