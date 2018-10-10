import time
import os
import cmath
import math
import serial
#import statistics
import binascii
import binhex
import thread
#import snap7
#import _mysql
#import MySQLdb
#import csv
import sys
import urllib3
import json
#ttyusb0 down




class mySql:
    def __init__(self, gaugeDevId):
        self.gaugeDevId = gaugeDevId
        self.data={"gaugeDevId":"3",
                   "tableName":"m1",
                   "Serial":"249146279"}

        self.GetDitails()

        #self.SaveValues()
        #self.DB = MySQLdb.connect(host="5.144.130.31", user="hpcoco_ksg", passwd="O}#0buq@KP?F", db="hpcoco_PyV3")
        #self.DB=MySQLdb.connect(host="192.168.100.58",user="ksgv2",passwd="ksgv2",db="ksg_v2")
	    #self.DB = MySQLdb.connect(host="localhost", user="root", passwd="1372", db="KSG")
        #self.co = self.DB.cursor()
        #self.Co.execute("""SELECT * FROM m1 LIMIT 0,%s""",(20,))
        #print (self.Co.fetchall( ,"\n")

        #self.GetMasterUnit()
        #self.GetCurentPartType()
        #self.GetMeanValue()

    def GetDitails(self):
        http = urllib3.PoolManager()
        reqdata=self.data
        reqdata["request"]="GetDitails"
        r = http.request('GET','http://payesh.hpco.co/savier.php',fields={'data': json.dumps(reqdata)})
        rd=r.data[3:].decode('utf-8')
        
        self.obj=json.loads(rd)
        print(self.obj)
        for x in self.obj:
            self.data[x]=self.obj[x]
            self.x=self.obj[x]
            pass
        self.meanValue=self.obj['meanValue']
    

    def SaveValues(self,SQLQuerryStr):
        http = urllib3.PoolManager()
        reqdata=self.data
        reqdata["request"]="setValues"
        #reqdata["params"]=params
        reqdata["SQLQuerryStr"]=SQLQuerryStr
        print SQLQuerryStr
        #                                                                                                      ADD ALL VALUES HERE
        b = http.request('GET','http://payesh.hpco.co/savier.php',fields={'data': json.dumps(reqdata)})
        print b.data


    #def GetMeanValue(self):
        #if self.partType == 1 or self.partType == "1":
        #    self.meanValue = 75
        #    self.gaugeId = 1
        #if self.partType == 2 or self.partType == "2":
        #    self.meanValue = 83
        #    self.gaugeId = 3
        #return self.meanValue



# from threading import Thread

