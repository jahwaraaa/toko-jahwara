from django.conf import settings


def site_verification(request):
    return {'google_site_verification': settings.GOOGLE_SITE_VERIFICATION}