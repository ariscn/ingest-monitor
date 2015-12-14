#!/usr/bin/python

import os.path
from datetime import datetime
from datetime import timedelta
import smtplib
from email.mime.text import MIMEText
import logging
import urllib
import time
import argparse
import sys

# smtp.gmail.com 587

class MailSender:
    def __init__(self, server, port, username, password):
        self.server = server
        self.port = port
        self.username = username
        self.password = password

    """
    """
    def SendMail(self, from_addr, to_addr, subject, body):
        msg = MIMEText(body)
        msg['Subject'] = subject
        msg['From'] =  from_addr
        msg['To'] = ", ".join(to_addr)

        try:
            server = smtplib.SMTP(self.server, self.port) #port 465 or 587
            server.ehlo()
            server.starttls()
            server.ehlo()
            server.login(self.username, self.password)
            server.sendmail(from_addr, to_addr, msg.as_string())
            server.close()
        except smtplib.SMTPException:
            print "Unable to send message"

if __name__ == '__main__':

    parser = argparse.ArgumentParser(description='Mail Sender')
    parser.add_argument('-s','--subject', help='Subject', required=False)
    parser.add_argument('-b','--body', help='Body', required=False)
    parser.add_argument('-f','--file', help='File', required=False)
    parser.add_argument('-i','--input', help='From stdin', required=False, action='store_true')
    args = vars(parser.parse_args())

    subject =  None
    body =  None
    filename =  None
    stdin = 0

    if args['subject'] is not None:
       subject = args['subject']
    if args['body'] is not None:
       body = args['body']
    if args['file'] is not None:
       filename = args['file']
    if args['input'] is not None:
       stdin = 1

    if filename is not None:
       with open(filename) as f:
          body = f.read()
    if stdin == 1:
       body = sys.stdin.read()

    sender = MailSender("smtp.gmail.com", 587, "mailer@cognitivenetworks.com", "456test456")
    sender.SendMail("mailer@cognitivenetworks.com", ["ops@cognitivenetworks.com"], subject, body)
