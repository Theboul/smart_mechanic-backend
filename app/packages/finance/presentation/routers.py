from fastapi import APIRouter, Depends, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
import uuid
from typing import List, Optional
import stripe

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.config import settings
from app.packages.identity.domain.models import Usuario
from app.packages.workshops.infrastructure.repositories import WorkshopRepository
from app.packages.emergencies.infrastructure.repositories import IncidentRepository
from app.packages.finance.infrastructure.repositories import FinanceRepository
from app.packages.finance.presentation.schemas import PaymentCreate, PaymentResponse
from app.packages.finance.application.close_incident import CloseIncidentUseCase
from app.packages.finance.presentation.stripe_webhook import router as webhook_router

stripe.api_key = settings.STRIPE_SECRET_KEY

router = APIRouter()
router.include_router(webhook_router)

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

@router.post("/emergencies/{incident_id}/payment-intent")
async def create_payment_intent(
    incident_id: uuid.UUID,
    payment_in: PaymentCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """Generar un PaymentIntent en Stripe para el pago de la emergencia."""
    from app.core.exceptions import NotFoundError, BadRequestError

    # 1. Validar incidente y taller
    incident_repo = IncidentRepository(db)
    incident = await incident_repo.get_by_id(incident_id)
    if not incident:
        raise NotFoundError("Incidente no encontrado.")
    
    if not incident.id_taller:
        raise BadRequestError("El incidente no tiene un taller asignado.")

    try:
        # Stripe espera el monto en centavos (ej: 10.00 USD -> 1000 centavos)
        amount_cents = int(payment_in.monto_total * 100)
        
        intent = stripe.PaymentIntent.create(
            amount=amount_cents,
            currency="usd",
            metadata={
                "incident_id": str(incident_id),
                "id_taller": str(incident.id_taller),
                "monto_total": str(payment_in.monto_total)
            },
            automatic_payment_methods={
                "enabled": True,
            },
        )
        return {"clientSecret": intent.client_secret}
    except Exception as e:
        raise BadRequestError(f"Error al crear el PaymentIntent de Stripe: {str(e)}")

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
