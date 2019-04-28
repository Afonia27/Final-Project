#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Fri Jan 25 00:14:29 2019
@author: AfanasiChihaioglo
"""
# -*- coding: utf-8 -*-

# =============================================================================
# This software implements the project which aimed to create the innovative
# way to monitor vehicle state of healh based on the scoring algortyhm. Score
# was then regressed over period of time and the value of gradient was used
# to judje onto performance of the vehicle. 
# Additionally software is capable of establishing connection to the vehicle
# with any ELM327 compatable vehicles. Connection is established through the 
# OBD2 port vie the ELM327 obd connector. 
# Finnally, the connection to AWS Sumerian is established via AWS IoT connection
# UI Created by: PyQt5 UI code generator 5.9.2
# ============================================================================= 

import sys
import obd
from PyQt5.QtWidgets import QApplication, QMainWindow, QFileDialog, QSizePolicy, QDialog,QPushButton, QVBoxLayout, QLineEdit, QLabel, QWidget
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtGui import QIcon, QImage, QPalette, QBrush, QPixmap
from PyQt5.QtCore import pyqtSlot, QSize
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from sklearn.linear_model import LinearRegression
import random
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT as NavigationToolbar
from matplotlib.figure import Figure
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import statsmodels.api as sm

# =============================================================================
# Amazon Web Services class which handles the connection to AWS IoT
# =============================================================================
class AWS(object):
    def __init__(self):
        #Two json's below created to update the Thing shadow 
        self.jsonError = """
        {
            "state" : {
                "reported" : {
                    "y_rotation" : "red"
                 }
             }
        }
        """
        self.jsonOK = """
        {
            "state" : {
                "reported" : {
                    "y_rotation" : "white"
                 }
             }
        }
        """
        # Initiation insturctions forcertificate based connectio
        self.myMQTTClient = AWSIoTMQTTClient("AfAWS")
        self.myMQTTClient.configureEndpoint("a3tjcvi6tnbsej-ats.iot.eu-west-2.amazonaws.com", 8883)
        #Function below uses Thing keys and certificates as file paths as follows: (RootCA cert, private key, Thing cert )
        self.myMQTTClient.configureCredentials("/Users/AfanasiChihaioglo/Desktop/Project/Sumerian IoT/New/AmazonRootCA1.pem", "/Users/AfanasiChihaioglo/Desktop/Project/Sumerian IoT/New/d7078f9608-private.pem.key", "/Users/AfanasiChihaioglo/Desktop/Project/Sumerian IoT/New/d7078f9608-certificate.pem.crt")
        self.myMQTTClient.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
        self.myMQTTClient.configureDrainingFrequency(2)  # Draining: 2 Hz
        self.myMQTTClient.configureConnectDisconnectTimeout(10)  # 10 sec
        self. myMQTTClient.configureMQTTOperationTimeout(5)  # 5 sec
    
    #Function to publish a MQTT request to update a Thing's shadow
    def Sumerian(self,mode = 1):
        self.myMQTTClient.connect()
        if mode == 1:
            self.myMQTTClient.publish("$aws/things/box/shadow/update", self.jsonError, 0)
        elif mode == 0:
            self.myMQTTClient.publish("$aws/things/box/shadow/update", self.jsonOK, 0)
        self.myMQTTClient.disconnect()    

# =============================================================================
# Class for handling the pop-up window containing the graph plot
# =============================================================================     
class Window(QDialog):
    def __init__(self, parent=None):
        super(Window, self).__init__(parent)

        # a figure instance to plot on
        self.figure = plt.figure()
        #Canvas Widget which takes the figure parameter
        self.canvas = FigureCanvas(self.figure)
        # this is the Navigation widget
        # it takes the Canvas widget and a parent
        self.toolbar = NavigationToolbar(self.canvas, self)
        # Setting the layout for the windows
        layout = QVBoxLayout()
        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

# =============================================================================
# Class containing the functions handling the functionality and the actual 
# window design created using Qt Designer and tranlsated to .py format
# ============================================================================= 
class Ui_MainWindow(object):
    
    #Initialisation contains globals because IDE kept changing format
    #However, the self.Days shall be normally used
    def __init__(self):
        global Days
        Days = np.zeros([1, 1])
        global Error_scores
        Error_scores = np.zeros([1,1])
        
    
    def openWindow(self):
        self.window = Window()
        self.window.show()
    
    #Function to open the file with data for plotting by pressing the menu bar
    #button "File"
    def openFile(self):    
        options = QFileDialog.Options()
        global Days
        global Error_scores
        #Open the dialog for user to choose the file path
        fileName, _ = QFileDialog.getOpenFileName(None,"QFileDialog.getOpenFileName()", "","All Files (*);;Text Files (*.txt)", options=options)
        if fileName:
            self.textBrowser_Info.append(fileName) #Append name of the file to Information box
            file = open(fileName,"r")
            self.textBrowser_Info.append(file.read())
            file.close()
            print(fileName)
        
        #Read data from the file usign filepath and parse it
        df = pd.read_csv(fileName,sep="\s+")      
        df.columns = ['Error Scores', 'Days']
        df.head()
        Days = df[['Days']].values #Contains days related to every error score
        Error_scores = df['Error Scores'].values  # Error Scores
        print(str(Error_scores.ndim)+str(Error_scores.shape))
        
    #Function used to connect to the vehicle     
    def connectVehicle(self):
        connection = obd.OBD() #Establish the connection to the vehicle
        if connection.is_connected() == True:
            self.textBrowser_Info.append("Connection is successfully established")
        else:
            self.textBrowser_Info.append("Connection could not be established")
        
        cmd = obd.commands.RPM # select an OBD command to check RPM to verify the connection
        response = connection.query(cmd) # send the command, and parse the response
        response = connection.query(obd.commands.GET_DTC)
        if str(response.value) == '[]':
            self.textBrowser_Info.append("No DTC found")
        else:
            self.textBrowser_Info.append(str(response.value))
    
    #Function to Load list of DTC, calculate the score and append it to text box            
    def loadDTC(self):
        options = QFileDialog.Options()
        fileDTC, _ = QFileDialog.getOpenFileName(None,"QFileDialog.getOpenFileName()", "","All Files (*);;Text Files (*.txt)", options=options)
        if fileDTC:
            self.textBrowser_Info.append(fileDTC)
            file = open(fileDTC,"r")
            self.textBrowser_Info.append(file.read())
            file.close()
            print(fileDTC)
            df = pd.read_csv(fileDTC,header=0, names=['DTC'],sep="\s+")
            score = 0
            undefined = 0
            DTC = ""
            for i in range(0,len(df['DTC'])):
                DTC = list(df['DTC'][i])
                if DTC[0] == "P":
                    score+=3
                elif DTC[0] == "C":
                    score+=2
                elif DTC[0] == "B":
                    score+=1
                else:
                    undefined+=1
            self.textBrowser_Score.clear()
            self.textBrowser_Score.append(str(score))
            
            print("Undefined:"+ str(undefined))

                
    #Function to Generate Regression Model by pressing the 'Generate' button, 
    #Two options availiable in this code, Linear Regression and Lowess Regression
    #Currently, Linear Regression is commented out
    def generateRegressor(self,score): 
        global Days #These globals are used to link to the ones mentioned above
        global Error_scores
        self.textBrowser_Gradient.clear()  #To empty the text boxes
        self.textBrowser_Intercept.clear()
        print("This is X:",Days)
        print("Shape is:",Error_scores.ndim)
        if score != 0:
            Error_scores[len(Error_scores)-1] = score
            print(Days)
            score = 0
        self.openWindow()

        #Function which takes arrays as an input and produces the graph for Linear Regression
        def lin_regplot(X, y, model):
            plt.scatter(X, y, c='steelblue', edgecolor='white', s=70)
            plt.plot(X, model.predict(X), color='black', lw=2)
            return 
        
        #Function which takes arrays as an input and produces the graph for Lowess Regression
        def lowess_regplot(X, y,z):
            plt.scatter(X, z, c='steelblue', edgecolor='white', s=70)
            plt.plot(X, y[:,1], color='black', lw=2)
            return

        #Create linear regressor and append values to boxes
#        slr = LinearRegression()    
#        slr.fit(Days, Error_scores)
#        y_pred = slr.predict(Days)
#        gradient = slr.coef_[0]
#        y_intercept= slr.intercept_
        
        #Lowess 
        lowess = sm.nonparametric.lowess
        Days1 = np.resize(Days,(len(Days),))  # Lowess requries the vector so resize
        w = lowess(Error_scores, Days1, frac=1./2.1) # Generate the Lowess Regressor
        gradient = (w[len(w)-1][1] - w[len(w)-2][1])/(w[len(w)-1][0] - w[len(w)-2][0]) # m = y2-y1/x2-x1
        y_intercept = w[len(w)-1][1] - gradient*(w[len(w)-1][0])  # intercept c= y-mx
        self.textBrowser_Gradient.append(str(gradient))
        self.textBrowser_Intercept.append(str(y_intercept))
        print(gradient)
        print(y_intercept)
        
        #Calculate the new Error score
        Nominal_gradient = 10.6   #THIS IS IMPORTANT VALUE TO CHANGE
        delta_Score=((Nominal_gradient-gradient)*(Days[len(Days)-1]+1))+y_intercept
        Last_Error_Score = Error_scores[len(Error_scores)-1]
        print(Last_Error_Score)
        New_Error_Score = Last_Error_Score+delta_Score
        print(delta_Score)

        
        if gradient >= Nominal_gradient or delta_Score <= 0 or Last_Error_Score >= New_Error_Score:
            self.textBrowser_Info.append("IT IS TIME TO CHECK THE VEHICLE, HIGH SCORE ")
        
        if abs(Last_Error_Score-(gradient*Days[len(Days)-1]+y_intercept)) >= 5:
            self.textBrowser_Info.append("IT IS TIME TO CHECK THE VEHICLE, HIGH OFFSET ")
        
        
        
        #Calculate day of failure
        day_of_failure= (New_Error_Score-y_intercept) / gradient 
        
        if day_of_failure <= Days[len(Days)-1]:
            self.textBrowser_Info.append("IT IS TIME TO CHECK THE VEHICLE, DATE ")
            
        self.textBrowser_Failure.clear()
        self.textBrowser_Failure.append(str(float(day_of_failure)))

        
        #lin_regplot(Days, Error_scores, slr) #PLOT Linear Regression
        #plt.plot(Days,w[:,1], color = 'black')
        lowess_regplot(Days,w,Error_scores)
        plt.xlabel('Time in days')
        plt.ylabel('Current score')
        plt.title("Score= "+str(Last_Error_Score)+" Day of failure= %.2f" % day_of_failure)
        
        #Plot red dotted lines and extend the line
        plt.plot([0,day_of_failure],[New_Error_Score,New_Error_Score],'r--')  
        plt.plot([day_of_failure,day_of_failure],[0,New_Error_Score],'r--')
        #plt.plot([0,day_of_failure],[y_intercept,New_Error_Score],'k') # FOR LINEAR Regression
        plt.plot([w[len(w)-1][0],day_of_failure],[w[len(w)-1][1],New_Error_Score],'k') # FOR Lowess Regression

        plt.show()
        return Days
    
    #Send update request to IoT
    def sendToSumerian(self):
        self.AWS = AWS()
        textboxVal = self.textEdit_WritePoint.toPlainText()
        self.textEdit_WritePoint.setText("")
        if textboxVal == "":
            return
        if textboxVal == "Error":
            self.AWS.Sumerian(1)
        elif textboxVal == "OK":
            self.AWS.Sumerian(0)
        
    #Add the value to Error Score array and increment the Days array
    def addValue(self):
        textboxValue = self.textEdit_WritePoint.toPlainText()
        self.textEdit_WritePoint.setText("")
        if textboxValue == "":
            return
        #print(Days.shape)
        global Days
        global Error_scores
        print(Days)
        print(Error_scores)
        Days = np.append(Days,[Days[len(Days)-1]+1]) # Add the new Day value on day-axis to host new score
        Days = np.reshape(Days,(np.size(Days),-1)) # Reshape the array to be in correct format
        Error_scores = np.append(Error_scores,[float(textboxValue)]) # Add the new point from the text menu
        print(Days)
        print(Error_scores)
        
    #Function which creates all of the backend of visual for the software.
    #Transformed code from Qt Designer
    def setupUi(self, MainWindow):
        MainWindow.setObjectName("MainWindow")
        MainWindow.setEnabled(True)
        MainWindow.resize(981, 565)
        MainWindow.setMinimumSize(QtCore.QSize(186, 565))
        MainWindow.setMaximumSize(QtCore.QSize(981, 565))
        MainWindow.setLayoutDirection(QtCore.Qt.LeftToRight)
        MainWindow.setAutoFillBackground(False)
        
        #Definiton of objects
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setStyleSheet("background-image: url(Jaguar-FUTURE-TYPE.jpg);")
        self.centralwidget.setObjectName("centralwidget")
        self.pushButton_Generate = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Generate.setGeometry(QtCore.QRect(50, 390, 186, 41))
        palette = QtGui.QPalette()
        self.pushButton_Generate.setPalette(palette)
        self.pushButton_Generate.setStyleSheet("QPushButton{ border-width: 2px; border-radius: 10px; border-color: beige; font: bold 14px; min-width: 10em; padding: 6px; }"
                                               "QPushButton:pressed{ border-style: inset; border-width: 2px; border-radius: 10px; border-color: blue; font: bold 14px; min-width: 10em; padding: 6px; }")

        self.pushButton_Generate.setObjectName("pushButton_Generate")
        self.textBrowser_Info = QtWidgets.QTextBrowser(self.centralwidget)
        self.textBrowser_Info.setGeometry(QtCore.QRect(50, 50, 186, 331))
        self.textBrowser_Info.setStyleSheet("background-image: url(:/White/white.jpg);")
        self.textBrowser_Info.setObjectName("textBrowser_Info")
        self.label_Information = QtWidgets.QLabel(self.centralwidget)
        self.label_Information.setGeometry(QtCore.QRect(80, 20, 141, 31))
        self.label_Information.setStyleSheet("background-image: url(:/transparent/transparent.png);\n"
"font: 27pt \"Apple Symbols\";\n"
"font: 75 25pt \"Helvetica\";")
        self.label_Information.setObjectName("label_Information")
        self.pushButton_Connect = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Connect.setGeometry(QtCore.QRect(50, 450, 186, 41))
        palette = QtGui.QPalette()
        self.pushButton_Connect.setPalette(palette)
        self.pushButton_Connect.setStyleSheet("QPushButton{ border-width: 2px; border-radius: 10px; border-color: beige; font: bold 14px; min-width: 10em; padding: 6px; }"
                                               "QPushButton:pressed{ border-style: inset; border-width: 2px; border-radius: 10px; border-color: blue; font: bold 14px; min-width: 10em; padding: 6px; }")
        self.pushButton_Connect.setObjectName("pushButton_Connect")
        self.pushButton_AddPoint = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_AddPoint.setGeometry(QtCore.QRect(250, 420, 186, 41))
        palette = QtGui.QPalette()
        self.pushButton_AddPoint.setPalette(palette)
        self.pushButton_AddPoint.setStyleSheet("QPushButton{ border-width: 2px; border-radius: 10px; border-color: beige; font: bold 14px; min-width: 10em; padding: 6px; }"
                                               "QPushButton:pressed{ border-style: inset; border-width: 2px; border-radius: 10px; border-color: blue; font: bold 14px; min-width: 10em; padding: 6px; }")
        self.pushButton_AddPoint.setObjectName("pushButton_AddPoint")
        
        self.pushButton_Sumerian = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton_Sumerian.setGeometry(QtCore.QRect(560, 420, 186, 41))
        palette = QtGui.QPalette()
        self.pushButton_Sumerian.setPalette(palette)
        self.pushButton_Sumerian.setStyleSheet("QPushButton{ border-width: 2px; border-radius: 10px; border-color: beige; font: bold 14px; min-width: 10em; padding: 6px; }"
                                               "QPushButton:pressed{ border-style: inset; border-width: 2px; border-radius: 10px; border-color: blue; font: bold 14px; min-width: 10em; padding: 6px; }")
        self.pushButton_Sumerian.setObjectName("pushButton_Sumerian")
        
        self.verticalLayoutWidget = QtWidgets.QWidget(self.centralwidget)
        self.verticalLayoutWidget.setGeometry(QtCore.QRect(860, 20, 108, 488))
        self.verticalLayoutWidget.setObjectName("verticalLayoutWidget")
        self.verticalLayout = QtWidgets.QVBoxLayout(self.verticalLayoutWidget)
        self.verticalLayout.setContentsMargins(0, 0, 0, 0)
        self.verticalLayout.setObjectName("verticalLayout")
        self.label_Gradient = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_Gradient.setStyleSheet("font: 22pt \"Apple Symbols\";")
        self.label_Gradient.setObjectName("label_Gradient")
        self.verticalLayout.addWidget(self.label_Gradient)
        self.textBrowser_Gradient = QtWidgets.QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser_Gradient.setStyleSheet("background-image: url(:/White/white.jpg);\n"
"font: 75 18pt \"Helvetica\";")
        self.textBrowser_Gradient.setObjectName("textBrowser_Gradient")
        self.verticalLayout.addWidget(self.textBrowser_Gradient)
        self.label_Intercept = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_Intercept.setStyleSheet("\n"
"font: 22pt \"Apple Symbols\";")
        self.label_Intercept.setObjectName("label_Intercept")
        self.verticalLayout.addWidget(self.label_Intercept)
        self.textBrowser_Intercept = QtWidgets.QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser_Intercept.setStyleSheet("background-image: url(:/White/white.jpg);\n"
"font: 75 18pt \"Helvetica\";")
        self.textBrowser_Intercept.setObjectName("textBrowser_Intercept")
        self.verticalLayout.addWidget(self.textBrowser_Intercept)
        self.label_Score = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_Score.setStyleSheet("\n"
"font: 22pt \"Apple Symbols\";")
        self.label_Score.setObjectName("label_Score")
        self.verticalLayout.addWidget(self.label_Score)
        self.textBrowser_Score = QtWidgets.QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser_Score.setStyleSheet("background-image: url(:/White/white.jpg);\n"
"font: 75 18pt \"Helvetica\";")
        self.textBrowser_Score.setObjectName("textBrowser_Score")
        self.verticalLayout.addWidget(self.textBrowser_Score)
        self.label_Failure = QtWidgets.QLabel(self.verticalLayoutWidget)
        self.label_Failure.setStyleSheet("\n"
"font: 22pt \"Apple Symbols\";")
        self.label_Failure.setObjectName("label_Failure")
        self.verticalLayout.addWidget(self.label_Failure)
        self.textBrowser_Failure = QtWidgets.QTextBrowser(self.verticalLayoutWidget)
        self.textBrowser_Failure.setStyleSheet("background-image: url(:/White/white.jpg);\n"
"font: 75 18pt \"Helvetica\";\n"
"")
        self.textBrowser_Failure.setObjectName("textBrowser_Failure")
        self.verticalLayout.addWidget(self.textBrowser_Failure)
        self.textEdit_WritePoint = QtWidgets.QTextEdit(self.centralwidget)
        self.textEdit_WritePoint.setGeometry(QtCore.QRect(450, 420, 91, 41))
        font = QtGui.QFont()
        font.setFamily("Helvetica")
        font.setPointSize(18)
        self.textEdit_WritePoint.setFont(font)
        self.textEdit_WritePoint.setObjectName("textEdit_WritePoint")
        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QtWidgets.QMenuBar(MainWindow)
        self.menubar.setGeometry(QtCore.QRect(0, 0, 981, 22))
        self.menubar.setAutoFillBackground(False)
        self.menubar.setStyleSheet("\n"
"background-color: qlineargradient(spread:pad, x1:0, y1:0, x2:1, y2:0, stop:0 rgba(0, 0, 0, 255), stop:1 rgba(255, 255, 255, 255));")
        self.menubar.setObjectName("menubar")
        self.menuFIle = QtWidgets.QMenu(self.menubar)
        self.menuFIle.setObjectName("menuFIle")
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionDownload = QtWidgets.QAction(MainWindow)
        self.actionDownload.setObjectName("actionDownload")
        self.actionLoad_DTC_s = QtWidgets.QAction(MainWindow)
        self.actionLoad_DTC_s.setObjectName("actionLoad_DTC_s")
        self.menuFIle.addAction(self.actionDownload)
        self.menuFIle.addAction(self.actionLoad_DTC_s)
        self.actionDownload.triggered.connect(self.openFile)
        self.actionLoad_DTC_s.triggered.connect(self.loadDTC)
        self.menubar.addAction(self.menuFIle.menuAction())

        self.retranslateUi(MainWindow)

        #Attach functions to the buttons
        self.pushButton_Generate.clicked.connect(self.generateRegressor)
        self.pushButton_Connect.clicked.connect(self.connectVehicle)
        self.pushButton_AddPoint.clicked.connect(self.addValue)
        self.pushButton_Sumerian.clicked.connect(self.sendToSumerian)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)

    #Function which creates all of the frontend of visual for the software.
    #Transformed code from Qt Designer
    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", ""))
        self.pushButton_Generate.setText(_translate("MainWindow", "Generate"))
        self.label_Information.setText(_translate("MainWindow", "Information"))
        self.pushButton_Connect.setText(_translate("MainWindow", "Connect to vehicle"))
        self.pushButton_AddPoint.setText(_translate("MainWindow", "Add new point"))
        self.pushButton_Sumerian.setText(_translate("MainWindow", "Send to AWS"))
        self.label_Gradient.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">Gradient</p></body></html>"))
        self.textBrowser_Gradient.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Helvetica\'; font-size:18pt; font-weight:72; font-style:normal;\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'.SF NS Text\'; font-size:13pt; font-weight:400;\"><br /></p></body></html>"))
        self.label_Intercept.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">Intercept</p></body></html>"))
        self.textBrowser_Intercept.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Helvetica\'; font-size:18pt; font-weight:72; font-style:normal;\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.label_Score.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">Score</p></body></html>"))
        self.textBrowser_Score.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Helvetica\'; font-size:18pt; font-weight:72; font-style:normal;\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.label_Failure.setText(_translate("MainWindow", "<html><head/><body><p align=\"center\">Failure Day</p></body></html>"))
        self.textBrowser_Failure.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Helvetica\'; font-size:18pt; font-weight:72; font-style:normal;\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.textEdit_WritePoint.setHtml(_translate("MainWindow", "<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
"<html><head><meta name=\"qrichtext\" content=\"1\" /><style type=\"text/css\">\n"
"p, li { white-space: pre-wrap; }\n"
"</style></head><body style=\" font-family:\'Helvetica\'; font-size:18pt; font-weight:400; font-style:normal;\">\n"
"<p align=\"center\" style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px;\"><br /></p></body></html>"))
        self.menuFIle.setTitle(_translate("MainWindow", "FIle"))
        self.actionDownload.setText(_translate("MainWindow", "Load Data"))
        self.actionLoad_DTC_s.setText(_translate("MainWindow", "Load DTC\'s"))



# =============================================================================
# Class to initiate the window
# ============================================================================= 
class AppWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.show()  
    

# The initiation of the program, the main loop      
if __name__ == "__main__":
    Days = np.empty([1, 1])
    def run_app():
        app = QApplication(sys.argv) 
        window = AppWindow()
        window.show()
        app.exec_()
    run_app()