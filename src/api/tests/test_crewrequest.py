from django.test import TestCase

from django.core import mail

from api.models import CrewMemberRequest, CrewMember
from .base import reverse, APITestCaseMixin, LoggedInMixin


class CrewRequestTestCase(APITestCaseMixin, LoggedInMixin, TestCase):
    auth_user_id = 1
    fixtures = ["test_crewrequest"]

    def test_crewrequest_approval_adds_crew_to_movie(self):
        self.assertEqual(1, CrewMember.objects.count())
        cmr = CrewMemberRequest.objects.get(pk=1)

        unchanged_attrs = ["requestor", "user", "role", "movie"]

        old_state = {attr: getattr(cmr, attr) for attr in unchanged_attrs}
        self.assertEqual("S", cmr.state)

        expected_crew_with_attr = {
            "profile": old_state.get("user").profile,
            "movie": old_state.get("movie"),
            "role": old_state.get("role"),
        }

        res = self.client.patch(
            reverse("api:crewmemberrequest-detail", args=["v1", 1]),
            data={"state": "A"},
        )
        self.assertEquals(200, res.status_code)

        cmr.refresh_from_db()
        new_state = {attr: getattr(cmr, attr) for attr in unchanged_attrs}

        self.assertEqual("A", cmr.state)
        self.assertEqual(old_state, new_state)

        self.assertEquals(len(mail.outbox), 0)

        self.assertEqual(2, CrewMember.objects.count())
        self.assertTrue(CrewMember.objects.filter(**expected_crew_with_attr).exists())
