"""
"""

import cherrypy
from cherrypy.process import wspbus
from mako.template import Template
import string
import sys
import os
from datetime import datetime
from datetime import timedelta
import logging
from logging import handlers
import sqlite3
try:
    from urllib import unquote
    from urllib import urlencode
except ImportError:
    from urllib.parse import unquote
    from urllib.parse import urlencode
import urllib
from asq.initiators import query
import requests

def norm(s):
   return s or ""

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

"""
"""
class DB:
    """
    """
    def __init__(self, filename):
        self.db = filename
        self.conn = None
        self.cursor = None

    """
    """
    def Connect(self):
        self.conn = sqlite3.connect(self.db)
        self.conn.row_factory = dict_factory
        self.cursor = self.conn.cursor()

    """
    """
    def Query(self, query):
        if self.conn is None:
           Connect()

        self.cursor.execute(query)
        return self.cursor.fetchall()

    """
    """
    def Execute(self, query, data):
        if self.conn is None:
           Connect()

        self.conn.execute(query, data)
        self.conn.commit()

    """
    """
    def ExecuteNonQuery(self, query):
        if self.conn is None:
           Connect()

        self.conn.execute(query)
        self.conn.commit()

    """
    """
    def Close(self):
        self.conn.close()

"""
"""
class Repository:
    """
    """
    def  __init__(self):
        self.db = DB(os.environ['MONITOR_DB'])
        self.db.Connect()

    """
    """
    def GetAllChannels(self):
        data = self.db.Query("SELECT * FROM Channels ORDER BY Channel")
        return data

    """
    """
    def GetChannels(self, server):
        data = self.db.Query("SELECT * FROM Channels WHERE IPAddress='{0}' ORDER BY Channel".format(server))
        return data

    """
    """
    def GetChannelsByLocation(self, location):
        sql = """SELECT t1.IPAddress, t1.ProcessID, t1.Hostname, t1.Location, t1.Channel, t1.ContentID, t1.Start, t1.Duration, t1.Title, t1.Signal, t1.LastUpdate
                  FROM Channels t1
                  WHERE t1.Location='{0}' ORDER BY t1.Channel""".format(location)
        data = self.db.Query(sql)
        return data


    """
    """
    def GetLocations(self):
        sql = """SELECT DISTINCT t1.Location,
                      (SELECT COUNT(DISTINCT t2.IPAddress)
                       FROM Channels t2
                       WHERE t1.Location = t2.Location) as ServerCount
                 FROM Channels t1
                 ORDER BY t1.Location"""
        data = self.db.Query(sql)
        return data

    """
    """
    def GetServers(self, location):
        print(location)
        #sql = """SELECT DISTINCT Hostname, IPAddress, Location,
        #              (SELECT COUNT(*)
        #               FROM Channels t2
        #               WHERE t1.IPAddress = t2.IPAddress) as ChannelCount,
        #              (SELECT COUNT(*)
        #               FROM Alarms t2
        #               WHERE t1.Channel = t2.Channel AND t2.AlarmClear IS NULL) as DownCount
        #         FROM Channels t1
        #         WHERE Location='{0}' ORDER BY IPAddress""".format(location)
        sql = """SELECT Hostname, IPAddress, Location,
                      (SELECT COUNT(*)
                       FROM Channels t2
                       WHERE t1.IPAddress = t2.IPAddress) as ChannelCount,
                      (SELECT COUNT(*)
                       FROM Alarms t2
                       WHERE t1.Channel = t2.Channel AND t2.AlarmClear IS NULL) as DownCount
                 FROM Channels t1
                 WHERE Location='{0}' GROUP BY Hostname, IPAddress ORDER BY IPAddress """.format(location)
        data = self.db.Query(sql)
        return data

    """
    """
    def InsertChannel(self, channel):
        sql = 'INSERT INTO Channels (IPAddress, ProcessID, Hostname, Location, Channel, ContentID, Start, Duration, Title, Signal, LastUpdate) VALUES (?,?,?,?,?,?,?,?,?,?,?)'
        data = (channel['IPAddress'], channel['ProcessID'], channel['Hostname'], channel['Location'], channel['Channel'], channel['ContentID'], channel['Start'], channel['Duration'], channel['Title'], channel['Signal'], channel['LastUpdate'])
        self.db.Execute(sql, data)

    """
    """
    def GetChannel(self, ipaddress, processid, channel):
        if channel != "None":
            sql = "SELECT * FROM Channels WHERE Channel='{0}' AND IPAddress='{1}'".format(channel, ipaddress)
        else:
            sql = "SELECT * FROM Channels WHERE IPAddress='{0}'".format(ipaddress)

        result = self.db.Query(sql)
        return result

    """
    """
    def UpdateChannel(self, channel):
        sql = 'UPDATE Channels SET IPAddress=?, ProcessID=?, ContentID=?, Start=?, Duration=?, Title=?, Signal=?, LastUpdate=?, Errors=? WHERE ID=?'
        data = (channel['IPAddress'], channel['ProcessID'], channel['ContentID'], channel['Start'], channel['Duration'], channel['Title'], channel['Signal'], channel['LastUpdate'], channel['Errors'], channel['ID'])
        self.db.Execute(sql, data)

    """
    """
    def DeleteChannels(self):
        sql = "DELETE FROM Channels WHERE ID > 0"
        self.db.ExecuteNonQuery(sql)

    """
    """
    def DeleteChannelsByServer(self, name):
        sql = "DELETE FROM Channels WHERE IPAddress ='{0}'".format(name)
        self.db.ExecuteNonQuery(sql)

    """
    """
    def DeleteChannelsByLocation(self, name):
        sql = "DELETE FROM Channels WHERE Location ='{0}'".format(name)
        self.db.ExecuteNonQuery(sql)

    """
    """
    def GetCurrentAlarms(self):
        sql = "SELECT t1.Channel, t1.AlarmType, t1.AlarmSet, t1.AlarmClear, t2.IPAddress, t2.Hostname from Alarms as t1, Channels as t2  WHERE AlarmClear IS NULL AND t1.Channel = t2.Channel"
        result = self.db.Query(sql)
        return result

    def ClearAlarms(self):
        sql = "DELETE FROM Alarms WHERE ID > 0"
        self.db.ExecuteNonQuery(sql)

    def UpdateAlarms(self, channel, to_set, to_clear):
        if (len(to_set) > 0):
            for i in to_set:
               sql = "INSERT INTO  Alarms (Channel, AlarmType, AlarmSet) VALUES (?, ?, ?)"
               data = (channel, i, to_set[i])
               self.db.Execute(sql, data)

        if (len(to_clear) > 0):
            for i in to_clear:
               sql = "UPDATE Alarms SET AlarmClear=? WHERE Channel=? AND AlarmType=? AND AlarmClear IS NULL"
               data = (to_clear[i], channel, i)
               self.db.Execute(sql, data)

