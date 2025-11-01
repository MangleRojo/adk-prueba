from google.adk.agents.llm_agent import Agent
from google.adk.models.lite_llm import LiteLlm
import os

root_agent = Agent(
    model=LiteLlm(
        model="openrouter/minimax/minimax-m2:free",  # Especifica el modelo con prefijo 'openrouter/'
        api_key=os.getenv("OPENROUTER_API_KEY"),  # Lee la API key del entorno
        api_base="https://openrouter.ai/api/v1"   # URL base de OpenRouter
    ),
    name='root_agent',
    description='Gente agéntica.',
    instruction='Reflexiona y responde preguntas de manera clara y concisa.',
)
