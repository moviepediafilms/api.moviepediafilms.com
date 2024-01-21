from django.shortcuts import render
from django.http import Http404
from .models import Page, MetaValue
from django.template import RequestContext
import re
from logging import getLogger

logger = getLogger(__name__)


def get_meta_values():
    """
    list of dictionaries containing name and value
    append all name with meta. prefix
    return as a dictionary
    """
    meta_values = MetaValue.objects.all()
    return {"meta." + meta_value.name: meta_value.value for meta_value in meta_values}


def _get_nested_attribute_value(obj, attribute_name):
    nested_attributes = attribute_name.split(".")
    nested_value = obj
    for nested_attribute in nested_attributes:
        nested_value = getattr(nested_value, nested_attribute)
        if nested_value is None:
            break
        if callable(nested_value):
            nested_value = nested_value()
    logger.debug(
        f"get_nested_attribute_value: {obj}, {attribute_name} -> {nested_value}"
    )
    return nested_value


def _get_value(value: str, selected_model_instance, request, extras):
    """
    parse the attribute value to find any variable used {{<var>}}
    for each variable
      - try to get the value from the model
      - if the value is not found, try to get the value from the context
      - if the value is not found, return the original value
    """
    original_value = value
    var_pattern = re.compile(r"{{(.*?)}}")
    matches = re.findall(var_pattern, value)
    template_context = RequestContext(request)

    get_matcher = lambda x: f"{{{{{x}}}}}"
    modal_name_lower = selected_model_instance.__class__.__name__.lower()

    for match in matches:
        # match can be the following:
        # - direct attribute name like 'meta.title' or 'meta.description' from extras
        # - nested attribute access like 'movie.title' or 'movie.description'
        # - a variable like 'base_url'
        original_match = match
        match = match.strip()

        try:
            value = value.replace(get_matcher(original_match), str(extras[match]))
        except KeyError:
            try:
                if "." in match:
                    model_name, attribute_name = match.split(".", 1)
                    if model_name == modal_name_lower:
                        val = _get_nested_attribute_value(
                            selected_model_instance, attribute_name
                        )
                    else:
                        val = _get_nested_attribute_value(
                            selected_model_instance, match
                        )
                else:
                    val = getattr(selected_model_instance, match)
                value = value.replace(get_matcher(original_match), str(val))
            except AttributeError:
                try:
                    if "." in match:
                        val = _get_nested_attribute_value(template_context, match)
                    else:
                        val = getattr(template_context, match)

                    value = value.replace(get_matcher(original_match), str(val))
                except AttributeError:
                    pass
    logger.debug(f"get_value: {original_value} -> {value}")
    return value


def _get_model(model_pk: str, page: Page):
    """return the model instance for the given model_pk,
    if model_pk is None, return None
    if model_pk is not None, but the model does not exist, raise Http404"""
    selected_model = None
    if model_pk:
        model_class = page.models_to_select.model_class()
        try:
            key = {page.model_pk: int(model_pk)}
        except ValueError:
            key = {page.model_pk: model_pk}
        try:
            selected_model = model_class.objects.get(**key)
            logger.info(f"selected_model={selected_model}")
        except model_class.DoesNotExist:
            logger.error(
                f"Model with app_label={page.models_to_select.app_label} and model={page.models_to_select.model} with {key} does not exist"
            )
            raise Http404()
    return selected_model


def _get_extras(request):
    host = request.META.get("HTTP_HOST", "")
    base_url = f"{request.scheme}://{host}"
    extras = {"base_url": base_url}
    extras.update(get_meta_values())
    return extras


def _get_page_and_model_pk(path):
    """
    Match the incoming URL path with saved Page models,
    the content Page.url can be a fixed path or a url pattern, use is_pattern to differentiate between the two
    """
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
            raise Http404()
        else:
            # capture the model_pk from the matched url
            model_pk = match.group(page.model_pk)
    return page, model_pk


def generate_seo_tags(request, path=None):
    path = path or request.path
    path = "/" + path.strip("/")
    logger.info(f"generate_seo_tags: {path}")

    page, model_pk = _get_page_and_model_pk(path)
    logger.info(f"matched page={page}, model_pk={model_pk}")

    selected_model_instance = _get_model(model_pk, page)
    extras = _get_extras(request)

    tags = [line.strip() for line in page.tags.split("\n")] if page.tags else []
    tags = [_get_value(tag, selected_model_instance, request, extras) for tag in tags]
    return render(
        request,
        "seo/seo_tags_template.html",
        {
            "tags": tags,
        },
    )
