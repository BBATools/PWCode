import os, sys
from pathlib import Path
self_path = Path(__file__).resolve()
bin_dir = str(self_path.parents[2]) + '/bin'
sys.path.insert(0, bin_dir) 
from database.jdbc import Jdbc

data_dir = str(self_path.parents[2]) + '/_DATA'

# Postgresql example:
#url = 'jdbc:postgresql://localhost:5432/'
#driver_jar = '/home/bba/bin/PWCode/bin/vendor/jdbc/postgresql-42.2.6.jar'
#driver_class = 'org.postgresql.Driver'
#user = 'postgres'
#pwd = 'P@ssw0rd'


# H2 example
url = 'jdbc:h2:/home/bba/Desktop/DoculiveHist_dbo;LAZY_QUERY_EXECUTION=1'
driver_jar = bin_dir + '/vendor/jdbc/h2-1.4.196.jar'
driver_class = 'org.h2.Driver'
user = ''
pwd = ''

#print('test')
jdbc = Jdbc(url, user, pwd, driver_jar, driver_class, True, True)

if jdbc:
    column_position = 3
    table_name = 'EDOKFILES'
    sql_str = 'SELECT EDKID, EFILE FROM ' + table_name
    cnt1 = 0
    cnt2 = 0
    for edkid, efile in jdbc.query(sql_str):
        cnt1 += 1
        fname = table_name + '_' + str(column_position) + '_' + str(cnt1)
        print('%6d. Parsing %s' % (cnt1, fname))
        with open(data_dir + '/' + fname, 'wb') as f:
            f.write(efile)
        cnt2 += 1
        #sys.exit()

    print('Done: extracted %d files (%d skipped).' % (cnt1, (cnt1 - cnt2)))











































