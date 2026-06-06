import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_active_user
from app.core.exceptions import ForbiddenError, NotFoundError
from app.packages.identity.domain.models import Usuario
from app.packages.quotations.application.cancel_request import CancelQuotationRequestUseCase
from app.packages.quotations.application.create_quote import CreateWorkshopQuotationUseCase
from app.packages.quotations.application.create_request import CreateQuotationRequestUseCase
from app.packages.quotations.application.get_request_quotes import GetQuotationRequestQuotesUseCase
from app.packages.quotations.application.list_my_requests import ListMyQuotationRequestsUseCase
from app.packages.quotations.application.list_workshop_inbox import ListWorkshopInboxUseCase
from app.packages.quotations.application.reject_request import RejectQuotationRequestUseCase
from app.packages.quotations.application.search_compatible_workshops import SearchCompatibleWorkshopsUseCase
from app.packages.quotations.application.select_quote import SelectQuotationUseCase
from app.packages.quotations.domain.models import SolicitudCotizacionTaller
from app.packages.quotations.presentation.schemas import (
    QuotationIncidentResponse,
    QuotationRequestCreate,
    QuotationRequestResponse,
    QuotationRequestSelect,
    QuotationResponse,
    QuotationWorkshopInboxItemResponse,
    QuotationWorkshopOptionResponse,
    QuotationWorkshopQuoteCreate,
    QuotationWorkshopRejectCreate,
)
from app.packages.workshops.dependencies import get_selected_branch_id

router = APIRouter()


def _build_workshop_option(branch, distance_km) -> QuotationWorkshopOptionResponse:
    return QuotationWorkshopOptionResponse(
        id_taller=branch.id_taller,
        id_sucursal_representante=branch.id_sucursal,
        workshop_name=branch.taller.nombre if branch.taller else None,
        branch_name=branch.nombre,
        distancia_km=distance_km,
    )


def _build_request_response(request, compatible_workshops=None) -> QuotationRequestResponse:
    vehicle_brand = getattr(request.vehiculo, "marca", None) if getattr(request, "vehiculo", None) else None
    vehicle_model = getattr(request.vehiculo, "modelo", None) if getattr(request, "vehiculo", None) else None
    vehicle_plate = getattr(request.vehiculo, "matricula", None) if getattr(request, "vehiculo", None) else None
    vehicle_bits = [part for part in [vehicle_brand, vehicle_model, vehicle_plate] if part]
    return QuotationRequestResponse(
        id_solicitud_cotizacion=request.id_solicitud_cotizacion,
        id_cliente=request.id_cliente,
        id_vehiculo=request.id_vehiculo,
        client_name=getattr(request.cliente, "nombre", None) if getattr(request, "cliente", None) else None,
        client_phone=getattr(request.cliente, "telefono", None) if getattr(request, "cliente", None) else None,
        vehicle_label=" - ".join(vehicle_bits) if vehicle_bits else None,
        vehicle_brand=vehicle_brand,
        vehicle_model=vehicle_model,
        vehicle_plate=vehicle_plate,
        descripcion=request.descripcion,
        observaciones=request.observaciones,
        prioridad=request.prioridad,
        categoria_servicio=request.categoria_servicio,
        estado=request.estado,
        fecha_vencimiento=request.fecha_vencimiento,
        fecha_creacion=request.fecha_creacion,
        fecha_modificacion=request.fecha_modificacion,
        compatible_workshops=compatible_workshops or [],
    )


