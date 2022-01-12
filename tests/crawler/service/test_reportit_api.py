import pytest

from types import SimpleNamespace
from datetime import datetime

from py_reportit.shared.config.container import Container
from py_reportit.shared.model.report_answer import ReportAnswer

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

@pytest.fixture
def container() -> Container:
    return Container()

"""
def test_get_reports(monkeypatch, container: Container):
    requests_mock = SimpleNamespace(json=lambda: { "reports": MOCK_REPORTS })
    monkeypatch.setattr(requests, "get", lambda url: requests_mock)

    reportit_service = container.reportit_service()

    reports = reportit_service.get_reports()

    assert len(reports) == 3

    assert reports[0].id == 21905
    assert reports[1].id == 21906
    assert reports[2].id == 22323

    assert reports[0].created_at == datetime(2021, 12, 21, 12, 4, 21)
    assert reports[0].updated_at == datetime(2021, 12, 21, 13, 34, 23)
"""

REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER = """
<!DOCTYPE html>
<html>
    <head>
		<meta charset="UTF-8">
		<title>Report-it</title>
    </head>
	<body>
		<div class="container">
			<div class="panel panel-primary">
									<div class="card-header"><b>Incident <span class="badge">392</span> : Title ABCD</b></div>
						<div class="card-body">
							<div class="row">
								<div class="col-xs-12 col-md-6">
									<div class="panel card">
										<div class="card-body">
											<b>Description :</b><br>Very nice description.										</div>
									</div>
									<table class="table">
										<tbody>
											<tr><th scope="row">Status :</th><td><span class="badge bg-success">Closed</span></td></tr>
																						<tr><th scope="row">Sent on :</th><td>13.03.2013 18:24</td></tr>
										</tbody>
									</table>
								</div>
								<div class="col-xs-12 col-md-6">
									<p><img alt="" src="https://maps.googleapis.com/maps/api/staticmap?center=49.595054,6.1506319&zoom=16&size=530x250&markers=icon:https://reportit.vdl.lu/assets/images/map-pins/pin-green-2.png%7C49.595054,6.1506319&sensor=false&key=AIzaSyDspvLyvhli0Vb9Hexspgua2TtibXjbJZI" class="img-thumbnail" /></p>
																	</div>
							</div>
							<div class="row">
								<div class="col-xs-12 col-md-6">
									<br>
																	</div>
								<div class="col-xs-12 col-md-6">
									<br>
									<p><b>Comments: </b></p>												<div class="panel card">
													<div class="card-header">
														Closed by <i>Service Party</i> on 15.03.2013 13:53													</div>
																													<div class="card-body">
																	Ceci n'est pas une pipe															</div>
																											</div>
																				</div>
							</div>
						</div>
									</div>
			<a class="btn btn-primary" href="./index.php?lang=en" role="button"><span class="glyphicon glyphicon-chevron-left" aria-hidden="true"></span> Back</a>
		</div>
    </body>
</html>
"""

def test_get_report_with_answers__finished_without_photo_with_answer(monkeypatch, container: Container):
    reportit_service = container.reportit_service()

    requests_mock = SimpleNamespace(text=REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER)
    monkeypatch.setattr(reportit_service, "fetch_report_page", lambda reportId: requests_mock)

    report = reportit_service.get_report_with_answers(392)

    assert report.id == 392
    assert report.title == "Title ABCD"
    assert report.description == "Very nice description."
    assert report.status == "finished"
    assert report.created_at == datetime(2013, 3, 13, 18, 24)
    assert report.updated_at == datetime(2013, 3, 15, 13, 53)
    assert report.has_photo == False
    assert report.latitude == "49.595054"
    assert report.longitude == "6.1506319"

    assert len(report.answers) == 1

    answer: ReportAnswer = report.answers[0]

    assert answer.created_at == datetime(2013, 3, 15, 13, 53)
    assert answer.author == "Service Party"
    assert answer.text == "Ceci n'est pas une pipe"
    assert answer.closing == True
    assert answer.order == 0

