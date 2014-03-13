#!/usr/bin/env python
# coding: utf-8
# Copyright (c) 2011-2014, Sylvain Hellegouarch, Abram Hindle
# All rights reserved.
# 
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
# 
#  * Redistributions of source code must retain the above copyright notice,
#    this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in the
#    documentation and/or other materials provided with the distribution.
#  * Neither the name of ws4py nor the names of its contributors may be used
#    to endorse or promote products derived from this software without
#    specific prior written permission.
# 
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.

# pip install ws4py
# pip install gevent

from gevent import monkey
monkey.patch_all()
import os
import gevent
from ws4py.client.geventclient import WebSocketClient
import json


world = dict()
# set this to something sane 
calls = 3000
class WorldClient(WebSocketClient):
    def opened(self):
        self.count = 0

    def send_new_entity(self,i):
        entity = "X"+str(i)
        data = {'x':i,'y':i}
        world[entity] = data
        packet = { entity : data }
        self.send(json.dumps(packet))
        print "Sent %s" % entity

    def closed(self, code, reason):
        print(("Closed down", code, reason))

    def receive_my_message(self,m):
        print "RECV %s " % m
        w = json.loads(m.data)
        kcnt = 0
        for key in w:
            if (key in world):
                assert world[key] == w[key]
            world[key] = w[key]
            kcnt += 1
        if (kcnt > 0):
            self.count += 1
        if (self.count >= calls):
            self.close(reason='Bye bye')

    def incoming(self):
        while self.count < calls:
            m = ws.receive()
            print "Incoming RECV %s " %m
            if m is not None:
                self.receive_my_message( m )
            else:
                return

    def outgoing(self):
        for i in range(0,calls):
            self.send_new_entity(i)
        

if __name__ == '__main__':
    try:
        os.system("killall gunicorn");
        os.system("bash run.sh &");
        print "Sleeping 3 seconds"
        gevent.sleep(3)
        ws = WorldClient('ws://127.0.0.1:8000/subscribe', protocols=['http-only', 'chat'])
        ws.daemon = False
        ws.connect()     
        ''' what we're doing here is that we're sending new entities and getting them
            back on the websocket '''
        greenlets = [
            gevent.spawn(ws.incoming),
            gevent.spawn(ws.outgoing),
            ]
        gevent.joinall(greenlets)
        # here's our final test
        assert ws.count == calls, ("Expected Responses were given! %d %d" % (ws.count, calls))
        print "Looks like the tests passed!"
    finally:
        #except KeyboardInterrupt:
        ws.close()
        os.system("killall gunicorn");
        print "Sleeping 2 seconds"
        gevent.sleep(2)
