import logging
import os
from celery import Celery
from celery.signals import after_setup_logger

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'locallibrary.settings')

app = Celery('locallibrary')
app.config_from_object('django.conf:settings')

app.conf.update({
    'broker_url': 'filesystem://',
    'broker_transport_options': {
        'data_folder_in': './broker/out',
        'data_folder_out': './broker/out',
        'data_folder_processed': './broker/processed'
    },
    'result_persistent': False,
    'task_serializer': 'json',
    'result_serializer': 'json',
    'accept_content': ['json']})

logger = logging.getLogger(__name__)


for f in ['./broker/out', './broker/processed']:
    if not os.path.exists(f):
        os.makedirs(f)



@after_setup_logger.connect
def setup_loggers(logger, *args, **kwargs):
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # add filehandler
    fh = logging.FileHandler('logs.log')
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(formatter)
    logger.addHandler(fh)

@app.task()
def add(x, y):
    logger.info('Found addition')
    logger.info('Added {0} and {1} to result, '.format(x,y))
    return x+y


if __name__ == '__main__':
    task = add.s(x=2, y=3).delay()

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()

#celery -A catalog worker --loglevel=debug --concurrency=4

#celery --app=locallibrary.catalog worker --concurrency=1 --loglevel=INFO
