import sys
import os
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



con = mdb.connect("localhost", "root", "thebakery", "orient")

with con:
    cur = con.cursor()
    #cur.execute("SELECT VERSION()")
    cur.execute("""
                CREATE TEMPORARY TABLE segment_user_events
        select user_events.* from user_events where start_hc <=5;
                """)
    
    cur.execute("""
                CREATE TEMPORARY TABLE success_uids
SELECT DISTINCT uid FROM segment_user_events WHERE
path = 'BODY|DIV#container|DIV.row|DIV.col-md-8|DIV.shelf-main|FORM#profile_submit|DIV#npcShelfFormApp_content|DIV#form_view|DIV#npcShelfFormApp_fields|TABLE.fields submit|TBODY|TR|TD|DIV.row|DIV.col-md-6 col-xs-6|DIV.submit text-right|A.fields submit standard|IMG' OR 
path = 'BODY|DIV.container|DIV.row|DIV.col-md-8 col-sm-8|DIV.block-grey|DIV#npcShelfFormApp_content|DIV#form_view|FORM#profile_submit|DIV#npcShelfFormApp_fields|TABLE.fields submit|TBODY|TR|TD.submit|A.fields submit pull-right standard|IMG';
                """)
    
    cur.execute("""
CREATE TEMPORARY TABLE failure_uids
SELECT distinct A.uid from segment_user_events as A
    LEFT JOIN 
success_uids
as B
ON (A.uid = B.uid)
WHERE B.uid IS NULL;
""")

    cur.execute("""
                CREATE TEMPORARY TABLE failure_uids_events
Select segment_user_events.* from segment_user_events,
failure_uids as b
where segment_user_events.uid = b.uid;
                """)
    
    cur.execute("""
                CREATE TEMPORARY TABLE success_uids_events
Select segment_user_events.* from segment_user_events,
success_uids as b
where segment_user_events.uid = b.uid;
""")
    
    
    cur.execute("""
                CREATE TEMPORARY TABLE success_uids_events_cnt
SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href,
      COUNT(*) AS cnt
FROM success_uids_events
GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href order by cnt desc;
                """)
    
    
    cur.execute("""
                CREATE TEMPORARY TABLE failure_uids_events_cnt
SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href,
      COUNT(*) AS cnt
FROM failure_uids_events
GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href order by cnt desc;
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
                SELECT * from all_uid_events_cnt limit 2;
                """)
    output = cur.fetchall()
    print output
    


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
        