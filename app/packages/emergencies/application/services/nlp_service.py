import logging
import json
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

class NLPService:
    """
    Servicio optimizado para procesar texto usando Gemini 3.1 Flash Lite.
    Recibe la transcripción enviada desde el frontend.
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            self.model_id = "gemini-3.1-flash-lite-preview" 
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY no configurada.")

    async def process_report(self, transcription_text: str) -> dict:
        """
        Procesa el texto del reporte para extraer detalles estructurados.
        """
        if not self.client or not transcription_text:
            return self._get_fallback_analysis()

        prompt_text = """
        Eres un asistente experto en mecánica automotriz. Analiza el reporte del usuario 
        y extrae la información en formato JSON puro:
        {
            "summary": "Resumen técnico del problema",
            "intent": "emergencia_mecanica",
            "entities": {
                "falla": "Sistema afectado",
                "ubicacion": "Lugar mencionado (o 'No especificada')",
                "gravedad": "Nivel de urgencia (baja, media, alta)"
            }
        }
        """

        try:
            # Llamada asíncrona
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=[prompt_text, f"Reporte del usuario: {transcription_text}"],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            
            # Extraer JSON de la respuesta de texto
            analysis = json.loads(response.text)
            return analysis
            
        except Exception as e:
            logger.error(f"Error en análisis con Gemini 3.1: {str(e)}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> dict:
        """Análisis genérico de respaldo."""
        return {
            "summary": "Reporte recibido (Análisis en curso).",
            "intent": "emergencia_mecanica",
            "entities": {
                "falla": "general",
                "ubicacion": "No especificada",
                "gravedad": "media"
            }
        }
