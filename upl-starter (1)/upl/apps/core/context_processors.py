from .models import SiteSetting


def site_settings(request):
    return {"S": SiteSetting.all_dict()}
