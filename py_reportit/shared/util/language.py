from pycld2 import detect

def detect_most_likely_language(text) -> str:
    return detect(text)[2][0][1]
