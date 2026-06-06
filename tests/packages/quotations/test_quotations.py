import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.core.exceptions import BadRequestError
from app.packages.identity.domain.models import Usuario, Vehiculo
from app.packages.quotations.application.cancel_request import CancelQuotationRequestUseCase
from app.packages.quotations.application.create_request import CreateQuotationRequestUseCase
from app.packages.quotations.application.search_compatible_workshops import SearchCompatibleWorkshopsUseCase
from app.packages.quotations.application.select_quote import SelectQuotationUseCase
from app.packages.quotations.domain.models import Cotizacion, SolicitudCotizacion, SolicitudCotizacionTaller
from app.packages.workshops.domain.models import Taller, SucursalTaller


@pytest.mark.asyncio
async def test_search_compatible_workshops_groups_by_workshop():
    db = AsyncMock()

    workshop_a = uuid.uuid4()
    workshop_b = uuid.uuid4()

    branch_a1 = MagicMock(spec=SucursalTaller)
    branch_a1.id_taller = workshop_a
    branch_a1.id_sucursal = uuid.uuid4()
    branch_a1.nombre = "Sucursal A1"
    branch_a1.taller = MagicMock(spec=Taller)
    branch_a1.taller.nombre = "Taller A"

    branch_a2 = MagicMock(spec=SucursalTaller)
    branch_a2.id_taller = workshop_a
    branch_a2.id_sucursal = uuid.uuid4()
    branch_a2.nombre = "Sucursal A2"
    branch_a2.taller = MagicMock(spec=Taller)
    branch_a2.taller.nombre = "Taller A"

    branch_b = MagicMock(spec=SucursalTaller)
    branch_b.id_taller = workshop_b
    branch_b.id_sucursal = uuid.uuid4()
    branch_b.nombre = "Sucursal B1"
    branch_b.taller = MagicMock(spec=Taller)
    branch_b.taller.nombre = "Taller B"

    service = SearchCompatibleWorkshopsUseCase(db)
    service.assignment_repo.get_nearby_workshops = AsyncMock(
        return_value=[
            (branch_a1, 1200.0),
            (branch_a2, 1800.0),
            (branch_b, 2500.0),
        ]
    )

    rows = await service.execute(latitud=-16.5, longitud=-68.15)

    assert len(rows) == 2
    assert rows[0][0].id_taller == workshop_a
    assert rows[1][0].id_taller == workshop_b


@pytest.mark.asyncio
async def test_create_request_persists_request_and_links():
    db = AsyncMock()
    service = CreateQuotationRequestUseCase(db)

    creator = MagicMock(spec=Usuario)
    creator.id_usuario = uuid.uuid4()
    creator.rol_nombre = "cliente"

    vehicle = MagicMock(spec=Vehiculo)
    vehicle.id_usuario = creator.id_usuario
    vehicle.id_vehiculo = uuid.uuid4()
    service.user_repo.get_vehicle_by_id = AsyncMock(return_value=vehicle)

    branch_one = MagicMock(spec=SucursalTaller)
    branch_one.id_taller = uuid.uuid4()
    branch_one.id_sucursal = uuid.uuid4()
    branch_one.nombre = "Sucursal 1"
    branch_one.taller = MagicMock(spec=Taller)
    branch_one.taller.nombre = "Taller 1"

    branch_two = MagicMock(spec=SucursalTaller)
    branch_two.id_taller = uuid.uuid4()
    branch_two.id_sucursal = uuid.uuid4()
    branch_two.nombre = "Sucursal 2"
    branch_two.taller = MagicMock(spec=Taller)
    branch_two.taller.nombre = "Taller 2"

    service.search_compatible_workshops = AsyncMock(
        return_value=[
            (branch_one, Decimal("1.20")),
            (branch_two, Decimal("2.50")),
        ]
    )

    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    request, links = await service.execute(
        creator=creator,
        id_vehiculo=vehicle.id_vehiculo,
        latitud=-16.5,
        longitud=-68.15,
        descripcion="Necesito comparacion de talleres",
        observaciones="Cliente desea cita",
        prioridad="MEDIA",
        categoria_servicio=None,
        radius_km=10.0,
    )

    assert isinstance(request, SolicitudCotizacion)
    assert request.estado == "ABIERTA"
    assert len(links) == 2
    assert db.add.call_count == 3


