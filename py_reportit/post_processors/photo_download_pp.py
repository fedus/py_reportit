from py_reportit.post_processors.abstract_pp import AbstractPostProcessor


class PhotoDownload(AbstractPostProcessor):

    def process(self):
        print("Process.")
