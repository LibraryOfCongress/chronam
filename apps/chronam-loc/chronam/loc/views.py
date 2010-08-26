import django.http
import django.template.loader


def home(request):
    context = django.template.RequestContext(request, {})
    t = django.template.loader.get_template('home.html')
    return django.http.HttpResponse(content=t.render(context))
