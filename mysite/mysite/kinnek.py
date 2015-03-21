import sys
import string
import os
import numpy as np
import pandas as pd
from collections import Counter
import csv
import math
import MySQLdb as mdb
import base64
import time
import resource
import json

event_max_column_values = {}
event_max_column_value_attributes = {}
event_data = {}

#Runs the data


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

def get_matthew_corr_coef(feature,fname, print_all, MIN_CORRELATION, conv_events, nc_events):
    min_ctr = min(min(conv_events[feature]),min(nc_events[feature]))
    max_ctr = max(max(conv_events[feature]),max(nc_events[feature]))
    tp = get_cumsum_counts1(feature,conv_events,min_ctr, max_ctr)
    fp = get_cumsum_counts1(feature,nc_events,min_ctr, max_ctr)
    
    fn = get_cumsum_counts2(feature,conv_events,min_ctr, max_ctr)
    tn = get_cumsum_counts2(feature,nc_events, min_ctr, max_ctr)
    #min_cnt = np.min([np.min(tp.keys()),np.min(fp.keys()),np.min(tn.keys()),np.min(fn.keys())])
    #max_cnt = np.max([np.max(tp.keys()),np.max(fp.keys()),np.max(tn.keys()),np.max(fn.keys())])
    
    
    output_tuples = []
    significance_higher = False
    mcc_max = 0
    mcc_max_dict = {}
    precision_max = 0
    precision_max_dict = {}
    recall_max = 0
    recall_max_dict = {}
    cost_max = 0
    cost_max_dict = {}
    npv_max = 0
    npv_max_dict = {}
    f1_max = 0
    f1_max_dict = {}
    scaled_mcc_max = 0
    scaled_mcc_max_dict = {}
    
    for i in range(min_ctr,max_ctr+1):
        tpv = tp[i]
        fpv = fp[i]
        tnv = tn[i]
        fnv = fn[i]
        total = tpv + fpv + tnv + fnv
        leverage = (tpv + 0.0)/total - (tpv + fpv + 0.0)/total * (0.0 + tpv + fnv)/total
        lift = ((tpv + 0.0)/total)/(((tpv + fpv + 0.0)/total) * ((tpv + fnv + 0.0)/total))
        #print tpv,fpv,tnv,fnv,total,lift,leverage
        if i == min_ctr:
            event_max_column_value_attributes[feature] = {"event": feature}
        if ((min_ctr > 0 and i == min_ctr) or (min_ctr == 0 and i == min_ctr + 1)):
            event_max_column_value_attributes[feature].update({"num_people_clicked": (tpv + fpv)})
            
        #print i,tpv,fpv,tnv,fnv
        mcc = (tpv * tnv  - fpv * fnv)/math.sqrt(max(tpv + fpv,1)*max(tpv + fnv,1)*max(tnv + fpv,1) * max(tnv + fnv,1))

        significance = abs(mcc) * abs(mcc) * total
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
        scaled_mcc = num_users * mcc * mcc
        f1_score = 2 * (precision * negative_predictive_value)/(negative_predictive_value + precision)
        output_tuples.append((i,tpv,fpv,tnv,fnv,mcc,significance,precision,recall, cost,negative_predictive_value,f1_score,num_users,scaled_mcc,lift,leverage))
        output_dict = {}
        output_dict["i"] = i
        output_dict["tpv"] = tpv
        output_dict["fpv"] = fpv
        output_dict["fnv"] = fnv
        output_dict["mcc"] = mcc
        output_dict["precision"] = precision
        output_dict["recall"] = recall
        output_dict["cost"] = cost
        output_dict["significance"] = significance
        output_dict["negative_predictive_value"] = negative_predictive_value
        output_dict["f1"] = f1_score
        output_dict["num_users"] = num_users
        output_dict["scaled_mcc"] = scaled_mcc
        output_dict["lift"] = lift
        output_dict["leverage"] = leverage
        
        if abs(mcc) > mcc_max:
            mcc_max = abs(mcc)
            mcc_max_dict = output_dict
        if precision > precision_max:
            precision_max = precision
            precision_max_dict = output_dict
        if recall > recall_max:
            recall_max = recall
            recall_max_dict = output_dict
        if cost > cost_max:
            cost_max = cost
            cost_max_dict = output_dict
        if negative_predictive_value > npv_max:
            npv_max = negative_predictive_value
            npv_max_dict = output_dict
        if f1_score > f1_max:
            f1_max = f1_score
            f1_max_dict = output_dict
        if scaled_mcc > scaled_mcc_max:
            scaled_mcc_max = scaled_mcc
            scaled_mcc_max_dict = output_dict           



    str_output = ""
    if significance_higher:
        event_max_column_values[feature] = {"mcc_max": mcc_max, "precision_max":precision_max,"recall_max":recall_max,"cost_max":cost_max,"npv_max":npv_max,"f1_max":f1_max, "scaled_mcc_max":scaled_mcc_max}
        event_max_column_value_attributes[feature].update({"precision_max_dict":precision_max_dict,"scaled_mcc_max_dict":scaled_mcc_max_dict,"mcc_max_dict":mcc_max_dict})

        
        if print_all:
            writer = open(fname,"wb")
            writer.write(str(scaled_mcc_max_dict))
            writer.write("\n");
            writer.write(feature)
            writer.write("\n");
            writer.write("i\tTrue positives\tFalse Positives\tTrue Negatives\tFalse Negatives\tMCC\tChi squared\tPrecision\tRecall\tCost\tNPV\tF1\tNum_users\tscaled_MCC\tLift\tLeverage\n")
        else:
            str_output = feature
            str_output = str_output + "\n"
            str_output = str_output + "i\tTrue positives\tFalse Positives\tTrue Negatives\tFalse Negatives\tMCC\tChi squared\tPrecision\tRecall\tCost\tNPV\tF1\tNum_users\tscaled_MCC\tLift\tLeverage\n"
        for row in output_tuples:
            if print_all:
                writer.write(str(row[0]) + "\t" + str(row[1]) + "\t" + str(row[2]) + "\t" + str(row[3]) + "\t" + str(row[4]) + "\t" + str(row[5]) + "\t" + str(row[6]) + "\t" + str(row[7]) + "\t" + str(row[8]) + "\t" + str(row[9]) + "\t" + str(row[10]) + "\t" + str(row[11]) + "\t" + str(row[12]) + "\t" +  str(row[13]) + "\t" + str(row[14]) + "\t" + str(row[15]) )
                writer.write("\n")
            else:
                str_output = str_output + str(row[0]) + "\t" + str(row[1]) + "\t" + str(row[2]) + "\t" + str(row[3]) + "\t" + str(row[4]) + "\t" + str(row[5]) + "\t" + str(row[6]) + "\t" + str(row[7]) + "\t" + str(row    [8]) + "\t" + str(row[9]) + "\t" + str(row[10]) + "\t" + str(row[11]) + "\t" + str(row[12]) + "\t" + str(row[13]) + "\t" + str(row[14]) + "\t" + str(row[15]) 
                str_output = str_output + "\n"
        if print_all:
            writer.close()
        else:
            event_data[feature] = str_output 
    return


