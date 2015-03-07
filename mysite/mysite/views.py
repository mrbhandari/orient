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
from kinnek import generate_event_files, create_foldername_for_user
import urllib2
import pandas as pd

import datetime

def convert_date(timestamp):
  return(
      datetime.datetime.fromtimestamp(
          int(timestamp/1000)
      ).strftime('%Y-%m-%d %H:%M:%S')
  )


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
    requestdict = dict(request.GET._iterlists())
    try:
        graph_num = requestdict['graph'][0]
    except KeyError, e:
        graph_num = 5
        
    return render_to_response('loggedin.html',
                              {'full_name': request.user.username,
                               'graph_num': graph_num})

def invalid_login(request):
    return render_to_response('invalid_login.html')

def logout(request):
    auth.logout(request)
    return render_to_response('logout.html')


def read_graph_data(request):
  print "Now fetching created user files"
  merchant, username = request.user.profile.merchant, request.user.username
  print merchant, username
  
  
  #PROJECT_ROOT = os.path.dirname(os.path.realpath(__file__))
  MYPATH =  os.path.join('/data/', create_foldername_for_user(username))
  FILETYPE = ".txt"
  FILELIST = [ f for f in listdir(MYPATH) if (isfile(join(MYPATH,f)) and f.endswith(FILETYPE))]

  results_collection = []
  newlist = []
  newlist = sorted(FILELIST, key=lambda item: int(item.replace('event', '').replace('.txt', '')))
  print newlist
  
  with open(os.path.join(MYPATH, 'summary.json'), 'r' ) as f:
    summary_data = json.load(f)
  
  with open(os.path.join(MYPATH, 'table.json'), 'r' ) as f:
    table_json_dict = eval(f.read())
    df = pd.DataFrame.from_dict(table_json_dict).transpose()
    min_max = {}
    for k in df.columns.values:
       min_max[k] = {'min':df[k].min(),'max':df[k].max()}
    print min_max
    min_max = json.dumps(min_max, ensure_ascii=False)
    print "XXXXXXSJKJSLDKJLSDKJFLSDKJFLSDKJFLSKDJFLSDKJFLSDKJ"
    table_json =  json.dumps(table_json_dict, ensure_ascii=False)
  
  for filename in newlist:
    read_results = []
    results_object = {}
    path = os.path.join(MYPATH, filename)
    
    
    #open the file
    with open(path, 'rU') as f:
        reader = csv.reader(f, delimiter='\t')
        print path
        for row in reader:
            if row[0] != '':
              read_results.append(row)

    if len(read_results)>0: #check there is something in the file
      
      #format expects title first and then header in terms of order
      if len(read_results[0]) == 1:
        graph_meta_metrics = read_results[0][0]
        read_results.pop(0) #remove it
      
      #format expected is a row of json data next
      if len(read_results[0]) == 1:
        graph_title = read_results[0][0]
        read_results.pop(0) #remove it
      
      header_row = 1
      
      if header_row == 1:
        results_object = {"series": [],
          "title": graph_title,
        'meta_metrics': graph_meta_metrics,
        }
        for i in read_results[0]:
          results_object['series'].append(
            {"name": i,
            "data": [],
              }
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
    else:
      print "NO DATA IN FILE !!!!!!"
      
    
    
  results_collection_meta = {
    'meta': summary_data,
    'table_json': {'table_data' : table_json,
                   'min_max': min_max },
    'each_graph': results_collection,
    }
  
  json_results = json.dumps(results_collection_meta)
  #print json_results
  
  return HttpResponse(json_results)

def print_graph(request):
  request_dict = dict(request.GET._iterlists())
  
  graph_id = request_dict['graph_id'][0]
  return render_to_response('graphs.html', {
            'graph_id': graph_id,
    })

def get_graph_data(request):
  
  request_dict = dict(request.POST._iterlists())
  filter_query = request_dict['filter_query'][0]
  success_query = request_dict['success_query'][0]
  
  generate_event_files(False, False, filter_query, success_query, request.user.profile.merchant, request.user.username)
  result = {'status': 'Generated all the data. Now loading on page.'}
  
  json_results = json.dumps(result)
  return HttpResponse(json_results)

def test_graph_data(request):
  request_dict = dict(request.POST._iterlists())
  filter_query = request_dict['filter_query'][0]
  success_query = request_dict['success_query'][0]
  test_summary = generate_event_files(True, False, filter_query, success_query, request.user.profile.merchant, request.user.username)
  #result = {'Total Users': 55,
  #          'Users meeting consideration criteria': test_summary[0],
  #          'Users considered successful': test_summary[1]}
  json_results = json.dumps(test_summary)
  return HttpResponse(json_results)

def translate_hash(request_dict):
  for i in ['path', 'href', 'url']:
    try:
      request_dict[i][0] = request_dict[i][0].replace('%23', '#').replace('%26', '&')
    except KeyError, e:
      pass
  return request_dict

def return_user_event_details(request):
    table_prefix = create_foldername_for_user(request.user.username) +"_"
    request_dict = dict(request.GET._iterlists())
    request_dict = translate_hash(request_dict)
    sql_query = create_user_event_sql_query(request_dict, table_prefix)
    sql_results =  list(get_sql_data(sql_query))
    sql_results = [list(i) for i in sql_results]
    #convert startime
    for i in range(0,len(sql_results)):
      print sql_results[i][0]
      sql_results[i][0] = convert_date(sql_results[i][0])
      sql_results[i][2] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][2]  +"'> "+ sql_results[i][2] +"</a>"
      sql_results[i][7] = "<a target='_blank' href='"+  sql_results[i][6]  +"'><img class='img' src='"+  sql_results[i][7]  +"'></a>"
      sql_results[i][9] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][9]  +"'> "+ sql_results[i][9] +"</a>"
    print sql_results
    sql_results.insert(0, ['log_time', 'visit_id', 'url', 'css_class', 'element', 'element_txt', 'label', 'img_src', 'name_attr', 'referrer'])
    
    return render_to_response('user_event_details.html', {
            'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results
    })


