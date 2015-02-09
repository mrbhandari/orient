import sys
import os
import numpy as np
import pandas as pd
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


event_max_column_values = {}
event_data = {}
def get_cumsum_counts1(feature,array,min_ctr,max_ctr):
    total = len(array[feature])
    ctr = Counter(array[feature])

    arr1 = {}
    arr1[min_ctr - 1] = total
    for i in range(min_ctr,max_ctr+1):
        arr1[i] = arr1[i-1] - ctr[i-1]
    return arr1

def get_cumsum_counts2(feature,array,min_ctr,max_ctr):
    ctr = Counter(array[feature])
    total = len(array[feature])
    arr1 = {}
    arr1[max_ctr] = total - ctr[max_ctr]
    for i in range(max_ctr -1,min_ctr - 1,-1):
        arr1[i] = arr1[i+1] - ctr[i]
    return arr1

def str2bool(v):
    return v.lower() in ("yes", "true", "t", "1")

def get_matthew_corr_coef(feature,fname, print_all, MIN_CORRELATION):
    min_ctr = min(min(conv_events[feature]),min(nc_events[feature]))
    max_ctr = max(max(conv_events[feature]),max(nc_events[feature]))
    tp = get_cumsum_counts1(feature,conv_events,min_ctr, max_ctr)
    fp = get_cumsum_counts1(feature,nc_events,min_ctr, max_ctr)
    
    fn = get_cumsum_counts2(feature,conv_events,min_ctr, max_ctr)
    tn = get_cumsum_counts2(feature,nc_events, min_ctr, max_ctr)
    min_cnt = np.min([np.min(tp.keys()),np.min(fp.keys()),np.min(tn.keys()),np.min(fn.keys())])
    max_cnt = np.max([np.max(tp.keys()),np.max(fp.keys()),np.max(tn.keys()),np.max(fn.keys())])
    mcc_arr = []
    output_tuples = []
    significance_higher = False
    mcc_max = 0
    precision_max = 0
    recall_max = 0
    cost_max = 0
    npv_max = 0
    f1_max = 0
    scaled_mcc_max = 0
    for i in range(min_ctr,max_ctr+1):
        tpv = tp[i]
        fpv = fp[i]
        tnv = tn[i]
        fnv = fn[i]
        total = tpv + fpv + tnv + fnv
        #print i,tpv,fpv,tnv,fnv
        mcc = (tpv * tnv  - fpv * fnv)/math.sqrt(max(tpv + fpv,1)*max(tpv + fnv,1)*max(tnv + fpv,1) * max(tnv + fnv,1))

        significance = mcc * mcc * total
        if significance >= 2.5:
            if print_all:
                significance_higher = significance_higher | (mcc >= MIN_CORRELATION)
            else:
                significance_higher = True
        precision = tpv/(tpv + fpv + 1.00)
        recall = tpv/(tpv + fnv + 1.00)
        negative_predictive_value = tnv/(tnv + fnv + 1.00)
        cost = 10 * tpv - fpv
        num_users = tpv + fpv
        scaled_mcc = num_users * mcc
            
        #print "PRC",precision,recall,cost
        f1_score = 2 * (precision * negative_predictive_value)/(negative_predictive_value + precision)
        output_tuples.append((i,tpv,fpv,tnv,fnv,mcc,significance,precision,recall, cost,negative_predictive_value,f1_score,num_users,scaled_mcc))
        mcc_max = max(mcc_max,abs(mcc))
        precision_max = max(precision_max,precision)
        recall_max = max(recall_max, recall)
        cost_max = max(cost_max,cost)
        npv_max = max(npv_max, negative_predictive_value)
        f1_max = max(f1_max,f1_score)
        scaled_mcc_max = max(scaled_mcc_max,scaled_mcc)
        mcc_arr.append(mcc)

    str_output = ""
    if significance_higher:
        event_max_column_values[feature] = {"mcc_max": mcc_max, "precision_max":precision_max,"recall_max":recall_max,"cost_max":cost_max,"npv_max":npv_max,"f1_max":f1_max, "scaled_mcc_max":scaled_mcc_max}
        if print_all:
            writer = open(fname,"wb")
            writer.write(feature)
            writer.write("\n");
            writer.write("i\tTrue positives\tFalse Positives\tTrue Negatives\tFalse Negatives\tMCC\tChi squared\tPrecision\tRecall\tCost\tNPV\tF1\tNum_users\tscaled_MCC\n")
        else:
            str_output = feature
            str_output = str_output + "\n"
            str_output = str_output + "i\tTrue positives\tFalse Positives\tTrue Negatives\tFalse Negatives\tMCC\tChi squared\tPrecision\tRecall\tCost\tNPV\tF1\tNum_users\tscaled_MCC\n"
        for row in output_tuples:
            if print_all:
                writer.write(str(row[0]) + "\t" + str(row[1]) + "\t" + str(row[2]) + "\t" + str(row[3]) + "\t" + str(row[4]) + "\t" + str(row[5]) + "\t" + str(row[6]) + "\t" + str(row[7]) + "\t" + str(row[8]) + "\t" + str(row[9]) + "\t" + str(row[10]) + "\t" + str(row[11]) + "\t" + str(row[12]) + "\t" +  str(row[13]) )
                writer.write("\n")
            else:
                str_output = str_output + str(row[0]) + "\t" + str(row[1]) + "\t" + str(row[2]) + "\t" + str(row[3]) + "\t" + str(row[4]) + "\t" + str(row[5]) + "\t" + str(row[6]) + "\t" + str(row[7]) + "\t" + str(row    [8]) + "\t" + str(row[9]) + "\t" + str(row[10]) + "\t" + str(row[11]) + "\t" + str(row[12]) + "\t" + str(row[13])
                str_output = str_output + "\n"
        if print_all:
            writer.close()
        else:
            event_data[feature] = str_output 
    return



