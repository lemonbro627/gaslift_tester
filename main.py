import time
from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QCheckBox
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QSize
from PyQt5.QtGui import QImage, QPalette, QBrush
from PyQt5 import QtCore, QtGui
import queue
import serial
import sys
import os
import yaml
from datetime import datetime as dt
import traceback
import logging


def qt_message_handler(mode, context, message):
    if mode == QtCore.QtInfoMsg:
        mode = 'INFO'
    elif mode == QtCore.QtWarningMsg:
        mode = 'WARNING'
    elif mode == QtCore.QtCriticalMsg:
        mode = 'CRITICAL'
    elif mode == QtCore.QtFatalMsg:
        mode = 'FATAL'
    else:
        mode = 'DEBUG'
    with open(f'logs/crash_log-{dt.now().strftime("%Y-%m-%d_%H-%M-%S")}.txt','a') as f:
        print('qt_message_handler: line: %d, func: %s(), file: %s' % (context.line, context.function, context.file))
        f.write('qt_message_handler: line: %d, func: %s(), file: %s' % (context.line, context.function, context.file))
        print('  %s: %s\n' % (mode, message))
        f.write('  %s: %s\n' % (mode, message))


QtCore.qInstallMessageHandler(qt_message_handler)

logging.basicConfig(filename=f'logs/program_{dt.now().strftime("%Y-%m-%d_%H-%M-%S")}.txt', encoding='utf-8', level=logging.DEBUG)

default_config = """MIN_WEIGHT_1: 2,5
MIN_WEIGHT_2: 2,5
MIN_WEIGHT_3: 2,5
MIN_WEIGHT_4: 2,5
MIN_WEIGHT_5: 2,5
SERIAL_SPEED: 9600
SERIAL_PORT: COM3
SLEEP_AFTER_START: 3
SLEEP_AFTER_CHECK: 5
ENABLE_LOGS: TRUE"""

if not os.path.exists("./config.yaml"):
    with open("./config.yaml") as f:
        f.write(default_config)

with open("./config.yaml") as f:
    config = yaml.load(f, Loader=yaml.FullLoader)

if not os.path.exists('logs'):
    os.mkdir('logs')

global iflogs
iflogs = True if config['ENABLE_LOGS'] == '1' else False
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

global cycles
cycles = {
    'p1': 0,
    'p2': 0,
    'p3': 0,
    'p4': 0,
    'p5': 0
}

global state
state = {
    'p1': 0,
    'p2': 0,
    'p3': 0,
    'p4': 0,
    'p5': 0
}

global zero
zero = {
    'p1': 0.0,
    'p2': 0.0,
    'p3': 0.0,
    'p4': 0.0,
    'p5': 0.0
}


# global stime