REPORT_FINISHED_WITH_PHOTO_WITH_ANSWERS = """
<!DOCTYPE html>
<html>
    <head>
		<meta charset="UTF-8">
		<title>Report-it</title>
    </head>
	<body>
		<div class="container">
			<div class="panel panel-primary">
									<div class="card-header"><b>Incident <span class="badge">499</span> : En Titel mat Ümläut</b></div>
						<div class="card-body">
							<div class="row">
								<div class="col-xs-12 col-md-6">
									<div class="panel card">
										<div class="card-body">
											<b>Description :</b><br>										</div>
									</div>
									<table class="table">
										<tbody>
											<tr><th scope="row">Status :</th><td><span class="badge bg-success">Closed</span></td></tr>
																						<tr><th scope="row">Sent on :</th><td>28.06.2013 12:03</td></tr>
										</tbody>
									</table>
								</div>
								<div class="col-xs-12 col-md-6">
									<p><img alt="" src="https://maps.googleapis.com/maps/api/staticmap?center=49.610428698086,6.1251032352448&zoom=16&size=530x250&markers=icon:https://reportit.vdl.lu/assets/images/map-pins/pin-green-2.png%7C49.610428698086,6.1251032352448&sensor=false&key=AIzaSyDspvLyvhli0Vb9Hexspgua2TtibXjbJZI" class="img-thumbnail" /></p>
																	</div>
							</div>
							<div class="row">
								<div class="col-xs-12 col-md-6">
									<br>
								<p><img alt="" src="binary-image-data" class="img-thumbnail" /></p>								</div>
								<div class="col-xs-12 col-md-6">
									<br>
									<p><b>Comments: </b></p>												<div class="panel card">
													<div class="card-header">
														Submitted by <i>Service Party</i> on 01.07.2013 08:35													</div>
																													<div class="card-body">
																	Daat ass fier de Service Fête.Mir hun daat viruginn.																</div>
																											</div>
																								<div class="panel card">
													<div class="card-header">
														Submitted by <i>Service Fête</i> on 04.07.2013 12:18													</div>
																													<div class="card-body">
																	D'Avenue Monterey ass eng Staatsstrooss. An dësem Fall ass de Service Fiesta zoustänneg. 																</div>
																											</div>
																								<div class="panel card">
													<div class="card-header">
														Closed by <i>Service Fiesta</i> on 04.07.2013 12:19													</div>
																									</div>
																				</div>
							</div>
						</div>
									</div>
			<a class="btn btn-primary" href="./index.php?lang=en" role="button"><span class="glyphicon glyphicon-chevron-left" aria-hidden="true"></span> Back</a>
		</div>
    </body>
</html>
"""

def test_get_report_with_answers__finished_with_photo_with_answers(monkeypatch, container: Container):    
    reportit_service = container.reportit_service()

    requests_mock = SimpleNamespace(text=REPORT_FINISHED_WITH_PHOTO_WITH_ANSWERS)
    monkeypatch.setattr(reportit_service, "fetch_report_page", lambda reportId: requests_mock)

    report = reportit_service.get_report_with_answers(499)

    assert report.id == 499
    assert report.title == "En Titel mat Ümläut"
    assert report.description == None
    assert report.status == "finished"
    assert report.created_at == datetime(2013, 6, 28, 12, 3)
    assert report.updated_at == datetime(2013, 7, 4, 12, 19)
    assert report.has_photo == True
    assert report.latitude == "49.610428698086"
    assert report.longitude == "6.1251032352448"

    assert len(report.answers) == 3

    answer1: ReportAnswer = report.answers[0]

    assert answer1.created_at == datetime(2013, 7, 1, 8, 35)
    assert answer1.author == "Service Party"
    assert answer1.text == "Daat ass fier de Service Fête.Mir hun daat viruginn."
    assert answer1.closing == False
    assert answer1.order == 0

    answer2: ReportAnswer = report.answers[1]

    assert answer2.created_at == datetime(2013, 7, 4, 12, 18)
    assert answer2.author == "Service Fête"
    assert answer2.text == "D'Avenue Monterey ass eng Staatsstrooss. An dësem Fall ass de Service Fiesta zoustänneg."
    assert answer2.closing == False
    assert answer2.order == 1

    answer3: ReportAnswer = report.answers[2]

    assert answer3.created_at == datetime(2013, 7, 4, 12, 19)
    assert answer3.author == "Service Fiesta"
    assert answer3.text == ""
    assert answer3.closing == True
    assert answer3.order == 2