con = mdb.connect("localhost", "root", "thebakery", "orient")

with con:
    cur = con.cursor()
    cur.execute("""
                CREATE TEMPORARY TABLE user_segment
        select distinct user_events.uid from user_events where start_hc <=5 and (landing_url ='http://www.kinnek.com/' or landing_url = 'http://kinnek.com/');
                """)
#select distinct user_events.uid from user_events where start_hc <=5 and (landing_url ='http://www.kinnek.com/' or landing_url = 'http://kinnek.com/');    
#select distinct user_events.uid from user_events where start_hc <=5 and referrer ='';
#select distinct user_events.uid from user_events;
    cur.execute("""
                CREATE TEMPORARY TABLE success_uids
SELECT DISTINCT t1.uid,t1.log_time FROM user_events t1 join user_segment t2 on (t1.uid=t2.uid) where
etype='click' and img_src='http://resources.kinnek.com/static/css/Buyer/Products/get_quotes_button.f382438052ec.png';
                """)
#name_attr='confirmpurchase' or name_attr='order';
#etype='click' and img_src='http://resources.kinnek.com/static/css/Buyer/Products/get_quotes_button.f382438052ec.png';
    cur.execute("""
CREATE TEMPORARY TABLE failure_uids
SELECT distinct A.uid from user_segment A where A.uid not in (select uid from success_uids);
""")

    cur.execute("""
                CREATE TEMPORARY  TABLE failure_uids_events
Select a.* from user_events a,
failure_uids as b
where a.uid = b.uid;
                """)
    
    cur.execute("""
                CREATE TEMPORARY  TABLE success_uids_events
Select a.* from user_events a,
success_uids as b
where a.uid = b.uid and a.log_time < b.log_time;
""")
    
    
    cur.execute("""
                CREATE TEMPORARY  TABLE success_uids_events_cnt
SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr,
      COUNT(*) AS cnt
FROM success_uids_events
GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr order by cnt desc;
                """)
    
        
    cur.execute("""
                CREATE TEMPORARY  TABLE failure_uids_events_cnt
SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr,
      COUNT(*) AS cnt
FROM failure_uids_events
GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr order by cnt desc;
                """)
    
    
    cur.execute("""
                Alter table success_uids_events_cnt add converted boolean default True;
                """)
    
    
    cur.execute("""
                Alter table failure_uids_events_cnt add converted boolean default False;
                """)
    
    
    cur.execute("""
                CREATE TEMPORARY table all_uid_events_cnt
SELECT success_uids_events_cnt.* FROM success_uids_events_cnt
UNION SELECT failure_uids_events_cnt.* FROM failure_uids_events_cnt;
                """)
    
    
    cur.execute("""
                SELECT count(*) from all_uid_events_cnt;
                """)
    
    cur.execute("""
                SELECT * from all_uid_events_cnt order by uid;
                """)
    print "HERE"
    conv_events = {}
    nc_events = {}
    event_metadata = {}
    total_conv = 0
    total_nc = 0
    conv_uids = set()
    nc_uids = set()
    prev_uid = ""
    prev_conv = 0
    agg_event_ctr = {}
    column_names = cur.description
    for row in cur.fetchall(): 
        #print "OUTPUT:" +  str(row)
        uid = row[0]
        if prev_uid != uid:
            if prev_uid != "":
                #print "going to output canonicalized events for ", prev_uid
                #print "prev_conv ", prev_conv

                for event_signature in agg_event_ctr.keys():
                    #print "outputting ", event_signature, agg_event_ctr[event_signature]
                    if event_signature in event_metadata:
                        event_metadata[event_signature] += 1
                    else:
                        event_metadata[event_signature] = 1
                    if prev_conv != 0:
                        if event_signature not in conv_events:
                            conv_events[event_signature] = []
                        conv_events[event_signature].append(agg_event_ctr[event_signature])
                    else:
                        if event_signature not in nc_events:
                            nc_events[event_signature] = []
                        nc_events[event_signature].append(agg_event_ctr[event_signature])
            agg_event_ctr = {} 
       
        prev_conv = row[-1]
        prev_uid = uid
       
        is_conv = row[-1]
        event_signatures = set()
        event_signature_str = ""
        for i in range(1,len(row) - 2):
            field_name = column_names[i][0]
            if str(row[i]).strip() == "":
                continue
            if event_signature_str == "":
                event_signature_str = field_name+ "=" + str(row[i])
            else:
                event_signature_str = event_signature_str + "::" + field_name + "=" + str(row[i])
            event_signature_temp = field_name + "=" + str(row[i])
            if event_signature_temp:
                if event_signature_temp in agg_event_ctr:
                    agg_event_ctr[event_signature_temp] = agg_event_ctr[event_signature_temp] + row[-2]
                else:
                    agg_event_ctr[event_signature_temp] = row[-2]
