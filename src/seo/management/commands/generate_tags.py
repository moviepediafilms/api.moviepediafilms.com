from django.core.management.base import BaseCommand
from django.contrib.contenttypes.models import ContentType
from django.db import transaction
from django.db.utils import IntegrityError
from seo.models import Page
import json


class Command(BaseCommand):
    help = "Generate page models for specified URLs from a JSON file"

    def add_arguments(self, parser):
        parser.add_argument("json_file", type=str)

    def handle(self, *args, **options):
        with open(options["json_file"], "r") as f:
            json_data = json.load(f)
            with transaction.atomic():
                for page in json_data:
                    try:
                        models_to_select = page.get("models_to_select")
                        model_pk = page.get("model_pk")
                        if models_to_select:
                            models_to_select = ContentType.objects.get(
                                pk=models_to_select
                            )
                        page_model = Page.objects.create(
                            url=page.get("url"),
                            is_pattern=page.get("is_pattern", False),
                            model_pk=model_pk,
                            models_to_select=models_to_select,
                            tags=page.get("tags"),
                        )
                        page_model.save()
                    except IntegrityError as e:
                        self.stdout.write(
                            self.style.ERROR(
                                "Error while creating page model for {}".format(
                                    page["url"]
                                )
                            )
                        )
                        self.stdout.write(self.style.ERROR(e))
                        continue
                    except Exception as e:
                        self.stdout.write(
                            self.style.ERROR(
                                "Error while creating page model for {}".format(
                                    page["url"]
                                )
                            )
                        )
                        self.stdout.write(self.style.ERROR(e))
                        continue
                    else:
                        self.stdout.write(
                            self.style.SUCCESS(
                                "Page model for {} created successfully".format(
                                    page["url"]
                                )
                            )
                        )
