#필요한 라이브러리 호출
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QComboBox, QCheckBox, QTextEdit, QPushButton, QDialog, \
    QVBoxLayout, QGridLayout, QHBoxLayout, QGraphicsOpacityEffect
from PyQt5.QtGui import QPixmap, QFont, QFontDatabase, QColor, QIcon
from PyQt5.QtMultimedia import *
from PyQt5.QtMultimediaWidgets import *
import sys
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread, QUrl
import google_speech
import numpy as np
import papago
import time
import mediapipe as mp
import cv2
import csv
import pandas as pd
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.sequence import pad_sequences
import Text_To_Speech
import tensorflow as tf
from tensorflow import keras
from tensorflow.keras import layers
import video_merge_cv


def delta(list1, list2):
    sum = 0
    if len(list1) != 0 and len(list2) != 0:
        for i in range(len(list2)):
            if list1[i] >= 0 and list1[i] <= 1 and list2[i] >= 0 and list2[i] <= 1:
                sum += (list2[i] - list1[i]) ** 2
    return sum

def Vector(point1, point2):
    return point2 - point1


def make_VectorList(landmarkLD, ConnectionList):
    VectorList = []
    for i in ConnectionList:
        VectorList.append(Vector(landmarkLD[i[0]], landmarkLD[i[1]]))
    return VectorList

# Opencv 카메라 열기
class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)

    def __init__(self, video):
        super().__init__()
        self._run_flag = True
        self.file = video  # 어떤 영상 들고올건지(입력 -> 0번, 출력 -> 저장된 영상)

    def run(self):
        for i in range(len(self.file)):
            while self._run_flag:
                ret, cv_img = self.file[i].read()
                cv2.waitKey(1)
                if ret:
                    self.change_pixmap_signal.emit(cv_img)  # Cv 이미지 -> Pyqt에 표현
                else:
                    break
        # shut down capture system
        '''self.cap.release()'''

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False

        self.wait()


