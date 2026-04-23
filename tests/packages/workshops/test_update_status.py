import pytest
import uuid
from app.packages.workshops.application.update_status import UpdateIncidentStatusUseCase
from app.packages.emergencies.domain.models import Incidente
from app.core.exceptions import ForbiddenError
from unittest.mock import AsyncMock, MagicMock

@pytest.mark.asyncio
async def test_update_status_success():
    # Setup
    mock_repo = MagicMock()
    id_taller = uuid.uuid4()
    id_incidente = uuid.uuid4()
    
    mock_incident = MagicMock(spec=Incidente)
    mock_incident.id_taller = id_taller
    mock_incident.estado_incidente = "TALLER_ASIGNADO"
    mock_incident.historial = []
    
    mock_repo.get_by_id = AsyncMock(return_value=mock_incident)
    mock_repo.session = MagicMock()
    mock_repo.session.commit = AsyncMock()
    mock_repo.session.refresh = AsyncMock()

    # Execute
    use_case = UpdateIncidentStatusUseCase(mock_repo)
    result = await use_case.execute(id_taller, id_incidente, "EN_CAMINO", "Mecanico Juan")

    # Assertions
    assert result.estado_incidente == "EN_CAMINO"
    assert len(result.historial) == 1
    assert result.historial[0].historial_actor == "Mecanico Juan"

@pytest.mark.asyncio
async def test_update_status_forbidden():
    # Setup - El incidente pertenece a OTRO taller
    mock_repo = MagicMock()
    id_taller_autenticado = uuid.uuid4()
    id_taller_propietario = uuid.uuid4()
    id_incidente = uuid.uuid4()
    
    mock_incident = MagicMock(spec=Incidente)
    mock_incident.id_taller = id_taller_propietario # Diferente al autenticado
    
    mock_repo.get_by_id = AsyncMock(return_value=mock_incident)

    # Execute & Assert
    use_case = UpdateIncidentStatusUseCase(mock_repo)
    with pytest.raises(ForbiddenError):
        await use_case.execute(id_taller_autenticado, id_incidente, "EN_CAMINO", "Mecanico Juan")
