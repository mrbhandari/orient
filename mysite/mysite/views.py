from django.shortcuts import render_to_response
from django.http import HttpResponseRedirect, HttpResponse
from django.contrib import auth
from django.core.context_processors import csrf
from random import randint
import json
from os import listdir
from os.path import isfile, join
import os
import os.path
import csv

PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
MYPATH = os.path.join(PROJECT_ROOT, '../../../../../../../data/')
FILETYPE = ".txt"
FILELIST = [ f for f in listdir(MYPATH) if (isfile(join(MYPATH,f)) and f.endswith(FILETYPE))]



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
                              {'full_name': request.user.username,
                               'FILELIST': FILELIST})

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
    
    print results
    
    json_results = json.dumps(results)
    print json_results
    return HttpResponse(json_results)





def set_post_status_series(request):
  
  results_collection = []

  print FILELIST
  for filename in FILELIST:
    read_results = []
    results_object = {}
    path = os.path.join(PROJECT_ROOT, '../../../../../../../data/' + filename)
    
    print
    #open the file
    with open(path, 'rU') as f:
        reader = csv.reader(f, delimiter='\t')
        for row in reader:
            if row[0] != '':
              read_results.append(row)
    
    #format expects title first and then header in terms of order
    if len(read_results[0]) == 1:
      graph_title = read_results[0][0]
      read_results.pop(0) #remove it
      
    header_row = 1
    
    if header_row == 1:
      results_object = {"series": [],
        "title": graph_title}
      for i in read_results[0]:
        results_object['series'].append(
          {"name": i,
          "data": []}
        )
      for i in read_results[1:]:
        n = 0 
        for x in i:
          try:
            results_object['series'][n]['data'].append([float(i[0]),float(x)])
          except ValueError:
            pass
          n +=1
    #print results_object
    
    results_collection.append(results_object)
    
  json_results = json.dumps(results_collection)
  #print json_results
  
  return HttpResponse(json_results)

#[{
#    "name": "Month",
#    "data": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
#}, {
#    "name": "Revenue",
#    "data": [23987, 24784, 25899, 25569, 25897, 25668, 24114, 23899, 24987, 25111, 25899, 23221]
#}, {
#    "name": "Overhead",
#    "data": [21990, 22365, 21987, 22369, 22558, 22987, 23521, 23003, 22756, 23112, 22987, 22897]
#}]
  