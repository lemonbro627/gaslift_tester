import time

from PyQt5.QtWidgets import QWidget, QPushButton, QApplication, QLabel, QCheckBox
from PyQt5.QtGui import QPainter, QPen, QColor
from PyQt5.QtCore import Qt, QObject, QThread, pyqtSignal
from PyQt5 import QtCore
import queue
import serial
import sys
from os import path, mkdir
import config
from datetime import datetime as dt

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
        filename = f'test_{dt.now().strftime("%Y-%m-%d_%H-%M-%S")}.csv'
        with open(filename, 'a') as f:
            f.write("date;p1;p2;p3;p4;p5")
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
    def __init__(self):
        QtCore.QThread.__init__(self)

    running = False
    def run(self):
        with q.mutex:
            q.queue.clear()
        time.sleep(config.SLEEP_AFTER_START)
        if not q.empty():
            data = q.get_nowait()
            print(data)
            print(config.MIN_WEIGHT)
            print(float(data[0]))
            print(float(data[0]) < float(config.MIN_WEIGHT))
            print('123')
            self.do_btn_1_2_on_off()


class Main(QWidget):
    piston_state = {
        'p1': 'off',
        'p2': 'off',
        'p3': 'off',
        'p4': 'off',
        'p5': 'off'
    }
    piston_hand = {
        'p1': 'off',
        'p2': 'off',
        'p3': 'off',
        'p4': 'off',
        'p5': 'off'
    }

    def __init__(self):
        super().__init__()
        self.serial = serial.Serial(config.SERIAL_PORT, config.SERIAL_SPEED)
        print(self.serial)


        self.start_stop_btn = QPushButton('START', self)
        self.label_1_1 = QLabel('Поршень 1', self)
        self.label_2_1 = QLabel('Поршень 2', self)
        self.label_3_1 = QLabel('Поршень 3', self)
        self.label_4_1 = QLabel('Поршень 4', self)
        self.label_5_1 = QLabel('Поршень 5', self)
        self.label_0_2 = QLabel('Включен?', self)
        self.btn_1_2 = QCheckBox('Выключен', self)
        self.btn_2_2 = QCheckBox('Выключен', self)
        self.btn_3_2 = QCheckBox('Выключен', self)
        self.btn_4_2 = QCheckBox('Выключен', self)
        self.btn_5_2 = QCheckBox('Выключен', self)
        self.label_0_3 = QLabel('Давление', self)
        self.label_1_3 = QLabel('0.00', self)
        self.label_2_3 = QLabel('0.00', self)
        self.label_3_3 = QLabel('0.00', self)
        self.label_4_3 = QLabel('0.00', self)
        self.label_5_3 = QLabel('0.00', self)
        self.thread_get = GetData(self.serial)
        self.thread_check = CheckData()
        self.thread_get.scale_1.connect(self.label_1_3.setText)
        self.thread_get.scale_2.connect(self.label_2_3.setText)
        self.thread_get.scale_3.connect(self.label_3_3.setText)
        self.thread_get.scale_4.connect(self.label_4_3.setText)
        self.thread_get.scale_5.connect(self.label_5_3.setText)

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
        self.label_1_1.setStyleSheet("QLabel {background-color: yellow;}")

        self.btn_1_2.resize(self.btn_1_2.sizeHint())
        self.btn_1_2.resize(150, 50)
        self.btn_1_2.move(200, 150)
        self.btn_1_2.clicked.connect(self.do_btn_1_2_on_off)

        self.label_2_1.resize(150, 50)
        self.label_2_1.move(300, 100)
        self.label_2_1.setAlignment(Qt.AlignCenter)
        self.label_2_1.setStyleSheet("QLabel {background-color: yellow;}")

        self.btn_2_2.resize(self.btn_2_2.sizeHint())
        self.btn_2_2.resize(150, 50)
        self.btn_2_2.move(350, 150)
        self.btn_2_2.clicked.connect(self.do_btn_2_2_on_off)

        self.label_3_1.resize(150, 50)
        self.label_3_1.move(450, 100)
        self.label_3_1.setAlignment(Qt.AlignCenter)
        self.label_3_1.setStyleSheet("QLabel {background-color: yellow;}")

        self.btn_3_2.resize(self.btn_3_2.sizeHint())
        self.btn_3_2.resize(150, 50)
        self.btn_3_2.move(500, 150)
        self.btn_3_2.clicked.connect(self.do_btn_3_2_on_off)

        self.label_4_1.resize(150, 50)
        self.label_4_1.move(600, 100)
        self.label_4_1.setAlignment(Qt.AlignCenter)
        self.label_4_1.setStyleSheet("QLabel {background-color: yellow;}")

        self.btn_4_2.resize(self.btn_4_2.sizeHint())
        self.btn_4_2.resize(150, 50)
        self.btn_4_2.move(650, 150)
        self.btn_4_2.clicked.connect(self.do_btn_4_2_on_off)

        self.label_5_1.resize(150, 50)
        self.label_5_1.move(750, 100)
        self.label_5_1.setAlignment(Qt.AlignCenter)
        self.label_5_1.setStyleSheet("QLabel {background-color: yellow;}")

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
        self.thread_get.start()

    def do_start_stop(self):
        print('Start_stop button clicked')
        if self.start_stop_btn.text() == 'START':
            self.start_stop_btn.setText('STOP')
            self.thread_check.start()
        elif self.start_stop_btn.text() == 'STOP':
            self.start_stop_btn.setText('START')
            self.thread_check.quit()
        self.do_btn_1_2_on_off()
        self.btn_1_2.toggle()
        self.do_btn_2_2_on_off()
        self.btn_2_2.toggle()
        self.do_btn_3_2_on_off()
        self.btn_3_2.toggle()
        self.do_btn_4_2_on_off()
        self.btn_4_2.toggle()
        self.do_btn_5_2_on_off()
        self.btn_5_2.toggle()

    def do_btn_1_2_on_off(self):
        if self.piston_state['p1'] == 'on':
            self.btn_1_2.setText('Выключен')
            self.piston_state['p1'] = 'off'
            self.label_1_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.piston_state['p1'] == 'off':
            self.btn_1_2.setText('Включен')
            self.piston_state['p1'] = 'on'
            self.label_1_1.setStyleSheet("QLabel {background-color: green;}")
        self.serial.write('1'.encode('ascii'))

    def do_btn_2_2_on_off(self):
        if self.piston_state['p2'] == 'on':
            self.btn_2_2.setText('Выключен')
            self.piston_state['p2'] = 'off'
            self.label_2_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.piston_state['p2'] == 'off':
            self.btn_2_2.setText('Включен')
            self.piston_state['p2'] = 'on'
            self.label_2_1.setStyleSheet("QLabel {background-color: green;}")
        self.serial.write('2'.encode('ascii'))

    def do_btn_3_2_on_off(self):
        if self.piston_state['p3'] == 'on':
            self.btn_3_2.setText('Выключен')
            self.piston_state['p3'] = 'off'
            self.label_3_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.piston_state['p3'] == 'off':
            self.btn_3_2.setText('Включен')
            self.piston_state['p3'] = 'on'
            self.label_3_1.setStyleSheet("QLabel {background-color: green;}")
        self.serial.write('3'.encode('ascii'))

    def do_btn_4_2_on_off(self):
        if self.piston_state['p4'] == 'on':
            self.btn_4_2.setText('Выключен')
            self.piston_state['p4'] = 'off'
            self.label_4_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.piston_state['p4'] == 'off':
            self.btn_4_2.setText('Включен')
            self.piston_state['p4'] = 'on'
            self.label_4_1.setStyleSheet("QLabel {background-color: green;}")
        self.serial.write('4'.encode('ascii'))

    def do_btn_5_2_on_off(self):
        if self.piston_state['p5'] == 'on':
            self.btn_5_2.setText('Выключен')
            self.piston_state['p5'] = 'off'
            self.label_5_1.setStyleSheet("QLabel {background-color: yellow;}")
        elif self.piston_state['p5'] == 'off':
            self.btn_5_2.setText('Включен')
            self.piston_state['p5'] = 'on'
            self.label_5_1.setStyleSheet("QLabel {background-color: green;}")
        self.serial.write('5'.encode('ascii'))


if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = Main()
    sys.exit(app.exec_())