def return_event_detail(request):
    table_prefix = create_foldername_for_user(request.user.username) +"_"
    request_dict = dict(request.GET._iterlists())
    request_dict = translate_hash(request_dict)
    sql_query = create_event_sql_query(request_dict, table_prefix)
    sql_results =  list(get_sql_data(sql_query))
    sql_results = [list(i) for i in sql_results]
    for i in range(0,len(sql_results)):
      
      sql_results[i][1] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][1]  +"'> "+ sql_results[i][1] +"</a>"
      sql_results[i][6] = "<a target='_blank' href='"+  sql_results[i][6]  +"'><img class='img' src='"+  sql_results[i][6]  +"'></a>"
    
    
    print sql_results
    sql_results.insert(0, ['cnt', 'url', 'css_class', 'element', 'element_txt', 'label', 'img_src', 'name_attr'])
    
    
    
    
    return render_to_response('event_details.html', {
            'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results
    })

quadrant_definitions = {
  'tp': {
    'table': 'success',
    'sign': '>='
  },
  'fn': {
    'table': 'success',
    'sign': '>='
  },
  'fp': {
    'table': 'failure',
    'sign': '>='
  },
  'tn': {
    'table': 'failure',
    'sign': '>='
  },
}

def return_user_quad_details(request):
    table_prefix = create_foldername_for_user(request.user.username) +"_"
    request_dict = dict(request.GET._iterlists())
    request_dict = translate_hash(request_dict)
    quadrant = request_dict['quadrant'][0]
    
    
    table = quadrant_definitions[quadrant]['table']
    sign = quadrant_definitions[quadrant]['sign']
    print quadrant, table, sign
    request_dict.pop("quadrant", None)
    
    
    sql_query = create_uid_quad_sql_query(request_dict, table, sign, table_prefix)
    
    if quadrant == 'fn':
      sql_query = """SELECT  count(*), uid from %ssuccess_uids_events_cnt where uid not in (select x.uid from (""" % (table_prefix) + sql_query+ """) x) group by uid""" 
    
    if quadrant == 'tn':
      sql_query = """SELECT  count(*), uid from %sfailure_uids_events_cnt where uid not in (select x.uid from (""" % (table_prefix) + sql_query+ """) x) group by uid""" 
    
    sql_results =  list(get_sql_data(sql_query))
    sql_results.insert(0, ['cnt', 'uid'])
    
    return render_to_response('user_quad_details.html', {
            'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results,
    })
  
  
