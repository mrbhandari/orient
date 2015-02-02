import sys
import os
import numpy as np
from collections import Counter
#your_djangoproject_home="/Users/tempuser/orient/mysite/"
#
#sys.path.append(your_djangoproject_home)
#os.environ['DJANGO_SETTINGS_MODULE'] = 'mysite.settings'
#import django
#django.setup()

import csv
import math
#from django.db import connection

import MySQLdb as mdb



def get_cumsum_counts1(feature,array):
    total = len(array[feature])
    ctr = Counter(array[feature])
    min_cnt = np.min(array[feature])
    max_cnt = np.max(array[feature])

    arr1 = {}
    arr1[0] = total
    for i in range(1,max_cnt+1):
        arr1[i] = arr1[i-1] - ctr[i-1]
    return arr1
def get_cumsum_counts2(feature,array):
    ctr = Counter(array[feature])
    min_cnt = np.min(array[feature])
    max_cnt = np.max(array[feature])

    arr1 = {}
    arr1[max_cnt] = np.sum(np.array(array[feature] < max_cnt))
    for i in range(max_cnt-1,-1,-1):
        arr1[i] = arr1[i+1] - ctr[i]
    return arr1

def get_matthew_corr_coef(feature,log_values=0):
    tp = get_cumsum_counts1(feature,conv_events)
    fp = get_cumsum_counts1(feature,nc_events)
    
    fn = get_cumsum_counts2(feature,conv_events)
    tn = get_cumsum_counts2(feature,nc_events)
    min_cnt = np.min([np.min(tp.keys()),np.min(fp.keys()),np.min(tn.keys()),np.min(fn.keys())])
    max_cnt = np.min([np.max(tp.keys()),np.max(fp.keys()),np.max(tn.keys()),np.max(fn.keys())])
    mcc_arr = []
    for i in range(min_cnt,max_cnt):
        tpv = tp[i]
        fpv = fp[i]
        tnv = tn[i]
        fnv = fn[i]
        total = tpv + fpv + tnv + fnv
        mcc = (tpv * tnv  - fpv * fnv)/math.sqrt(max(tpv + fpv,1)*max(tpv + fnv,1)*max(tnv + fpv,1) * max(tnv + fnv,1))
        significance = mcc * mcc * total
        if log_values == 1:
            print mcc
        elif log_values == 2:
            print i,"\t",tpv,"\t",fpv,"\t",fnv,"\t",tnv,"\t",mcc,"\t",significance
            #print i, "\t", tpv/(tpv + fpv + 0.0), "\t", fnv/(tnv + fnv + 0.0)
        mcc_arr.append(mcc)
    return range(min_cnt,max_cnt),mcc_arr



con = mdb.connect("localhost", "root", "thebakery", "orient")

with con:
    cur = con.cursor()
    #cur.execute("SELECT VERSION()")
    cur.execute("""
                   CREATE TEMPORARY TABLE success_uids
SELECT DISTINCT uid FROM user_events WHERE
path = 'BODY|DIV#container|DIV.row|DIV.col-md-8|DIV.shelf-main|FORM#profile_submit|DIV#npcShelfFormApp_content|DIV#form_view|DIV#npcShelfFormApp_fields|TABLE.fields submit|TBODY|TR|TD|DIV.row|DIV.col-md-6 col-xs-6|DIV.submit text-right|A.fields submit standard|IMG' OR 
path = 'BODY|DIV.container|DIV.row|DIV.col-md-8 col-sm-8|DIV.block-grey|DIV#npcShelfFormApp_content|DIV#form_view|FORM#profile_submit|DIV#npcShelfFormApp_fields|TABLE.fields submit|TBODY|TR|TD.submit|A.fields submit pull-right standard|IMG';""")

    cur.execute("""
CREATE TEMPORARY TABLE failure_uids
SELECT distinct A.uid from user_events as A
    LEFT JOIN 
success_uids
as B
ON (A.uid = B.uid)
WHERE B.uid IS NULL;""")

    cur.execute("""
                CREATE TEMPORARY TABLE failure_uids_events
                Select user_events.* from user_events,
                failure_uids as b
                where user_events.uid = b.uid;
                """)
    
    cur.execute("""
                CREATE TEMPORARY TABLE success_uids_events
Select user_events.* from user_events,
success_uids as b
where user_events.uid = b.uid;
""")
    
    
    cur.execute("""
                CREATE TEMPORARY TABLE success_uids_events_cnt
SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title,
      COUNT(*) AS cnt
FROM success_uids_events
GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title order by cnt desc;
                """)
    
        
    cur.execute("""
                CREATE TEMPORARY TABLE failure_uids_events_cnt
SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title,
      COUNT(*) AS cnt
FROM failure_uids_events
GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title order by cnt desc;
                """)
    
    
    cur.execute("""
                Alter table success_uids_events_cnt add converted boolean default True;
                """)
    
    
    cur.execute("""
                Alter table failure_uids_events_cnt add converted boolean default False;
                """)
    
    
    cur.execute("""
                Create TEMPORARY table all_uid_events_cnt
SELECT success_uids_events_cnt.* FROM success_uids_events_cnt
UNION SELECT failure_uids_events_cnt.* FROM failure_uids_events_cnt;
                """)
    
    
    cur.execute("""
                SELECT count(*) from all_uid_events_cnt;
                """)
    
    cur.execute("""
                SELECT * from all_uid_events_cnt;
                """)
    conv_events = {}
    nc_events = {}
    event_metadata = {}
    for row in cur.fetchall():
        is_conv = row[-1]
        event_signature = ""
        for i in range(1,len(row) - 2):
            event_signature = event_signature + " " + str(row[i])
        if event_signature in event_metadata:
            event_metadata[event_signature] += 1
        else:
            event_metadata[event_signature] = 1
        if is_conv == 0:
            if event_signature not in conv_events:
                conv_events[event_signature] = []
            conv_events[event_signature].append(row[-2])
        else:
            print "not a conversion"
            if event_signature not in conv_events:
                nc_events[event_signature] = []
            nc_events[event_signature].append(row[-2])

    for event in event_metadata:
        
        if event in conv_events and event in nc_events:
            print event
            x,mcc_arr = get_matthew_corr_coef(event)
            print event, mcc_arr


