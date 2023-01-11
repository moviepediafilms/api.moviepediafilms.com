import datetime
from logging import getLogger

import httplib2
from google.oauth2 import id_token
from google.auth.transport import requests
from googleapiclient import discovery
from oauth2client import client

from django.conf import settings
from rest_framework.authtoken.views import ObtainAuthToken
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework import views, viewsets, mixins
from api.serializers.auth import (
    TokenSerializer,
    VerifyEmailSerializer,
    ActivationResentSerializer,
    ForgotPasswordSerializer,
    ResetPasswordSerializer,
)
from api.models import User, Profile


logger = getLogger("api.auth")


class AuthTokenView(ObtainAuthToken):
    "Auth view expects `username` and `password` as POST payload"

    serializer_class = TokenSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data["user"]
        token, _ = Token.objects.get_or_create(user=user)
        return Response({"token": token.key, "user_id": user.pk, "email": user.email})


class AccountVerifyView(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    permission_classes = []
    queryset = Token.objects

    def get_serializer_class(self):
        serializer_class = {
            "verify": VerifyEmailSerializer,
            "resend": ActivationResentSerializer,
            "forgot": ForgotPasswordSerializer,
            "reset": ResetPasswordSerializer,
            "partial_update": VerifyEmailSerializer,  # only only for openapi schema generation
            "update": VerifyEmailSerializer,  # only only for openapi schema generation
        }.get(self.action)
        if not serializer_class:
            print(self.action)
            return super().get_serializer_class()
        return serializer_class

    @action(methods=["get"], detail=True)
    def verify(self, request, *args, **kwargs):
        self.update(request, *args, **kwargs)
        return Response({"success": True})

    @action(methods=["post"], detail=False)
    def resend(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True})

    @action(methods=["post"], detail=False)
    def forgot(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True})

    @action(methods=["post"], detail=True)
    def reset(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response({"success": True})


class GoogleSignInView(views.APIView):

    permission_classes = []

    def post(self, request, **kwargs):
        """called when a user opts to login with Google.
        If its an existing user generate a token and let him login (like normal login flow),
        otherwise, Create the User and Profile with details fetchned from People API and then proceed with normal login flow

        :param request: request with post data containing "id_token" and "code"
        :type request: [type]
        :raises ValueError: when fail to verify the audience in the response from Google
        :return: class:`response.Response`
        :rtype: [type]
        """

        token = request.data["id_token"]
        auth_code = request.data.get("code")
        try:
            # check the doc below to see fields present in google_auth_res
            # https://developers.google.com/identity/sign-in/web/backend-auth
            google_auth_res = id_token.verify_oauth2_token(
                token, requests.Request(), settings.GOOGLE_CLIENT_ID
            )
        except ValueError as ex:
            logger.exception(ex)
            return Response({"error": str(ex)}, status=400)
        else:
            if not google_auth_res.get("aud") == settings.GOOGLE_CLIENT_ID:
                raise ValueError("Could not verify audience.")

            # at this point user is authenticated by google
            logger.info(google_auth_res)
            email = google_auth_res.get("email")
            account_id = google_auth_res["sub"]
            profile_data = dict(
                first_name=google_auth_res.get("given_name"),
                last_name=google_auth_res.get("family_name"),
                image=google_auth_res.get("picture"),
            )
            try:
                user = User.objects.get(email=email)
            except User.DoesNotExist:
                extra_details = fetch_profile_details(auth_code, account_id)
                profile_data.update(extra_details)
                logger.info(f"profile data: {profile_data}")

                user = User.objects.create(
                    email=email,
                    username=email,
                    first_name=profile_data.pop("first_name"),
                    last_name=profile_data.pop("last_name"),
                    is_active=True,
                )
                Profile.objects.create(user=user, **profile_data)
            token, _ = Token.objects.get_or_create(user=user)
            return Response(
                {"token": token.key, "user_id": user.pk, "email": user.email}
            )


def fetch_profile_details(auth_code, account_id):
    """
    Use People API to extract mobile, gender and birthday
    using google-api-python-client and discovery mechanism

    Python client doc: https://github.com/googleapis/google-api-python-client/blob/master/docs/start.md
    Googles People API: https://googleapis.github.io/google-api-python-client/docs/dyn/people_v1.html

    example response from People API:
    {
        "genders": [{"value": "male"}],
        "birthdays": [{"date": {"year": 1093, "month": 3, "day": 11}}],
        "phoneNumbers": [{"value": "1234567890", "type": "home"}],
    }

    Args:
        auth_code [str]: Google auth code obtained on client device via grantOfflineAccess
        account_id [str]: Google account ID of user

    Returns:
        dict: a dict with "gender", "mobile" and "dob" keys populated from People API response

    Note:
        for a advance usecase where we get both a auth_code(for sign in flows) and id_token(for api calls at backend) we can use method describe on this page
        https://developers.google.com/identity/sign-in/web/reference#gapiauth2authorizeparams_callback
    """
    data = {}
    if not auth_code or not account_id:
        return data
    credentials = client.credentials_from_clientsecrets_and_code(
        settings.GOOGLE_SECRET_FILE,
        [
            "https://www.googleapis.com/auth/user.phonenumbers.read",
            "https://www.googleapis.com/auth/user.gender.read",
            "https://www.googleapis.com/auth/user.birthday.read",
        ],
        auth_code,
    )
    http_auth = credentials.authorize(httplib2.Http())
    people_service = discovery.build("people", "v1", http=http_auth)
    try:
        people_res = (
            people_service.people()
            .get(
                resourceName=f"people/{account_id}",
                personFields="genders,phoneNumbers,birthdays,names",
            )
            .execute()
        )
    except Exception as ex:
        logger.exception(ex)
        return {}
    else:
        logger.debug(people_res)
        genders = people_res.get("genders", [])
        gender = next((g.get("value")[0] for g in genders if g.get("value")), None)
        if gender:
            gender = gender[0].upper()
            data["gender"] = gender if gender != "U" else "O"

        birthdays = people_res.get("birthdays", [])
        dob = next(
            (bd.get("date") for bd in birthdays if len(bd.get("date").keys()) == 3),
            None,
        )
        if dob:
            data["dob"] = datetime.date(**dob)

        phoneNumbers = people_res.get("phoneNumbers", [])
        data["mobile"] = next(
            (ph.get("value") for ph in phoneNumbers if ph.get("value")), None
        )

        names = people_res.get("names", [])
        names = next(
            (
                name
                for name in names
                if name.get("familyName") and name.get("givenName")
            ),
            None,
        )
        if names:
            data["first_name"] = names.get("givenName")
            data["last_name"] = names.get("familyName")

        return data
