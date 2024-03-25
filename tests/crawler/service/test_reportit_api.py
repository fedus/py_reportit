import pytest
import json

from types import SimpleNamespace
from datetime import datetime
from unittest.mock import Mock, call

from py_reportit.crawler.service.reportit_api import ReportFetchException
from py_reportit.shared.model.report import Report
from py_reportit.shared.config.container import Container
from py_reportit.shared.model.report_answer import ReportAnswer
from resources.report_finished_without_photo_with_answer import REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER
from resources.report_finished_with_photo_with_answers import REPORT_FINISHED_WITH_PHOTO_WITH_ANSWERS


@pytest.fixture
def container() -> Container:
    return Container(config={"FETCH_REPORTS_TIMEOUT_SECONDS": 1})


def build_response_mock(data: str, status: int = 200) -> SimpleNamespace:
    return SimpleNamespace(
        raise_for_status=lambda: None,
        json=lambda: json.loads(data),
        text=data,
        status_code=status
    )

def test_get_report_with_answers__finished_without_photo_with_answer(monkeypatch, container: Container):
    reportit_service = container.reportit_service()

    requests_mock = SimpleNamespace(text=REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER)
    monkeypatch.setattr(reportit_service, "fetch_report_page", lambda reportId: requests_mock)

    report = reportit_service.get_report_with_answers(29003)

    assert report.id == 29003
    assert report.title == "title"
    assert report.description == "Public light not working"
    assert report.status == "finished"
    assert report.created_at == datetime(2024, 3, 3, 11, 21)
    assert report.updated_at == datetime(2024, 3, 11, 6, 24)
    assert report.has_photo == False
    assert report.latitude == None
    assert report.longitude == None

    assert len(report.answers) == 1

    answer: ReportAnswer = report.answers[0]

    assert answer.created_at == datetime(2024, 3, 11, 6, 24)
    assert answer.author == "Service Éclairage public"
    assert answer.text == "Merci pour votre engagement."
    assert answer.closing == True
    assert answer.order == 0

def test_get_report_with_answers__finished_with_photo_with_answers(monkeypatch, container: Container):
    reportit_service = container.reportit_service()

    requests_mock = SimpleNamespace(text=REPORT_FINISHED_WITH_PHOTO_WITH_ANSWERS)
    monkeypatch.setattr(reportit_service, "fetch_report_page", lambda reportId: requests_mock)

    report = reportit_service.get_report_with_answers(28931)

    assert report.id == 28931
    assert report.title == "arbre tombé"
    assert report.description == "E Bam ass emgefal teschet Neiduerf a Cents."
    assert report.status == "finished"
    assert report.created_at == datetime(2024, 2, 23, 10, 2)
    assert report.updated_at == datetime(2024, 2, 26, 8, 23)
    assert report.has_photo == True
    assert report.latitude == None
    assert report.longitude == None

    assert len(report.answers) == 2

    answer1: ReportAnswer = report.answers[0]

    assert answer1.created_at == datetime(2024, 2, 26, 8, 22)
    assert answer1.author == "Service Forêts"
    assert answer1.text == "Gudde moien,\nDe Bam deen emgefall ass, ass vun ons weg geholl ginn.\nBourg Brigitte\nService Forêts\nT: 4796-2565"
    assert answer1.closing == False
    assert answer1.order == 0

    answer2: ReportAnswer = report.answers[1]

    assert answer2.created_at == datetime(2024, 2, 26, 8, 23)
    assert answer2.author == "Service Forêts"
    assert answer2.text == "udde moien,\nDe Bam deen emgefall ass, ass vun ons weg geholl ginn.\nBourg Brigitte\nService Forêts\nT: 4796-2565"
    assert answer2.closing == True
    assert answer2.order == 1

