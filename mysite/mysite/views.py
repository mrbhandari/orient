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
import urlparse
import datetime
import urllib


def get_domain(source_url):
  parsed_uri = urlparse.urlparse( source_url)
  domain = '{uri.scheme}://{uri.netloc}/'.format(uri=parsed_uri)
  return domain


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
      #print sql_results[i][0]
      sql_results[i][0] = convert_date(sql_results[i][0])
      sql_results[i][2] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][2].replace("loginkey", "lk")  +"'> "+ sql_results[i][2] +"</a>"
      sql_results[i][7] = "<a target='_blank' href='"+  sql_results[i][6]  +"'><img class='img' src='"+  sql_results[i][7]  +"'></a>"
      sql_results[i][9] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][9]  +"'> "+ sql_results[i][9] +"</a>"
    #print sql_results
    sql_results.insert(0, ['log_time', 'visit_id', 'url', 'css_class', 'element', 'element_txt', 'label', 'img_src', 'name_attr', 'referrer'])
    
    return render_to_response('user_event_details.html', {
            'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results
    })




#returns html associated with object 
def visualize_sql(sql_object):
  #print sql_object['element']
  
  
  href_domain = get_domain(sql_object['url'])
  
  output_str = ''
  
  print sql_object
  
  if sql_object['name_attr'] and sql_object['name_attr']!= 'null':
    output_str += 'Name: ' + sql_object['name_attr']
  
  if sql_object['element'] == 'option':
    output_str += '<select>'
    
  if sql_object['element'] == 'input' and sql_object['label'] != 'null':
    output_str += '<div>' + sql_object['label'] + '<div>'
  
  output_str += '<' + sql_object['element'] + ' '
  
  if sql_object['css_class'] and sql_object['css_class'] != 'null':
    output_str += ' class="' +  sql_object['css_class'] + '" '#open tag
  
  if sql_object['element_txt'] != 'null' and sql_object['element'] in ["textarea",]:
    output_str += 'value="' + sql_object['element_txt']  +'" '
  
  if sql_object['element'] == 'a':
    link_ref = urlparse.urljoin(href_domain, sql_object['href'])
    print link_ref
    output_str += 'href="' +   link_ref  +'" target="_blank" class="livepreview" '
    
  if sql_object['element'] == 'input' and sql_object['element_txt'] != 'null':
    output_str += 'placeholder="' + sql_object['element_txt']  +'" '
    
  if sql_object['element'] == 'input' and sql_object['input_type'] != 'null':
    output_str += 'type="' + sql_object['input_type']  +'" ' 
  
  
  if sql_object['element'] == 'img' and sql_object['img_src'] != 'null':
    link_ref = urlparse.urljoin(href_domain, sql_object['img_src'])
    output_str += 'src="' + link_ref  +'" '
    
  if sql_object['element'] == 'img' and sql_object['element_txt'] != 'null':
    output_str += 'alt="' + sql_object['element_txt']  +'" '
  
  output_str += '>' #close opening tab

  
  
  if sql_object['element_txt'] != 'null' and sql_object['element'] not in [ "select", "textarea", "input", "img"]:
    output_str += sql_object['element_txt']
  
  
  
  output_str += '</' + sql_object['element'] + '>' #ending tab
  
  if sql_object['element'] == 'option':
    output_str += '</select>'
  print output_str
  
  if output_str == "< ></>":
    output_str = "Pageview"
  
  return output_str

