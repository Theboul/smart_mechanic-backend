from unittest.mock import MagicMock

from geoalchemy2.elements import WKBElement

from app.packages.assignment.infrastructure.repositories import AssignmentRepository


def test_to_geography_expression_uses_wkt_for_string_point():
    repo = AssignmentRepository(MagicMock())

    expr = repo._to_geography_expression("POINT(-68.15 -16.5)")

    compiled = str(expr)
    assert "ST_GeogFromText" in compiled


def test_to_geography_expression_uses_wkb_for_binary_point():
    repo = AssignmentRepository(MagicMock())
    point_wkb = WKBElement(
        bytes.fromhex("010100000000000000000000000000000000000000"),
        srid=4326,
        extended=False,
    )

    expr = repo._to_geography_expression(point_wkb)

    compiled = str(expr)
    assert "ST_GeomFromWKB" in compiled
    assert "ST_GeogFromText" not in compiled
