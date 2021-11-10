from typing import TypedDict


class GeocodeResult(TypedDict):
    street: str
    postcode: str
    neighbourhood: str
    country_code: str

