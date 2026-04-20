import uuid
from fastapi import UploadFile
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.emergencies.domain.models import EvidenciaIncidente
from app.packages.identity.domain.models import Usuario
from app.packages.identity.infrastructure.repositories import UserRepository
from app.core.exceptions import NotFoundError, ForbiddenError
from app.core.storage import upload_file_local


class UploadEvidenceUseCase:
    def __init__(
        self,
        incident_repository: IncidentRepository,
        user_repository: UserRepository
    ):
        self.incident_repository = incident_repository
        self.user_repository = user_repository

    async def execute(
        self,
        current_user: Usuario,
        incident_id: uuid.UUID,
        file: UploadFile,
        evidencia_tipo: str
    ) -> EvidenciaIncidente:
        """(CU6) Cargar evidencia multimedia: valida, sube a S3 y registra la URL en la BD."""
        # 1. Validar que el incidente existe
        incidente = await self.incident_repository.get_by_id(incident_id)
        if not incidente:
            raise NotFoundError("Incidente no encontrado.")

        # 2. Validar que el vehículo del incidente pertenece al usuario
        vehicle = await self.user_repository.get_vehicle_by_id(incidente.id_vehiculo)
        if not vehicle or vehicle.id_usuario != current_user.id_usuario:
            raise ForbiddenError("No tiene permisos para subir evidencia a este incidente.")

        # 3. Guardar archivo localmente con un nombre único
        filename = f"evidencias/{incident_id}/{uuid.uuid4()}_{file.filename}"
        url = await upload_file_local(file.file, filename)

        if not url:
            from app.core.exceptions import BadRequestError
            raise BadRequestError("Error al subir el archivo. Intente de nuevo.")

        # 4. Persistir el registro en la BD
        evidencia = EvidenciaIncidente(
            id_incidente=incident_id,
            evidencia_tipo=evidencia_tipo,
            archivo_url=url,
        )

        return await self.incident_repository.add_evidence(evidencia)
