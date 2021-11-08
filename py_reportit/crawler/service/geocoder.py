import requests
import logging

from string import Template

from py_reportit.shared.model.geocode_result import GeocodeResult

logger = logging.getLogger(f"py_reportit.{__name__}")

class GeocoderService:

    def __init__(self, config):
        self.config = config
        self.request_uri_template = Template(self.config.get('GEOCODE_REQUEST_URI_TEMPLATE'))
        self.api_key = self.config.get('GEOCODE_API_KEY')

    def get_neighbourhood_and_street(self, latitude: float, longitude: float) -> GeocodeResult:
        logger.debug(f"Geolocating for latitude {latitude} and longitude {longitude}")

        request_url = self.request_uri_template.substitute({
            'API_KEY': self.api_key,
            'LAT': latitude,
            'LON': longitude
        })

        r = requests.get(request_url)
        r.raise_for_status()
        resp_json = r.json()

        address_json = resp_json['address']

        street = address_json['road'] if 'road' in address_json else None
        postcode = int(address_json['postcode']) if 'postcode' in address_json else None
        neighbourhood = address_json['suburb'] if 'suburb' in address_json else None

        return GeocodeResult(
            street=street,
            postcode=postcode,
            neighbourhood=neighbourhood
        )