def _build_quote_response(quote) -> QuotationResponse:
    return QuotationResponse(
        id_cotizacion=quote.id_cotizacion,
        id_solicitud_cotizacion=quote.id_solicitud_cotizacion,
        id_solicitud_taller=quote.id_solicitud_taller,
        id_taller=quote.id_taller,
        id_sucursal_representante=quote.id_sucursal_representante,
        id_admin_responde=quote.id_admin_responde,
        mano_obra_estimado=quote.mano_obra_estimado,
        repuestos_estimado=quote.repuestos_estimado,
        total_estimado=quote.total_estimado,
        tiempo_estimado_minutos=quote.tiempo_estimado_minutos,
        observaciones=quote.observaciones,
        vigencia_hasta=quote.vigencia_hasta,
        estado=quote.estado,
        id_incidente_generado=quote.id_incidente_generado,
        fecha_creacion=quote.fecha_creacion,
        fecha_modificacion=quote.fecha_modificacion,
        workshop_name=quote.taller.nombre if quote.taller else None,
        branch_name=quote.sucursal_representante.nombre if quote.sucursal_representante else None,
        responder_name=quote.admin_responde.nombre if quote.admin_responde else None,
    )


def _build_inbox_item(item: SolicitudCotizacionTaller) -> QuotationWorkshopInboxItemResponse:
    compatible = []
    request = item.solicitud
    if request and request.talleres:
        for row in request.talleres:
            if row.sucursal_representante:
                compatible.append(
                    _build_workshop_option(
                        row.sucursal_representante,
                        row.distancia_km,
                    )
                )
    return QuotationWorkshopInboxItemResponse(
        id_solicitud_taller=item.id_solicitud_taller,
        id_solicitud_cotizacion=item.id_solicitud_cotizacion,
        id_taller=item.id_taller,
        id_sucursal_representante=item.id_sucursal_representante,
        workshop_name=item.taller.nombre if item.taller else None,
        branch_name=item.sucursal_representante.nombre if item.sucursal_representante else None,
        estado_envio=item.estado_envio,
        fecha_envio=item.fecha_envio,
        fecha_actualizacion=item.fecha_actualizacion,
        request=_build_request_response(request, compatible_workshops=compatible),
    )


@router.get("/compatibility/search", response_model=list[QuotationWorkshopOptionResponse])
async def search_compatibility(
    latitud: float = Query(..., ge=-90, le=90),
    longitud: float = Query(..., ge=-180, le=180),
    categoria_servicio: Optional[str] = Query(None),
    radius_km: float = Query(10.0, gt=0, le=100),
    db: AsyncSession = Depends(get_db),
):
    use_case = SearchCompatibleWorkshopsUseCase(db)
    rows = await use_case.execute(
        latitud=latitud,
        longitud=longitud,
        categoria_servicio=categoria_servicio,
        radius_km=radius_km,
    )
    return [_build_workshop_option(branch, distance) for branch, distance in rows]


