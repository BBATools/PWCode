import os, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parents[2]) + '/bin') 
from database.jdbc import Jdbc


# Postgresql example:
#url = 'jdbc:postgresql://localhost:5432/'
#driver_jar = '/home/bba/bin/PWCode/bin/vendor/jdbc/postgresql-42.2.6.jar'
#driver_class = 'org.postgresql.Driver'
#user = 'postgres'
#pwd = 'P@ssw0rd'

# H2 example
url = 'jdbc:h2:/home/bba/Desktop/DoculiveHist_dbo;LAZY_QUERY_EXECUTION=1'
driver_jar = '/home/bba/bin/PWCode/bin/vendor/jdbc/h2-1.4.196.jar'
driver_class = 'org.h2.Driver'
user = ''
pwd = ''


jdbc = Jdbc(url, user, pwd, driver_jar, driver_class, True, True)
extract_dir = '/home/bba/extract_dir'

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
        with open(extract_dir + '/' + fname, 'wb') as f:
            f.write(efile)
        cnt2 += 1
        sys.exit()

    print('Done: extracted %d files (%d skipped).' % (cnt1, (cnt1 - cnt2)))


























