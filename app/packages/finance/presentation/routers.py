from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.packages.identity.domain.models import Usuario
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.finance.infrastructure.repositories import FinanceRepository
from app.packages.finance.presentation.schemas import PaymentCreate, PaymentResponse
from app.packages.finance.application.close_incident import CloseIncidentUseCase

router = APIRouter()

@router.post("/emergencies/{incident_id}/pay", response_model=PaymentResponse)
async def process_payment(
    incident_id: uuid.UUID,
    payment_in: PaymentCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(Fase 5) Registrar el pago final de una emergencia y cerrar el caso."""
    from app.core.exceptions import ForbiddenError
    
    workshop_repo = WorkshopRepository(db)
    incident_repo = IncidentRepository(db)
    finance_repo = FinanceRepository(db)
    
    # 1. Obtener taller del usuario
    taller = await workshop_repo.get_by_admin(current_user.id_usuario)
    if not taller:
        raise ForbiddenError("No eres administrador de un taller.")
        
    # 2. Ejecutar cierre
    use_case = CloseIncidentUseCase(finance_repo, incident_repo)
    return await use_case.execute(
        id_taller=taller.id_taller,
        id_incidente=incident_id,
        monto_total=payment_in.monto_total
    )

@router.get("/reports", response_model=List[PaymentResponse])
async def get_financial_reports(
    workshop_id: Optional[uuid.UUID] = Query(None),
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """(CU19/CU25) Obtener reportes de pagos. Multi-tenant."""
    from sqlalchemy import select
    from app.packages.finance.domain.models import Pago
    
    query = select(Pago)
    
    # Lógica de Seguridad Multi-tenant
    if current_user.rol_nombre == "admin_taller":
        workshop_repo = WorkshopRepository(db)
        workshop = await workshop_repo.get_by_admin(current_user.id_usuario)
        if not workshop:
            return []
        query = query.where(Pago.id_taller == workshop.id_taller)
    elif current_user.rol_nombre == "superadmin":
        if workshop_id:
            query = query.where(Pago.id_taller == workshop_id)
    else:
        from fastapi import HTTPException
        raise HTTPException(status_code=403, detail="Acceso denegado")
        
    result = await db.execute(query.order_by(Pago.fecha_pago.desc()))
    return result.scalars().all()
