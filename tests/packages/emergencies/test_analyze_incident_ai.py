import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from app.packages.emergencies.application.analyze_incident_ai import AnalyzeIncidentAIUseCase
from app.packages.emergencies.domain.models import Incidente, EvidenciaIncidente

@pytest.mark.asyncio
async def test_analyze_incident_ai_success():
    # 1. Setup Mocks
    mock_repo = MagicMock()
    
    # Simular un incidente con una foto
    incident_id = uuid.uuid4()
    mock_incident = MagicMock(spec=Incidente)
    mock_incident.id_incidente = incident_id
    mock_incident.evidencias = [
        EvidenciaIncidente(id_evidencia=uuid.uuid4(), evidencia_tipo="foto", archivo_url="http://test.com/img.jpg")
    ]
    mock_incident.historial = []
    
    mock_repo.get_by_id = AsyncMock(return_value=mock_incident)
    mock_repo.session = MagicMock()
    mock_repo.session.commit = AsyncMock()
    mock_repo.session.refresh = AsyncMock()

    # Mock de los servicios externos
    with patch("app.packages.emergencies.application.analyze_incident_ai.VisionService") as MockVision, \
         patch("app.packages.emergencies.application.analyze_incident_ai.NLPService") as MockNLP:
        
        MockVision.return_value.analyze_image = AsyncMock(return_value={
            "top_class": "frenos",
            "confidence": 0.95
        })
        MockNLP.return_value.process_report = AsyncMock(return_value={
            "summary": "Problema en los frenos detectado",
            "entities": {"falla": "pastillas gastadas"}
        })

        # 2. Execute
        use_case = AnalyzeIncidentAIUseCase(mock_repo)
        result = await use_case.execute(incident_id)

        # 3. Assertions
        assert result is not None
        assert result.estado_incidente == "ANALIZADO"
        assert "DIAGNÓSTICO IA" in result.resumen_ia
        assert len(result.historial) == 1
        assert result.historial[0].incidente_estado_nuevo == "ANALIZADO"
        mock_repo.get_by_id.assert_called_once_with(incident_id)
        mock_repo.session.commit.assert_called_once()
