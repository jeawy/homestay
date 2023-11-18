import pdb
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import redirect
from property import settings

def login_check(func):
    def login_decorator(request, *args, **kwargs):
        if request.user.is_anonymous and 'json' in request.GET:
            print("JWT INFO:" + request.META['HTTP_AUTHORIZATION'])
            print("anonymous user is "+str(request.user.is_anonymous))
            return HttpResponse('Unauthorized', status=401)
            #return HttpResponseForbidden()
        elif request.user.is_anonymous:
            url = settings.LOGIN_URL
            if request.path:
                url = settings.LOGIN_URL + "?next="+str(request.path)
            return redirect(url)
        return func(request, *args, **kwargs)

    return login_decorator