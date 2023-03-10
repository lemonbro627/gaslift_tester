import time
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5 import QtCore
import queue
import serial
import sys
import os
import yaml
from datetime import datetime as dt

default_config = """MIN_WEIGHT_1: 2500
MIN_WEIGHT_2: 2500
MIN_WEIGHT_3: 2500
MIN_WEIGHT_4: 2500
MIN_WEIGHT_5: 2500
SERIAL_SPEED: 9600
SERIAL_PORT: COM3
SLEEP_AFTER_START: 3
SLEEP_AFTER_CHECK: 5"""

if not os.path.exists("config.yaml"):
    with open("config.yaml") as f:
        f.write(default_config)

with open("config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

if not os.path.exists('logs'):
    os.mkdir('logs')

global filename
filename = f'logs/test_{dt.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'

global piston_master
piston_master = {
        'p1': 'on',
        'p2': 'on',
        'p3': 'on',
        'p4': 'on',
        'p5': 'on'
    }

global q
q = queue.LifoQueue()

# global stime

class GetData(QThread):
    def __init__(self, serial):
        QtCore.QThread.__init__(self)
        self.serial = serial
        print(self.serial)

    running = False
    scale_1 = pyqtSignal(str)
    scale_2 = pyqtSignal(str)
    scale_3 = pyqtSignal(str)
    scale_4 = pyqtSignal(str)
    scale_5 = pyqtSignal(str)

    def run(self):
        with open(filename, 'a') as f:
            f.write("date;p1;p2;p3;p4;p5\n")
        while True:
            try:
                line = self.serial.readline()
                data = str(line)[2:-5].split(';')
                q.put_nowait(data)
                with open(filename,'a') as f:
                    f.write(f"{dt.now()};{data[0].replace('.',',')};{data[1].replace('.',',')};{data[2].replace('.',',')};{data[3].replace('.',',')};{data[4].replace('.',',')}\n")
            except Exception as e:
                print(f'Error while parsing response from Arduino: {e}')

            self.scale_1.emit(str(data[0]))
            self.scale_2.emit(str(data[1]))
            self.scale_3.emit(str(data[2]))
            self.scale_4.emit(str(data[3]))
            self.scale_5.emit(str(data[4]))


class CheckData(QThread):
    def __init__(self, serial):
        QtCore.QThread.__init__(self)
        self.serial = serial

    running = False
    p1 = pyqtSignal()
    p2 = pyqtSignal()
    p3 = pyqtSignal()
    p4 = pyqtSignal()
    p5 = pyqtSignal()

    def run(self):
        while self.running:
            with q.mutex:
                q.queue.clear()
            if piston_master['p1'] == 'on':
                self.serial.write('1'.encode('ascii'))
            if piston_master['p2'] == 'on':
                self.serial.write('2'.encode('ascii'))
            if piston_master['p3'] == 'on':
                self.serial.write('3'.encode('ascii'))
            if piston_master['p4'] == 'on':
                self.serial.write('4'.encode('ascii'))
            if piston_master['p5'] == 'on':
                self.serial.write('5'.encode('ascii'))
            with open(filename, 'a') as f:
                f.write(
                    f"{dt.now()};SLEEP AFTER START\n")
            time.sleep(config.SLEEP_AFTER_START)
            with open(filename, 'a') as f:
                f.write(
                    f"{dt.now()};START MEASURING\n")
            if not q.empty():
                data = q.get_nowait()
                print(f'piston_master: {piston_master}')
                print(f'data: {data}')
                print(f'min: {config.MIN_WEIGHT}')
                if piston_master['p1'] == 'on':
                    if float(data[0]) < float(config['MIN_WEIGHT_1']):
                        piston_master['p1'] = 'off'
                        self.p1.emit()
                elif piston_master['p1'] == 'off':
                    if float(data[0]) > float(config['MIN_WEIGHT_1']):
                        piston_master['p1'] = 'on'
                        self.p1.emit()

                if piston_master['p2'] == 'on':
                    if float(data[1]) < float(config['MIN_WEIGHT_2']):
                        piston_master['p2'] = 'off'
                        self.p2.emit()
                elif piston_master['p2'] == 'off':
                    if float(data[1]) > float(config['MIN_WEIGHT_2']):
                        piston_master['p2'] = 'on'
                        self.p2.emit()

                if piston_master['p3'] == 'on':
                    if float(data[2]) < float(config['MIN_WEIGHT_3']):
                        piston_master['p3'] = 'off'
                        self.p3.emit()
                elif piston_master['p3'] == 'off':
                    if float(data[2]) > float(config['MIN_WEIGHT_3']):
                        piston_master['p3'] = 'on'
                        self.p3.emit()

                if piston_master['p4'] == 'on':
                    if float(data[3]) < float(config['MIN_WEIGHT_4']):
                        piston_master['p4'] = 'off'
                        self.p4.emit()
                elif piston_master['p4'] == 'off':
                    if float(data[3]) > float(config['MIN_WEIGHT_4']):
                        piston_master['p4'] = 'on'
                        self.p4.emit()

                if piston_master['p5'] == 'on':
                    if float(data[4]) < float(config['MIN_WEIGHT_5']):
                        piston_master['p5'] = 'off'
                        self.p5.emit()
                elif piston_master['p5'] == 'off':
                    if float(data[4]) > float(config['MIN_WEIGHT_5']):
                        piston_master['p5'] = 'on'
                        self.p5.emit()

                with open(filename, 'a') as f:
                    f.write(
                        f"{dt.now()};STOP MEASURING\n")

                if piston_master['p1'] == 'on':
                    self.serial.write('1'.encode('ascii'))
                if piston_master['p2'] == 'on':
                    self.serial.write('2'.encode('ascii'))
                if piston_master['p3'] == 'on':
                    self.serial.write('3'.encode('ascii'))
                if piston_master['p4'] == 'on':
                    self.serial.write('4'.encode('ascii'))
                if piston_master['p5'] == 'on':
                    self.serial.write('5'.encode('ascii'))
            with open(filename, 'a') as f:
                f.write(
                    f"{dt.now()};START SLEEP AFTER CHECK\n")
            time.sleep(config.SLEEP_AFTER_CHECK)


class Main(QWidget):
    piston_color = {
        'p1': 'g',
        'p2': 'g',
        'p3': 'g',
        'p4': 'g',
        'p5': 'g'
    }

    def __init__(self):
        super().__init__()
        self.serial = serial.Serial(config.SERIAL_PORT, config.SERIAL_SPEED)
        self.serial.setDTR(False)
        time.sleep(1)
        self.serial.flushInput()
        self.serial.setDTR(True)


        self.start_stop_btn = QPushButton('START', self)
        self.label_1_1 = QLabel('?????????????? 1', self)
        self.label_2_1 = QLabel('?????????????? 2', self)
        self.label_3_1 = QLabel('?????????????? 3', self)
        self.label_4_1 = QLabel('?????????????? 4', self)
        self.label_5_1 = QLabel('?????????????? 5', self)
        self.label_0_2 = QLabel('???????????????', self)
        self.btn_1_2 = QCheckBox('??????????????', self)
        self.btn_2_2 = QCheckBox('??????????????', self)
        self.btn_3_2 = QCheckBox('??????????????', self)
        self.btn_4_2 = QCheckBox('??????????????', self)
        self.btn_5_2 = QCheckBox('??????????????', self)
        self.label_0_3 = QLabel('????????????????', self)
        self.label_1_3 = QLabel('0,00', self)
        self.label_2_3 = QLabel('0,00', self)
        self.label_3_3 = QLabel('0,00', self)
        self.label_4_3 = QLabel('0,00', self)
        self.label_5_3 = QLabel('0,00', self)
        self.thread_get = GetData(self.serial)
        self.thread_check = CheckData(self.serial)
        self.thread_get.scale_1.connect(self.label_1_3.setText)
        self.thread_get.scale_2.connect(self.label_2_3.setText)
        self.thread_get.scale_3.connect(self.label_3_3.setText)
        self.thread_get.scale_4.connect(self.label_4_3.setText)
        self.thread_get.scale_5.connect(self.label_5_3.setText)
        self.thread_check.p1.connect(self.do_btn_1_2_color)
        self.thread_check.p2.connect(self.do_btn_2_2_color)
        self.thread_check.p3.connect(self.do_btn_3_2_color)
        self.thread_check.p4.connect(self.do_btn_4_2_color)
        self.thread_check.p5.connect(self.do_btn_5_2_color)

        self.initUI()

    def initUI(self):

        # btn.setToolTip('This is a <b>QPushButton</b> widget')
        self.start_stop_btn.resize(self.start_stop_btn.sizeHint())
        self.start_stop_btn.resize(200, 110)
        self.start_stop_btn.move(1040, 570)
        self.start_stop_btn.clicked.connect(self.do_start_stop)

        self.label_0_2.resize(150, 50)
        self.label_0_2.move(0, 150)
        self.label_0_2.setAlignment(Qt.AlignCenter)
        self.label_0_2.setStyleSheet("QLabel {border-style: solid;border-width: 1px;border-color: black;}")

        self.label_0_3.resize(150, 50)
        self.label_0_3.move(0, 250)
        self.label_0_3.setAlignment(Qt.AlignCenter)
        self.label_0_3.setStyleSheet("QLabel {border-style: solid;border-width: 1px;border-color: black;}")

        self.label_1_1.resize(150, 50)
        self.label_1_1.move(150, 100)
        self.label_1_1.setAlignment(Qt.AlignCenter)
        self.label_1_1.setStyleSheet("QLabel {background-color: green;}")

        self.btn_1_2.resize(self.btn_1_2.sizeHint())
        self.btn_1_2.resize(150, 50)
        self.btn_1_2.move(200, 150)
        self.btn_1_2.clicked.connect(self.do_btn_1_2_on_off)

        self.label_2_1.resize(150, 50)
        self.label_2_1.move(300, 100)
        self.label_2_1.setAlignment(Qt.AlignCenter)
        self.label_2_1.setStyleSheet("QLabel {background-color: green;}")

        self.btn_2_2.resize(self.btn_2_2.sizeHint())
        self.btn_2_2.resize(150, 50)
        self.btn_2_2.move(350, 150)
        self.btn_2_2.clicked.connect(self.do_btn_2_2_on_off)

        self.label_3_1.resize(150, 50)
        self.label_3_1.move(450, 100)
        self.label_3_1.setAlignment(Qt.AlignCenter)
        self.label_3_1.setStyleSheet("QLabel {background-color: green;}")

        self.btn_3_2.resize(self.btn_3_2.sizeHint())
        self.btn_3_2.resize(150, 50)
        self.btn_3_2.move(500, 150)
        self.btn_3_2.clicked.connect(self.do_btn_3_2_on_off)

        self.label_4_1.resize(150, 50)
        self.label_4_1.move(600, 100)
        self.label_4_1.setAlignment(Qt.AlignCenter)
        self.label_4_1.setStyleSheet("QLabel {background-color: green;}")

        self.btn_4_2.resize(self.btn_4_2.sizeHint())
        self.btn_4_2.resize(150, 50)
        self.btn_4_2.move(650, 150)
        self.btn_4_2.clicked.connect(self.do_btn_4_2_on_off)

        self.label_5_1.resize(150, 50)
        self.label_5_1.move(750, 100)
        self.label_5_1.setAlignment(Qt.AlignCenter)
        self.label_5_1.setStyleSheet("QLabel {background-color: green;}")

        self.btn_5_2.resize(self.btn_5_2.sizeHint())
        self.btn_5_2.resize(150, 50)
        self.btn_5_2.move(800, 150)
        self.btn_5_2.clicked.connect(self.do_btn_5_2_on_off)

        self.label_1_3.resize(150, 50)
        self.label_1_3.move(150, 250)
        self.label_1_3.setAlignment(Qt.AlignCenter)

        self.label_2_3.resize(150, 50)
        self.label_2_3.move(300, 250)
        self.label_2_3.setAlignment(Qt.AlignCenter)

        self.label_3_3.resize(150, 50)
        self.label_3_3.move(450, 250)
        self.label_3_3.setAlignment(Qt.AlignCenter)

        self.label_4_3.resize(150, 50)
        self.label_4_3.move(600, 250)
        self.label_4_3.setAlignment(Qt.AlignCenter)

        self.label_5_3.resize(150, 50)
        self.label_5_3.move(750, 250)
        self.label_5_3.setAlignment(Qt.AlignCenter)

        self.setGeometry(0, 0, 1280, 720)
        self.setWindowTitle('TESTER')
        self.show()
        self.btn_1_2.toggle()
        self.btn_2_2.toggle()
        self.btn_3_2.toggle()
        self.btn_4_2.toggle()
        self.btn_5_2.toggle()
        self.thread_get.start()

    def do_start_stop(self):
        print('Start_stop button clicked')
        if self.start_stop_btn.text() == 'START':
            self.start_stop_btn.setText('STOP')
            self.thread_check.start()
            self.thread_check.running = True
            with open(filename, 'a') as f:
                f.write(
                    f"{dt.now()};START BUTTON PUSHED\n")
        elif self.start_stop_btn.text() == 'STOP':
            self.start_stop_btn.setText('START')
            self.thread_check.running = False
            self.thread_check.quit()
            with open(filename, 'a') as f:
                f.write(
                    f"{dt.now()};STOP BUTTON PUSHED\n")
            if piston_master['p1'] == 'on':
                self.serial.write('1'.encode('ascii'))
            if piston_master['p2'] == 'on':
                self.serial.write('2'.encode('ascii'))
            if piston_master['p3'] == 'on':
                self.serial.write('3'.encode('ascii'))
            if piston_master['p4'] == 'on':
                self.serial.write('4'.encode('ascii'))
            if piston_master['p5'] == 'on':
                self.serial.write('5'.encode('ascii'))


    def do_btn_1_2_on_off(self):
        if self.btn_1_2.text() == '??????????????':
            self.btn_1_2.setText('????????????????')
            piston_master['p1'] = 'off'
            # self.label_1_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_1_2.text() == '????????????????':
            self.btn_1_2.setText('??????????????')
            piston_master['p1'] = 'on'
            # self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p1'] == 'off' and self.piston_color['p1'] == 'y':
            self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
        # self.serial.write('1'.encode('ascii'))
        # self.btn_1_2.toggle()

    def do_btn_2_2_on_off(self):
        if self.btn_2_2.text() == '??????????????':
            self.btn_2_2.setText('????????????????')
            piston_master['p2'] = 'off'
            # self.label_2_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_2_2.text() == '????????????????':
            self.btn_2_2.setText('??????????????')
            piston_master['p2'] = 'on'
            # self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p2'] == 'off' and self.piston_color['p2'] == 'y':
            self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p2'] = 'g'
        # self.serial.write('2'.encode('ascii'))
        # self.btn_2_2.toggle()

    def do_btn_3_2_on_off(self):
        if self.btn_3_2.text() == '??????????????':
            self.btn_3_2.setText('????????????????')
            piston_master['p3'] = 'off'
            # self.label_3_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_3_2.text() == '????????????????':
            self.btn_3_2.setText('??????????????')
            piston_master['p3'] = 'on'
            # self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p3'] == 'off' and self.piston_color['p3'] == 'y':
            self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p3'] = 'g'
        # self.serial.write('3'.encode('ascii'))
        # self.btn_3_2.toggle()

    def do_btn_4_2_on_off(self):
        if self.btn_4_2.text() == '??????????????':
            self.btn_4_2.setText('????????????????')
            piston_master['p4'] = 'off'
            # self.label_4_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_4_2.text() == '????????????????':
            self.btn_4_2.setText('??????????????')
            piston_master['p4'] = 'on'
            # self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p4'] == 'off' and self.piston_color['p4'] == 'y':
            self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p4'] = 'g'
        # self.serial.write('4'.encode('ascii'))
        # self.btn_4_2.toggle()

    def do_btn_5_2_on_off(self):
        if self.btn_5_2.text() == '??????????????':
            self.btn_5_2.setText('????????????????')
            piston_master['p5'] = 'off'
            # self.label_5_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_5_2.text() == '????????????????':
            self.btn_5_2.setText('??????????????')
            piston_master['p5'] = 'on'
            # self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p5'] == 'off' and self.piston_color['p5'] == 'y':
            self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p5'] = 'g'
        # self.serial.write('5'.encode('ascii'))
        # self.btn_5_2.toggle()

    def do_btn_1_2_color(self):
        if self.piston_color['p1'] == 'g':
            self.label_1_1.setStyleSheet("QLabel {background-color: yellow;}")
            self.piston_color['p1'] = 'y'
        elif self.piston_color['p1'] == 'y':
            self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p1'] = 'g'

    def do_btn_2_2_color(self):
        if self.piston_color['p2'] == 'g':
            self.label_2_1.setStyleSheet("QLabel {background-color: yellow;}")
            self.piston_color['p2'] = 'y'
        elif self.piston_color['p2'] == 'y':
            self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p2'] = 'g'

    def do_btn_3_2_color(self):
        if self.piston_color['p3'] == 'g':
            self.label_3_1.setStyleSheet("QLabel {background-color: yellow;}")
            self.piston_color['p3'] = 'y'
        elif self.piston_color['p3'] == 'y':
            self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p3'] = 'g'

    def do_btn_4_2_color(self):
        if self.piston_color['p4'] == 'g':
            self.label_4_1.setStyleSheet("QLabel {background-color: yellow;}")
            self.piston_color['p4'] = 'y'
        elif self.piston_color['p4'] == 'y':
            self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p4'] = 'g'

    def do_btn_5_2_color(self):
        if self.piston_color['p5'] == 'g':
            self.label_5_1.setStyleSheet("QLabel {background-color: yellow;}")
            self.piston_color['p5'] = 'y'
        elif self.piston_color['p5'] == 'y':
            self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p5'] = 'g'


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())
