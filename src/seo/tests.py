from django.test import TestCase
from seo.models import Page, MetaValue
from api.models.movie import Movie
from django.contrib.contenttypes.models import ContentType


# Create your tests here for the SEO app.
class TestSEO(TestCase):
    def setUp(self):
        # set HTTP_HOST on self.client
        self.client.defaults["HTTP_HOST"] = "testhost"

    def test_generate_seo_tags_with_path_static_content(self):
        Page.objects.create(
            url="/about-us",
            is_pattern=False,
            tags="""
                                   <title>About Us</title>
                                    <meta name="description" content="About Us">
                                   """,
        )
        response = self.client.get("/about-us/")

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>About Us</title>")
        self.assertContains(response, '<meta name="description" content="About Us">')

    def test_generate_seo_tags_with_meta_base_url(self):
        description = "Some test description"
        MetaValue.objects.create(name="description", value=description)

        Page.objects.create(
            url="/about-us",
            is_pattern=False,
            tags="""
                                   <title>About Us</title>
                                    <meta name="description" content="{{meta.description}}">
                                    <meta name="base_url" content="{{base_url}}">
                                   """,
        )
        response = self.client.get("/about-us/")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>About Us</title>")
        self.assertContains(
            response, f'<meta name="description" content="{description}">'
        )
        self.assertContains(
            response, '<meta name="base_url" content="http://testhost">'
        )

    def test_generate_seo_tags_with_path_and_model_pk_with_int(self):
        description = "Some test description"
        MetaValue.objects.create(name="description", value=description)
        Movie.objects.create(
            id=1,
            title="Test Movie",
            about="Test About",
            runtime=100,
            publish_on="2020-01-01T00:00:00Z",
        )
        movie = Movie.objects.get(id=1)
        Page.objects.create(
            url="/movie/(?P<id>\d+)/(?P<slug>[\w-]+)",
            is_pattern=True,
            tags="""
                                   <title>{{movie.title}}</title>
                                    <meta name="description" content="{{meta.description}}">
                                    <meta name="description" content="{{movie.about}}">
                                    <meta name="publish_date" content="{{movie.publish_on}}">
                                   """,
            models_to_select=ContentType.objects.get(app_label="api", model="movie"),
            model_pk="id",
        )
        response = self.client.get("/movie/1/test-movie")
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "<title>Test Movie</title>")
        self.assertContains(
            response, f'<meta name="description" content="{description}">'
        )
        self.assertContains(
            response, f'<meta name="description" content="{movie.about}">'
        )
        self.assertContains(
            response, f'<meta name="publish_date" content="{movie.publish_on}">'
        )

    def test_generate_seo_tags_with_path_and_model_pk_and_no_match(self):
        Page.objects.create(
            url="/movie/(?P<id>\d+)/(?P<slug>[\w-]+)",
            is_pattern=True,
            tags="""
                                   <title>{{movie.title}}</title>
                                    <meta name="description" content="{{meta.description}}">
                                    <meta name="description" content="{{movie.about}}">
                                    <meta name="publish_date" content="{{movie.publish_on}}">
                                   """,
            models_to_select=ContentType.objects.get(app_label="api", model="movie"),
            model_pk="id",
        )
        response = self.client.get("/movie/1/test-movie")
        self.assertEqual(response.status_code, 404)

    def test_generate_seo_tags_with_path_no_match(self):
        Page.objects.create(
            url="/movie/(?P<id>\d+)/(?P<slug>[\w-]+)",
            is_pattern=True,
            tags="""
                                   <title>{{movie.title}}</title>
                                    <meta name="description" content="{{meta.description}}">
                                    <meta name="description" content="{{movie.about}}">
                                    <meta name="publish_date" content="{{movie.publish_on}}">
                                   """,
            models_to_select=ContentType.objects.get(app_label="api", model="movie"),
            model_pk="id",
        )
        response = self.client.get("/movie/")
        self.assertEqual(response.status_code, 404)

    def test_dont_allow_admin_pages(self):
        with self.assertRaises(ValueError):
            Page.objects.create(
                url="/admin",
                is_pattern=False,
                tags="""
                                       <title>About Us</title>
                                        <meta name="description" content="About Us">
                                       """,
            )