def my_custom_sql():
    cursor = connection.cursor()

    #cursor.execute("UPDATE bar SET foo = 1 WHERE baz = %s", [self.baz])

    cursor.execute("""
                   CREATE TEMPORARY TABLE success_uids
SELECT DISTINCT uid FROM user_events WHERE
path = 'BODY|DIV#container|DIV.row|DIV.col-md-8|DIV.shelf-main|FORM#profile_submit|DIV#npcShelfFormApp_content|DIV#form_view|DIV#npcShelfFormApp_fields|TABLE.fields submit|TBODY|TR|TD|DIV.row|DIV.col-md-6 col-xs-6|DIV.submit text-right|A.fields submit standard|IMG' OR 
path = 'BODY|DIV.container|DIV.row|DIV.col-md-8 col-sm-8|DIV.block-grey|DIV#npcShelfFormApp_content|DIV#form_view|FORM#profile_submit|DIV#npcShelfFormApp_fields|TABLE.fields submit|TBODY|TR|TD.submit|A.fields submit pull-right standard|IMG';

CREATE TEMPORARY TABLE failure_uids
SELECT distinct A.uid from user_events as A
    LEFT JOIN 
success_uids
as B
ON (A.uid = B.uid)
WHERE B.uid IS NULL;

select count(*) from success_uids; 
select count(*) from failure_uids;                     
                   """)
    rows = cursor.fetchall()
    print rows
    return rows


def generate_output():
    inputtsv = []
    with open("cleaned_output_with_quote_by_posts.tsv") as tsv:
        for line in csv.reader(tsv, dialect="excel-tab"):
            inputtsv.append(line)
            
    ['29887', 'COMPANY_PROFILE', '11', '1']
            
    events = ['QUOTE_BY_POSTS',]
    #'MYPOST_SUPPLIER_NAV', 'MY_POSTS', 'LEAD_DETAILS', 'NEW_LEADS', 'SENT_MESSAGE', 'CREATE_POST', 'COMPANY_PROFILE', 'QUOTES', 'CREATED_NEW_POST', 'BROWSE_NPC']
    eventlist = []
    for i in inputtsv:
        eventlist.append(i[1])
    
    #events = set(eventlist)
    
    maxoccurance = 40
    
    
    
    for e in events:
        print e
        print '\n'
        print ('\t').join(['x','TP','FP','FN','TN','chisq','phi'])
        for x in range(0,maxoccurance+1):
            TP, FP, FN, TN = 0, 0, 0, 0    
            for row in inputtsv:
                if row[1] == e:
                    print row
                    count_of_event = float(row[2])
                    conversion_event= float(row[3])
                    
                    if count_of_event >= x and conversion_event == 1:
                        TP +=1
                    if count_of_event >= x and conversion_event == 0:    
                        FP +=1
                    if count_of_event < x and conversion_event == 1:    
                        FN +=1
                    if count_of_event < x and conversion_event == 0:    
                        TN +=1
            try:
                phi = (TP * TN - FP * FN) / math.sqrt((TP+FP)*(TP+FN)*(TN+FP)*(TN+FN))
            
            except ZeroDivisionError:
                phi = (TP * TN - FP * FN) / 1
    
            
            chisq = phi**2 * (TP + FP + FN + TN)
            
            if chisq > 2.7:
                print ('\t').join([str(x), str(TP), str(FP), str(FN), str(TN), str(chisq), str(phi)])
        
