#!/usr/bin/python2.7
#coding:utf-8
import socket
import sys
import threading
import select
import re

MAXBUF=8192

threads = []
forbid_web = ("map.baidu.com",)
forbid_user = ("127.0.0.2",)
fish_web = ("pt.hit.edu.cn",)

#多线程处理
class Handler(threading.Thread):
    def __init__(self,conn):
        super(Handler,self).__init__()
        self.is_connect = False
        self.is_forbid_site = False
        self.is_forbid_user = False
        self.is_fish_web = False
        self.source=conn
        self.hostname=""
        self.header=""
        #异常处理
        try:
            self.destnation=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error :
            print("Failed to create socket.")
            sys.exit()

    #获取请求报文头部信息
    def get_headers(self):
        header=self.source.recv(MAXBUF)
        self.header = header
        if not header:
            return
        search_result = re.search(r'Host:\s*(\S*)',header)
        if search_result:
            self.hostname = search_result.group(1)
        #检查是否是禁止访问的网站
        for f in forbid_web:
            if self.hostname == f:
                self.is_forbid_site = True
                break
        #检查是否是钓鱼网站
        for fi in fish_web:
            if self.hostname == fi:
                self.is_fish_web = True
                break


    def conn_destnation(self):
        if not self.header:
            return
        port="80"
        if self.hostname.find(':') >0:
            addr,port=self.hostname.split(':')
        else:
            addr=self.hostname
        try:
            ip=socket.gethostbyname(addr)
        except socket.gaierror:
            print("can't get ip!'")
            sys.exit()
        port = int(port)
        self.destnation.connect((ip,port))
        self.is_connect = True

    def send_remote(self):
        self.destnation.send(self.header)

    def forbid_for_web(self):
        self.source.send("<h1>unable to visit!</h1>")    

    def for_fish(self):
        back_data = "HTTP/1.1 302 Moved Temporarily\r\nLocation: http://today.hit.edu.cn\r\n\r\n"
        self.source.send(back_data)

    def renderto(self):
        if not self.header:
            return
        readsocket=[self.destnation]
        while True:
            (rlist,wlist,elist)=select.select(readsocket,[],[],3)
            if rlist:
                data=rlist[0].recv(MAXBUF)
                if len(data)>0:
                    try:
                        a = self.source.send(data)
                        print("sending bytes : " + str(a))
                    except socket.error:
                        print("send error!")
                        sys.exit()
                else:
                    break
            else:
                break


    def run(self):
        readsocket = [self.source]
        while True:
            (rlist,wlist,elist) = select.select(readsocket,[],[],5)
            if rlist:
                self.get_headers()
                if not self.is_forbid_site: 
                    if not self.is_fish_web:
                        if not self.is_connect:
                            self.conn_destnation()
                        self.send_remote()
                        self.renderto()
                    else:
                        self.for_fish()
                        self.source.close()
                        self.destnation.close()
                        break
                else:
                    self.forbid_for_web()
                    self.source.close()
                    self.destnation.close()
                    break
            else:
                self.source.close()
                self.destnation.close()
                break

class Server():

    def __init__(self,host,port):
        self.host=host
        self.port=port
        try:
            self.server=socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        except socket.error:
            print("Failed to create socket.")
            sys.exit()
        self.server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        try:
            self.server.bind((host,port))
        except socket.error:
            print("Failed to bind.")
        self.server.listen(5)

    def start(self):
        request_sock=[self.server]
        while True:
            (rlist,wlist,elist) = select.select(request_sock,[],[],3)
            if rlist:
                flag = False
                conn,addr=self.server.accept()
                for user in forbid_user:
                    if user == addr[0]:
                        flag = True
                        break
                if not flag:
                    new_thread = Handler(conn)
                    new_thread.start()
                    threads.append(new_thread)
                else:
                    print("forbiden user!")
                    self.server.close()
                    break




# 等待所有线程完成
for t in threads:
    t.join()



if __name__=='__main__':
    print("Listening...")
    s=Server('127.1.1.1',8080)
    s.start()
