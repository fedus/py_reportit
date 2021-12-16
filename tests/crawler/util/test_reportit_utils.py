from py_reportit.crawler.util.reportit_utils import *

test_string_1 = "One two three"
test_string_2 = "Four five six seven eight nine"

test_string_3 = "ééééé ààààà"
test_string_4 = "😄 h ello 😄 nice day"

def test_calc_expected_status_length():
    assert calc_expected_status_length(test_string_1) == 13
    assert calc_expected_status_length(test_string_2) == 30

    assert calc_expected_status_length(test_string_3) == 11
    assert calc_expected_status_length(test_string_4) == 21

def test_twitter_wrap_chunks():
    wrapped_1 = twitter_wrap(test_string_1)

    assert len(wrapped_1) == 1
    assert wrapped_1[0] == test_string_1

    wrapped_2 = twitter_wrap(test_string_2, 11)

    assert len(wrapped_2) == 3
    assert wrapped_2[0] == "Four five"
    assert wrapped_2[1] == "six seven"
    assert wrapped_2[2] == "eight nine"

    # Becomes "ééééé", "ààààà"
    wrapped_3 = twitter_wrap(test_string_3, 8)

    assert len(wrapped_3) == 2
    assert wrapped_3[0] == "ééééé"
    assert wrapped_3[1] == "ààààà"

    # Becomes "😄", "h e", "llo", "😄 ", "nic", "e", "day"
    wrapped_4 = twitter_wrap(test_string_4, 3)

    assert len(wrapped_4) == 7
    assert wrapped_4[0] == "😄"
    assert wrapped_4[1] == "h e"
    assert wrapped_4[2] == "llo"
    assert wrapped_4[3] == "😄 "
    assert wrapped_4[4] == "nic"
    assert wrapped_4[5] == "e"
    assert wrapped_4[6] == "day"
