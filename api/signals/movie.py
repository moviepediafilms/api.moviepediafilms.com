from api.constants import CREW_MEMBER_REQUEST_STATE
from logging import getLogger
from django.db.models.signals import post_save
from django.dispatch import receiver
from api.models import Movie, CrewMember, CrewMemberRequest
from api.decorators import ignore_raw

from api.emails import email_trigger, TEMPLATES

logger = getLogger("api.signals")


@receiver(post_save, sender=Movie)
@ignore_raw
def on_movie_submission(sender, **kwargs):
    if kwargs.get("created"):
        # new submission
        movie = kwargs.get("instance")
        director = CrewMember.objects.filter(movie=movie, role__name="Director").first()
        if director and director.profile.user == movie.order.owner:
            logger.debug("Submission by Director")
            # d-a2b26474eff54ca98154f1ac24cae8c0
            email_trigger(director.user, TEMPLATES.SUBMIT_CONFIRM_DIRECTOR)
        else:
            # either director is not yet set (very unlikely to happen)
            # or a crew member made this submission
            logger.debug("Submission by crew member")
            # 2 emails to send, one to director, another to the crew member who made the submission
            # d-f7a6a234d110411ea140e9a43fcd3fe8 to director, handle full/partial/full profile
            email_trigger(director.owner, TEMPLATES.DIRECTOR_APPROVAL)
            # d-9937bf56a2a34301ab7ae37a94bc5a0c to the crew member
            email_trigger(movie.order.owner, TEMPLATES.SUBMIT_CONFIRM_CREW)
            # add notification to director's profile


@receiver(post_save, sender=CrewMemberRequest)
@ignore_raw
def crew_membership_approved(sender, **kwargs):
    cmr = kwargs.get("instance")
    if cmr.state == CREW_MEMBER_REQUEST_STATE.APPROVED:
        cm, _ = CrewMember.objects.get_or_create(
            movie=cmr.movie, profile=cmr.user.profile, role=cmr.role
        )
        logger.info(f"{cm} a crew membership was approved and added to movie")