"""
"""

TEMPLATE_BASE = os.path.dirname(os.path.realpath(__file__)) + '/templates/'

class MonitorSite:
    """
    """
    @cherrypy.expose
    def index(self, thumbnails=None):
        raise cherrypy.HTTPRedirect("/location")

    """
    """
    @cherrypy.expose
    def api(self, query=None):
        repo = Repository()
        data = repo.GetAllChannels()
        return repr(data)

    """
    """
    @cherrypy.expose
    def server(self, name=None, thumbnails=None, deletechannels=None):
        repo = Repository()
        name = unquote(name)
        if deletechannels is not None:
            repo = Repository()
            repo.DeleteChannelsByServer(name)
            raise cherrypy.HTTPRedirect("/location", 307)

        channellist = repo.GetChannels(name)
        view = "server"
        if thumbnails is not None:
            template = Template(filename=TEMPLATE_BASE + "monitor_thumbnails.html")
        else:
            template = Template(filename=TEMPLATE_BASE + "monitor.html")
        title = "Server: {0}".format(name)
        return template.render(view=view, channellist=channellist, IPAddress=name, title=title)

    """
    """
    @cherrypy.expose
    def location(self, name=None, thumbnails=None, deletechannels=None):
        repo = Repository()
        if deletechannels is not None:
            if (name is not None):
                repo.DeleteChannelsByLocation(unquote(name))
            else:
                repo.DeleteChannels()
            raise cherrypy.HTTPRedirect("/location", 307)

        if name is not None:
            if thumbnails is not None:
                channellist = repo.GetChannelsByLocation(name)
                template = Template(filename=TEMPLATE_BASE + "monitor_thumbnails.html")
                title = "Location: {0}".format(name)
                view = "location"
                return template.render(view=view, channellist=channellist, IPAddress=name, title=title)
            else:
                servers = repo.GetServers(unquote(name))
                for row in servers:
                   row.setdefault('URL', "/server?{0}".format(urlencode({'name':row['IPAddress']})))
                template = Template(filename=TEMPLATE_BASE + "monitor_servers.html")
                title = "Location: {0}".format(name)
                id = urlencode({'name':name})
                return template.render(model=servers, id=id, Location=name, title=title)
        else:
            locations = repo.GetLocations()
            for row in locations:
               row.setdefault('URL', "/location?{0}".format(urlencode({'name':row['Location']})))
            template = Template(filename=TEMPLATE_BASE + "monitor_locations.html")
            title = "All Locations"
            return template.render(model=locations, title=title)

    """
    """
    @cherrypy.expose
    def alarms(self, show=None, clearalarms=None):
        repo = Repository()
        if clearalarms is not None:
            repo = Repository()
            # repo.ClearAlarms()
            raise cherrypy.HTTPRedirect("/alarms", 307)

        if (show is None):
            repo = Repository()
            alarms = repo.GetCurrentAlarms()
            template = Template(filename=TEMPLATE_BASE + "monitor_alarms.html")
            return template.render(model=alarms, title="Current Alarms")

    """
    """
    @cherrypy.expose
    def search(self, term=None):
        if (term is None):
            template = Template(filename=TEMPLATE_BASE + "search.html")
            return template.render(model=None, title="Enter a Hostname, Location or Channel")
        else:
            print("Searching for {0}".format(term))
            repo = Repository()
            allchannels = repo.GetAllChannels()
            servers = query(allchannels).where(lambda x: x['Hostname'] == term).to_list()
            locations = query(allchannels).where(lambda x: x['Location'] == term).to_list()
            channels = query(allchannels).where(lambda x: x['Channel'] == term).to_list()
            template = Template(filename=TEMPLATE_BASE + "search.html")

            if (len(servers) > 0):
                to_return = servers
                title = "Found Server(s)"
            elif (len(locations) > 0):
                to_return = locations
                title = "Found Location(s)"
            elif (len(channels) > 0):
                to_return = channels
                title = "Found Channel(s)"
            else:
                to_return = []
                title = "Did not find any matches"

            if (to_return is not None):
               for row in to_return:
                   row.setdefault('URL', "/server?{0}".format(urlencode({'name':row['IPAddress']})))
            return template.render(model=to_return, title=title)

    """
    """
    @cherrypy.expose
    def deletechannels(self):
        repo = Repository()
        repo.DeleteChannels()
        raise cherrypy.HTTPRedirect("/", 307)

    """
    """
    @cherrypy.expose
    def datadogs(self):
        to_return = []
        with open(os.environ['DATADOG_FILE'], "rU") as f:
            lines = f.readlines()
            for dd in lines:
                dd = dd.strip('\n')
                url = "http://{0}/?cmd=status".format(dd)
                try:
                    out = requests.get(url)
                    if out.status_code == 200:
                        items=eval(out.content)
                        for item in items:
                           contents = item[1].split("_")
                           cid = contents[0]
                           channel = contents[1]
                           points1 = item[2]
                           points2 = item[3]

                           if channel == 'INFOMERCIAL':
                               continue
                           if points1 == 0 and points2 == 0:
                               continue

                           row = {"channel":channel, "cid":cid, "points1":points1, "points2":points2, "datadog":dd}
                           to_return.append(row)
                except:
                     print("Cannot connect to {0}".format(dd))

        template = Template(filename=TEMPLATE_BASE + "datadogs.html")
        return template.render(model=to_return, title="Datadogs")

    """
    """
    @cherrypy.expose
    def poststatus(self, **params):
        ProcessID = cherrypy.request.params.get('ProcessID', None)
        IPAddress = cherrypy.request.params.get('IPAddress', None)
        ContentID = cherrypy.request.params.get('ContentID', None)
        Signal = cherrypy.request.params.get('Signal', None)
        Hostname = cherrypy.request.params.get('Hostname', None)
        Location = cherrypy.request.params.get('Location', None)
        Start = cherrypy.request.params.get('Start', None)
        Duration = cherrypy.request.params.get('Duration', None)
        Title = cherrypy.request.params.get('Title', None)
        Errors = cherrypy.request.params.get('Errors', None)
        Channel = cherrypy.request.params.get('Channel', None)

        print(Errors)
        if (Channel is None):
           print("IPAddress {0}, Process {1}, Channel {2}".format(IPAddress, ProcessID, Channel))
           return

        repo = Repository()
        item = repo.GetChannel(IPAddress, ProcessID, Channel)
        if len(item) == 0 :
            print("New Channel {0}".format(Channel))
            item = {}
            item['ProcessID'] = int(ProcessID)
            item['IPAddress'] = norm(IPAddress)
            item['Hostname'] = norm(Hostname)
            item['Location'] = Location
            item['Channel'] = norm(Channel)
            item['ContentID'] = norm(ContentID)
            item['Start'] = norm(Start)
            item['Duration'] = norm(Duration)
            item['Title'] = norm(Title)
            item['Signal'] = Signal
            item['Errors'] = Errors;
            item['LastUpdate'] = datetime.now()
            item['Alarms'] = {}
            repo.InsertChannel(item)
        else:
            print("Update Channel {0}".format(Channel))
            item = item[0]
            item['ProcessID'] = int(ProcessID)
            item['IPAddress'] = norm(IPAddress)
            item['Hostname'] = norm(Hostname)
            item['Location'] = Location
            item['Channel'] = norm(Channel)
            item['ContentID'] = norm(ContentID)
            item['Start'] = norm(Start)
            item['Duration'] = norm(Duration)
            item['Title'] = norm(Title)
            item['Signal'] = Signal
            item['Errors'] = Errors;
            item['LastUpdate'] = datetime.now()
            repo.UpdateChannel(item)

        return ""

def Start():
    print("Starting...")
    # monitor_conf = os.path.join(os.path.dirname(__file__), 'monitor.conf')
    monitor_conf = {
        'global': {
            'server.socket_host': '0.0.0.0',
            'server.socket_port': 9000,
            'server.thread_pool': 10,
        },
        '/': {
            'tools.staticdir.root': os.path.dirname(__file__),
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': 'static',
        },
    }
    cherrypy.quickstart(MonitorSite(), config=monitor_conf)

if __name__ == '__main__':
    Start()