@pytest.mark.asyncio
async def test_select_quote_creates_incident_from_quotation():
    db = AsyncMock()
    service = SelectQuotationUseCase(db)

    client = MagicMock(spec=Usuario)
    client.id_usuario = uuid.uuid4()
    client.rol_nombre = "cliente"
    client.nombre = "Cliente Test"
    client.telefono = "70000000"

    request = MagicMock(spec=SolicitudCotizacion)
    request.id_solicitud_cotizacion = uuid.uuid4()
    request.id_cliente = client.id_usuario
    request.id_vehiculo = uuid.uuid4()
    request.ubicacion_cliente = "POINT(-68.15 -16.5)"
    request.descripcion = "Solicitud de prueba"
    request.observaciones = "Observaciones"
    request.prioridad = "ALTA"
    request.estado = "ABIERTA"
    request.fecha_vencimiento = datetime.utcnow() + timedelta(hours=4)

    quote = MagicMock(spec=Cotizacion)
    quote.id_cotizacion = uuid.uuid4()
    quote.id_solicitud_cotizacion = request.id_solicitud_cotizacion
    quote.id_solicitud_taller = uuid.uuid4()
    quote.id_taller = uuid.uuid4()
    quote.id_sucursal_representante = uuid.uuid4()
    quote.id_admin_responde = uuid.uuid4()
    quote.estado = "PENDIENTE"
    quote.vigencia_hasta = datetime.utcnow() + timedelta(hours=1)

    sibling_quote = MagicMock(spec=Cotizacion)
    sibling_quote.id_cotizacion = uuid.uuid4()
    sibling_quote.estado = "PENDIENTE"

    sibling_link = MagicMock(spec=SolicitudCotizacionTaller)
    sibling_link.id_taller = uuid.uuid4()
    sibling_link.estado_envio = "RESPONDIDA"

    accepted_link = MagicMock(spec=SolicitudCotizacionTaller)
    accepted_link.id_taller = quote.id_taller
    accepted_link.estado_envio = "RESPONDIDA"

    request.cotizaciones = [quote, sibling_quote]
    request.talleres = [accepted_link, sibling_link]

    service.repo.get_quote_by_id = AsyncMock(return_value=quote)
    service.repo.get_request_with_details = AsyncMock(return_value=request)
    db.add = MagicMock()
    db.flush = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    incident = await service.execute(
        current_user=client,
        request_id=request.id_solicitud_cotizacion,
        quote_id=quote.id_cotizacion,
    )

    assert incident.id_cotizacion_origen == quote.id_cotizacion
    assert incident.origen == "COTIZACION"
    assert incident.estado_incidente == "TALLER_ASIGNADO"
    assert request.estado == "SELECCIONADA"
    assert quote.estado == "ACEPTADA"
    assert sibling_quote.estado == "RECHAZADA"
    assert sibling_link.estado_envio == "RECHAZADA"
    assert db.add.call_count == 3


@pytest.mark.asyncio
async def test_select_quote_rejects_mismatched_request():
    db = AsyncMock()
    service = SelectQuotationUseCase(db)

    client = MagicMock(spec=Usuario)
    client.id_usuario = uuid.uuid4()
    client.rol_nombre = "cliente"
    client.nombre = "Cliente Test"

    quote = MagicMock(spec=Cotizacion)
    quote.id_cotizacion = uuid.uuid4()
    quote.id_solicitud_cotizacion = uuid.uuid4()
    quote.estado = "PENDIENTE"
    quote.vigencia_hasta = datetime.utcnow() + timedelta(hours=1)

    service.repo.get_quote_by_id = AsyncMock(return_value=quote)
    service.repo.get_request_with_details = AsyncMock(return_value=MagicMock(spec=SolicitudCotizacion))

    with pytest.raises(BadRequestError):
        await service.execute(
            current_user=client,
            request_id=uuid.uuid4(),
            quote_id=quote.id_cotizacion,
        )


@pytest.mark.asyncio
async def test_cancel_request_marks_request_links_and_quotes_as_cancelled():
    db = AsyncMock()
    db.commit = AsyncMock()
    db.refresh = AsyncMock()

    service = CancelQuotationRequestUseCase(db)

    client = MagicMock(spec=Usuario)
    client.id_usuario = uuid.uuid4()
    client.nombre = "Cliente Test"

    request = MagicMock(spec=SolicitudCotizacion)
    request.id_solicitud_cotizacion = uuid.uuid4()
    request.id_cliente = client.id_usuario
    request.estado = "ABIERTA"

    link_pending = MagicMock(spec=SolicitudCotizacionTaller)
    link_pending.id_taller = uuid.uuid4()
    link_pending.id_solicitud_taller = uuid.uuid4()
    link_pending.estado_envio = "ENVIADA"

    link_answered = MagicMock(spec=SolicitudCotizacionTaller)
    link_answered.id_taller = uuid.uuid4()
    link_answered.id_solicitud_taller = uuid.uuid4()
    link_answered.estado_envio = "RESPONDIDA"

    quote = MagicMock(spec=Cotizacion)
    quote.estado = "PENDIENTE"

    request.talleres = [link_pending, link_answered]
    request.cotizaciones = [quote]

    service.repo.get_request_with_details = AsyncMock(return_value=request)

    result = await service.execute(
        current_user=client,
        request_id=request.id_solicitud_cotizacion,
    )

    assert result is request
    assert request.estado == "CANCELADA"
    assert link_pending.estado_envio == "CANCELADA"
    assert link_answered.estado_envio == "CANCELADA"
    assert quote.estado == "CANCELADA"
    db.commit.assert_awaited_once()
