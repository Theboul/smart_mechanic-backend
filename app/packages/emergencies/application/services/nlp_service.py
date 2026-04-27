import logging
import json
import httpx
from google import genai
from google.genai import types
from app.core.config import settings

logger = logging.getLogger(__name__)

class NLPService:
    """
    Servicio avanzado que utiliza Gemini 1.5 Flash para análisis multimodal.
    Combina visión artificial, audio y texto para un diagnóstico consolidado.
    """
    
    def __init__(self):
        self.api_key = settings.GEMINI_API_KEY
        if self.api_key:
            self.client = genai.Client(api_key=self.api_key)
            # Usamos el identificador confirmado en la lista de modelos
            self.model_id = "gemini-flash-latest" 
        else:
            self.client = None
            logger.warning("GEMINI_API_KEY no configurada.")

    async def _get_file_bytes(self, path_or_url: str) -> bytes:
        """Descarga un archivo si es URL o lo lee si es local."""
        if path_or_url.startswith(("http://", "https://")):
            async with httpx.AsyncClient() as client:
                response = await client.get(path_or_url)
                response.raise_for_status()
                return response.content
        else:
            from pathlib import Path
            path = Path(path_or_url)
            if path.exists():
                return path.read_bytes()
        raise FileNotFoundError(f"No se pudo acceder al archivo: {path_or_url}")

    async def process_report(self, transcription_text: str, vision_data: dict = None, audio_url: str = None, image_url: str = None) -> dict:
        """
        Procesa el reporte usando Gemini Multimodal.
        Ahora integra la imagen real y el audio en el prompt.
        """
        if not self.client:
            return self._get_fallback_analysis()

        contents = []
        
        # 1. Preparar contexto de Roboflow (Especialista en detección técnica)
        vision_context = "No hay datos de detección técnica previos."
        if vision_data and vision_data.get("top_class") != "desconocido":
            vision_context = f"Detección técnica de Roboflow: '{vision_data['top_class']}' ({vision_data['confidence']*100:.1f}% confianza)."

        # 2. Adjuntar Imagen si existe (Visión de Gemini)
        if image_url:
            try:
                img_bytes = await self._get_file_bytes(image_url)
                contents.append(types.Part.from_bytes(data=img_bytes, mime_type="image/jpeg"))
                logger.info(f"Imagen adjuntada a Gemini: {image_url}")
            except Exception as e:
                logger.error(f"Error al cargar imagen para Gemini: {str(e)}")

        # 3. Adjuntar Audio si existe (Voz del cliente)
        audio_msg = ""
        if audio_url:
            try:
                audio_bytes = await self._get_file_bytes(audio_url)
                contents.append(types.Part.from_bytes(data=audio_bytes, mime_type="audio/mpeg"))
                audio_msg = "He adjuntado un audio. ESCÚCHALO atentamente para entender el problema."
                logger.info(f"Audio adjuntado a Gemini: {audio_url}")
            except Exception as e:
                logger.error(f"Error al cargar audio para Gemini: {str(e)}")

        prompt_text = f"""
        Eres "El Sistema", el asistente experto de Smart Mechanic.
        
        CONTEXTO TÉCNICO:
        - {vision_context}
        - DESCRIPCIÓN DEL USUARIO: {transcription_text or 'Sin descripción escrita'}
        - {audio_msg}

        INSTRUCCIONES:
        1. Analiza la imagen y el audio adjuntos (si existen).
        2. Si hay audio, transcríbelo en "transcription". Si no hay, usa la descripción del usuario.
        3. Crea un "summary" empático, profesional y muy breve (máximo 120 caracteres).
        4. Identifica la "falla" técnica y la "gravedad" (BAJA, MEDIA, ALTA).
        5. IMPORTANTE: Si la imagen muestra daños graves que Roboflow no detectó, prioriza lo que TÚ ves.

        Responde estrictamente en JSON:
        {{
          "transcription": "...",
          "summary": "...",
          "falla": "...",
          "gravedad": "..."
        }}
        """
        contents.append(prompt_text)

        try:
            logger.info(f"Llamando a Gemini ({self.model_id})...")
            response = await self.client.aio.models.generate_content(
                model=self.model_id,
                contents=contents,
                config=types.GenerateContentConfig(
                    response_mime_type="application/json"
                )
            )
            return json.loads(response.text)
            
        except Exception as e:
            logger.error(f"Error en Gemini Multimodal: {str(e)}")
            return self._get_fallback_analysis()

    def _get_fallback_analysis(self) -> dict:
        return {
            "transcription": "No disponible",
            "summary": "Reporte recibido. Estamos analizando tu caso.",
            "falla": "Revisión manual requerida",
            "gravedad": "MEDIA"
        }
