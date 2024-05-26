"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""
# Its an Audio Video Screen Recoder in Python 3
# -*- coding: utf-8 -*-
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

from PyQt5 import QtCore, QtGui, QtWidgets  # pip install pyqt5
from PyQt5.QtWidgets import QFileDialog
import os
import pyautogui  # pip install pyautogui
import cv2
import numpy as np
import pygetwindow as gw
import _thread
import imutils
import time
import signal
from threading import Thread
import shlex
import psutil
import subprocess
from subprocess import Popen
from dateutil.relativedelta import relativedelta # Install it via: pip install python-dateutil


try:
    os.remove("output_video.mp4")
except:
    pass

drawing = False
global x1, y1, x2, y2, num, h, w, windowRegion
x1, y1, x2, y2, h, w = 0, 0, 0, 0, 0, 0
windowRegion = 0
num = 0


class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        self.threadpool = QtCore.QThreadPool()
        MainWindow.setObjectName("MainWindow")

        sizeObject = QtWidgets.QDesktopWidget().screenGeometry(-1)

        H = (sizeObject.height())
        W = (sizeObject.width())

        self.W = W
        self.H = H
        MainWindow.resize(W // 8, H // 10)
        MainWindow.setMinimumSize(QtCore.QSize(W // 5, H // 7))
        MainWindow.setAcceptDrops(True)
        self.centralwidget = QtWidgets.QWidget(MainWindow)
        self.centralwidget.setObjectName("centralwidget")
        self.gridLayout = QtWidgets.QGridLayout(self.centralwidget)
        self.gridLayout.setObjectName("gridLayout")
        self.comboBox = QtWidgets.QComboBox(self.centralwidget)
        self.comboBox.setObjectName("comboBox")
        self.comboBox.addItem('')
        self.cmd = ""
        """ AUDIO and VIDIO DEVICES """
        from PyQt5.QtMultimedia import QAudioDeviceInfo, QAudio, QCameraInfo
        # List of Audio Input Devices
        input_audio_deviceInfos = QAudioDeviceInfo.availableDevices(QAudio.AudioInput)
        for device in input_audio_deviceInfos:
            self.comboBox.addItem(device.deviceName())
        """ ----------------------  """
        self.comboBox.setCurrentIndex(1)
        self.Mic = input_audio_deviceInfos[0].deviceName()
        self.gridLayout.addWidget(self.comboBox, 1, 0, 1, 1)
        self.radioButton = QtWidgets.QRadioButton(self.centralwidget)
        self.radioButton.setObjectName("radioButton")
        self.gridLayout.addWidget(self.radioButton, 2, 0, 1, 1)
        self.pushButton = QtWidgets.QPushButton(self.centralwidget)
        self.pushButton.setMinimumSize(QtCore.QSize(0, 23))
        self.pushButton.setIconSize(QtCore.QSize(16, 25))
        self.pushButton.setObjectName("pushButton")
        self.gridLayout.addWidget(self.pushButton, 3, 0, 1, 1)
        MainWindow.setCentralWidget(self.centralwidget)
        self.statusbar = QtWidgets.QStatusBar(MainWindow)
        self.statusbar.setObjectName("statusbar")
        MainWindow.setStatusBar(self.statusbar)
        self.actionNew = QtWidgets.QAction(MainWindow)
        self.actionNew.setObjectName("actionNew")
        self.retranslateUi(MainWindow)
        QtCore.QMetaObject.connectSlotsByName(MainWindow)
        self.clicked = False
        self.pushButton.clicked.connect(self.takeSnapNow)
        self.radioButton.toggled.connect(self.setStatus)
        self.comboBox.currentIndexChanged[str].connect(self.setAudioDevice)
        self.th = {}
        self.cap = ""
        self.useCam = False
        self.st = 0
        self.arguments = ''
        self.process = None

    def setAudioDevice(self, audioD):
        self.Mic = audioD

    def setStatus(self):
        if self.useCam == False:
            self.useCam = True
        else:
            self.useCam = False

    def draw_rect(self, event, x, y, flags, param):
        global x1, y1, drawing, num, img, img2, x2, y2
        if event == cv2.EVENT_LBUTTONDOWN:
            drawing = True
            x1, y1 = x, y
        elif event == cv2.EVENT_MOUSEMOVE:
            if drawing == True:
                a, b = x, y
                if a != x & b != y:
                    img = img2.copy()

                    cv2.rectangle(img, (x1, y1), (x, y), (0, 255, 0), 2)
        elif event == cv2.EVENT_LBUTTONUP:
            drawing = False
            num += 1
            font = cv2.FONT_HERSHEY_SIMPLEX
            x2 = x
            y2 = y

    def takeSnap(self):
        global x1, y1, drawing, num, img, img2, x2, y2, h, w
        global windowRegion
        if self.useCam == False:
            key = ord('a')

            im1 = pyautogui.screenshot()
            im1.save(r"monitor-1.png")

            img = cv2.imread('monitor-1.png')  # reading image
            try:
                os.remove('monitor-1.png')
            except:
                pass
            cv2.putText(img, "Click and select the Region, Press w to confirm selection ", (self.W // 8, self.H // 2),
                        cv2.FONT_HERSHEY_TRIPLEX, 1.3, (20, 255, 0), 2, cv2.LINE_AA)

            img2 = img.copy()
            cv2.namedWindow("main", cv2.WINDOW_NORMAL)
            cv2.setMouseCallback("main", self.draw_rect)
            cv2.setWindowProperty("main", cv2.WND_PROP_FULLSCREEN, cv2.WINDOW_FULLSCREEN);

            while key != ord('w'):
                cv2.imshow("main", img)
                key = cv2.waitKey(1) & 0xFF
            (h, w) = ((y2 - y1), (x2 - x1))
            if key == ord('w'):
                cv2.destroyAllWindows()

        else:
            x1, y1, w, h = (0, 0, self.W, self.H)
        if w % 2 == 0:
            pass
        else:
            w = w + 1
        if h % 2 == 0:
            pass
        else:
            h = h + 1
        windowRegion = (x1, y1, w, h)
        return x1, y1, w, h

    def run(self, inp, out):
        global windowRegion
        self.st = time.time()
        cnt = 0
        while (True):
            if self.useCam == True:
                windowRegion = (0, 0, self.W, self.H)
            frame = np.array(pyautogui.screenshot(region=windowRegion), dtype="uint8")
            frame = imutils.resize(frame, width=480)
            frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            cv2.imshow("Preview", frame)
            rt = relativedelta(seconds=time.time() - self.st)
            st = ('{:02d}:{:02d}:{:02d}'.format(int(rt.hours), int(rt.minutes), int(rt.seconds)))
            self.pushButton.setText('Stop Recording: ' + st)
            if cv2.waitKey(1) == 27:
                w = gw.getWindowsWithTitle('Windows PowerShell')[0]
                w.close()
                cv2.destroyAllWindows()
                break

    def takeSnapNow(self):

        if self.clicked == False:

            filename = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget, "Save video to file",
                                                             os.sep.join((os.path.expanduser('~'), 'Desktop')),
                                                             "MP4(*.mp4);;AVI(*.avi);;MKV(*.mkv);;MOV(*.mov)")

            while filename[0] == '':
                pyautogui.alert(text='Please write a video name', title='File name required', button='OK')
                filename = QtWidgets.QFileDialog.getSaveFileName(self.centralwidget, "Save video to file",
                                                                 os.sep.join((os.path.expanduser('~'), 'Desktop')),
                                                                 "MP4(*.mp4);;AVI(*.avi);;MKV(*.mkv);;MOV(*.mov)")

            try:
                os.remove(filename[0])
            except:
                pass

            x1, y1, w, h = self.takeSnap()

            # self.cmd = r'"ffmpeg -rtbufsize 100M -f dshow -i audio="{}" -f -y -rtbufsize 100M -f gdigrab -framerate 30 -offset_x {} -offset_y {} -video_size {}x{} -draw_mouse 1 -i desktop -c:v libx264 -r 30 -preset ultrafast -tune zerolatency -crf 25 -pix_fmt yuv420p "{}"'.format(self.Mic,x1,y1,w,h,filename[0])

            self.cmd = """ffmpeg -rtbufsize 1500M -f dshow -i audio="{}" -f -y -rtbufsize 1500M -f gdigrab -framerate ntsc -offset_x {} -offset_y {} -video_size {}x{} -draw_mouse 1 -i desktop -c:v libx264 -r 30 -preset ultrafast -tune zerolatency -crf 1 -pix_fmt yuv420p "{}" """.format(
                self.Mic, x1, y1, w, h, filename[0])

            self.arguments = shlex.split(self.cmd)

            self.th[0] = Thread(target=self.run, args=(1, 1))
            self.th[1] = Thread(target=self.makeVideo, args=(1,))
            self.th[0].start()
            self.th[1].start()
            self.clicked = True

            self.pushButton.setShortcut("Ctrl+r")
            self.radioButton.setEnabled(False)
        else:
            self.pushButton.setEnabled(False)

            self.pushButton.setText('Finalizing...')

            w = gw.getWindowsWithTitle('Windows PowerShell')[0]
            w.close()

            self.clicked = False

    def makeVideo(self, inp):

        # self.process = subprocess.Popen(self.arguments, shell=True)
        FNULL = open(os.devnull, 'w')
        retcode = subprocess.call(self.arguments, stdout=FNULL, stderr=subprocess.STDOUT)

    def retranslateUi(self, MainWindow):
        _translate = QtCore.QCoreApplication.translate
        MainWindow.setWindowTitle(_translate("MainWindow", "PyShine Video Recorder"))
        self.comboBox.setItemText(0, _translate("MainWindow", "Select Audio Device"))
        self.radioButton.setText(_translate("MainWindow", "Full Screen"))
        self.pushButton.setText(_translate("MainWindow", "Start Recording"))
        self.pushButton.setShortcut(_translate("MainWindow", "Ctrl+r"))
        self.actionNew.setText(_translate("MainWindow", "New"))


if __name__ == "__main__":
    import sys

    app = QtWidgets.QApplication(sys.argv)
    MainWindow = QtWidgets.QMainWindow()
    ui = Ui_MainWindow()
    ui.setupUi(MainWindow)
    MainWindow.show()
    sys.exit(app.exec_())

"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""

# Its an Audio Video Screen Recoder in Python 3.
# -*- coding: utf-8 -*-
"""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""""



