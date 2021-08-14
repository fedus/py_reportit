from py_reportit.model.report import Report

def extract_ids(reports: list[Report]) -> list[int]:
    return list(map(lambda report: report.id, reports))

def get_lowest_and_highest_ids(reports: list[Report]) -> tuple[int]:
    ids = extract_ids(reports)
    return (min(ids), max(ids))
