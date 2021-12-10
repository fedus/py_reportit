from py_reportit.shared.config import config

def get_filter_array() -> list[str]:
    return config.get('PARTIAL_CLOSURE_FILTERS', '').split(',')

def text_indicates_partial_closure(text: str) -> bool:
    return any(filter_term.lower() in text.lower() for filter_term in get_filter_array())
