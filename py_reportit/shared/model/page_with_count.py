from typing import TypedDict
from sqlakeyset import Page

class PageWithCount(TypedDict):
    page: Page
    total_count: int
