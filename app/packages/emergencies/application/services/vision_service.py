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
        self.client = InferenceHTTPClient(
            api_url=settings.ROBOFLOW_API_URL,
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
            # Ejecutar el workflow
            result = self.client.run_workflow(
                workspace_name=self.workspace,
                workflow_id=self.workflow_id,
                images={"image": image_url},
                use_cache=True
            )
            
            # Extracción basada en el JSON real de Roboflow Workflows:
            # Estructura: result[0]["predictions"]["image"]["predictions"][0]
            
            top_class = "desconocido"
            confidence = 0.0
            
            if result and isinstance(result, list) and len(result) > 0:
                wf_result = result[0]
                # Acceder al diccionario de predicciones
                predictions_container = wf_result.get("predictions", {})
                
                # Roboflow suele usar el nombre del campo de entrada ("image") como llave
                image_preds = predictions_container.get("image", {})
                actual_predictions = image_preds.get("predictions", [])
                
                if actual_predictions:
                    # Tomamos la primera detección (la de mayor confianza usualmente)
                    first_det = actual_predictions[0]
                    top_class = first_det.get("class", "indeterminado")
                    confidence = first_det.get("confidence", 0.0)
            
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