def return_user_detail (request):
    table_prefix = create_foldername_for_user(request.user.username) +"_"
    request_dict = dict(request.GET._iterlists())
    request_dict = translate_hash(request_dict)
    sql_query = create_uid_sql_query(request_dict, table_prefix)
    sql_results =  list(get_sql_data(sql_query))
    sql_results = [list(i) for i in sql_results]
    
    
    for i in range(0,len(sql_results)):
      print "doing this"
      sql_results[i][2] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][2]  +"'> "+ sql_results[i][2] +"</a>"
      sql_results[i][7] = "<a target='_blank'   href='"+  sql_results[i][6]  +"'><img class='img' src='"+  sql_results[i][7]  +"'></a>"
      
    sql_results.insert(0, ['cnt', 'uid', 'url', 'css_class', 'element', 'element_txt', 'label', 'img_src', 'name_attr'])
    
    return render_to_response('user_details.html', {
            'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results,
    })


def create_user_event_sql_query(query_dict, table_prefix):
    sql_query = """select log_time, visit_id, url, css_class, element, element_txt, label, img_src, name_attr, referrer from %sall_segment_events where """ % (table_prefix)
    sql_query += join_where_clause(query_dict)
    sql_query += """ order by log_time"""
    return sql_query


def create_event_sql_query(query_dict, table_prefix):
    sql_query = """select count(*) as cnt, url, css_class, element, element_txt, label, img_src, name_attr  from %sall_segment_events where """ % (table_prefix)
    sql_query += join_where_clause(query_dict)
    sql_query += """group by url, css_class, element, element_txt, label, img_src, name_attr order by cnt desc"""
    return sql_query

def create_uid_quad_sql_query(query_dict, table, sign, table_prefix):
    output =''
    min_count = ''
    sql_query = """select * from (select sum(cnt) as cnt, uid from %s""" % (table_prefix) + table + """_uids_events_cnt where """
    sql_query += join_where_clause(query_dict)
    sql_query += """ group by uid) t1 where """ + join_where_greaterless_clause(query_dict, sign)
    return sql_query

def create_uid_sql_query(query_dict, table_prefix):
    sql_query = """select count(*) as cnt, uid, url, css_class, element, element_txt, label, img_src, name_attr  from %sall_segment_events where """ % (table_prefix)
    sql_query += join_where_clause(query_dict)
    sql_query += """group by uid, url, css_class, element, element_txt, label, img_src, name_attr order by cnt desc"""
    return sql_query

def join_where_clause(query_dict):
  #takes any arguments and makes them greater than sequel queries, except for count
    sql_query = ''
    i = 0
    count_column_exists = 0
    itotal = len(query_dict)

    if query_dict.get('cnt') >-1:
      count_column_exists = 1
      itotal = 0
      for key, value in query_dict.iteritems():
        try:
          int(value[0])
        except:
          itotal+=1
    
    print ['count_column_exists', count_column_exists]
    print ['itotal', itotal]
    
    for key, value in query_dict.iteritems():
      #determine if there is a count column that should be treated as an integer
      if key != 'cnt':
        try:
          sql_query = sql_query + " " + key + "=" + str(int(value[0])) + " and "
          print "int worked"
        except:
          sql_query = sql_query + " " + key + "= '" + value[0] + "' and "
        #if i < itotal - 1: #add and for all non int values
        #    sql_query = sql_query + " and "
      i+=1
    return sql_query[:-4] #removes the last and

def join_where_greaterless_clause(query_dict, sign):
  #takes any numerical arguments and makes them greater than sql queries; only works for one number
    sql_query = ''
    i = 0
    for key, value in query_dict.iteritems():
      if key == 'cnt':
        try:
          sql_query = sql_query + " " + key + sign + str(int(value[0])) + ""
          print "int worked"
        except:
          pass
    return sql_query


import MySQLdb as mdb

def get_sql_data(sql_query):
  con = mdb.connect("localhost", "root", "thebakery", "orient")
  
  with con:
      cur = con.cursor()
      cur.execute(sql_query)
      return cur.fetchall() 
      
