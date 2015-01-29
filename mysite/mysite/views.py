from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from random import randint
import json

def render_home(request):
  error = None
  if 'error' in request.GET:
    error = request.GET.get('error','')
  return render_to_response('index.html',
                            {'error':error})


def login(request):
    c = {}
    c.update(csrf(request))
    return render_to_response('login.html', c)

def auth_view(request):
    username = request.POST.get('username', '')
    password = request.POST.get('password', '')
    #check if user exists
    user = auth.authenticate(username=username, password=password)
    
    if user is not None:
        #signify in the system the user is logged in now
        auth.login(request, user)
        return HttpResponseRedirect('/accounts/loggedin')
    else:
        return HttpResponseRedirect('/accounts/invalid')
    
def loggedin(request):
    return render_to_response('loggedin.html',
                              {'full_name': request.user.username})

def invalid_login(request):
    return render_to_response('invalid_login.html')

def logout(request):
    auth.logout(request)
    return render_to_response('logout.html')
  
def series(request):
    results = []
    
    for i in xrange(1, 11):
        results.append({
            'y': randint(0, 100)
        })
        
    json_results = json.dumps(results)
    return HttpResponse(json_results)