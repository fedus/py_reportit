from py_reportit.crawler.post_processors.photo_download_pp import PhotoDownload
from py_reportit.crawler.post_processors.answer_pp import AnswerFetch
from py_reportit.crawler.post_processors.twitter_pp import Twitter

post_processors = [PhotoDownload, AnswerFetch, Twitter]