class Indicator:
    data = []
    isPartLoaded = False
    isOnline = False
    measurementRequest = " AAA%cO" % 255
    coolant = 0
    isReady = False
    threadState = True

    def dataStatistic(self):

        self.data = self.data[5:-20]

        if self.data.__len__() > 0:
            self.dataMin = min(self.data)
            self.dataMax = max(self.data)
            self.dataAverage = float((self.dataMin + self.dataMax)) / 2
            self.Ovality = float((self.dataMax - self.dataMin)) / 2
        else:
            self.dataMin = 0
            self.dataMax = 0
            self.dataAverage = 0
            self.Ovality = 0


            # print self.dataMin
            # print self.dataAverage
            # print self.dataMax
            # print self.Ovality

    def read(self, stat=0):
        while self.threadState:
            self.Rs.write(self.measurementRequest)
            tempValue = self.Rs.read(3)
            # print tempValue
            if tempValue.__len__() > 0:

                data = [int(binascii.b2a_hex(tempValue[0]), 16), int(binascii.b2a_hex(tempValue[1]), 16)]
                # print data
                if data[1] > 250:
                    res = float((data[0] - 255)) / 10
		    #print res
                else:
                    res = float((data[0] + data[1] * 16)) / 10
                    #print res
		    # print binascii.b2a_hex(tempValue[2])
			
            else:
                res = 0
                tempValue="%c%c%c"%(0,0,0)


            if (not self.isPartLoaded) and res != 0:  # part is loaded
                self.isPartLoaded = True
                self.data.append(res)
                self.coolant = 0
            elif self.isPartLoaded and res != 0:
                self.data.append(res)
                self.coolant = 0
            elif self.isPartLoaded and res == 0 and self.coolant < 10:
                self.coolant += 1
                self.data.append(res)
            elif self.isPartLoaded and res == 0 and self.coolant > 9:
                self.isPartLoaded = False
                self.coolant = 0
                self.dataStatistic()
                self.isReady = True

            if tempValue[2] == '0':
                self.isPartLoaded = False
                self.coolant = 0
                self.dataStatistic()
                self.isReady = True
                return 0

            time.sleep(0.05)


    def Reset(self):
        # print self.data
        self.data = []
        self.dataMax = 0
        self.dataMin = 0
        self.Ovality = 0
        self.dataAverage = 0

    def __init__(self, idevname, inid, Comment=""):
        self.devname = idevname
        self.id = int(inid)
        self.Comment = Comment
        self.Rs = serial.Serial(port=self.devname.__str__(),
                                baudrate=9600,
                                parity=serial.PARITY_EVEN,
                                stopbits=serial.STOPBITS_ONE,
                                bytesize=serial.EIGHTBITS,
                                timeout=1)
        try:
            self.Rs.write(" AAA%ci%c"%(255,255))
            OkValue = self.Rs.read(2)
            if OkValue != "OK":
                http = urllib3.PoolManager()
                erlog=http.request('GET','http://payesh.hpco.co/err.php',fields={'errCode': '1','error':"Indicator error -%i -- %s \nthere is a unsatesfied connection , please cheack the cable and reboot again."%(self.id,self.Comment),'Serial':'249146279'})
                print(erlog.data[0:].decode('utf-8'))

            else:
                print "Indicator Id=%d \t Comment:%s \t is ready" % (self.id, self.Comment)
                self.isOnline = True
        except Exception, e:

            e=sys.exc_info()
            exc_type, exc_obj, exc_tb = sys.exc_info()
            fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
            http = urllib3.PoolManager()
            erlog=http.request('GET','http://payesh.hpco.co/err.php',fields={'errCode': '1','error':"Indicator error -%i -- %s \nthere is a unsatesfied connection , please cheack the cable and reboot again."%(self.id,self.Comment),'Serial':'249146279'})
            print(erlog.data[0:].decode('utf-8'))
            print("\n\nerror is :__________________________________\n")
            print(str(e))
            print("Indicator error -%i -- %s \nthere is a unsatesfied connection , please cheack the cable and reboot again."%(self.id,self.Comment))
            print("error was____________________________\n")
            print("""sysetem will restart automaticaly in 120 secends""")
            time.sleep(120)
            os.system("""sudo reboot""")
            
        self.indicatorThread = thread.start_new_thread(self.read, (1,))


