from py_reportit.crawler.post_processors.photo_download_pp import PhotoDownload
from py_reportit.crawler.post_processors.geocode_pp import Geocode
from py_reportit.crawler.post_processors.twitter_pp import Twitter

post_processors = [PhotoDownload, Geocode, Twitter]
