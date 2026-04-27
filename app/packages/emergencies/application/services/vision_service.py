import logging
from inference_sdk import InferenceHTTPClient
from app.core.config import settings

logger = logging.getLogger(__name__)

class VisionService:
    """
    Servicio para interactuar con Roboflow y clasificar evidencias visuales.
    Usa el SDK de Inference para ejecutar flujos de trabajo (workflows).
    """
    
    def __init__(self):
        # Usamos la URL serverless específica para Workflows como indicaste
        self.client = InferenceHTTPClient(
            api_url="https://serverless.roboflow.com",
            api_key=settings.ROBOFLOW_API_KEY
        )
        self.workspace = settings.ROBOFLOW_WORKSPACE
        self.workflow_id = settings.ROBOFLOW_WORKFLOW_ID

    async def analyze_image(self, image_url: str) -> dict:
        """
        Analiza una imagen usando un workflow de Roboflow.
        """
        logger.info(f"Enviando imagen a Roboflow Workflow: {self.workflow_id}")
        
        try:
            # Ejecutar el workflow tal como indica tu documentación
            result = self.client.run_workflow(
                workspace_name=self.workspace,
                workflow_id=self.workflow_id,
                images={"image": image_url},
                use_cache=True
            )
            
            # Verificamos si el resultado es válido
            if not result or not isinstance(result, list):
                logger.error(f"Respuesta inesperada de Roboflow: {result}")
                return {"top_class": "error_ia", "confidence": 0.0}

            # Según tu JSON: result[0]['predictions']['predictions']
            data = result[0]
            predictions = []
            
            if "predictions" in data and isinstance(data["predictions"], dict):
                predictions = data["predictions"].get("predictions", [])

            top_class = "desconocido"
            confidence = 0.0

            if predictions and len(predictions) > 0:
                # Tomamos la predicción con mayor confianza
                best_pred = max(predictions, key=lambda x: x.get("confidence", 0))
                top_class = best_pred.get("class", "indeterminado")
                confidence = best_pred.get("confidence", 0.0)
            
            logger.info(f"Resultado Roboflow Workflow: {top_class} ({confidence*100:.1f}%)")

            return {
                "top_class": top_class,
                "confidence": confidence,
                "raw_result": result
            }
            
        except Exception as e:
            logger.error(f"Error al llamar a Roboflow: {str(e)}")
            return {
                "top_class": "error_ia",
                "confidence": 0.0,
                "raw_result": {"error": str(e)}
            }