def test_get_report_with_lat_lon_from_previous_report(monkeypatch, container: Container):
    reportit_service = container.reportit_service()

    requests_mock = SimpleNamespace(text=REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER)
    monkeypatch.setattr(reportit_service, "fetch_report_page", lambda reportId: requests_mock)

    existing_report = Report(id=29003, latitude=49.603098302908904, longitude=6.132449755187587)

    report = reportit_service.get_report_with_answers(29003, existing_report)

    assert report.id == 29003
    assert report.title == "title"
    assert report.description == "Public light not working"
    assert report.status == "finished"
    assert report.created_at == datetime(2024, 3, 3, 11, 21)
    assert report.updated_at == datetime(2024, 3, 11, 6, 24)
    assert report.has_photo == False
    assert report.latitude == 49.603098302908904
    assert report.longitude == 6.132449755187587

    assert len(report.answers) == 1

    answer: ReportAnswer = report.answers[0]

    assert answer.created_at == datetime(2024, 3, 11, 6, 24)
    assert answer.author == "Service Éclairage public"
    assert answer.text == "Merci pour votre engagement."
    assert answer.closing == True
    assert answer.order == 0

def test_get_report_with_lat_lon_from_reports_data(monkeypatch, container: Container):
    reportit_service = container.reportit_service()

    requests_mock = SimpleNamespace(text=REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER)
    monkeypatch.setattr(reportit_service, "fetch_report_page", lambda reportId: requests_mock)

    reports_data = [
        {
            "title": "a",
            "description": "b",
            "latitude": 48.603098302908904,
            "longitude": 5.132449755187587
        },
        {
            "title": "ti\ntle",
            "description": "Public\nlight\tnot\rworking",
            "latitude": 49.603098302908904,
            "longitude": 6.132449755187587
        },
        {
            "title": "c",
            "description": "d",
            "latitude": 50.603098302908904,
            "longitude": 7.132449755187587
        }
    ]

    report = reportit_service.get_report_with_answers(29003, None, reports_data)

    assert report.id == 29003
    assert report.title == "title"
    assert report.description == "Public light not working"
    assert report.status == "finished"
    assert report.created_at == datetime(2024, 3, 3, 11, 21)
    assert report.updated_at == datetime(2024, 3, 11, 6, 24)
    assert report.has_photo == False
    assert report.latitude == 49.603098302908904
    assert report.longitude == 6.132449755187587

    assert len(report.answers) == 1

    answer: ReportAnswer = report.answers[0]

    assert answer.created_at == datetime(2024, 3, 11, 6, 24)
    assert answer.author == "Service Éclairage public"
    assert answer.text == "Merci pour votre engagement."
    assert answer.closing == True
    assert answer.order == 0

