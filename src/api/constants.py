class MOVIE_STATE:
    CREATED = "C"
    SUBMITTED = "S"
    PUBLISHED = "P"
    REJECTED = "R"
    # below states are not used
    HIDDEN = "H"
    ARCHIVED = "A"


class REVIEW_STATE:
    PUBLISHED = "S"
    BLOCKED = "H"


class GENDER:
    MALE = "M"
    FEMALE = "F"
    OTHERS = "O"


class CREW_MEMBER_REQUEST_STATE:
    SUBMITTED = "S"
    APPROVED = "A"
    DECLINED = "D"


class CONTEST_STATE:
    CREATED = "C"
    LIVE = "L"
    FINISHED = "F"


class MOVIE_TYPE:
    SHORT = "S"
    BLOG = "B"


class ORDER_STATE:
    # Just created, selected a package
    CREATED = "C"
    # Order is paid and it has a valid payment_id
    SUBMITTED = "S"
    # Order is rejected manually by admins
    REJECTED = "R"


REGULAR_MONTHLY_CONTEST_NAME = "Regular Monthly Contest"
RECOMMENDATION = "Recommendation"

DEFAULT_AVATARS = {
    GENDER.MALE: "/default_avatar_m.png",
    GENDER.FEMALE: "/default_avatar_f.png",
    GENDER.OTHERS: "/default_avatar_o.png",
    None: "/default_avatar_m.png",
}
