from typing import TypedDict


class GeocodeResult(TypedDict):
    street: str
    postcode: int
    neighbourhood: str