REPORT_RETRIEVAL_FORM_PAGE = """
<!DOCTYPE html>
<html lang="en">
    <head>
		<meta charset="UTF-8">
		<title>Report-it</title>
		
		<!-- Bootstrap CSS -->
		<script type="text/javascript">
//<![CDATA[
window["_csrf_"] = "08573a2818849800338f313c81363f68d0ea48b495bd76b6cfd5d69c60a923fbaf188cdb63c23abf5743357690a6bbcc41f90a774e8aab6a47481f5af131065e352165244b62361e70300d2e1171236c5f96f91ecf666235515c5ef5ac7fbe62377174567ef37076ba53c2d6c488db299fc380d6526757036df0f8b0534812e9d86448a4ab330bff32299a65bb59d9db7008420fac1d6fa79a2a3acbd5e56824";
//]]>
</script><script type="text/javascript" src="/TSbd/08180c6057ab20005479563e119ea9aaf0a13306d18dc03bcfbd0228725104d64ab8d80cd9167547?type=2"></script><script type="text/javascript" src="/ruxitagentjs_ICA27NQVdefgjqrux_10285240307101407.js" data-dtconfig="rid=RID_1113152726|rpid=379251805|domain=vdl.lu|reportUrl=/rb_346f84e3-bc47-4402-a52e-1ece4c66c238|uam=1|app=ea7c4b59f27d43eb|featureHash=ICA27NQVdefgjqrux|msl=153600|vcv=2|rdnt=1|uxrgce=1|bp=3|cuc=m2hr4a5p|srms=2,1,0,0%2Ftextarea%2Cinput%2Cselect%2Coption;0%2Fdatalist;0%2Fform%20button;0%2F%5Bdata-dtrum-input%5D;0%2F.data-dtrum-input;1%2F%5Edata%28%28%5C-.%2B%24%29%7C%24%29|mel=100000|dpvc=1|ssv=4|lastModification=1710552179386|tp=500,50,0,1|agentUri=/ruxitagentjs_ICA27NQVdefgjqrux_10285240307101407.js"></script><link href="/assets/framework/bootstrap-5.2.0-dist/css/bootstrap.min.css" rel="stylesheet">
		
		<!-- Bootstrap & Jquery JavaScript -->
		<script src="/assets/framework/jquery/jquery-3.6.0.min.js"></script>
		<script src="/assets/framework/bootstrap-5.2.0-dist/js/bootstrap.bundle.min.js"></script>
		
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
			<div class="container-lg">
				<div class="card mb-3 border-primary">
<div class="card-header text-white bg-primary">Search for an incident</div>
<div class="card-body"><form class="form-horizontal" id="search_form" method="post" name="form">
									<div class="row">
										<label class="col-sm-12 col-xl-3" for="search_id">Search by incident number :</label>
										<div class="col-sm-9 col-xl-7"><input type="text" class="form-control " id="search_id" name="search_id" value="" placeholder="Enter the incident number" required autocomplete="off">
</div>
										<input id="search_id_9ea5f12ccf149a827a9267791169e67c" name="search_id_9ea5f12ccf149a827a9267791169e67c" type="hidden" value="6581d20c50b93b05b0a2011fd32364e8" autocomplete="off">

										<div class="col-sm-3 col-xl-2"><button type="submit" class="btn btn-primary">Search</button>
</div>
									</div>
								</form></div>
</div>
			</div>
		</main>
    </body>
</html><script id="f5_cspm">(function(){var f5_cspm={f5_p:'ADHOKMCLELIMNFEEJNPLFJKDBMIIGPGLMBFNMLKJBKNFCDKIFKHGHDAMFOJGFMBODBIBNGNHAAHPAPDMIBMAKEEAAABLOHHCJEBOKGCDLIINLCJFFNDCIOIPJPGOLILD',setCharAt:function(str,index,chr){if(index>str.length-1)return str;return str.substr(0,index)+chr+str.substr(index+1);},get_byte:function(str,i){var s=(i/16)|0;i=(i&15);s=s*32;return((str.charCodeAt(i+16+s)-65)<<4)|(str.charCodeAt(i+s)-65);},set_byte:function(str,i,b){var s=(i/16)|0;i=(i&15);s=s*32;str=f5_cspm.setCharAt(str,(i+16+s),String.fromCharCode((b>>4)+65));str=f5_cspm.setCharAt(str,(i+s),String.fromCharCode((b&15)+65));return str;},set_latency:function(str,latency){latency=latency&0xffff;str=f5_cspm.set_byte(str,40,(latency>>8));str=f5_cspm.set_byte(str,41,(latency&0xff));str=f5_cspm.set_byte(str,35,2);return str;},wait_perf_data:function(){try{var wp=window.performance.timing;if(wp.loadEventEnd>0){var res=wp.loadEventEnd-wp.navigationStart;if(res<60001){var cookie_val=f5_cspm.set_latency(f5_cspm.f5_p,res);window.document.cookie='f5avr0281417664aaaaaaaaaaaaaaaa_cspm_='+encodeURIComponent(cookie_val)+';path=/;'+'';}
return;}}
catch(err){return;}
setTimeout(f5_cspm.wait_perf_data,100);return;},go:function(){var chunk=window.document.cookie.split(/\s*;\s*/);for(var i=0;i<chunk.length;++i){var pair=chunk[i].split(/\s*=\s*/);if(pair[0]=='f5_cspm'&&pair[1]=='1234')
{var d=new Date();d.setTime(d.getTime()-1000);window.document.cookie='f5_cspm=;expires='+d.toUTCString()+';path=/;'+';';setTimeout(f5_cspm.wait_perf_data,100);}}}}
f5_cspm.go();}());</script>
"""


def test_extract_report_id_input_field(container: Container):
    reportit_service = container.reportit_service()

    field_name = reportit_service.extract_report_id_input_field(REPORT_RETRIEVAL_FORM_PAGE)

    assert field_name == "search_id"


