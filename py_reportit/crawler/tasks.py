from .celery import app

@app.task
def add(x, y):
    if x < 10:
        add.logger("help")
        add.delay(x+1,y+1)
    return x + y
