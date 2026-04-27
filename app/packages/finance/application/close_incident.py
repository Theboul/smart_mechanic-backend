import uuid
from decimal import Decimal
from app.packages.finance.infrastructure.repositories import FinanceRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.finance.domain.models import Pago
from app.packages.emergencies.domain.models import HistorialIncidente
from app.core.exceptions import NotFoundError, ForbiddenError

class CloseIncidentUseCase:
    """
    Caso de Uso (CU): Cierre y Pago del Incidente.
    Registra el pago final y marca el incidente como FINALIZADO.
    """
    
    def __init__(self, finance_repo: FinanceRepository, incident_repo: IncidentRepository):
        self.finance_repo = finance_repo
        self.incident_repo = incident_repo

    async def execute(self, id_taller: uuid.UUID, id_incidente: uuid.UUID, monto_total: Decimal):
        # 1. Validar incidente
        incidente = await self.incident_repo.get_by_id(id_incidente)
        if not incidente:
            raise NotFoundError("Incidente no encontrado.")
            
        if incidente.id_taller != id_taller:
            raise ForbiddenError("No puedes cerrar un incidente que no te pertenece.")

        # 2. Calcular comisión (10%)
        comision = monto_total * Decimal("0.10")
        
        # 3. Crear registro de pago
        pago = Pago(
            id_incidente=id_incidente,
            id_taller=id_taller,
            monto=monto_total,
            monto_comision=comision,
            estado_pago="PAGADO",
            fecha_pago=None # SQLAlchemy lo manejará si hay default, sino se asignará
        )
        
        # 4. Actualizar incidente e Historial
        estado_anterior = incidente.estado_incidente
        incidente.estado_incidente = "COMPLETADO"
        
        # Liberar al técnico si existe
        if incidente.id_tecnico:
            from app.packages.workshops.domain.models import Tecnico
            from sqlalchemy.future import select
            result = await self.incident_repo.session.execute(
                select(Tecnico).where(Tecnico.id_usuario == incidente.id_tecnico)
            )
            tecnico = result.scalar_one_or_none()
            if tecnico:
                tecnico.estado = True

        historial = HistorialIncidente(
            id_incidente=id_incidente,
            incidente_estado_anterior=estado_anterior,
            incidente_estado_nuevo="COMPLETADO",
            historial_actor="SISTEMA_FINANCIERO",
            fecha=None
        )
        incidente.historial.append(historial)
        
        await self.finance_repo.create_payment(pago)
        await self.incident_repo.session.commit()
        
        return pago
