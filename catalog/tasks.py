import logging

from django.urls import reverse
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .celery import app


@app.task
def send_verification_email(user_id):
    UserModel = get_user_model()
    try:
        user = UserModel.objects.get(pk=user_id)
        send_mail(
            'Verify your QuickPublisher account',
            'Follow this link to verify your account: '
                'http://localhost:8000%s' % reverse('verify', kwargs={'uuid': str(user.verification_uuid)}),
            'from@quickpublisher.dev',
            [user.email],
            fail_silently=False,
        )
    except UserModel.DoesNotExist:
        logging.warning("Tried to send verification email to non-existing use")


#from celery import Celery

#celery -A catalog.tasks worker -l info

#app = Celery('catalog', broker='redis://localhost:6379',  include=['catalog.tasks'])
i = 1 +2

#app.conf.update(Celery_TAST_RESULT_EXPIRES=3600,)

if __name__ == '__main__':
  #  app.start()
    pass
#@app.task
def add(x, y, newdoc):
    newdoc.save()
    return x + y