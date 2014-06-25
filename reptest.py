#!/usr/bin/python

'''
############################################################################
# JUSTIN'S DEAD SLAVE CHECKER PYTHON SCRIPT, REQUIRES PYTHON, AS WELL AS   #
#                           mysql-connector-python                         #
#             yum install mysql-connector-python python                    #
#                            written by:                                   #
#                     Justin Reiners, Hotlines Inc.                        #
#this script uses the local socket to connect to mysql, parse results of   #
#         SHOW SLAVE STATUS\G and decide to alert or not.                  #
# This should be scheduled in roots crontab, at 15 minute intervals.       #
############################################################################
'''


import sys
from socket import gethostname
import smtplib
import mysql.connector

#fill in email info, uses local smtp service
emailSubject = "Replication problem on slave %s"
emailTo = "justin@hotlinesinc.com"
emailFrom = "admin@hotlinesinc.com"

text = "Uh oh, looks like SLAVE-IO or SLAVE-SQL is stopped on this host, please log in and see what is up. you may need to\
 issue the following command via root access. 'mysqladmin start-slave'\n\n"

def runCmd(cmd):
    cnx = mysql.connector.connect(user='root',
                                  unix_socket='/var/lib/mysql/mysql.sock')
    cur = cnx.cursor(buffered=True)
    cur.execute(cmd)
    columns = tuple( [d[0].decode('utf8') for d in cur.description] )
    row = cur.fetchone()
    if row is None:
        raise StandardError("MySQL Server not configured as Slave")
    result = dict(zip(columns, row))
    cur.close()
    cnx.close()
    return result

try:
    slave_status = runCmd("SHOW SLAVE STATUS")
except mysql.connector.Error, e:
    print >> sys.stderr, "There was a MySQL error:", e
    sys.exit(1)
except StandardError, e:
    print >> sys.stderr, "There was an error:", e
    sys.exit(1)

if (slave_status['Slave_IO_Running'] == 'Yes' and
    slave_status['Slave_SQL_Running'] == 'Yes' and
    slave_status['Last_Errno'] == 0):
    #print "Cool"
    
    else:
    emailBody = [
        "From: %s" % emailFrom,
        "To: %s" % emailTo,
        "Subject: %s" % (emailSubject %  gethostname()),
        "", text ,
        '\n'.join([ k + ' : '+ str(v) for k,v in slave_status.iteritems()]),
        "\r\n",
        ]
    server = smtplib.SMTP("localhost")
    server.sendmail(emailFrom, [emailTo], '\r\n'.join(emailBody))
    server.quit()
