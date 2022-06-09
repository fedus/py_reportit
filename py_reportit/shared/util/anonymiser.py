import re
from typing import Callable
from toolz import pipe

ANONYMISER_PAIRS: list[tuple[str, re.Pattern]] = [
    ("[name removed]",
     re.compile(r"^(?![Ss]ervice|[vV]ielen|[vV]illm|der |[yY]ours |[mM]eilleures |[mM]erci )([A-Za-zÀ-ÖØ-öø-ÿ]*|[A-Za-zÀ-ÖØ-öø-ÿ]\.) [A-Za-zÀ-ÖØ-öø-ÿ]+\s*$", flags=re.MULTILINE)),
    (r"\1 [name removed]",
     re.compile(r"(monsieur|madame|här|herr|frau|dear) +(([A-Za-zÀ-ÖØ-öø-ÿ]* |[A-Za-zÀ-ÖØ-öø-ÿ]\. )?[A-Za-zÀ-ÖØ-öø-ÿ]+)\s*[,\.]?$", flags=re.MULTILINE|re.IGNORECASE)),
    (r"\1 [name removed] ",
     re.compile(r"([mM]onsieur|[mM]adame|[hH]är|[hH]err|[fF]rau) +(([A-Z][A-Za-zÀ-ÖØ-öø-ÿ]+ |[A-Z]\.? )?[A-Z][A-Za-zÀ-ÖØ-öø-ÿ]+)\s*", flags=re.MULTILINE)),
    ("[email removed]", re.compile(
        r"([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\"([]!#-[^-~ \t]|(\\[\t -~]))+\")@([-!#-'*+/-9=?A-Z^-~]+(\.[-!#-'*+/-9=?A-Z^-~]+)*|\[[\t -Z^-~]*])")),
    ("[phone removed]", re.compile(r"\d(?:\W*\d){5,}"))
]


def build_anonymiser(anonymiser: tuple[str, re.Pattern]) -> Callable[[str], str]:
    def call_anonymiser(text: str) -> str:
        replacement_text = anonymiser[0]
        pattern = anonymiser[1]
        return re.sub(pattern, replacement_text, text)

    return call_anonymiser


ANONYMISERS: list[Callable[[str], str]] = list(map(build_anonymiser, ANONYMISER_PAIRS))


def anonymise(text: str) -> str:
    return pipe(text, *ANONYMISERS)