def test_extract_nonces(container: Container):
    reportit_service = container.reportit_service()

    nonce = reportit_service.extract_nonces(REPORT_RETRIEVAL_FORM_PAGE)

    assert nonce == {"search_id_9ea5f12ccf149a827a9267791169e67c": "6581d20c50b93b05b0a2011fd32364e8"}


# def test_fetch_report_page(container: Container):
#     # Cache empty, successful page fetch
#     r_session_mock = Mock()
#     r_session_mock.crawler_get.return_value = build_response_mock(REPORT_RETRIEVAL_FORM_PAGE)
#     r_session_mock.crawler_post.return_value = build_response_mock(REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER)
#
#     with container.requests_session.override(r_session_mock):
#         reportit_service = container.reportit_service()
#
#         response = reportit_service.fetch_report_page(392)
#
#     r_session_mock.crawler_get.assert_called_once_with(None, params={"session_number": 392})
#     r_session_mock.crawler_post.assert_called_once_with(
#         None,
#         {"search_id": 392, "search_id0": "aa3397b33358a2c43898ec7ac22e6443", "session_number": 392},
#         timeout=1
#     )
#     assert response.text == REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER
#
#     # Cache full, successful page fetch
#     r_session_mock = Mock()
#     r_session_mock.crawler_get.return_value = build_response_mock(REPORT_RETRIEVAL_FORM_PAGE)
#     r_session_mock.crawler_post.return_value = build_response_mock(REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER)
#
#     with container.requests_session.override(r_session_mock):
#         reportit_service = container.reportit_service()
#
#         response = reportit_service.fetch_report_page(392)
#
#     r_session_mock.crawler_get.assert_not_called()
#     r_session_mock.crawler_post.assert_called_once_with(
#         None,
#         {"search_id": 392, "search_id0": "aa3397b33358a2c43898ec7ac22e6443", "session_number": 392},
#         timeout=1
#     )
#     assert response.text == REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER
#
#     # Cache full, unsuccessful page fetch at first try
#     r_session_mock = Mock()
#     r_session_mock.crawler_get.return_value = build_response_mock(REPORT_RETRIEVAL_FORM_PAGE)
#     r_session_mock.crawler_post.side_effect = [
#         build_response_mock(None, 204),
#         build_response_mock(REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER, 200)
#     ]
#
#     with container.requests_session.override(r_session_mock):
#         reportit_service = container.reportit_service()
#
#         response = reportit_service.fetch_report_page(392)
#
#     r_session_mock.crawler_get.assert_called_once_with(None, params={"session_number": 392})
#     r_session_mock.crawler_post.has_calls([
#         call(
#             None,
#             {"search_id": 392, "search_id0": "aa3397b33358a2c43898ec7ac22e6443", "session_number": 392},
#             timeout=1
#         ),
#         call(
#             None,
#             {"search_id": 392, "search_id0": "aa3397b33358a2c43898ec7ac22e6443", "session_number": 392},
#             timeout=1
#         )
#     ], any_order=False)
#     assert r_session_mock.crawler_post.call_count == 2
#     assert response.text == REPORT_FINISHED_WITHOUT_PHOTO_WITH_ANSWER
#
#     # Cache full, unsuccessful page fetch at first and second try
#     r_session_mock = Mock()
#     r_session_mock.crawler_get.return_value = build_response_mock(REPORT_RETRIEVAL_FORM_PAGE)
#     r_session_mock.crawler_post.return_value = build_response_mock(None, 204)
#
#     with container.requests_session.override(r_session_mock):
#         reportit_service = container.reportit_service()
#
#         with pytest.raises(ReportFetchException):
#             reportit_service.fetch_report_page(392)
#
#     r_session_mock.crawler_get.assert_called_once_with(None, params={"session_number": 392})
#     r_session_mock.crawler_post.has_calls([
#         call(
#             None,
#             {"search_id": 392, "search_id0": "aa3397b33358a2c43898ec7ac22e6443", "session_number": 392},
#             timeout=1
#         ),
#         call(
#             None,
#             {"search_id": 392, "search_id0": "aa3397b33358a2c43898ec7ac22e6443", "session_number": 392},
#             timeout=1
#         )
#     ], any_order=False)
#     assert r_session_mock.crawler_post.call_count == 2
