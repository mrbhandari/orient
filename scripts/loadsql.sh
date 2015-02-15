#!/bin/bash

#PRE=`echo "LOAD DATA LOCAL  INFILE '"`
#POST=`echo "' into table kinnek_user_events FIELDS terminated by '\t' lines terminated by '\n' (uid, start_time, ip_address, user_agent,referrer, visit_id, url, etype, log_time, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, start_hc, ref_domain,landing_url, name_attr);"`
#
#find /data -name '*.tsv' | awk -v PRE="$PRE" -v POST="$POST" '{ print PRE,$0,POST }'
#|mysql -u root -p orient --local-infile;

FILES=/data/*.tsv
for f in $FILES
    
    
do
    echo "Processing $f file..."

    echo "use orient; LOAD DATA LOCAL  INFILE '$f' into table kinnek_user_events FIELDS terminated by '\t' lines terminated by '\n' (uid, start_time, ip_address, user_agent,referrer, visit_id, url, etype, log_time, is_conversion, element, element_txt, css_class, path, title, img_src, label, href, start_hc, ref_domain,landing_url, name_attr);"| mysql -u root --password=thebakery orient --local-infile
done