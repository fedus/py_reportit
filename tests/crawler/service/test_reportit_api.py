import pytest

from types import SimpleNamespace
from datetime import datetime
from unittest.mock import Mock

from py_reportit.shared.config.container import Container
from py_reportit.shared.model.report_answer import ReportAnswer

@pytest.fixture
def container() -> Container:
    return Container()

def build_response_mock(data: dict) -> SimpleNamespace:
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: data
    )

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

REPORT_RETRIEVAL_FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
    <head>
		<meta charset="UTF-8">
		<title>Report-it</title>

		<!-- Bootstrap CSS -->
		<link href="/assets/framework/bootstrap-5.1.3-dist/css/bootstrap.min.css" rel="stylesheet" integrity="sha384-1BmE4kWBq78iYhFldvKuhfTAU6auU8tT94WrHftjDbrCEXSU1oBoqyl2QvZ6jIW3" crossorigin="anonymous">

		<!-- Bootstrap & Jquery JavaScript -->
		<script src="/assets/framework/jquery/jquery-3.6.0.min.js"></script>
		<script src="/assets/framework/bootstrap-5.1.3-dist/js/bootstrap.bundle.min.js"></script>

		<!-- Icons -->
		<link rel="stylesheet" href="/assets/font/bootstrap-icons-1.5.0/bootstrap-icons.css">

		<!-- Piwik -->
<script type="text/javascript">
  var _paq = _paq || [];
  /* tracker methods like "setCustomDimension" should be called before "trackPageView" */
  _paq.push(['trackPageView']);
  _paq.push(['enableLinkTracking']);
  (function() {
    var u="//piwik.vdl.lu/";
    _paq.push(['setTrackerUrl', u+'piwik.php']);
    _paq.push(['setSiteId', '19']);
    var d=document, g=d.createElement('script'), s=d.getElementsByTagName('script')[0];
    g.type='text/javascript'; g.async=true; g.defer=true; g.src=u+'piwik.js'; s.parentNode.insertBefore(g,s);
  })();
</script>
<!-- End Piwik Code -->
    </head>
	<body>
		<main>
			<div class="container-md">
				<div class="card mb-3 border-primary">
<div class="card-header text-white bg-primary">Search for an incident</div>
<div class="card-body"><form class="form-horizontal" id="search_form" method="post" name="form">
									<div class="row">
										<label class="col-sm-12 col-xl-3" for="search_id">Search by incident number :</label>
										<div class="col-sm-9 col-xl-7"><input type="text" class="form-control " id="search_id" name="search_id" value="" placeholder="Enter the incident number" required autocomplete="off">
</div>
										<input id="search_id0" name="search_id0" type="hidden" value="aa3397b33358a2c43898ec7ac22e6443" autocomplete="off">
										<div class="col-sm-3 col-xl-2"><button type="submit" class="btn btn-primary">Search</button>
</div>
									</div>
								</form></div>
</div>
<br>
<a href="./index.php?lang=en" role="button" class="btn btn-primary"><span class="bi bi-chevron-left" title="" aria-hidden="true"></span> Back</a>
			</div>
		</main>
    </body>
</html>
"""

def test_extract_report_id_input_field(container: Container):
    reportit_service = container.reportit_service()

    field_name = reportit_service.extract_report_id_input_field(REPORT_RETRIEVAL_FORM_PAGE)

    assert field_name == "search_id"

def test_extract_nonces(container: Container):
    reportit_service = container.reportit_service()

    nonce = reportit_service.extract_nonces(REPORT_RETRIEVAL_FORM_PAGE)

    assert nonce == { "search_id0": "aa3397b33358a2c43898ec7ac22e6443" }
