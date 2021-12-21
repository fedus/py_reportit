import requests
import pytest

from datetime import datetime

from py_reportit.shared.config.container import Container

MOCK_REPORTS = [
    {
        "id": 21906,
        "title": "Title 2",
        "description": "Description 2",
        "photo_url": "https://reportit.vdl.lu/photo/21906.jpg",
        "thumbnail_url": "https://reportit.vdl.lu/thumbnail/21906.jpg",
        "latitude": 49.61490385687302,
        "longitude": 6.131666636493964,
        "created_at": "2021-12-21 12:04:21",
        "updated_at": "2021-12-21 13:34:23",
        "key_category": "",
        "id_service": 14,
        "status": "accepted"
    },
    {
        "id": 22323,
        "title": "Title 3",
        "description": "Description 3",
        "photo_url": "https://reportit.vdl.lu/photo/22323.jpg",
        "thumbnail_url": "https://reportit.vdl.lu/thumbnail/22323.jpg",
        "latitude": 49.613667863493866,
        "longitude": 6.134274533706225,
        "created_at": "2021-12-21 12:04:21",
        "updated_at": "2021-12-21 13:34:23",
        "key_category": "",
        "id_service": 14,
        "status": "accepted"
    },
    {
        "id": 21905,
        "title": "Title 1",
        "description": "Description 1",
        "photo_url": None,
        "thumbnail_url": None,
        "latitude": 49.603071407305265,
        "longitude": 6.132741055464037,
        "created_at": "2021-12-21 12:04:21",
        "updated_at": "2021-12-21 13:34:23",
        "key_category": "",
        "id_service": 14,
        "status": "accepted"
    },
]

class RequestsMock:
    pass

@pytest.fixture
def container() -> Container:
    return Container()

def test_get_reports(monkeypatch, container: Container):
    RequestsMock.json = lambda: { "reports": MOCK_REPORTS }
    monkeypatch.setattr(requests, "get", lambda url: RequestsMock)
    
    reportit_service = container.reportit_service()

    reports = reportit_service.get_reports()

    assert len(reports) == 3

    assert reports[0].id == 21905
    assert reports[1].id == 21906
    assert reports[2].id == 22323

    assert reports[0].created_at == datetime(2021, 12, 21, 12, 4, 21)
    assert reports[0].updated_at == datetime(2021, 12, 21, 13, 34, 23)
