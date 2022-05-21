import re
from typing import Callable
from toolz import pipe

ANONYMIZER_PAIRS: list[tuple[str, re.Pattern]] = [
    ("[name redacted]",
     re.compile(r"^(?![Ss]ervice|[vV]ielen|[vV]illm|der |[yY]ours |[mM]eilleures |[mM]erci )([a-zA-Z]*|[a-zA-Z]\.) [a-zA-Z]+\s*$", flags=re.MULTILINE)),
    ("[email redacted]", re.compile(
        r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")),
    ("[phone redacted]", re.compile(r"6\d1[- ]?\d{2}[- ]?\d[- ]?\d[- ]?\d{2}"))
]


def build_anonymizer(anonymizer: tuple[str, re.Pattern]) -> Callable[[str], str]:
    def call_anonymizer(text: str) -> str:
        replacement_text = anonymizer[0]
        pattern = anonymizer[1]
        return re.sub(pattern, replacement_text, text)

    return call_anonymizer


ANONYMIZERS: list[Callable[[str], str]] = list(map(build_anonymizer, ANONYMIZER_PAIRS))


def anonymise(text: str) -> str:
    return pipe(text, *ANONYMIZERS)
