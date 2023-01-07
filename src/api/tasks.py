from moviepedia import celery_app
from django.core.management import call_command


@celery_app.task(bind=True)
def run_management(self, name):
    if name in [
        "updateengagementscore",
        "updatepopscore",
        "updateroles",
        "updatetopcreators",
        "updatetopcurators",
        "updatemovierecommends",
        "youtubelinkfix",
    ]:
        call_command(name)
