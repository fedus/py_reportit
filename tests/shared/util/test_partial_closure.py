from py_reportit.shared.config import config
from py_reportit.shared.util import partial_closure

mock_filter_words = ["word1", "word2", "word3"]

def test_get_filter_array(monkeypatch):
    monkeypatch.setitem(config, "PARTIAL_CLOSURE_FILTERS", ",".join(mock_filter_words))

    assert partial_closure.get_filter_array() == mock_filter_words

def test_text_indicates_partial_closure(monkeypatch):
    monkeypatch.setitem(config, "PARTIAL_CLOSURE_FILTERS", ",".join(mock_filter_words))

    assert partial_closure.text_indicates_partial_closure("Bla bla WOrD1 nana") == True
    assert partial_closure.text_indicates_partial_closure("WORD2") == True
    assert partial_closure.text_indicates_partial_closure("\n\nLorem ispum dolorword3abcdef") == True
    assert partial_closure.text_indicates_partial_closure("Bla bla nana") == False
