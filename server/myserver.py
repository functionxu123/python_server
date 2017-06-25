#coding=utf-8
'''
Created on 2017年6月11日

@author: Shell
'''
import socket
import threading
import sys
import os.path as op
import datetime

rootdir='../nets'
dir404=op.join(rootdir,'404.html')

        
GMT_FORMAT = '%a, %d %b %Y %H:%M:%S GMT'
servername='MyServer'


class myserver(object):
    def __init__(self,port=80,version=socket.AF_INET,proto=socket.SOCK_STREAM):
        self.port=port
        self.version=version
        self.protocal=proto
        self.thread=[]
        
    def getlines(self,sock):#获取一次请求内容，以一次接受超时为界，这里由于recv的阻塞效果，要有一定思考
        sock.settimeout(1)
        total_data=[]
        err=1
        #可以通过返回一个状态值告诉进程当前连接状态
        while True:
            try:
                data = sock.recv(1024)
                if not data:
                    err=-1   
            except socket.timeout,msg:#注意接受超时的错误
                break#接受超时就算是一次接受
             
            if not data: break
            total_data.append(data)
        return ''.join(total_data)
    
    def getlines2(self,sock):#另一种以\r\n\r\n为结尾做判断的连接,这个是有问题的
        total_data=''
        while True:
            try:
                data=sock.recv(1024)
            except socket.error,msg:
                break
                
            if not data:break#连接断开了
            
            total_data=total_data+data
            if '\r\n\r\n' in total_data:#到达末尾
                break
        return total_data
    
    def getlines3(self,sock):#另一种以获取的数据长度判断结尾,这个是有问题的，如果数据长度是buf长度的整数倍的话会有问题
        #但是如果结合超时和长度来判断的话就应该没问题了         
        total_data=''
        buflen=10240
        while True:
            try:
                sock.settimeout(2)
                data=sock.recv(buflen)
            except socket.timeout,msg:#注意接受超时的错误
                break#接受超时就算是一次接受
            except socket.error,msg:
                break
                
            if not data:break#连接断开了
            
            total_data=total_data+data
            if len(data)<buflen:#到达末尾
                break
        return total_data
    
    def startup(self):#启动服务器
        print '启动服务器....'
        self.s=socket.socket(self.version,self.protocal)
        try:#绑定时的错误判定
            self.s.bind(('0.0.0.0',self.port))
            print 'has bind port %d'%self.port
        except socket.error,msg:
            print 'Bind failed. Error Code : ' + str(msg[0]) + ' Message ' + str(msg[1])
            sys.exit()
            
        self.s.listen(5)
        while True:
            sock,addr=self.s.accept()
            print 'getconnect:%s'%str(addr )
            t=threading.Thread(target=self.process_con,args=(sock,addr)) #启动一个线程去处理
            self.thread.append(t)  

            t.setDaemon(True)#随主进程一起end  
            t.start() #thread start                                                        
            
    def process_req(self,par):
        par_map={}
        for i in par:
            tep=i.split(':')
            par_map[tep[0].strip()]=tep[1].strip()
        return par_map
            
    def process_head(self,head):#返回为get/post   路径       参数map（没有为空）
        tep=head.split(' ')
        pro=[]
        par={}
        pro.append(tep[0].strip())#加入方式
        gethead=tep[1].split('?')#dir
        
        mdir=rootdir+gethead[0]
        if not(len(op.splitext(mdir))>1 and op.splitext(mdir)[-1]):#表示没有深入到文件
            mdir=op.join(mdir,'index.html')#这里可以更改添加的后缀
        pro.append(mdir)#添加路径
        
        if '?' in tep[1]:#解析参数
            tep_par=gethead[1].split('&')
            for i in tep_par:
                tepi=i.split('=')
                par[tepi[0].strip()]=tepi[1].strip()
        
        pro.append(par)
        
        pro.append(tep[2])
        #print pro
        
        return pro
    
    def sendback(self,sock,head,par):#发送响应头和文件
        if op.exists(head[1]):
            self.sendhead(sock, 200, 'OK',head,par)
            self.sendfile(sock, head[1])
        else:
            self.sendhead(sock, 404, 'Not Found',head,par)
            self.sendfile(sock, dir404)
        
        sock.close()
        
        
    def sendhead(self,sock,num,infor,head,par):#发送响应头
        tep=[]
        tep.append(head[3]+' '+str(num)+' '+infor+'\r\n')

        # 生成datetime对象的过程和我可能不同，这里是拿当前时间来生成
        tep.append('Date:'+datetime.datetime.utcnow().strftime(GMT_FORMAT)+'\r\n')
        tep.append('Server:'+servername+'\r\n')
        tep.append('Connection:'+'closed'+'\r\n')#关闭连接
        #Content-type:image/jpeg
        
        if num==200:#这里进行文件后缀的添加
            if op.splitext(head[1])[-1].lower()=='.jpg':
                tep.append('Content-type: image/jpeg\r\n')
        
        tep.append('\r\n')#这是与正文之间的分割
        sdstr=''.join(tep)

        sock.send(sdstr)
    
    def sendfile(self,sock,path):#返回需要的html
        with open(path,'rb') as f:
            while True:
                tep=f.read(2048)
                if not tep:
                    break
                sock.send(tep)
            
    def process_con(self,sock,addr):#process thread
        print threading.current_thread().name
        
        while True:
            req= self.getlines3(sock)#这里应该判断接受的完整性
            if req:
                print req
                sp=req.strip().split('\r\n')
                print sp
                #下面处理请求
                head=self.process_head(sp[0])
                par=self.process_req(sp[1:])
                #下面处理文件返回
                print '请求文件%s'%head[1]
                
                self.sendback(sock, head,par)                    
                
            else:
                break
        
        sock.close()
        print threading.current_thread().name+' has exit!'
    
if __name__=='__main__':
    t=myserver()
    t.startup()
         


    