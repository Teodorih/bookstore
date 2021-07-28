from celery import Celery

app = Celery('catalog', broker='redis://localhost:6379',  include=['catalog.tasks'])
i = 1 +2

app.conf.update(Celery_TAST_RESULT_EXPIRES=3600,)

if __name__ == '__main__':
    app.start()

@app.task
def add(x, y):
    return x + y