def create_full_event_detail(request):
    table_prefix = create_foldername_for_user(request.user.username) +"_"
    request_dict = dict(request.GET._iterlists())
    request_dict = translate_hash(request_dict)
    
    merchant, username = request.user.profile.merchant, request.user.username
    
    sql_query = create_event_sql_query(request_dict, table_prefix, merchant)
    sql_results =  list(get_sql_data(sql_query))
    sql_results = [list(i) for i in sql_results]
    print sql_results
    col_heading = ['count', 'url', 'css_class', 'element', 'element_txt', 'label', 'img_src', 'name_attr', 'href', 'input_type']
    
    print('lensql_results', len(sql_results))
    
    for i in range(0,len(sql_results)):
      sql_object = {}
      for n in range(0, len(sql_results[i])):
        sql_object[col_heading[n]] = sql_results[i][n]
      #print sql_object
      #print "XXXXXX"
      sql_results[i][1] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][1].replace("loginkey", "lk")  +"'> "+ sql_results[i][1].replace("loginkey", "lk") +"</a>"
      if sql_results[i][6] != '':
        sql_results[i][6] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][6]  +"'> "+ sql_results[i][6][:20] +"...</a>"
      
      
      #append the visualize column
      sql_results[i].insert(2, visualize_sql(sql_object))
    
    #add the last column on that you were appending
    col_heading.insert(2, 'visualize')
    sql_results.insert(0, col_heading)
    
    return {'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results }
    
    
def return_event_detail(request):
    return render_to_response('event_details.html', create_full_event_detail(request))


def visualize_recommendation(request):
  
  num_results = 5
  full_response = create_full_event_detail(request)
  sql_results = full_response['sql_results']
  short_sql_results = []
  
  for i in range(0,
                 min(num_results +1, len(sql_results))
                 ): #get max of num results or the lenght of the array
    short_sql_results.append([sql_results[i][0], sql_results[i][2], sql_results[i][1]])

  return render_to_response('visualize_recommendation.html',
                            {'sql_results': short_sql_results })
  
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
      sql_results[i][2] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][2].replace("loginkey", "lk")  +"'> "+ sql_results[i][2].replace("loginkey", "lk") +"</a>"
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



def create_event_sql_query(query_dict, table_prefix, merchant):
    analysis_type = ''
    try:
      analysis_type = query_dict['analysis_type'][0]
    except:
      pass
    query_dict.pop("analysis_type", None)
    print analysis_type
    print "XXXXXXXXXXXXXXXXXXXXXXXXXXX"
    if analysis_type == 'exit_rate':
      table_name = merchant + '_user_events'
    else:
      table_name = table_prefix + 'all_segment_events'
    print table_name
    sql_query = """select count(*) as cnt, url, css_class, element, element_txt, label, img_src, name_attr, href, input_type  from %s where """ % (table_name)
    sql_query += join_where_clause(query_dict)
    sql_query += """group by url, css_class, element, element_txt, label, img_src, name_attr, href, input_type order by cnt desc limit 1000"""
    
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
    
    
#Exit rate stuff
def exit_rate(request):
    merchant_url_toggle = ''
    request_dict = dict(request.GET._iterlists())
    merchant, username = request.user.profile.merchant, request.user.username
    if merchant.lower() == 'budsies':
      merchant_url_toggle = 1
    sql_query = """SELECT 
        a.*, a.visit_cnt / (1.0 + a.num_source) AS exit_rate
    FROM
        (SELECT 
            LOWER(url1),
                LOWER(event1),
                SUM(num_pairs) AS visit_cnt,
                num_source
        FROM
            %s_adjacency_graph
        WHERE
            event2 = '"EXIT"'
        GROUP BY LOWER(url1) , LOWER(event1)
        ORDER BY visit_cnt DESC) AS a
    WHERE
        a.num_source > 100
    ORDER BY exit_rate DESC
    LIMIT 100;""" % (merchant)
  
    print sql_query
    sql_results = get_sql_data(sql_query)
    sql_results =  list(get_sql_data(sql_query))
    sql_results = [list(i) for i in sql_results]
    # LOWER(url1), LOWER(event1), visit_cnt, num_source, exit_rate


    for i in range(0,len(sql_results)):
    
      solution_button  = "<a target='_blank' type='button' class='btn btn-default dropdown-toggle' href='"+ convert_title_to_url(sql_results[i][1], '/accounts/loggedin/get_next_events/?', '&analysis_type=exit_rate&include_url=0'+ merchant_url_toggle) +"'>Solution</a>"
      sql_results[i][1] = "<a class='livepreview truncate' target='_blank' href='"+  convert_title_to_url(sql_results[i][1], '/accounts/loggedin/get_event_details/?', '&analysis_type=exit_rate')  +"'> "+ sql_results[i][1] + "</a>"
      sql_results[i].insert(2, solution_button)
    
    sql_results.insert(0, ['URL', 'Event', 'Solution', 'Exits', 'Total Visits', 'Exit Rate'])
    
    
    return render_to_response('exit_rate.html', {
            'mydict': request_dict,
            'sql_query': sql_query,
            'sql_results': sql_results,
    })