#        print "EVENT SIGNATURE",event_signature_str
        event_signatures.add(event_signature_str)
        for event_signature in event_signatures:
            if event_signature in event_metadata:
                event_metadata[event_signature] += 1
            else:
                event_metadata[event_signature] = 1
            if is_conv != 0:
                conv_uids.add(row[0])
                if event_signature not in conv_events:
                    conv_events[event_signature] = []
                conv_events[event_signature].append(row[-2])
            else:
                nc_uids.add(row[0])
                if event_signature not in nc_events:
                    nc_events[event_signature] = []
                nc_events[event_signature].append(row[-2])

    ctr = 0
    total_conv = len(conv_uids)
    total_nc = len(nc_uids)
    print len(sys.argv), "\t",sys.argv
    print_all = str2bool(sys.argv[1])
    MIN_CORRELATION = 0.2
    if len(sys.argv) == 3:
        MIN_CORRELATION = float(sys.argv[2])
    print "print_all", print_all, "min_correlation", MIN_CORRELATION + 0.1
    for event in event_metadata:
        #print "ALL EVENT", event
        if event in conv_events and event in nc_events:
            #print "Event signature: ",event
            #print "Num users with non-zero counts and converted: ", len(conv_events[event])
            #print "Num users with non-zero counts and did not convert: ", len(nc_events[event])
            num_conv_with_zero = total_conv - len(conv_events[event])
            num_nc_with_zero = total_nc - len(nc_events[event])
            conv_events[event].extend([0] * num_conv_with_zero)
            nc_events[event].extend([0] * num_nc_with_zero)
            
            filename = "/data/event" + str(ctr) + ".txt"
            get_matthew_corr_coef(event,filename, print_all, MIN_CORRELATION)
            #print event, mcc_arr
            ctr += 1

    if not print_all:
        print "got here"
        #metrics = ["f1_max","precision_max","recall_max","cost_max","npv_max","mcc_max"]
        metrics = ["scaled_mcc_max"]
        df = pd.DataFrame(event_max_column_values).transpose()
        ctr = 0
        top_k_metrics_to_print = 10
        for metric in metrics:
            print metric
            for ind in df.sort(metric,ascending=False)[:top_k_metrics_to_print].index:
                fname = "/data/event" + str(ctr+1) + ".txt"
                print ctr + 1, " file "
                writer = open(fname,"wb")
                writer.write(event_data[ind])
                writer.close()
                ctr += 1

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
        

