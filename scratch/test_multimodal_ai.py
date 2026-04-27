import asyncio
import os
import sys
import logging

# Configurar logs para ver qué pasa
logging.basicConfig(level=logging.INFO)

# Añadir el path del proyecto para poder importar app
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.packages.emergencies.application.services.vision_service import VisionService
from app.packages.emergencies.application.services.nlp_service import NLPService

async def test_ai():
    print("Iniciando Prueba de IA Multimodal...")
    
    vision = VisionService()
    nlp = NLPService()
    
    # Rutas de los archivos reales encontrados
    img_path = r"c:\Users\brad3\Proyectos\Proyecto-SI2-Examen-1\taller-backend\uploads\evidencias\d0fa5990-208b-4503-8d6c-eaef26cb171d\5d64c344-c978-400d-bfe0-ebb55f29e8b8_scaled_1000294031.jpg"
    audio_path = r"c:\Users\brad3\Proyectos\Proyecto-SI2-Examen-1\taller-backend\uploads\evidencias\d0fa5990-208b-4503-8d6c-eaef26cb171d\dc392cac-eac0-453b-b498-ca3d299db477_sos_audio_1777259604682.m4a"

    # 1. Prueba de Roboflow
    print("\n--- [1] Probando Roboflow (Vision Tecnica) ---")
    try:
        vision_result = await vision.analyze_image(img_path)
        print(f"Roboflow detecto: {vision_result['top_class']} ({vision_result['confidence']*100:.1f}%)")
    except Exception as e:
        print(f"Error en Roboflow: {e}")
        vision_result = {"top_class": "error", "confidence": 0}

    # 2. Prueba de Gemini Multimodal
    print("\n--- [2] Probando Gemini 1.5 Flash (Vision + Audio + NLP) ---")
    try:
        nlp_result = await nlp.process_report(
            transcription_text="El cliente envio una foto y un audio desde el movil.",
            vision_data=vision_result,
            audio_url=audio_path,
            image_url=img_path
        )
        
        print("\nRESULTADO CONSOLIDADO DE LA IA:")
        print(f"Transcripcion: {nlp_result.get('transcription')}")
        print(f"Resumen: {nlp_result.get('summary')}")
        print(f"Falla: {nlp_result.get('falla')}")
        print(f"Gravedad: {nlp_result.get('gravedad')}")
        
    except Exception as e:
        print(f"❌ Error en Gemini: {e}")

if __name__ == "__main__":
    asyncio.run(test_ai())