def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)


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
        if iflogs:
            f = open(filename, 'a')
            f.write("date;p1 cycle;p1;p2 cycle;p2;p3 cycle;p3;p4 cycle;p4;p5 cycle;p5\n")
            f.close()
        while True:
            try:
                line = self.serial.readline()
                data = str(line)[2:-5].split(';')
                for i in range(0, len(data)):
                    tmp = float(int(float(data[i]) / 100) / 10)
                    data[i] = tmp
                print(data)
                q.put_nowait(data)
                if iflogs:
                    f = open(filename, 'a')
                    f.write(
                        f"{dt.now()};{data[0].replace('.', ',')};{data[1].replace('.', ',')};{data[2].replace('.', ',')};{data[3].replace('.', ',')};{data[4].replace('.', ',')}\n")
                    f.close()
            except Exception as e:
                logging.error(e)
                print(f'Error while parsing response from Arduino: {e}')

            try:
                self.scale_1.emit(str(float(data[0]) - float(zero['p1'])))
            except Exception as e:
                logging.error(e)
                self.scale_1.emit('0')
            try:
                self.scale_2.emit(str(float(data[1]) - float(zero['p2'])))
            except Exception as e:
                logging.error(e)
                self.scale_2.emit('0')
            try:
                self.scale_3.emit(str(float(data[2]) - float(zero['p3'])))
            except Exception as e:
                logging.error(e)
                self.scale_3.emit('0')
            try:
                self.scale_4.emit(str(float(data[3]) - float(zero['p4'])))
            except Exception as e:
                logging.error(e)
                self.scale_4.emit('0')
            try:
                self.scale_5.emit(str(float(data[4]) - float(zero['p5'])))
            except Exception as e:
                logging.error(e)
                self.scale_5.emit('0')


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

    p1c = pyqtSignal(str)
    p2c = pyqtSignal(str)
    p3c = pyqtSignal(str)
    p4c = pyqtSignal(str)
    p5c = pyqtSignal(str)

    def run(self):
        while self.running:
            with q.mutex:
                q.queue.clear()
            time.sleep(0.5)
            if not q.empty():
                data = q.get_nowait()
                zero['p1'] = float(data[0])
                zero['p2'] = float(data[1])
                zero['p3'] = float(data[2])
                zero['p4'] = float(data[3])
                zero['p5'] = float(data[4])
            if piston_master['p1'] == 'on':
                self.serial.write('1'.encode('ascii'))
                state['p1'] = 1
            if piston_master['p2'] == 'on':
                self.serial.write('2'.encode('ascii'))
                state['p2'] = 1
            if piston_master['p3'] == 'on':
                self.serial.write('3'.encode('ascii'))
                state['p3'] = 1
            if piston_master['p4'] == 'on':
                self.serial.write('4'.encode('ascii'))
                state['p4'] = 1
            if piston_master['p5'] == 'on':
                self.serial.write('5'.encode('ascii'))
                state['p5'] = 1
            if iflogs:
                f = open(filename, 'a')
                f.write(f"{dt.now()};SLEEP AFTER START\n")
                f.close()
            time.sleep(config['SLEEP_AFTER_START'])
            if iflogs:
                f = open(filename, 'a')
                f.write(f"{dt.now()};START MEASURING\n")
                f.close()
            if not q.empty():
                data = q.get_nowait()
                print(f'piston_master: {piston_master}')
                print(f'data: {data}')
                print(f'zero: {zero}')
                if iflogs:
                    f = open(filename, 'a')
                    f.write(f"{dt.now()};"
                            f"{str(cycles['p1'])};"
                            f"{str(float(data[0]) - float(zero['p1'])).replace('.', ',')};"
                            f"{str(cycles['p2'])};"
                            f"{str(float(data[1]) - float(zero['p2'])).replace('.', ',')};"
                            f"{str(cycles['p3'])};"
                            f"{str(float(data[2]) - float(zero['p3'])).replace('.', ',')};"
                            f"{str(cycles['p4'])};"
                            f"{str(float(data[3]) - float(zero['p4'])).replace('.', ',')};"
                            f"{str(cycles['p5'])};"
                            f"{str(float(data[4]) - float(zero['p5'])).replace('.', ',')}"
                            f"\n")
                    f.close()
                print(
                    f'min p1: {config["MIN_WEIGHT_1"]}, p2: {config["MIN_WEIGHT_2"]}, p3: {config["MIN_WEIGHT_3"]}, p4: {config["MIN_WEIGHT_4"]}, p5: {config["MIN_WEIGHT_5"]}')
                if piston_master['p1'] == 'on':
                    if float(data[0]) - float(zero['p1']) < float(config['MIN_WEIGHT_1']):
                        piston_master['p1'] = 'off'
                        self.p1.emit()
                elif piston_master['p1'] == 'off':
                    if float(data[0]) - float(zero['p1']) > float(config['MIN_WEIGHT_1']):
                        piston_master['p1'] = 'on'
                        self.p1.emit()

                if piston_master['p2'] == 'on':
                    if float(data[1]) - float(zero['p2']) < float(config['MIN_WEIGHT_2']):
                        piston_master['p2'] = 'off'
                        self.p2.emit()
                elif piston_master['p2'] == 'off':
                    if float(data[1]) - float(zero['p2']) > float(config['MIN_WEIGHT_2']):
                        piston_master['p2'] = 'on'
                        self.p2.emit()

                if piston_master['p3'] == 'on':
                    if float(data[2]) - float(zero['p3']) < float(config['MIN_WEIGHT_3']):
                        piston_master['p3'] = 'off'
                        self.p3.emit()
                elif piston_master['p3'] == 'off':
                    if float(data[2]) - float(zero['p3']) > float(config['MIN_WEIGHT_3']):
                        piston_master['p3'] = 'on'
                        self.p3.emit()

                if piston_master['p4'] == 'on':
                    if float(data[3]) - float(zero['p4']) < float(config['MIN_WEIGHT_4']):
                        piston_master['p4'] = 'off'
                        self.p4.emit()
                elif piston_master['p4'] == 'off':
                    if float(data[3]) - float(zero['p4']) > float(config['MIN_WEIGHT_4']):
                        piston_master['p4'] = 'on'
                        self.p4.emit()

                if piston_master['p5'] == 'on':
                    if float(data[4]) - float(zero['p5']) < float(config['MIN_WEIGHT_5']):
                        piston_master['p5'] = 'off'
                        self.p5.emit()
                elif piston_master['p5'] == 'off':
                    if float(data[4]) - float(zero['p5']) > float(config['MIN_WEIGHT_5']):
                        piston_master['p5'] = 'on'
                        self.p5.emit()

                if iflogs:
                    f = open(filename, 'a')
                    f.write(f"{dt.now()};STOP MEASURING\n")
                    f.close()

                if piston_master['p1'] == 'on':
                    self.serial.write('1'.encode('ascii'))
                    cycles['p1'] += 1
                    self.p1c.emit(str(cycles['p1']))
                    state['p1'] = 0
                if piston_master['p2'] == 'on':
                    self.serial.write('2'.encode('ascii'))
                    cycles['p2'] += 1
                    self.p2c.emit(str(cycles['p2']))
                    state['p2'] = 0
                if piston_master['p3'] == 'on':
                    self.serial.write('3'.encode('ascii'))
                    cycles['p3'] += 1
                    self.p3c.emit(str(cycles['p3']))
                    state['p3'] = 0
                if piston_master['p4'] == 'on':
                    self.serial.write('4'.encode('ascii'))
                    cycles['p4'] += 1
                    self.p4c.emit(str(cycles['p4']))
                    state['p4'] = 0
                if piston_master['p5'] == 'on':
                    self.serial.write('5'.encode('ascii'))
                    cycles['p5'] += 1
                    self.p5c.emit(str(cycles['p5']))
                    state['p5'] = 0
            if iflogs:
                f = open(filename, 'a')
                f.write(f"{dt.now()};START SLEEP AFTER CHECK\n")
                f.close()
            time.sleep(config['SLEEP_AFTER_CHECK'])


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
        self.serial = serial.Serial(config['SERIAL_PORT'], config['SERIAL_SPEED'])
        self.serial.setDTR(False)
        time.sleep(1)
        self.serial.flushInput()
        self.serial.setDTR(True)

        QtGui.QFontDatabase.addApplicationFont(resource_path('files/GOST_A.TTF'))

        self.myfont = self.font()
        self.myfont.setPointSize(19)
        self.myfont.setFamily('GOST type A')

        oImage = QImage(resource_path('files/back.jpg'))
        # sImage = oImage.scaled(QSize(1280,720))
        palette = QPalette()
        palette.setBrush(QPalette.Window, QBrush(oImage))
        self.setPalette(palette)

        self.start_stop_btn = QPushButton('START', self)
        self.label_1_1 = QLabel('Поршень 1', self)
        self.label_2_1 = QLabel('Поршень 2', self)
        self.label_3_1 = QLabel('Поршень 3', self)
        self.label_4_1 = QLabel('Поршень 4', self)
        self.label_5_1 = QLabel('Поршень 5', self)
        self.label_0_2 = QLabel('Статус', self)
        self.btn_1_2 = QCheckBox('Включен', self)
        self.btn_2_2 = QCheckBox('Включен', self)
        self.btn_3_2 = QCheckBox('Включен', self)
        self.btn_4_2 = QCheckBox('Включен', self)
        self.btn_5_2 = QCheckBox('Включен', self)
        self.label_0_3 = QLabel('Результат измерения', self)
        self.label_1_3 = QLabel('0,0', self)
        self.label_2_3 = QLabel('0,0', self)
        self.label_3_3 = QLabel('0,0', self)
        self.label_4_3 = QLabel('0,0', self)
        self.label_5_3 = QLabel('0,0', self)
        self.label_0_4 = QLabel('Кол-во пройденных циклов', self)
        self.label_1_4 = QLabel('0', self)
        self.label_2_4 = QLabel('0', self)
        self.label_3_4 = QLabel('0', self)
        self.label_4_4 = QLabel('0', self)
        self.label_5_4 = QLabel('0', self)
        self.label_0_5 = QLabel('Сбросить кол-во циклов', self)
        self.btn_1_5 = QPushButton('Сбросить', self)
        self.btn_2_5 = QPushButton('Сбросить', self)
        self.btn_3_5 = QPushButton('Сбросить', self)
        self.btn_4_5 = QPushButton('Сбросить', self)
        self.btn_5_5 = QPushButton('Сбросить', self)
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
        self.thread_check.p1c.connect(self.label_1_4.setText)
        self.thread_check.p2c.connect(self.label_2_4.setText)
        self.thread_check.p3c.connect(self.label_3_4.setText)
        self.thread_check.p4c.connect(self.label_4_4.setText)
        self.thread_check.p5c.connect(self.label_5_4.setText)

        self.initUI()

    def initUI(self):

        # btn.setToolTip('This is a <b>QPushButton</b> widget')
        self.start_stop_btn.resize(self.start_stop_btn.sizeHint())
        self.start_stop_btn.resize(200, 110)
        self.start_stop_btn.move(1040, 470)
        self.start_stop_btn.clicked.connect(self.do_start_stop)
        self.start_stop_btn.setFont(self.myfont)

        self.label_0_2.resize(250, 50)
        self.label_0_2.move(0, 150)
        self.label_0_2.setAlignment(Qt.AlignCenter)
        self.label_0_2.setStyleSheet("QLabel {border-style: solid;border-width: 1px;border-color: black;}")
        self.label_0_2.setFont(self.myfont)

        self.label_0_3.resize(250, 50)
        self.label_0_3.move(0, 250)
        self.label_0_3.setAlignment(Qt.AlignCenter)
        self.label_0_3.setStyleSheet("QLabel {border-style: solid;border-width: 1px;border-color: black;}")
        self.label_0_3.setFont(self.myfont)

        self.label_0_4.resize(250, 50)
        self.label_0_4.move(0, 300)
        self.label_0_4.setAlignment(Qt.AlignCenter)
        self.label_0_4.setStyleSheet("QLabel {border-style: solid;border-width: 1px;border-color: black;}")
        self.label_0_4.setFont(self.myfont)

        self.label_1_1.resize(150, 50)
        self.label_1_1.move(250, 100)
        self.label_1_1.setAlignment(Qt.AlignCenter)
        self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
        self.label_1_1.setFont(self.myfont)

        self.btn_1_2.resize(self.btn_1_2.sizeHint())
        self.btn_1_2.resize(150, 50)
        self.btn_1_2.move(300, 150)
        self.btn_1_2.clicked.connect(self.do_btn_1_2_on_off)
        self.btn_1_2.setFont(self.myfont)

        self.label_2_1.resize(150, 50)
        self.label_2_1.move(400, 100)
        self.label_2_1.setAlignment(Qt.AlignCenter)
        self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
        self.label_2_1.setFont(self.myfont)

        self.btn_2_2.resize(self.btn_2_2.sizeHint())
        self.btn_2_2.resize(150, 50)
        self.btn_2_2.move(450, 150)
        self.btn_2_2.clicked.connect(self.do_btn_2_2_on_off)
        self.btn_2_2.setFont(self.myfont)

        self.label_3_1.resize(150, 50)
        self.label_3_1.move(550, 100)
        self.label_3_1.setAlignment(Qt.AlignCenter)
        self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
        self.label_3_1.setFont(self.myfont)

        self.btn_3_2.resize(self.btn_3_2.sizeHint())
        self.btn_3_2.resize(150, 50)
        self.btn_3_2.move(600, 150)
        self.btn_3_2.clicked.connect(self.do_btn_3_2_on_off)
        self.btn_3_2.setFont(self.myfont)

        self.label_4_1.resize(150, 50)
        self.label_4_1.move(700, 100)
        self.label_4_1.setAlignment(Qt.AlignCenter)
        self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
        self.label_4_1.setFont(self.myfont)

        self.btn_4_2.resize(self.btn_4_2.sizeHint())
        self.btn_4_2.resize(150, 50)
        self.btn_4_2.move(750, 150)
        self.btn_4_2.clicked.connect(self.do_btn_4_2_on_off)
        self.btn_4_2.setFont(self.myfont)

        self.label_5_1.resize(150, 50)
        self.label_5_1.move(850, 100)
        self.label_5_1.setAlignment(Qt.AlignCenter)
        self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
        self.label_5_1.setFont(self.myfont)

        self.btn_5_2.resize(self.btn_5_2.sizeHint())
        self.btn_5_2.resize(150, 50)
        self.btn_5_2.move(900, 150)
        self.btn_5_2.clicked.connect(self.do_btn_5_2_on_off)
        self.btn_5_2.setFont(self.myfont)

        self.label_1_3.resize(150, 50)
        self.label_1_3.move(250, 250)
        self.label_1_3.setAlignment(Qt.AlignCenter)
        self.label_1_3.setFont(self.myfont)

        self.label_2_3.resize(150, 50)
        self.label_2_3.move(400, 250)
        self.label_2_3.setAlignment(Qt.AlignCenter)
        self.label_2_3.setFont(self.myfont)

        self.label_3_3.resize(150, 50)
        self.label_3_3.move(550, 250)
        self.label_3_3.setAlignment(Qt.AlignCenter)
        self.label_3_3.setFont(self.myfont)

        self.label_4_3.resize(150, 50)
        self.label_4_3.move(700, 250)
        self.label_4_3.setAlignment(Qt.AlignCenter)
        self.label_4_3.setFont(self.myfont)

        self.label_5_3.resize(150, 50)
        self.label_5_3.move(850, 250)
        self.label_5_3.setAlignment(Qt.AlignCenter)
        self.label_5_3.setFont(self.myfont)

        self.label_1_4.resize(150, 50)
        self.label_1_4.move(250, 300)
        self.label_1_4.setAlignment(Qt.AlignCenter)
        self.label_1_4.setFont(self.myfont)

        self.label_2_4.resize(150, 50)
        self.label_2_4.move(400, 300)
        self.label_2_4.setAlignment(Qt.AlignCenter)
        self.label_2_4.setFont(self.myfont)

        self.label_3_4.resize(150, 50)
        self.label_3_4.move(550, 300)
        self.label_3_4.setAlignment(Qt.AlignCenter)
        self.label_3_4.setFont(self.myfont)

        self.label_4_4.resize(150, 50)
        self.label_4_4.move(700, 300)
        self.label_4_4.setAlignment(Qt.AlignCenter)
        self.label_4_4.setFont(self.myfont)

        self.label_5_4.resize(150, 50)
        self.label_5_4.move(850, 300)
        self.label_5_4.setAlignment(Qt.AlignCenter)
        self.label_5_4.setFont(self.myfont)

        self.label_0_5.resize(250, 50)
        self.label_0_5.move(0, 350)
        self.label_0_5.setAlignment(Qt.AlignCenter)
        self.label_0_5.setStyleSheet("QLabel {border-style: solid;border-width: 1px;border-color: black;}")
        self.label_0_5.setFont(self.myfont)

        self.btn_1_5.resize(self.btn_1_5.sizeHint())
        self.btn_1_5.resize(150, 50)
        self.btn_1_5.move(250, 350)
        self.btn_1_5.clicked.connect(self.do_btn_1_5_reset)
        self.btn_1_5.setFont(self.myfont)

        self.btn_2_5.resize(self.btn_2_5.sizeHint())
        self.btn_2_5.resize(150, 50)
        self.btn_2_5.move(400, 350)
        self.btn_2_5.clicked.connect(self.do_btn_2_5_reset)
        self.btn_2_5.setFont(self.myfont)

        self.btn_3_5.resize(self.btn_3_5.sizeHint())
        self.btn_3_5.resize(150, 50)
        self.btn_3_5.move(550, 350)
        self.btn_3_5.clicked.connect(self.do_btn_3_5_reset)
        self.btn_3_5.setFont(self.myfont)

        self.btn_4_5.resize(self.btn_4_5.sizeHint())
        self.btn_4_5.resize(150, 50)
        self.btn_4_5.move(700, 350)
        self.btn_4_5.clicked.connect(self.do_btn_4_5_reset)
        self.btn_4_5.setFont(self.myfont)

        self.btn_5_5.resize(self.btn_1_5.sizeHint())
        self.btn_5_5.resize(150, 50)
        self.btn_5_5.move(850, 350)
        self.btn_5_5.clicked.connect(self.do_btn_5_5_reset)
        self.btn_5_5.setFont(self.myfont)

        self.setGeometry(0, 0, 1879, 634)
        self.setFixedWidth(1879)
        self.setFixedHeight(634)
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
            if iflogs:
                f = open(filename, 'a')
                f.write(f"{dt.now()};START BUTTON PUSHED\n")
                f.close()
        elif self.start_stop_btn.text() == 'STOP':
            self.start_stop_btn.setText('START')
            self.thread_check.running = False
            self.thread_check.quit()
            if iflogs:
                f = open(filename, 'a')
                f.write(f"{dt.now()};STOP BUTTON PUSHED\n")
                f.close()
            if piston_master['p1'] == 'on' and state['p1'] == 1:
                self.serial.write('1'.encode('ascii'))
            if piston_master['p2'] == 'on' and state['p2'] == 1:
                self.serial.write('2'.encode('ascii'))
            if piston_master['p3'] == 'on' and state['p3'] == 1:
                self.serial.write('3'.encode('ascii'))
            if piston_master['p4'] == 'on' and state['p4'] == 1:
                self.serial.write('4'.encode('ascii'))
            if piston_master['p5'] == 'on' and state['p5'] == 1:
                self.serial.write('5'.encode('ascii'))

    def do_btn_1_2_on_off(self):
        if self.btn_1_2.text() == 'Включен':
            self.btn_1_2.setText('Выключен')
            piston_master['p1'] = 'off'
            if state['p1'] == 1:
                self.serial.write('1'.encode('ascii'))
                state['p1'] = 0
            # self.label_1_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_1_2.text() == 'Выключен':
            self.btn_1_2.setText('Включен')
            piston_master['p1'] = 'on'
            if state['p1'] == 0:
                self.serial.write('1'.encode('ascii'))
                state['p1'] = 1
            # self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p1'] == 'off' and self.piston_color['p1'] == 'y':
            self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p1'] = 'g'
        # self.btn_1_2.toggle()

    def do_btn_2_2_on_off(self):
        if self.btn_2_2.text() == 'Включен':
            self.btn_2_2.setText('Выключен')
            piston_master['p2'] = 'off'
            if state['p2'] == 1:
                self.serial.write('2'.encode('ascii'))
                state['p2'] = 0
            # self.label_2_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_2_2.text() == 'Выключен':
            self.btn_2_2.setText('Включен')
            piston_master['p2'] = 'on'
            if state['p2'] == 0:
                self.serial.write('2'.encode('ascii'))
                state['p2'] = 1
            # self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p2'] == 'off' and self.piston_color['p2'] == 'y':
            self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p2'] = 'g'
        # self.btn_2_2.toggle()

    def do_btn_3_2_on_off(self):
        if self.btn_3_2.text() == 'Включен':
            self.btn_3_2.setText('Выключен')
            piston_master['p3'] = 'off'
            if state['p3'] == 1:
                self.serial.write('3'.encode('ascii'))
                state['p3'] = 0
            # self.label_3_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_3_2.text() == 'Выключен':
            self.btn_3_2.setText('Включен')
            piston_master['p3'] = 'on'
            if state['p3'] == 0:
                self.serial.write('3'.encode('ascii'))
                state['p3'] = 1
            # self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p3'] == 'off' and self.piston_color['p3'] == 'y':
            self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p3'] = 'g'
        # self.btn_3_2.toggle()

    def do_btn_4_2_on_off(self):
        if self.btn_4_2.text() == 'Включен':
            self.btn_4_2.setText('Выключен')
            piston_master['p4'] = 'off'
            if state['p4'] == 1:
                self.serial.write('4'.encode('ascii'))
                state['p4'] = 0
            # self.label_4_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_4_2.text() == 'Выключен':
            self.btn_4_2.setText('Включен')
            piston_master['p4'] = 'on'
            if state['p4'] == 0:
                self.serial.write('4'.encode('ascii'))
                state['p4'] = 1
            # self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p4'] == 'off' and self.piston_color['p4'] == 'y':
            self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p4'] = 'g'
        # self.btn_4_2.toggle()

    def do_btn_5_2_on_off(self):
        if self.btn_5_2.text() == 'Включен':
            self.btn_5_2.setText('Выключен')
            piston_master['p5'] = 'off'
            if state['p5'] == 1:
                self.serial.write('5'.encode('ascii'))
                state['p5'] = 0
            # self.label_5_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.btn_5_2.text() == 'Выключен':
            self.btn_5_2.setText('Включен')
            piston_master['p5'] = 'on'
            if state['p5'] == 0:
                self.serial.write('5'.encode('ascii'))
                state['p5'] = 1
            # self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
        if piston_master['p5'] == 'off' and self.piston_color['p5'] == 'y':
            self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
            self.piston_color['p5'] = 'g'
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

    def do_btn_1_5_reset(self):
        cycles['p1'] = 0
        self.label_1_4.setText('0')

    def do_btn_2_5_reset(self):
        cycles['p2'] = 0
        self.label_2_4.setText('0')

    def do_btn_3_5_reset(self):
        cycles['p3'] = 0
        self.label_3_4.setText('0')

    def do_btn_4_5_reset(self):
        cycles['p4'] = 0
        self.label_4_4.setText('0')

    def do_btn_5_5_reset(self):
        cycles['p5'] = 0
        self.label_5_4.setText('0')

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())