def create_foldername_for_user(username):
    print "GENERATING FOLDERNAME"
    valid_chars = "-_%s%s" % (string.ascii_letters, string.digits)
    file_name_string = ''.join(c for c in username if c in valid_chars)
    return file_name_string


def generate_event_files(testing, print_all, filter_query, success_query, merchant_name, username, MIN_CORRELATION=0.2):
    temp_prefix = ''
    temp_table_prefix = ''

    if testing == True:
        temp_prefix = " TEMPORARY "
        temp_table_prefix = 'temp_'
        print "just testing if this is a good segment"
    user_folder = create_foldername_for_user(username)
    print user_folder
    main_folder = "/data/"
    folder = os.path.join(main_folder, user_folder)
    print folder
    
    merchant_name_ = merchant_name + "_"
    user_folder_ = user_folder + "_"
    
    ##segment_where ="""  img_src='http://resources.kinnek.com/static/css/Buyer/Products/get_quotes_button.f382438052ec.png'  """
    #start_hc <=5 and (landing_url ='http://www.kinnek.com/' or landing_url = 'http://kinnek.com/' or landing_url like 'http://www.kinnek.com/?%' or landing_url like 'http://kinnek.com/?%')
    #title = 'my requests | kinnek.com'
    ##success_where =""" name_attr='confirmpurchase' or name_attr='order' """
    #url='http://www.kinnek.com/post/#justcreated' or name='submit_profile'
    #url='http://www.kinnek.com/post/#justcreated' or name='submit_profile'
    #name_attr='confirmpurchase' or name_attr='order'
    
    con = mdb.connect("localhost", "root", "thebakery", "orient")
    
    with con:
        cur = con.cursor()
        if testing == False: #if not testing then drop all tables
            tablelist = ['%suser_segment' %(temp_table_prefix),'%ssuccess_uids' %(temp_table_prefix),'user_segment','success_uids', 'failure_uids','failure_uids_events','success_uids_events', 'success_uids_events_cnt', 'failure_uids_events_cnt', 'all_uid_events_cnt', 'all_segment_events']
            
            for i in tablelist:
                try:
                    print user_folder_
                    print i
                    sql_query = "drop table %s%s;" % (user_folder_, i)
                    print sql_query
                    cur.execute(sql_query)
                    print "success"
                except:
                    pass

        start_time = time.time()
        querya = """
                    CREATE %s TABLE %s%suser_segment
            select distinct %suser_events.uid from %suser_events where %s;""" % (temp_prefix, user_folder_, temp_table_prefix, merchant_name_, merchant_name_, filter_query)
        print "executing %s" % (querya)
        start_time = time.time()
        cur.execute(querya) 
        print "Took ", (time.time() - start_time), " seconds"
        
        queryb = """
                    CREATE %s TABLE %s%ssuccess_uids
    SELECT DISTINCT t1.uid,min(t1.log_time) as log_time FROM %suser_events t1 join %s%suser_segment t2 on (t1.uid=t2.uid) where %s group by t1.uid; """ % (temp_prefix, user_folder_, temp_table_prefix, merchant_name_, user_folder_, temp_table_prefix, success_query)
        print "executing %s" % (queryb)
        start_time = time.time()
        cur.execute(queryb)

        print "Took ", (time.time() - start_time), " seconds"

        print "Testing is true so just returning numbers"
        
        #Find total users
        start_time = time.time()
        cur.execute("""select count(*) from (select distinct uid from %suser_events) x;""" % (merchant_name_))
        total_user_count = cur.fetchone()
        print ['total_user_count', total_user_count]
        
        start_time = time.time()
        cur.execute("""
                SELECT count(*) from %s%suser_segment;
                """ % (user_folder_, temp_table_prefix))
        user_segment_count = cur.fetchone()
        print ['user_segment_count', user_segment_count]
        
        start_time = time.time()
        cur.execute("""
                SELECT count(*) from %s%ssuccess_uids;
                """ % (user_folder_, temp_table_prefix))
        success_uids_count = cur.fetchone()
        print ['success_uids_count', success_uids_count]
        
        summary_metrics = {'Total users': total_user_count[0],
                    'Users considered': user_segment_count[0],
                    'Users who attained success goal': success_uids_count[0]}
        
        if testing == True:    
            return summary_metrics

            
        query1 = """
        CREATE TABLE %sfailure_uids
        SELECT distinct A.uid from %suser_segment A where A.uid not in (select uid from %ssuccess_uids);
        """ % (user_folder_, user_folder_, user_folder_ )
        print "executing %s" % (query1)
        start_time = time.time()
        cur.execute(query1)
        print "Took ", (time.time() - start_time), " seconds"

        index_query1 = """ alter table %sfailure_uids add index (uid); """ % (user_folder_)

        print "executing ",index_query1
        start_time = time.time()
        cur.execute(index_query1)
        print "Took ", (time.time() - start_time), " seconds"
    
        query2 = """
                    CREATE TABLE %sfailure_uids_events
    Select a.* from %suser_events a,
    %sfailure_uids as b
    where a.uid = b.uid;
                    """ % (user_folder_, merchant_name_, user_folder_)
        print "executing %s" % (query2)
        start_time = time.time()
        cur.execute(query2)
        print "Took ", (time.time() - start_time), " seconds"
        
        query3 = """
                    CREATE TABLE %ssuccess_uids_events
    Select a.* from %suser_events a,
    %ssuccess_uids as b
    where a.uid = b.uid and a.log_time <= b.log_time;
    """ % (user_folder_, merchant_name_, user_folder_)
        print "executing %s" % (query3)
        start_time = time.time()
        cur.execute(query3)
        print "Took ", (time.time() - start_time), " seconds"
        
        
        query4 = """
                    CREATE TABLE %ssuccess_uids_events_cnt
    SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr, min(hc),
          COUNT(*) AS cnt
    FROM %ssuccess_uids_events
    GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr order by cnt desc;
                    """ % (user_folder_, user_folder_)
        print "executing %s" % (query4)
        start_time = time.time()
        cur.execute(query4)
        print "Took ", (time.time() - start_time), " seconds"
        
        query5 = """
                    CREATE  TABLE %sfailure_uids_events_cnt
    SELECT uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr, min(hc) as hc,
          COUNT(*) AS cnt
    FROM %sfailure_uids_events
    GROUP BY uid, etype, url, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, name_attr order by cnt desc;
                    """ % (user_folder_, user_folder_)
        print "executing %s" % (query5)
        start_time = time.time()
        cur.execute(query5)
        print "Took ", (time.time() - start_time), " seconds"
        
        
        start_time = time.time()
        cur.execute("""
                    Alter table %ssuccess_uids_events_cnt add converted boolean default True;
                    """ % (user_folder_))
        print "Took ", (time.time() - start_time), " seconds"
        
        
        start_time = time.time()
        cur.execute("""
                    Alter table %sfailure_uids_events_cnt add converted boolean default False;
                    """ % (user_folder_))
        print "Took ", (time.time() - start_time), " seconds"
        
        
        query6 = """
                    CREATE table %sall_uid_events_cnt
    SELECT %ssuccess_uids_events_cnt.* FROM %ssuccess_uids_events_cnt
    UNION SELECT %sfailure_uids_events_cnt.* FROM %sfailure_uids_events_cnt;
                    """ % (user_folder_, user_folder_,user_folder_, user_folder_,user_folder_)
        print "EXECUTING ", query6            
        start_time = time.time()
        cur.execute(query6)
        print "Took ", (time.time() - start_time), " seconds"
    
        start_time = time.time()
        cur.execute("""
                CREATE table %sall_segment_events
                SELECT %ssuccess_uids_events.* FROM %ssuccess_uids_events
                UNION SELECT %sfailure_uids_events.* FROM %sfailure_uids_events;
                                """ % (user_folder_, user_folder_,user_folder_, user_folder_,user_folder_))    
        print "Took ", (time.time() - start_time), " seconds"
        
        print "select count(*) from all_uid_events_cnt"
        start_time = time.time()
        cur.execute("""
                    SELECT count(*) from %sall_uid_events_cnt;
                    """ % (user_folder_))
        print "Took ", (time.time() - start_time), " seconds"
        
        print "last query"
        start_time = time.time()
        cur.execute("""
                    SELECT * from %sall_uid_events_cnt order by uid;
                    """ % (user_folder_))
        print "Took ", (time.time() - start_time), " seconds"
        print "HERE"
        
        #managing output directory, 
        #check if directory exists
        if not os.path.exists(folder):
            os.makedirs(folder)
            print "created the folder"
            print folder
            
        print "Starting to delete files in " + folder
        
        for the_file in os.listdir(folder):
            file_path = os.path.join(folder, the_file)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception, e:
                print "No files in this directory"
                print e
    
        print "finished deleting files in " + folder
    
        #write a summary of what you've just outputted in sql
        summary_json = {
            'users_considered': filter_query,
            'success_users': success_query,
            'metrics': json.dumps(summary_metrics),
        }
        with open(os.path.join(folder, 'summary.json'), 'w') as outfile:
            json.dump(summary_json, outfile)
        
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
        hc_ctr = {}
        all_min_hc = {}
        hc_ave_ctr = {}
        hc_sqrd_ctr = {}
        hc_stdev_ctr = {}
        event_total = {}
        column_names = cur.description
        start_time = time.time()
        print "Starting to go through all rows"
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
                    for event in hc_ctr:
                        if event not in event_total:
                            event_total[event] = 0
                        event_total[event] += 1
                        if event not in hc_ave_ctr:
                            hc_ave_ctr[event] = 0
                            hc_sqrd_ctr[event] = 0
                        if event not in all_min_hc:
                            all_min_hc[event] = []
                        all_min_hc[event].append(hc_ctr[event])
                        hc_ave_ctr[event] += hc_ctr[event]
                        hc_sqrd_ctr[event] += (hc_ctr[event] * hc_ctr[event])
                        #print "HC:",prev_uid, event, hc_ctr[event]

                agg_event_ctr.clear()
                hc_ctr.clear()
           
            prev_conv = row[-1]
            prev_uid = uid
           
            is_conv = row[-1]
            event_signatures = set()
            event_signature_str = ""
            for i in range(1,len(row) - 3):
                field_name = column_names[i][0]
                if str(row[i]).strip() == "" or str(row[i]).strip() == "null" or str(row[i]).strip() == "undefined" or field_name == "is_conversion":
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
                    if event_signature_temp in hc_ctr:
                        hc_ctr[event_signature_temp] = min(hc_ctr[event_signature_temp],row[-3])
                    else:
                        hc_ctr[event_signature_temp] = row[-3]
            #print "EVENT SIGNATURE",event_signature_str
            event_signatures.add(event_signature_str)
            for event_signature in event_signatures:
                hc_ctr[event_signature] = row[-3]

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
        
        print "Took ", (time.time() - start_time), " seconds"
        for e in event_total.keys():
            if event_total[e] > 1:
                hc_stdev_ctr[e] =  math.sqrt((event_total[e] * hc_sqrd_ctr[e] - hc_ave_ctr[e]*hc_ave_ctr[e])/(event_total[e] * (event_total[e]-1)))
            else:
                hc_stdev_ctr[e] =  0
            hc_ave_ctr[e] = (hc_ave_ctr[e] + 0.0)/(0.0 + event_total[e])
            #print e, "\t", hc_ave_ctr[e]
        ctr = 0
        total_conv = len(conv_uids)
        total_nc = len(nc_uids)
        #print len(sys.argv), "\t",sys.argv
        #print_all = str2bool(sys.argv[1])
        #MIN_CORRELATION = 0.2
        #if len(sys.argv) == 3:
        #    MIN_CORRELATION = float(sys.argv[2])
        print "print_all", print_all, "min_correlation", MIN_CORRELATION + 0.1
        for event in event_metadata:
            if event in conv_events and event in nc_events:
                num_conv_with_zero = total_conv - len(conv_events[event])
                num_nc_with_zero = total_nc - len(nc_events[event])
                conv_events[event].extend([0] * num_conv_with_zero)
                nc_events[event].extend([0] * num_nc_with_zero)
                
                filename = os.path.join(folder, "event" + str(ctr) + ".txt")
                get_matthew_corr_coef(event,filename, print_all, MIN_CORRELATION, conv_events, nc_events)
                ctr += 1
   
        start_time = time.time()
        print "starting to output data"
        if not print_all:
            #metrics = ["f1_max","precision_max","recall_max","cost_max","npv_max","mcc_max"]
            metrics = ["mcc_max"]
            df = pd.DataFrame(event_max_column_values).transpose()
            ctr = 0
            top_k_metrics_to_print = 500
            for metric in metrics:
                print metric
                summary_fname = os.path.join(folder, "table.json")
                summary_dict = {}
                print "writing ", summary_fname
                summary_file_writer = open(summary_fname, "wb")
                for ind in df.sort(metric,ascending=False)[:top_k_metrics_to_print].index:
                    fname = os.path.join(folder, "event" + str(ctr +1) + ".txt")
                    print ctr + 1, " file "
                    #print "event",event_max_column_value_attributes[ind]["event"]
                    #print "npc",event_max_column_value_attributes[ind]["num_people_clicked"]
                    #print "dict",event_max_column_value_attributes[ind]["scaled_mcc_max_dict"]
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"event":event_max_column_value_attributes[ind]["event"]})
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"num_people_clicked":event_max_column_value_attributes[ind]["num_people_clicked"]})
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"ave_clicks":hc_ave_ctr[ind]})
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"ave_clicks_stdev":hc_stdev_ctr[ind]})
                    first_percentile = np.percentile(np.array(all_min_hc[ind]),25)
                    second_percentile = np.percentile(np.array(all_min_hc[ind]),50)
                    third_percentile = np.percentile(np.array(all_min_hc[ind]),75)
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"ave_clicks_25th_percentile":first_percentile})
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"ave_clicks_50th_percentile":second_percentile})
                    event_max_column_value_attributes[ind][metric + "_dict"].update({"ave_clicks_75th_percentile":third_percentile})
                    writer = open(fname,"wb")
                    writer.write(json.dumps(event_max_column_value_attributes[ind][metric + "_dict"]))
                    writer.write("\n")
                    writer.write(event_data[ind])
                    writer.close()
                    summary_dict[str(ctr+1)] = event_max_column_value_attributes[ind][metric + "_dict"]
                    ctr += 1
                print "summary dataframe1"
                summary_df = pd.DataFrame.from_dict(summary_dict).transpose()
                summary_df["ave_clicks_rank"] = np.ceil(summary_df.ave_clicks.astype(float).rank()/(top_k_metrics_to_print/100))
                print "summary dataframe2"
                summary_dict.clear()
                summary_dict = summary_df.transpose().to_dict()
                print "summary dataframe3"
                summary_file_writer.write(str(summary_dict))
                print "summary dataframe4"
                summary_file_writer.close()
                print "done"
            print "Took ", (time.time() - start_time), " seconds"
#generate_event_files(False,False,"start_hc <= 5","element_txt='send invite' or css_class='ember-view ember-text-area paste-emails send-invite-email ui-autocomplete-input ui-autocomplete-loading' or element_txt='tweet link' or element_txt='invite friends'","travefy","admin")
