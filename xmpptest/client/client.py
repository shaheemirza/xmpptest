import datetime
import sys
import timeit
import sleekxmpp
import logging
import os
import time
from sleekxmpp.exceptions import XMPPError
from dateutil.parser import parse
from xmpptest.common.constants import XMPP_HOST, XMPP_PORT, DOMAIN_NAME, \
   INTERVAL, RUN_COUNT


class BasicClient(sleekxmpp.ClientXMPP):
    def __init__(self, jid, password, options, host, port):
        super(BasicClient, self).__init__(jid, password)
        self.results_dict = None
        self.thread_num = None
        self.worker_num = None
        self.options = options
        self.runs = 1
        self.errors = 0
        self.run_counter = 0
        self.boundjid.host = host
        self.boundjid.port = port
        self.auto_authorize = True
        self.auto_subscribe = True
        self.logger = logging.getLogger()
        self.register_plugin('xep_0030')# Service Discovery
        self.register_plugin('xep_0004')# Data Forms
        self.register_plugin('xep_0060')# PubSub
        self.register_plugin('xep_0199')# XMPP Ping
        self.register_plugin('xep_0077')# XPPP Basic registration

    def set_results_dict(self, results_dict):
        self.results_dict = results_dict

    def set_thread_num(self, thread_num):
        self.thread_num = thread_num

    def set_worker_num(self, worker_num):
        self.worker_num = worker_num

    def start(self, event):
        raise NotImplemented

    def message(self, msg):
        raise NotImplemented

    def add_to_result(self, values):
        name = "%s w%st%s" % (self, self.worker_num, self.thread_num)
        if not self.results_dict.get(name):
            self.results_dict[name] = {}
        # self.results_dict[name].update(dict)
        d = self.results_dict[name]
        d.update(values)
        self.results_dict[name] = d

    def set_result_time(self, key, start, stop):
        messages_time = self.get_result(key)
        timedelta = stop - start
        timedelta = timedelta.microseconds / 1000
        t = []
        if not isinstance(messages_time, list):
            messages_time = t
        t.extend(messages_time)
        t.append(timedelta)
        messages_time = t
        self.add_to_result({key: messages_time})

    def get_result(self, key):
        name = "%s w%st%s" % (self, self.worker_num, self.thread_num)
        if not self.results_dict.get(name):
            self.results_dict[name] = {}
        return self.results_dict[name].get(key)

    def cleanup(self):
        self.logger.info("%s cleanup" % self)
        for key, contacts in self.roster._rosters.items():
            for contact in contacts:
                if contact != self.boundjid.bare:
                    self.del_roster_item(contact)
        self.add_to_result({"stop_at": "%s" % datetime.datetime.now()})
        self.disconnect(wait=True)


class Sender(BasicClient):

    def __str__(self):
        return "Sender for %s with pid %s" % (self.msisdn, os.getpid())

    def __init__(self, msisdn, password, recipient, msg, options, host, port):
        super(Sender, self).__init__("%s@%s" % (msisdn, DOMAIN_NAME),
                                     password, options, host, port)
        self.receivers = []
        self.msisdn = msisdn
        self.msg = None
        self.to = None
        self.password = password
        self.create_msg(recipient, msg)
        self.add_event_handler('session_start', self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler("changed_status", self.changed_status)


    def changed_status(self, presence):
        frm = presence.get_from()
        if frm.user != self.msisdn:
            status = presence._get_stanza_values().get("status")
            if status:
                self.logger.info("%s got changed status from %s to %s" %
                                 (self, frm.user, status))

    def create_msg(self, to, msg):
        self.to = "%s@%s" % (to, DOMAIN_NAME)
        self.msg = msg


    # initial messages change
    def start(self, event):
        self.logger.info("%s got start" % self)
        self.add_to_result({"start_at": "%s" % datetime.datetime.now()})
        self.send_presence()
        # self.get_roster()
        # subscribe
        self.send_presence(pto=self.to, ptype='subscribe')
        # add to roster
        self.update_roster(self.to)
        # change presence status
        #self.send_presence(pstatus="initial status", pshow='xa')
        # trigger send message interval loop
        self.send_message(mto=self.to, mbody="start message")


    # main test code
    def message(self, msg):
        try:
            self.logger.info("%s got message %s" % (self, msg))
            if self.run_counter < self.options.runs:
                time.sleep(self.options.interval)
                sent_time = datetime.datetime.now()
                self.send_message(mto=self.to,
                                  mbody="%s %s %s" % (sent_time, self.msg,
                                                      self.run_counter))
                self.send_presence(pstatus="%s changed status %s" %
                                           (sent_time,  self.run_counter),
                                   pshow='xa')
                self.run_counter += 1
                self.add_to_result({"runs": self.run_counter})
            else:
                self.send_message(mto=self.to, mbody="cleanup")
                self.cleanup()
        except XMPPError as e:
            self.add_to_result({"errors": self.errors})
            self.add_to_result({"error_%s_cause_%s" % (self.errors, e)})
            self.errors += 1


class Receiver(BasicClient):

    def __str__(self):
        return "Receiver for %s with pid %s" % (self.msisdn, os.getpid())

    def __init__(self, msisdn, password, options, host, port):
        super(Receiver, self).__init__("%s@%s" % (msisdn, DOMAIN_NAME),
                                       password, options, host, port)
        self.msisdn = msisdn
        self.add_event_handler("session_start", self.start)
        self.add_event_handler("message", self.message)
        self.add_event_handler('presence_subscribed', self.subscribed)
        self.add_event_handler('presence_subscribe', self.subscribe)
        self.add_event_handler("changed_status", self.changed_status)

    def changed_status(self, presence):
        frm = presence.get_from()
        if frm.user != self.msisdn:
            status = presence._get_stanza_values().get("status")
            if status:
                self.logger.info("%s got changed status from %s to %s" %
                                 (self, frm.user, status))

    def subscribe(self, presence):
        self.logger.info("%s got subscribe" % self)

    def subscribed(self, presence):
        self.logger.info("%s got subscribed" % self)

    def start(self, event):
        self.logger.info("%s got start" % self)
        self.send_presence()
        # self.get_roster()

    def message(self, msg):
        try:
            self.logger.info("%s got message %s" % (self, msg))
            # have got and message so we can delete sender from roaste
            if 'cleanup' in msg['body']:
                self.cleanup()
            elif msg['type'] in ('chat', 'normal'):
                if not 'start message' in msg['body']:
                    # parse time from msg body
                    t = msg["body"].split()
                    t = "%s %s" % (t[0], t[1])
                    sent_time = parse(t)
                    now = datetime.datetime.now()
                    self.set_result_time("msg_time", start=sent_time, stop=now)
                    self.run_counter += 1
                    self.add_to_result({"runs": self.run_counter})
                msg.reply("Replay from %s on %s message" % (self, msg['body'])).send()
        except XMPPError as e:
            self.add_to_result({"errors": self.errors})
            self.add_to_result({"error_%s_cause_%s" % (self.errors, e)})
            self.errors += 1