class Set:
    def __init__(self):
        self.indicators = []
        self.isPartLoaded = False
        self.isOnLine = False
        self.partData = []

        self.SQLQuery = "INSERT INTO `PARTLIST` VALUES (%f,%f)"

        self.isInit = True
        self.isOnLine = True

    def _addIndicator_(self, newIndicator):
        self.indicators.append(newIndicator)
        self.isOnLine = self.isOnLine and self.indicators[-1].isOnline

    def _newPart_(self):

        for myIndicator in self.indicators:  # waiting for part reloaded
            while not myIndicator.isPartLoaded:
                time.sleep(0.050)

        for myIndicator in self.indicators:  # waiting for part Finished
            while myIndicator.isPartLoaded:
                time.sleep(0.050)
        self.partData = []  # reseting the previous part data
        for myIndicator in self.indicators:  # colecting data
            self.partData.append(
                (myIndicator.dataMax, myIndicator.dataAverage, myIndicator.dataMin, myIndicator.Ovality))

        for myIndicator in self.indicators:  # Reset indicators buffer
            myIndicator.Reset()
            # here data is ready and can be called by PartData Variable
	    print "part is : "
        print self.partData
        # sqlcorsor.execute(SQLQuery%(partData))
        # print self.indicators
        # self.writer.writerow( [time.time(),self.partData[0][2] ,self.partData[0][1] ,self.partData[0][0] ,self.partData[0][3] , self.partData[1][2] , self.partData[1][1] , self.partData[1][0] ,  self.partData[1][3] , self.partData[2][2] , self.partData[2][1] , self.partData[2][0] , self.partData[2][3]  ] )
        #mysql.co.execute("""INSERT INTO `m1` VALUES (NULL, %i, %i, CURRENT_TIMESTAMP, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f);""" % (mysql.gaugeId, mysql.partType, float(self.partData[0][2]) / 1000 + float(mysql.meanValue),float(self.partData[0][1]) / 1000 + float(mysql.meanValue),float(self.partData[0][0]) / 1000 + float(mysql.meanValue), float(self.partData[0][3]) / 1000,float(self.partData[1][2]) / 1000 + float(mysql.meanValue),float(self.partData[1][1]) / 1000 + float(mysql.meanValue),float(self.partData[1][0]) / 1000 + float(mysql.meanValue),float(self.partData[1][3]) / 1000,float(self.partData[2][2]) / 1000 + float(mysql.meanValue),float(self.partData[2][1]) / 1000 + float(mysql.meanValue),float(self.partData[2][0]) / 1000 + float(mysql.meanValue),float(self.partData[2][3]) / 1000,float(abs(self.partData[0][1] - self.partData[2][1])) / 1000))
        mysql.SaveValues("""INSERT INTO `m1` VALUES (NULL, %i, %i, CURRENT_TIMESTAMP, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f, %f);""" % (int(mysql.obj['gaugeId']),int( mysql.obj['productType']), float(self.partData[0][2]) / 1000 + float(mysql.meanValue),float(self.partData[0][1]) / 1000 + float(mysql.meanValue),float(self.partData[0][0]) / 1000 + float(mysql.meanValue), float(self.partData[0][3]) / 1000,float(self.partData[1][2]) / 1000 + float(mysql.meanValue),float(self.partData[1][1]) / 1000 + float(mysql.meanValue),float(self.partData[1][0]) / 1000 + float(mysql.meanValue),float(self.partData[1][3]) / 1000,float(self.partData[2][2]) / 1000 + float(mysql.meanValue),float(self.partData[2][1]) / 1000 + float(mysql.meanValue),float(self.partData[2][0]) / 1000 + float(mysql.meanValue),float(self.partData[2][3]) / 1000,float(abs(self.partData[0][1] - self.partData[2][1])) / 1000))
        ############################################################################################################
        #
        #
        #
        #
        #                        S Q L    Q U E R Y   M U S T   B E   A D D ED   H E R E
        #
        #
        #
        #
        #
        #
        #
        ############################################################################################################


if __name__ == '__main__':
    try:
        mysql = mySql(1)
        mysql.SaveValues("""INSERT INTO `unitonline` (`id`, `unitId`, `signalTime`, `signalType`) VALUES (NULL, '15', CURRENT_TIMESTAMP, '0');""")
        itop = Indicator('/dev/ttyUSB0', 1, "top")
        time.sleep(2)
        imid = Indicator('/dev/ttyUSB1', 2, "mid")
        time.sleep(2)
        ibot = Indicator('/dev/ttyUSB2', 3, "bottom")
        time.sleep(1)
        


        #print "\n\n\n\t\tM Y  S Q L  I S :"
        #mysql.SaveValues(SQLQuerryStr="""INSERT INTO `m1` VALUES ('hello')""")

        mySet = Set()
        mySet._addIndicator_(itop)
        mySet._addIndicator_(imid)
        mySet._addIndicator_(ibot)
        print("indicator Added")
        time.sleep(1)
        ## os.system("chromium-browser")
        def browseme(id):
            os.system("sudo chromium-browser --no-sandbox --kiosk http://payesh.hpco.co/charts/part_ditails_1.php")
        thread.start_new_thread(browseme, (1,))

        def onlineme(id):
            while True:
                mysql.SaveValues("""INSERT INTO `unitonline` (`id`, `unitId`, `signalTime`, `signalType`) VALUES (NULL, '15', CURRENT_TIMESTAMP, '2');""")
                time.sleep(300)
                pass
        thread.start_new_thread(onlineme, (2,))
        mysql.SaveValues("""INSERT INTO `unitonline` (`id`, `unitId`, `signalTime`, `signalType`) VALUES (NULL, '15', CURRENT_TIMESTAMP, '1');""")
        while True:
            mySet._newPart_()
            time.sleep(1)
    
    except Exception as ex:

        e=sys.exc_info()
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        http = urllib3.PoolManager()
        erlog=http.request('GET','http://payesh.hpco.co/err.php',fields={'errCode': '0','error':"%s - %s"%(e,(exc_type, fname, exc_tb.tb_lineno)),'Serial':'249146279'})
        print(erlog.data[0:].decode('utf-8'))
        print("\n\nerror is :__________________________________\n")
        print(str(e))
        print("error was____________________________\n")
        print("""sysetem will restart automaticaly in 120 secends""")
        time.sleep(120)
        os.system("""sudo reboot""")