# 시작 로고창
class Logo(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("수어 번역기")  # 창 이름
        self.setFixedSize(400, 251)  # 창 크기
        self.setWindowFlag(Qt.FramelessWindowHint)  # 테두리 X
        self.UI()

    def UI(self):
        self.image = QPixmap()  # 사진
        self.image.load("Images/Logo.png")  # 불러오기
        self.label = QLabel("", self)
        self.label.setPixmap(self.image)  # 사진 담기
        self.label.setGeometry(0, 0, 400, 251)  # 크기 조절
        self.setWindowOpacity(0)  # 화면 불투명도 0
        self.show()
        # 0.01초마다 불투명도 1씩 증가
        for i in range(100):
            i = i / 100
            self.setWindowOpacity(i)
            time.sleep(0.01)
        self.setWindowOpacity(1)
        time.sleep(0.3)
        self.hide()  # 창 숨기기


class App(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowIcon(QIcon("Images/Logo_square.png"))  # 윈도우 로고 설정
        self.setWindowTitle("수어 번역기")  # 화면 이름
        self.setFixedSize(1440, 810)  # 화면 크기
        self.display_width = 640  # 영상 가로
        self.display_height = 360  # 영상 세로
        self.A_point = 0  # 자동 인식용 카운트
        self.B_thread = None  # 입력 영상 쓰레드
        self.A_thread = None  # 출력 영상 쓰레드
        self.B_lang = "ko"  # 번역 전 언어
        self.A_lang = "ko"  # 번역 후 언어
        self.B_signal = "T"  # 번역 전 입력 방식(수어/텍스트)
        self.A_signal = "T"  # 번역 후 출력 방식(수어/텍스트)
        self.text = " "  # 주고받고 하는 텍스트
        self.S_lang = "ko-KR"  # 음성 인식 언어
        self.mode = "Manual"  # 인식 모드(자동/수동)
        self.fontsize = 1
        self.thickness = 8
        self.t = 0  # 추가 번역 실행 버튼
        self.B = 0
        self.SL = "KSL"
        self.word = ""
        self.video = ''
        self.result_list = []
        self.cap = None  # 카메라
        # 비디오 이름 리스트 - 한국어
        self.ko_videos = ["딸", "잃어버리다", "안내소", "어디", "도와주세요", "배", "아프다", "화장실"]
        self.ko_word = []
        # 비디오 이름 리스트 - 영어
        self.en_videos = ["daughter", "lost", "information_desk", "where", "help", "stomach", "sick", "toilet"]
        self.en_word = []
        self.initUI()

    def initUI(self):
        self.hbox = QHBoxLayout()  # 가로 레이아웃
        self.vbox = QVBoxLayout()  # 세로 레이아웃
        # 번역 전 입력 방식
        B_Check = QCheckBox("수어", self)
        B_Check.move(40, 120)
        B_Check.stateChanged.connect(self.B_Check_S)  # 체크박스 변화 시 함수 실행

        # 번역 전 언어
        B_Combobox = QComboBox(self)
        B_Combobox.addItem('한국어')  # 리스트에 '한국어' 추가
        B_Combobox.addItem('영어')  # 리스트에 '영어' 추가
        B_Combobox.setGeometry(180, 120, 360, 30)
        B_Combobox.setStyleSheet("background-color : white;" "border : 2px solid black;")  # 스타일
        B_Combobox.activated[str].connect(self.B_combobox)  # 콤보박스 변화 시 함수 실행

        # 번역 버튼
        self.B_button = QPushButton("", self)
        self.B_button.setGeometry(0, 660, 720, 150)
        self.B_button.setStyleSheet("background-color : skyblue;" "border:2px solid skyblue;"
                                    "background-image: url(Images/Translate_120.png);")  # 스타일
        self.B_button.raise_()  # 맨 위로
        self.B_button.clicked.connect(self.B_clicked)  # 누르면 실행 -> self.B_clicked
        self.B_button.setCursor(Qt.PointingHandCursor)  # 위에 커서 갖다놓으면 커서 모양 변경

        # 번역 전 텍스트 에딧창
        self.B_te = QTextEdit()
        self.B_te.setMaximumSize(638, 360)  # 최대 크기
        self.B_te.setMinimumSize(638, 360)  # 최소 크기
        self.B_te.setStyleSheet("border : 0px solid black;")  # 스타일
        self.B_te.setPlaceholderText("내용을 입력하세요")  # 미리 보기 텍스트
        font = QFont("Arial")  # 폰트 -> Arial
        font.setPointSize(15)  # 폰트 사이즈
        self.B_te.setFont(font)  # 폰트 설정
        self.B_te.textChanged.connect(self.B_textchange)  # 텍스트 변화 시 함수 실행

        # 음성 인식
        self.S_image = QPixmap()
        self.S_image.load("Images/mic_gray.png")  # 마이크 모양 사진
        self.S_button = QPushButton("", self)
        self.S_button.clicked.connect(self.S_clicked)  # 누르면 함수 실행
        self.S_button.setGeometry(10, 570, 60, 60)
        self.S_button.setCheckable(True)
        self.S_button.setIcon(QIcon(self.S_image))  # 버튼 아이콘
        # self.S_button.setStyleSheet("border : 0px solid black;" "background-image:url(mic_gray.png);")
        self.S_button.setCursor(Qt.PointingHandCursor)  # 위에 갖다놓으면 커서 모양 변화
        self.S_button.raise_()  # 맨 위로

        # 디자인
        B_label = QLabel("\n입력", self)
        B_label.setAlignment(Qt.AlignHCenter)
        B_label.setGeometry(0, 0, 720, 810)
        B_label.setStyleSheet("border : 1px solid black;" "background-color : white;")
        B_up = QLabel("", self)
        B_up.setGeometry(0, 0, 720, 180)
        B_up.setStyleSheet("border : 1px solid black;" "background-color : white;")
        B_up.lower()
        B_label.lower()

        # 국기
        self.B_nation = QLabel("", self)
        self.B_nation.setGeometry(315, 30, 90, 60)
        self.B_nation.setStyleSheet("border : 1px solid black;" "background-image : url(Images/Korea.png);")

        #검토용
        self.exam = QLabel("",self)
        self.exam.setGeometry(200,750,500,40)
        self.exam.setStyleSheet("background-color : transparent;" "border : 0px solid black;")

        # 번역 후 입력 방식
        A_Check = QCheckBox("수어", self)
        A_Check.move(760, 120)
        A_Check.stateChanged.connect(self.A_Check_S)  # 체크박스 상태 변화 시 함수 실행

        # 번역 후 언어
        A_Combobox = QComboBox(self)
        A_Combobox.addItem('한국어')  # 콤보박스에 '한국어' 추가
        A_Combobox.addItem('영어')  # 콤보박스에 '영어' 추가
        A_Combobox.setGeometry(900, 120, 360, 30)
        A_Combobox.setStyleSheet("background-color : white;" "border : 2px solid black")  # 스타일
        A_Combobox.activated[str].connect(self.A_combobox)  # 박스 상태 변화 시 함수 실행

        # 번역 후 텍스트창
        self.A_text = QLabel("", self)
        self.A_text.setMaximumSize(638, 360)  # 최대 크기
        self.A_text.setMinimumSize(638, 360)  # 최소 크기
        self.A_text.setWordWrap(True)  # 자동 줄 바꾸기
        self.A_text.setFont(font)  # 폰트
        self.A_text.setAlignment(Qt.AlignTop)  # 텍스트 정렬
        self.A_text.setAlignment(Qt.AlignLeft)  # 텍스트 정렬
        self.A_text.setStyleSheet("border : 0px solid black")  # 스타일

        # 디자인
        A_label = QLabel("\n출력", self)
        A_label.setAlignment(Qt.AlignHCenter)
        A_label.setGeometry(720, 0, 720, 810)
        A_label.setStyleSheet("border : 1px solid black;" "background-color : white;")
        A_up = QLabel("", self)
        A_up.setGeometry(720, 0, 720, 180)
        A_up.setStyleSheet("border : 1px solid black;" "background-color : white;")
        A_up.lower()
        A_label.lower()

        # 국기
        self.A_nation = QLabel("", self)
        self.A_nation.setGeometry(1035, 30, 90, 60)
        self.A_nation.setStyleSheet("border : 1px solid black;" "background-image : url(Images/Korea.png);")  # 스타일

        # 재생 버튼
        self.A_button = QPushButton("", self)
        self.A_button.setGeometry(720, 660, 720, 150)
        self.A_button.setStyleSheet("background-color : #F6B99D;" "border : 1px solid #F6B99D;"
                                    "background-image : url(Images/sound_120.png);")  # 스타일
        self.A_button.raise_()  # 맨 위로
        self.A_button.clicked.connect(self.A_clicked)  # 누르면 함수 실행
        self.A_button.setCursor(Qt.PointingHandCursor)  # 위에서 커서 모양 변화

        # 레이아웃 구성
        self.hbox.addStretch(1)
        self.hbox.addWidget(self.B_te, 16)
        self.hbox.addStretch(2)
        self.hbox.addWidget(self.A_text, 16)
        self.hbox.addStretch(1)
        self.vbox.addStretch(4)
        self.vbox.addLayout(self.hbox, 4)
        self.vbox.addStretch(4)
        self.setLayout(self.vbox)
        self.S_button.raise_()




    def S_clicked(self):
        self.text = google_speech.recognize_speech_from_mic(self.B_lang)
        self.B_te.setStyleSheet("color : black;" "border : 0px solid black")
        self.B_te.setPlainText(self.text)  # 적힌 텍스트 -> self.text



    # 창 닫을때
    def B_closeEvent(self, event):
        self.B_thread.stop()
        event.accept()

    def A_closeEvent(self, event):
        self.A_thread.stop()
        event.accept()

    def closeEvent(self, event):
        cv2.destroyAllWindows()
        if self.cap != None:
            self.cap.release()
            self.cap = None

    @pyqtSlot(np.ndarray)
    # Opencv 이미지를 레이블에 입력
    def B_update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.B_image_label.setPixmap(qt_img)

    def A_update_image(self, cv_img):
        """Updates the image_label with a new opencv image"""
        qt_img = self.convert_cv_qt(cv_img)
        self.A_image_label.setPixmap(qt_img)

    def convert_cv_qt(self, cv_img):
        """Convert from an opencv image to QPixmap"""
        rgb_image = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        convert_to_Qt_format = QtGui.QImage(rgb_image.data, w, h, bytes_per_line, QtGui.QImage.Format_RGB888)
        p = convert_to_Qt_format.scaled(self.display_width, self.display_height, Qt.KeepAspectRatio)
        return QPixmap.fromImage(p)

    def B_textchange(self):
        self.B_te.setFontPointSize(18)
        self.B_te.setTextColor(QColor(0, 0, 0))
        self.source = self.B_te.toPlainText()
        self.text = self.source


    def B_combobox(self, text):
        if text == '한국어' and self.B_lang == 'en':
            self.B_lang = 'ko'
            self.S_lang = 'ko-KR'
            self.SL = "KSL"
            self.B_nation.setStyleSheet("border : 1px solid black;" "background-image : url(Images/Korea.png);")
        if text == '영어' and self.B_lang == 'ko':
            self.B_lang = 'en'
            self.S_lang = "en-US"
            self.SL = "ASL"
            self.B_nation.setStyleSheet("border : 1px solid black;" "background-image : url(Images/America.png);")

    def A_combobox(self, text):
        if self.A_thread != None:
            self.A_thread.stop()
            self.A_thread = None
        if text == '한국어' and self.A_lang == "en":
            self.A_lang = 'ko'
            self.A_nation.setStyleSheet("border : 1px solid black;" "background-image : url(Images/Korea.png);")
            if self.text != "":
                if self.A_signal == "T":
                    if self.B_lang == self.A_lang:
                        self.text = self.source
                        self.A_text.setText(self.text)
                        pass
                    else:
                        self.text = papago.get_translate(self.text, 'en', 'ko')
                        self.A_text.setText(self.text)
                elif self.A_signal == "S":
                    self.result_list=[]
                    if self.en_word != [] and self.ko_word != []:
                        self.word = self.en_word
                    else:
                        self.word = self.source
                        self.word = self.word.split(" ")
                        self.result_list = self.word

                    for i in range(len(self.word)):
                        if self.word[i] in self.en_videos:
                            num = self.en_videos.index(self.word[i])
                            self.result_list.append(self.ko_videos[num])
                    print(self.result_list)
                    self.ko_word = self.result_list
                    self.video = video_merge_cv.video_play(self.result_list)
                    self.A_thread = VideoThread(self.video)
                    # connect its signal to the update_image slot
                    self.A_thread.change_pixmap_signal.connect(self.A_update_image)
                    # start the thread
                    self.A_thread.start()

        elif text == '영어' and self.A_lang == "ko":
            self.A_lang = 'en'
            self.A_nation.setStyleSheet("border : 1px solid black;" "background-image : url(Images/America.png);")
            if self.A_signal == "T":
                if self.text != "":
                    if self.B_lang == self.A_lang:
                        self.text = self.source
                        self.A_text.setText(self.text)
                        pass
                    else:
                        self.text = papago.get_translate(self.text, 'ko', 'en')
                        self.A_text.setText(self.text)

            elif self.A_signal == "S":
                if self.ko_word != []:
                    self.word = self.ko_word
                else:
                    self.word = self.source
                    self.word = self.word.split(" ")

                self.result_list = []
                for i in range(len(self.word)):
                    if self.word[i] in self.ko_videos:
                        print('s')
                        print(self.word[i])
                        print(self.ko_videos)
                        num = self.ko_videos.index(self.word[i])
                        print(num)
                        self.result_list.append(self.en_videos[num])
                print(self.result_list)
                self.en_word = self.result_list
                self.video = video_merge_cv.video_play(self.result_list)
                self.A_thread = VideoThread(self.video)
                # connect its signal to the update_image slot
                self.A_thread.change_pixmap_signal.connect(self.A_update_image)
                # start the thread
                self.A_thread.start()
    def B_Check_S(self, B_state):
        self.B += 1
        if B_state == Qt.Checked:
            self.exam.show()
            self.B_signal = "S"
            self.S_button.hide()
            self.B_te.setText("")
            self.A_text.setText("")
            self.B_image_label = QLabel(self)  # 카메라 이미지 담을 레이블 생성
            self.B_image_label.setMaximumSize(self.display_width, self.display_height)
            self.hbox.replaceWidget(self.B_te, self.B_image_label)
            self.B_te.hide()
            # create the video capture thread
            while self.B_signal == "S":
                print("Start")
                self.data = self.SL_Translation()
                '''self.cap.release()
                self.B_image_label.clear()'''
                if self.data != [] or self.data == "":
                    self.word = predict_classes(self.SL, self.data)
                    if self.B_lang != self.A_lang:
                        if self.B_lang == "ko":
                            self.result_list = []
                            for i in range(len(self.word)):
                                if self.word[i] in self.ko_videos:
                                    num = self.ko_videos.index(self.word[i])
                                    self.result_list.append(self.en_videos[num])
                        elif self.B_lang == "en":
                            self.result_list = []
                            for i in range(len(self.word)):
                                if self.word[i] in self.en_videos:
                                    num = self.en_videos.index(self.word[i])
                                    self.result_list.append(self.ko_videos[num])
                    else:
                        self.result_list = self.word
                    if self.B_lang == 'ko':
                        self.ko_word = self.word
                    elif self.B_lang == 'en':
                        self.en_word = self.word

                    self.text = ""
                    for i in self.word:
                        i += ' '
                        self.text += i
                    self.exam.setText(self.text)
                    self.text = ""
                    for voca in self.result_list:
                        voca += ' '
                        self.text += voca

                    self.text = self.text[:-1]
                    self.source = self.text


                    print("수어 번역: ", self.result_list, self.text)
                    self.A_text.setText(self.text)

                else:
                    self.A_text.setText("")

        else:
            self.exam.hide()
            self.B_signal = "T"
            self.S_button.show()
            if self.cap != None:
                print("카메라 Off")
                self.cap.release()
                self.cap = None
            self.B_image_label.clear()
            self.hbox.replaceWidget(self.B_image_label, self.B_te)
            self.B_image_label.hide()
            self.B_te.show()
            self.B_te.raise_()

    def A_Check_S(self, A_state):
        if A_state == Qt.Checked:
            self.A_button.setStyleSheet("background-color : #F6B99D;" "border : 1px solid #F6B99D;"
                                        "background-image : url(Images/play_120.png);")
            self.A_signal = "S"
            self.A_image_label = QLabel(self)  # 카메라 이미지 담을 레이블 생성
            self.A_image_label.setMaximumSize(640,360)
            self.A_image_label.setMinimumSize(640,360)
            self.hbox.replaceWidget(self.A_text, self.A_image_label)
            self.A_text.hide()
            # create the video capture thread

        else:
            self.A_button.setStyleSheet("background-color : #F6B99D;" "border : 1px solid #F6B99D;"
                                        "background-image : url(Images/sound_120.png);")
            self.A_signal = "T"

            if self.A_thread != None:
                self.A_thread.stop()
                self.A_thread = None

            self.hbox.replaceWidget(self.A_image_label, self.A_text)
            self.A_image_label.hide()
            self.A_text.show()
            self.A_text.raise_()
            self.A_text.setText(self.text)
    def B_clicked(self):
        if self.B_signal == "T":
            if self.B_lang == self.A_lang:
                self.word = self.text
                self.word = self.word.split(" ")
                print(self.word)
                if 'information' in self.word:
                    n = self.word.index('information')
                    self.word.remove('information')
                    self.word.remove('desk')
                    self.word.insert(n, 'information_desk')
                self.result_list = self.word

            else:
                if self.B_lang == "ko":
                    self.result_list = []
                    self.word = self.source
                    self.word = self.word.split(" ")
                    for i in range(len(self.word)):
                        if self.word[i] in self.ko_videos:
                            num = self.ko_videos.index(self.word[i])
                            self.result_list.append(self.en_videos[num])
                elif self.B_lang == "en":
                    self.result_list = []
                    self.word = self.source
                    self.word = self.word.split(" ")
                    for i in range(len(self.word)):
                        if self.word[i] in self.en_videos:
                            num = self.en_videos.index(self.word[i])
                            self.result_list.append(self.ko_videos[num])
                print(self.result_list)
            if self.A_signal == "T":
                self.A_text.setText(self.text)
            elif self.A_signal == "S":
                print(self.result_list)
                if 'information' in self.result_list:
                    n = self.result_list.index('information')
                    self.result_list.remove('information')
                    self.result_list.remove('desk')
                    self.result.insert(n, 'information_desk')
                self.video = video_merge_cv.video_play(self.result_list)
                self.A_thread = VideoThread(self.video)
                # connect its signal to the update_image slot
                self.A_thread.change_pixmap_signal.connect(self.A_update_image)
                # start the thread
                self.A_thread.start()
        if self.B_signal == "S":
            self.t += 1

    def A_clicked(self):
        #self.exam.hide() #없애
        if self.A_signal == "S":
            if self.A_thread != None:
                self.A_thread.stop()
                self.A_thread = None
            if self.word != "":
                if self.A_lang == 'en':
                    self.word = self.en_word
                else:
                    self.word = self.ko_word
                self.video = video_merge_cv.video_play(self.word)
                self.A_thread = VideoThread(self.video)
                # connect its signal to the update_image slot
                self.A_thread.change_pixmap_signal.connect(self.A_update_image)
                # start the thread
                self.A_thread.start()
            else:
                pass
        if self.A_signal == "T":
            self.word = ""
            if self.text != "":
                while self.text[0] == " ":
                    self.text = self.text[1:]
                    if self.text == "":
                        break
                Text_To_Speech.speak(self.text, self.A_lang)
            if self.text == "":
                if self.A_lang == "ko":
                    Text_To_Speech.speak("텍스트가 존재하지 않습니다", "ko")
                elif self.A_lang == "en":
                    Text_To_Speech.speak("There is no text", "en")
    def SL_Translation(self):
        mp_drawing = mp.solutions.drawing_utils
        mp_holistic = mp.solutions.holistic
        if self.B_lang == 'ko':
            SL = "KSL"
        elif self.B_lang == "en":
            SL = "ASL"
        tempLD = []
        hand_all = 21
        pose_all = 25
        # sensitivity = int(input('임계값 설정: '))
        # delay = int(input('딜레이값 설정: '))
        sensitivity = 150
        delay = 10
        x_list1 = []
        x_list2 = []
        y_list1 = []
        y_list2 = []
        x_temp1 = []  #
        y_temp1 = []  #
        x_temp2 = []  #
        y_temp2 = []  #

        ConnectionList = [(0, 4), (4, 5), (5, 6), (6, 8), (0, 10), (0, 1), (1, 2), (2, 3), (3, 7), (0, 9),
                          (0, 12), (12, 24), (12, 14), (14, 25),
                          (25, 26), (26, 27), (27, 28), (28, 29),
                          (25, 30), (30, 31), (31, 32), (32, 33),
                          (25, 34), (34, 35), (35, 36), (36, 37),
                          (25, 38), (38, 39), (39, 40), (40, 41),
                          (25, 42), (42, 43), (43, 44), (44, 45),
                          (0, 11), (11, 23), (11, 13), (13, 46),
                          (46, 47), (47, 48), (48, 49), (49, 50),
                          (46, 51), (51, 52), (52, 53), (53, 54),
                          (46, 55), (55, 56), (56, 57), (57, 58),
                          (46, 59), (59, 60), (60, 61), (61, 62),
                          (46, 63), (63, 64), (64, 65), (65, 66)]
        # 10, 12, 13, 34, 36, 37
        # self.cap = cv2.VideoCapture(cv2.CAP_DSHOW+1) #카메라 캠 설정
        self.cap = cv2.VideoCapture(0)
        self.cap.set(3, self.display_width)
        image_width = 640
        self.cap.set(4, self.display_height)
        image_height = 360

        startSwitch = False
        startPose = False
        poseCount = 0
        poseTimeCount = 0
        AutoMode = False
        Eanswer = 'There is no translated {0}'.format(SL)
        sentence_end = False
        modeText2 = ''
        # prevTime = 0
        # curTime = 0
        q_is_pressed = False

        with mp_holistic.Holistic(upper_body_only=True,min_detection_confidence=0.5,
                                  min_tracking_confidence=0.5) as holistic:
            while self.B == 1:
                if len(tempLD) != 1:
                    if sentence_end == True:
                        break
                else:
                    if len(tempLD[0]) < 30:
                        modeText2 = "TOO FAST, Try again"
                        sentence_end = False
                    else:
                        if sentence_end == True:
                            break
                modeText = "Move to start"
                recColor = (0, 0, 255)
                x_landmarkLD = []
                y_landmarkLD = []
                z_landmarkLD = []
                if self.cap == None:
                    return ""
                ret, frame = self.cap.read()

                # Convert Color (BGR -> RGB)
                image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                # Process image
                results = holistic.process(image)

                # Visualization- Convert Color (RGB -> BGR)
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                # Pose List
                if results.pose_landmarks:
                    for landmark in results.pose_landmarks.landmark:
                        x_landmarkLD.append(landmark.x)
                        y_landmarkLD.append(landmark.y)
                        z_landmarkLD.append(landmark.z)
                else:
                    for i in range(pose_all):
                        x_landmarkLD.append(-1)
                        y_landmarkLD.append(-1)
                        z_landmarkLD.append(0)

                # Right Hand List
                if results.right_hand_landmarks:
                    for landmark in results.right_hand_landmarks.landmark:
                        x_landmarkLD.append(landmark.x)
                        y_landmarkLD.append(landmark.y)
                        z_landmarkLD.append(landmark.z)
                else:
                    for i in range(hand_all):
                        x_landmarkLD.append(-1)
                        y_landmarkLD.append(-1)
                        z_landmarkLD.append(0)

                # Left Hand List
                if results.left_hand_landmarks:
                    for landmark in results.left_hand_landmarks.landmark:
                        x_landmarkLD.append(landmark.x)
                        y_landmarkLD.append(landmark.y)
                        z_landmarkLD.append(landmark.z)
                else:
                    for i in range(hand_all):
                        x_landmarkLD.append(-1)
                        y_landmarkLD.append(-1)
                        z_landmarkLD.append(0)

                poseList = [(0, 12), (12, 14), (14, 16), (0, 11), (11, 13), (13, 15)]
                x_pose = make_VectorList(x_landmarkLD, poseList)
                y_pose = make_VectorList(y_landmarkLD, poseList)
                x_list2 = x_temp2  #
                x_temp2 = x_temp1  #
                x_temp1 = x_list1  #
                x_list1 = x_pose  #
                x_delta = delta(x_list1, x_list2)
                y_list2 = y_temp2  #
                y_temp2 = y_temp1  #
                y_temp1 = y_list1  #
                y_list1 = y_pose  #
                y_delta = delta(y_list1, y_list2)

                rightHand = (int(x_landmarkLD[25] * image_width), int(y_landmarkLD[25] * image_height))
                leftHand = (int(x_landmarkLD[46] * image_width), int(y_landmarkLD[46] * image_height))
                x_max = int(x_landmarkLD[11] * image_width)
                x_min = int(x_landmarkLD[12] * image_width)
                y_max = int(y_landmarkLD[24] * image_height)
                y_min = y_max - 70
                if y_min < 0:
                    y_min = 0
                if rightHand[0] <= x_max and rightHand[0] >= x_min and rightHand[1] <= y_max and rightHand[1] >= y_min and leftHand[0] <= x_max and leftHand[0] >= x_min and leftHand[1] <= y_max and leftHand[1] >= y_min:
                    recColor = (0, 255, 0)
                    if x_delta + y_delta < 0.000001 * sensitivity:
                        poseCount += 1
                    if poseCount > delay:
                        startPose = True
                else:
                    startPose = False
                '''
                cv2.putText(image, Eanswer, (30, 50), cv2.FONT_HERSHEY_DUPLEX, 1, (0, 255, 0))
                if modeText2 == '':
                    cv2.putText(image, modeText, (30, 100), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 255))
                else:
                    cv2.putText(image, modeText2, (30, 100), cv2.FONT_HERSHEY_DUPLEX, 1, (255, 0, 255))
                cv2.putText(image, "StartPose = " + str(startPose), (30, 150), cv2.FONT_HERSHEY_DUPLEX, 1,
                            (255, 0, 255))
                '''
                cv2.rectangle(image, (x_min, y_min), (x_max, y_max), recColor, 1)

                if startSwitch == False:
                    if self.t % 2 == 1: # 수동 인식- 번역 버튼 누르고 3초 뒤 동작 인식 시작
                        q_is_pressed = True
                        secs_start = time.time()
                        self.t = 2
                    elif self.t == 0:
                        self.B_update_image(image)
                    elif q_is_pressed == True:
                        secs_end = time.time()
                        secs_elapsed = int(secs_end - secs_start)
                        cv2.putText(frame, "timer = " + str(secs_elapsed), (30, 50), cv2.FONT_HERSHEY_DUPLEX, self.fontsize,(0, 0, 0), self.thickness)
                        cv2.putText(frame, "timer = " + str(secs_elapsed), (30, 50), cv2.FONT_HERSHEY_DUPLEX, self.fontsize,(255, 255, 255))
                        self.B_update_image(image)
                        if secs_elapsed == 2: #timer 시간 조절
                            startSwitch = True
                    if startPose == True: # 자동 인식- startPose == True는 공수 자세가 인식되었음을 뜻함. 공수 인식 후 3초 뒤 동작 인식 시작
                        if poseTimeCount == 0:
                            secs_start = time.time()
                            poseTimeCount += 1
                    if poseTimeCount >= 1:
                        secs_end = time.time()
                        secs_elapsed = int(secs_end - secs_start)
                        cv2.putText(image, "timer = " + str(secs_elapsed), (30, 50), cv2.FONT_HERSHEY_DUPLEX, self.fontsize,(0, 0, 0), self.thickness)
                        cv2.putText(image, "timer = " + str(secs_elapsed), (30, 50), cv2.FONT_HERSHEY_DUPLEX, self.fontsize,(255, 255, 255))
                        if secs_elapsed == 2:
                            startSwitch = True
                            poseCount = 0
                            poseTimeCount = 0

                self.B_update_image(image)

                cv2.waitKey(1)
                if self.B == 2:
                    self.B = 0
                    self.cap.release()
                    self.cap = None
                    return ""
                stopCount = 0
                flagTimeCount = 0
                startPose = False
                flagList = []
                tempLD = []
                temp1 = []

                while startSwitch == True:
                    # prevTime = curTime
                    # curTime = time.time()
                    # print(int(fpsCheck(prevTime, curTime)))
                    modeText = "Reading"
                    recColor = (0, 0, 255)
                    x_landmarkLD = []
                    y_landmarkLD = []
                    z_landmarkLD = []
                    if self.cap == None:
                        return ""
                    ret, frame = self.cap.read()

                    # Convert Color (BGR -> RGB)
                    image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

                    # Process image
                    results = holistic.process(image)

                    # Visualization- Convert Color (RGB -> BGR)
                    image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)

                    # Pose List
                    if results.pose_landmarks:
                        for landmark in results.pose_landmarks.landmark:
                            x_landmarkLD.append(landmark.x)
                            y_landmarkLD.append(landmark.y)
                            z_landmarkLD.append(landmark.z)
                    else:
                        for i in range(pose_all):
                            x_landmarkLD.append(-1)
                            y_landmarkLD.append(-1)
                            z_landmarkLD.append(0)

                    # Right Hand List
                    if results.right_hand_landmarks:
                        for landmark in results.right_hand_landmarks.landmark:
                            x_landmarkLD.append(landmark.x)
                            y_landmarkLD.append(landmark.y)
                            z_landmarkLD.append(landmark.z)
                    else:
                        for i in range(hand_all):
                            x_landmarkLD.append(-1)
                            y_landmarkLD.append(-1)
                            z_landmarkLD.append(0)

                            # Left Hand List
                    if results.left_hand_landmarks:
                        for landmark in results.left_hand_landmarks.landmark:
                            x_landmarkLD.append(landmark.x)
                            y_landmarkLD.append(landmark.y)
                            z_landmarkLD.append(landmark.z)
                    else:
                        for i in range(hand_all):
                            x_landmarkLD.append(-1)
                            y_landmarkLD.append(-1)
                            z_landmarkLD.append(0)
                    x_VectorList = make_VectorList(x_landmarkLD, ConnectionList)
                    y_VectorList = make_VectorList(y_landmarkLD, ConnectionList)
                    z_VectorList = make_VectorList(z_landmarkLD, ConnectionList)
                    VectorList = x_VectorList + y_VectorList + z_VectorList
                    # tempLD.append(VectorList)

                    poseList = [(0, 12), (12, 14), (14, 16), (0, 11), (11, 13), (13, 15)]
                    x_pose = make_VectorList(x_landmarkLD, poseList)
                    y_pose = make_VectorList(y_landmarkLD, poseList)
                    x_list2 = x_temp2  #
                    x_temp2 = x_temp1  #
                    x_temp1 = x_list1  #
                    x_list1 = x_pose  #
                    x_delta = delta(x_list1, x_list2)
                    y_list2 = y_temp2  #
                    y_temp2 = y_temp1  #
                    y_temp1 = y_list1  #
                    y_list1 = y_pose  #
                    y_delta = delta(y_list1, y_list2)
                    if x_delta + y_delta > 0.000001 * sensitivity:
                        stopCount = 0
                        flagTimeCount = 0
                    else:
                        stopCount += 1
                        # print('delta x: ', x_delta)
                        # print('delta y: ', y_delta)

                    rightHand = (int(x_landmarkLD[25] * image_width), int(y_landmarkLD[25] * image_height))
                    leftHand = (int(x_landmarkLD[46] * image_width), int(y_landmarkLD[46] * image_height))
                    x_max = int(x_landmarkLD[11] * image_width)
                    x_min = int(x_landmarkLD[12] * image_width)
                    y_max = int(y_landmarkLD[24] * image_height)
                    y_min = y_max - 70
                    if y_min < 0:
                        y_min = 0
                    if rightHand[0] <= x_max and rightHand[0] >= x_min and rightHand[1] <= y_max and rightHand[1] >= y_min and leftHand[0] <= x_max and leftHand[0] >= x_min and leftHand[1] <= y_max and leftHand[1] >= y_min:
                        recColor = (0, 255, 0)
                        if stopCount > delay:
                            startPose = True
                    else:
                        startPose = False

                    # Draw the landmarks & Show image
                    mp_drawing.draw_landmarks(image, results.right_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
                    mp_drawing.draw_landmarks(image, results.left_hand_landmarks, mp_holistic.HAND_CONNECTIONS)
                    mp_drawing.draw_landmarks(image, results.pose_landmarks, mp_holistic.UPPER_BODY_POSE_CONNECTIONS)
                    cv2.rectangle(image, (x_min, y_min), (x_max, y_max), recColor, 1)
                    cv2.putText(image, "stopCount = " + str(stopCount), (30, 50), cv2.FONT_HERSHEY_DUPLEX, self.fontsize,(0, 0, 0), self.thickness)
                    cv2.putText(image, "stopCount = " + str(stopCount), (30, 50), cv2.FONT_HERSHEY_DUPLEX, self.fontsize,(255, 255, 255))

                    # < flag 추출 >
                    key = cv2.waitKey(1) & 0xFF
                    if key == ord('s'):
                        sensitivity = int(input('sensitivity setting: '))
                    if key == ord('d'):
                        delay = int(input('delay setting: '))
                    if stopCount > delay or key == ord('q'):
                        flagTimeCount += 1
                        if flagTimeCount == 1:
                            flagList.append(len(tempLD))
                            cv2.putText(image, "FLAG", (30, 100), cv2.FONT_HERSHEY_DUPLEX, self.fontsize, (0, 0, 0), self.thickness)
                            cv2.putText(image, "FLAG", (30, 100), cv2.FONT_HERSHEY_DUPLEX, self.fontsize, (255, 255, 255))
                            print("FLAG")
                            tempLD.append(temp1)
                            temp1 = []
                    else:
                        temp1.append(VectorList)
                    # cv2.putText(image, "FlagCount = " + str(len(flagList)), (30, 150), cv2.FONT_HERSHEY_DUPLEX, 1,
                    #             (0, 255, 0))
                    self.B_update_image(image)

                    if self.B == 2:
                        self.B = 0
                        self.cap.release()
                        self.cap = None
                        return ""

                    if len(tempLD) != 0:
                        if startPose == True:
                            # print(flagList)
                            print(len(tempLD))
                            flagList = []
                            startSwitch = False
                            sentence_end = True
                            break
                        # < 데이터 추출 >
                        elif self.t % 2 == 1:
                            self.t = 0
                            # print(flagList)
                            print(len(tempLD))
                            flagList = []
                            startSwitch = False
                            sentence_end = True
                            break
        bundleLD = []
        for VectorList in tempLD:  # tempLD에는 인식한 프레임에서 따온 좌표 리스트가 들어있음. 단어 단위로 구분되어 있음. shape: (단어 개수, 각 단어별 프레임 개수, 5220)
            # for i in range(5):
            #     del VectorList[0]
            splitIndex = int(len(VectorList) // 30)  # VectorList는 단어별 좌표 리스트임.
            if len(VectorList) >= 30:
                splitLD = []
                for i in range(30):
                    splitLD += VectorList[i * splitIndex]
                bundleLD.append(splitLD)
        return bundleLD

def predict_classes(SL, bundleLD):
    # AI 사용
    OUTPUT = []

    if SL == 'KSL':
        model = load_model('KSL(Split)_LSTM.h5')
        y2o = ['딸', '잃어버리다', '안내소', '어디', '도와주세요', '배', '아프다', '화장실']
    elif SL == 'ASL':
        model = load_model('ASL(Split)_LSTM.h5')
        y2o = ['daughter', 'lost', 'information_desk', 'where', 'help', 'stomach', 'sick',
               'toilet']

    input_data = np.reshape(np.array(bundleLD), (len(bundleLD), 30, 174))  # 이 부분 새로 학습한 모델에 맞게 reshape 해주기

    if input_data.size != 0:
        #yhat = model.predict_classes(input_data) #텐서플로 구버전 코드

        yhat = model.predict(input_data)
        yhat = np.argmax(yhat, axis=1)
        for i in yhat:
            OUTPUT.append(y2o[int(i)])
    sentence = ''
    for voca in OUTPUT:
        voca += ' '
        sentence += voca
    '''sentence = sentence[:-1]
    if sentence == '딸 잃어버리다 안내소 어디 도와주세요':
        sentence = '딸을 잃어버렸어요. 안내소가 어디인가요? 도와주세요.'
    elif sentence == '딸 배 아프다 화장실 어디 도와주세요':
        sentence = '딸이 배가 아파요. 화장실이 어디인가요? 도와주세요.'
    elif sentence == '딸 잃어버리다 안내소 어디 도와주세요':
        sentence = '딸을 잃어버렸어요. 안내소가 어디인가요? 도와주세요.'
    '''
    return OUTPUT

if __name__ == "__main__":
    app = QApplication(sys.argv)
    a = App()
    '''b = Logo()
    b.show()
    b.close()'''
    a.show()

    sys.exit(app.exec_())