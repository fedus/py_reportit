from py_reportit.model.report import Report

def get_lowest_and_highest_ids(reports: list[Report]):
    ids = list(map(lambda report: report.id, reports))
    return (min(ids), max(ids))
