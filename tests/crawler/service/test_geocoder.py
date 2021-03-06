import pytest
import logging

from unittest.mock import Mock
from types import SimpleNamespace

from py_reportit.shared.config.container import Container

logger = logging.getLogger(__name__)

@pytest.fixture
def container() -> Container:
    return Container(config=SimpleNamespace(get=lambda config_value: ""))

def build_response_mock(data: dict) -> SimpleNamespace:
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: data
    )

def test_get_reports_not_luxembourg(caplog, container: Container):
    r_session_mock = Mock()
    r_session_mock.get.return_value = build_response_mock({"address": { "country_code": "not_lu" }})

    with container.requests_session.override(r_session_mock):
        geocoder_service = container.geocoder_service()

        with caplog.at_level(logging.WARNING):
            address_data = geocoder_service.get_neighbourhood_and_street(42.4544, 6.435)

    assert "not Luxembourg" in caplog.text

    assert address_data["street"] == None
    assert address_data["postcode"] == None
    assert address_data["neighbourhood"] == None

def test_get_reports_in_luxembourg_partial_data(container: Container):
    response_mock = build_response_mock(
        {
            "address": {
                "country_code": "lu",
                "road": "test road",
                "suburb": "test suburb"
            }
        }
    )

    r_session_mock = Mock()
    r_session_mock.get.return_value = response_mock

    with container.requests_session.override(r_session_mock):
        geocoder_service = container.geocoder_service()

        address_data = geocoder_service.get_neighbourhood_and_street(42.4544, 6.435)

    assert address_data["street"] == "test road"
    assert address_data["postcode"] == None
    assert address_data["neighbourhood"] == "test suburb"

def test_get_reports_in_luxembourg_full_data(container: Container):
    response_mock = build_response_mock(
        {
            "address": {
                "country_code": "lu",
                "road": "test road",
                "suburb": "test suburb",
                "postcode": "1999"
            }
        }
    )

    r_session_mock = Mock()
    r_session_mock.get.return_value = response_mock

    with container.requests_session.override(r_session_mock):
        geocoder_service = container.geocoder_service()

        address_data = geocoder_service.get_neighbourhood_and_street(42.4544, 6.435)

    assert address_data["street"] == "test road"
    assert address_data["postcode"] == "1999"
    assert address_data["neighbourhood"] == "test suburb"