@router.post("/requests", response_model=QuotationRequestResponse, status_code=status.HTTP_201_CREATED)
async def create_request(
    payload: QuotationRequestCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    use_case = CreateQuotationRequestUseCase(db)
    request, links = await use_case.execute(
        creator=current_user,
        id_vehiculo=payload.id_vehiculo,
        latitud=payload.latitud,
        longitud=payload.longitud,
        descripcion=payload.descripcion,
        observaciones=payload.observaciones,
        prioridad=payload.prioridad,
        categoria_servicio=payload.categoria_servicio,
        radius_km=payload.radius_km,
    )
    hydrated_request = await use_case.repo.get_request_with_details(request.id_solicitud_cotizacion)
    compatible = []
    for link in links:
        if link.sucursal_representante:
            compatible.append(_build_workshop_option(link.sucursal_representante, link.distancia_km))
    return _build_request_response(hydrated_request or request, compatible)


@router.get("/requests/me", response_model=list[QuotationRequestResponse])
async def list_my_requests(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    use_case = ListMyQuotationRequestsUseCase(db)
    requests = await use_case.execute(current_user.id_usuario)
    response = []
    for request in requests:
        compatible = []
        for row in request.talleres:
            if row.sucursal_representante:
                compatible.append(_build_workshop_option(row.sucursal_representante, row.distancia_km))
        response.append(_build_request_response(request, compatible))
    return response


@router.post("/requests/{request_id}/cancel", response_model=QuotationRequestResponse)
async def cancel_request(
    request_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    use_case = CancelQuotationRequestUseCase(db)
    request = await use_case.execute(
        current_user=current_user,
        request_id=request_id,
    )
    compatible = []
    for row in request.talleres:
        if row.sucursal_representante:
            compatible.append(_build_workshop_option(row.sucursal_representante, row.distancia_km))
    return _build_request_response(request, compatible)


@router.get("/requests/{request_id}/quotes", response_model=list[QuotationResponse])
async def list_request_quotes(
    request_id: uuid.UUID,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    use_case = GetQuotationRequestQuotesUseCase(db)
    quotes = await use_case.execute(request_id=request_id, client_id=current_user.id_usuario)
    return [_build_quote_response(quote) for quote in quotes]


@router.post("/requests/{request_id}/select", response_model=QuotationIncidentResponse, status_code=status.HTTP_201_CREATED)
async def select_quote(
    request_id: uuid.UUID,
    payload: QuotationRequestSelect,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.id_cotizacion is None:
        raise ForbiddenError("Debe seleccionar una cotizacion valida.")

    use_case = SelectQuotationUseCase(db)
    incident = await use_case.execute(
        current_user=current_user,
        request_id=request_id,
        quote_id=payload.id_cotizacion,
    )
    return QuotationIncidentResponse(
        id_incidente=incident.id_incidente,
        id_taller=incident.id_taller,
        id_sucursal=incident.id_sucursal,
        id_cotizacion_origen=incident.id_cotizacion_origen,
        origen=getattr(incident, "origen", None),
        estado_incidente=incident.estado_incidente,
        prioridad_incidente=incident.prioridad_incidente,
    )


@router.get("/workshop/inbox", response_model=list[QuotationWorkshopInboxItemResponse])
async def workshop_inbox(
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    selected_branch_id: Optional[uuid.UUID] = Depends(get_selected_branch_id),
):
    use_case = ListWorkshopInboxUseCase(db)
    workshop = await use_case.workshop_repo.get_by_admin(current_user.id_usuario)
    if not workshop:
        raise ForbiddenError("No tienes un taller registrado.")

    rows = await use_case.execute(
        workshop_id=workshop.id_taller,
        branch_id=selected_branch_id,
    )
    return [_build_inbox_item(row) for row in rows]


@router.post("/workshop/{request_id}/quote", response_model=QuotationResponse, status_code=status.HTTP_201_CREATED)
async def workshop_quote(
    request_id: uuid.UUID,
    payload: QuotationWorkshopQuoteCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    selected_branch_id: Optional[uuid.UUID] = Depends(get_selected_branch_id),
):
    use_case = CreateWorkshopQuotationUseCase(db)
    quote = await use_case.execute(
        current_user=current_user,
        request_id=request_id,
        payload=payload,
        selected_branch_id=selected_branch_id,
    )
    hydrated_quote = await use_case.repo.get_quote_with_details(quote.id_cotizacion)
    return _build_quote_response(hydrated_quote or quote)


@router.post("/workshop/{request_id}/reject", response_model=QuotationWorkshopInboxItemResponse)
async def workshop_reject(
    request_id: uuid.UUID,
    payload: QuotationWorkshopRejectCreate,
    current_user: Usuario = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
    selected_branch_id: Optional[uuid.UUID] = Depends(get_selected_branch_id),
):
    use_case = RejectQuotationRequestUseCase(db)
    link = await use_case.execute(
        current_user=current_user,
        request_id=request_id,
        selected_branch_id=selected_branch_id,
        motivo=payload.motivo,
    )
    workshop = await use_case.workshop_repo.get_by_admin(current_user.id_usuario)
    if not workshop:
        raise NotFoundError("No tienes un taller registrado.")
    rows = await ListWorkshopInboxUseCase(db).execute(
        workshop_id=workshop.id_taller,
        branch_id=selected_branch_id,
    )
    for item in rows:
        if item.id_solicitud_taller == link.id_solicitud_taller:
            return _build_inbox_item(item)
    raise NotFoundError("No fue posible recargar la solicitud rechazada.")
