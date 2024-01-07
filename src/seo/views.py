from django.shortcuts import render
from django.http import Http404
from .models import Page
from django.template import RequestContext
import re
from logging import getLogger

logger = getLogger(__name__)


def generate_seo_tags(request, path):
    path = "/" + path.strip("/")
    logger.info(f"generate_seo_tags: {path}")
    # Match the incoming URL path with saved Page models,
    # the content Page.url can be a fixed path or a url pattern, use is_pattern to differentiate between the two
    page = None
    model_pk = None
    try:
        page = Page.objects.get(url=path)
        model_pk = None
    except Page.DoesNotExist:
        logger.info(
            f"Page with direct match of url={path} does not exist, looking for pattern match"
        )
        # Handle the case when the URL path is not a fixed path
        pages = Page.objects.filter(is_pattern=True)
        match = None
        for page in pages:
            # parse the url as a regex and match it with the incoming path
            match = re.match(page.url, path)
            if match:
                break
        if not match:
            # return the page with url /
            try:
                page = Page.objects.get(url="/")
                model_pk = None
            except Page.DoesNotExist:
                raise Http404(
                    "Page is not configured for this URL, and no default page is configured."
                )
        else:
            # capture the model_pk from the matched url
            model_pk = match.group(page.model_pk)
    logger.info(f"matched page={page}, model_pk={model_pk}")
    # Get associated tags for the matched page

    # Fetch the associated model using the model key
    selected_model = None
    if model_pk:
        model_calss = page.models_to_select.model_class()
        try:
            key = {page.model_pk: int(model_pk)}
        except ValueError:
            key = {page.model_pk: model_pk}
        try:
            selected_model = model_calss.objects.get(**key)
            logger.info(f"selected_model={selected_model}")
        except model_calss.DoesNotExist:
            logger.error(
                f"Model with app_label={page.models_to_select.app_label} and model={page.models_to_select.model} with {key} does not exist"
            )
            selected_model = None

    def get_nested_attribute_value(obj, attribute_name):
        nested_attributes = attribute_name.split(".")
        nested_value = obj
        for nested_attribute in nested_attributes:
            nested_value = getattr(nested_value, nested_attribute)
            if nested_value is None:
                break
            if callable(nested_value):
                nested_value = nested_value()
        logger.info(
            f"get_nested_attribute_value: {obj}, {attribute_name} -> {nested_value}"
        )
        return nested_value

    def get_value(value: str):
        # parse the attribute value to find any variable used {{<var>}}
        # for each variable
        #  - try to get the value from the model
        #  - if the value is not found, try to get the value from the context
        #  - if the value is not found, return the original value
        original_value = value
        var_pattern = re.compile(r"{{(.*?)}}")
        matches = re.findall(var_pattern, value)
        template_context = RequestContext(request)
        base_url = f"{request.scheme}://{request.META['HTTP_HOST']}"
        extras = {"base_url": base_url}
        get_matcher = lambda x: f"{{{{{x}}}}}"

        for match in matches:
            # match can be the following:
            # - simple attribute name like 'title' or 'description'
            # - nested attribute access like 'movie.title' or 'movie.description'
            # - a variable like 'base_url'
            original_match = match
            match = match.strip()

            try:
                value = value.replace(get_matcher(original_match), str(extras[match]))
            except KeyError:
                try:
                    if "." in match:
                        val = get_nested_attribute_value(selected_model, match)
                    else:
                        val = getattr(selected_model, match)
                    value = value.replace(get_matcher(original_match), str(val))
                except AttributeError:
                    try:
                        if "." in match:
                            val = get_nested_attribute_value(template_context, match)
                        else:
                            val = getattr(template_context, match)

                        value = value.replace(get_matcher(original_match), str(val))
                    except AttributeError:
                        pass
        logger.info(f"get_value: {original_value} -> {value}")
        return value

    # convert the tags to a list of dictionaries, also get the value from model for the attribute values if the attribute value is from model
    tags = [line.strip() for line in page.tags.split("\n")] if page.tags else []
    tags = [get_value(tag) for tag in tags]
    context = {
        "tags": tags,
    }
    return render(request, "seo/seo_tags_template.html", context)