def get_next_events(request):
    include_url = 0
    
    query_dict = dict(request.GET._iterlists())
    if query_dict.get('include_url'):
      include_url = int(query_dict['include_url'][0])
      query_dict.pop("include_url", None)
    
    merchant, username = request.user.profile.merchant, request.user.username
    table_prefix = create_foldername_for_user(request.user.username) +"_"
    sql_query = next_event_sql_query(query_dict, table_prefix, merchant, include_url)
    print sql_query
    sql_results = get_sql_data(sql_query)
    sql_results =  list(get_sql_data(sql_query))
    sql_results = [list(i) for i in sql_results]
    # LOWER(url1), LOWER(event1), visit_cnt, num_source, exit_rate






    col_heading = ['count', 'url', 'css_class', 'element', 'element_txt', 'label', 'img_src', 'name_attr', 'href', 'input_type']
    
    
    
    for i in range(0,len(sql_results)):
      sql_object = {}
      if include_url == 0:
        sql_results[i].insert(1, 'na')
      for n in range(0, len(sql_results[i])):
        sql_object[col_heading[n]] = sql_results[i][n]
      
      
      
      sql_results[i][1] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][1].replace("loginkey", "lk")  +"'> "+ sql_results[i][1].replace("loginkey", "lk") +"</a>"
      if sql_results[i][6] != '':
        sql_results[i][6] = "<a class='livepreview' target='_blank' href='"+  sql_results[i][6]  +"'> "+ sql_results[i][6][:20] +"...</a>"
      
      
      
      
      #append the visualize column
      sql_results[i].insert(2, visualize_sql(sql_object))
    
    #add the last column on that you were appending
    col_heading.insert(2, 'visualize')
    sql_results.insert(0, col_heading)

    return render_to_response('get_next_events.html', {
            'mydict': query_dict,
            'sql_query': sql_query,
            'sql_results': sql_results,
    })

def next_event_sql_query(query_dict, table_prefix, merchant, include_url):
  url_selector, analysis_type = '', ''
  if include_url == 1:
    url_selector = ' t2.url, '
    
  
  try:
    analysis_type = query_dict['analysis_type'][0]
  except:
    pass
  query_dict.pop("analysis_type", None)
  if analysis_type == 'exit_rate':
    table_name = merchant + '_user_events'
  else:
    table_name = table_prefix + 'all_segment_events'
  print table_name
  
  sql_query = """SELECT 
    COUNT(*) AS count,
    %s
    t2.css_class,
    t2.element,
    t2.element_txt,
    t2.label,
    t2.img_src,
    t2.name_attr,
    t2.href,
    t2.input_type
    FROM
        (SELECT 
            uid, log_time, visit_id
        FROM
            %s
        WHERE
            %s ) t1
            JOIN
        %s t2 ON (t1.uid = t2.uid
            
            AND t1.visit_id = t2.visit_id)
    GROUP BY %s t2.css_class , t2.element , t2.element_txt , t2.label , t2.img_src , t2.name_attr , t2.href , t2.input_type
    ORDER BY count DESC LIMIT 1000""" % (url_selector, table_name, join_where_clause(query_dict),table_name, url_selector)
  #AND t2.log_time = (t1.log_time + 100000)
  print sql_query
  return sql_query

def convert_title_to_url(graph_title, prepend_string, postpend_string):
  detail_param = urllib.quote(graph_title[1:(len(graph_title)-1)].replace("&", "%26").replace("::", "&").replace("#", "%23"), safe='~@#$&()*!+=:;,.?/\'');
  print (prepend_string, detail_param) 
  return prepend_string + detail_param + postpend_string
