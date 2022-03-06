from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from py_reportit.web.routers import photos, reports, utilities, votes
from py_reportit.shared.config.container import Container
from py_reportit.shared.config import config

description = """
The Report-It Unchained API lets you do awesome stuff based on a repository of all Report-Its submitted to the City of Luxembourg's Report-It system. 🚀

### Reports

You can retrieve reports in three different ways:
- paginated and using filters (recommended)
- all at once (strongly discouraged)
- by ID

The `service` key of a report is inferred and a best guess based on the answers of that report, which inversely means that reports without answers do not have a value here.

Reports are enriched with meta data, such as the **language** (guessed using CLD2, `un` stands for unknown), reverse-geolocated **address data** of the report's location, and **all answers** given by the city.

You should **always** prefer the paginated endpoint over the endpoint that delivers all reports (ie a database dump), unless you **really** want to grab a complete copy of all the data at once.
If you do download the whole database, be warned that it may take some time to process your request.

### Photos

The photo endpoint allows you to download the photo relating to a given report ID.
"""

tags_metadata = [
    {
        "name": "reports",
        "description": "Search, filter and retrieve reports.",
    },
    {
        "name": "votes",
        "description": "Cast and retrieve votes"
    },
    {
        "name": "utilities",
        "description": "Query other useful information about reports."
    },
    {
        "name": "photos",
        "description": "Retrieve photos based on report IDs.",
    },
]

app = FastAPI(
    title="Report-It Unchained API",
    description=description,
    version="0.1.0",
    #terms_of_service="https://zug.lu/rprtt/terms/",
    contact={
        "name": "ZUG - Zentrum fir Urban Gerechtegkeet",
        "url": "https://zug.lu",
        "email": "info@zug.lu",
    },
    #license_info={
    #    "name": "Apache 2.0",
    #    "url": "https://www.apache.org/licenses/LICENSE-2.0.html",
    #},
    openapi_tags=tags_metadata,
)

app.include_router(reports.router)
app.include_router(photos.router)
app.include_router(votes.router)
app.include_router(utilities.router)
app.mount("/static/photos", StaticFiles(directory=config.get('PHOTO_DOWNLOAD_FOLDER')), name="static")

container = Container()

container.config.from_dict(config)

container.wire(modules=[__name__], packages=[".routers"])

app.container = container
