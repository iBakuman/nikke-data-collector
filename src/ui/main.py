# -*- coding: utf-8 -*-

################################################################################
## Form generated from reading UI file 'main.ui'
##
## Created by: Qt User Interface Compiler version 6.9.0
##
## WARNING! All changes made in this file will be lost when recompiling UI file!
################################################################################

from PySide6.QtCore import (QCoreApplication, QDate, QDateTime, QLocale,
    QMetaObject, QObject, QPoint, QRect,
    QSize, QTime, QUrl, Qt)
from PySide6.QtGui import (QAction, QBrush, QColor, QConicalGradient,
    QCursor, QFont, QFontDatabase, QGradient,
    QIcon, QImage, QKeySequence, QLinearGradient,
    QPainter, QPalette, QPixmap, QRadialGradient,
    QTransform)
from PySide6.QtWidgets import (QApplication, QComboBox, QDoubleSpinBox, QFrame,
    QGridLayout, QGroupBox, QHBoxLayout, QLabel,
    QMainWindow, QMenu, QMenuBar, QPushButton,
    QRadioButton, QSizePolicy, QSpacerItem, QStackedWidget,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(820, 440)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(330, 440))
        MainWindow.setMaximumSize(QSize(16777215, 16777215))
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        self.appLayout = QVBoxLayout(self.centralwidget)
        self.appLayout.setObjectName(u"appLayout")
        self.gridLayout_2 = QGridLayout()
        self.gridLayout_2.setObjectName(u"gridLayout_2")
        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.gridLayout_2.addWidget(self.label_3, 3, 0, 1, 1)

        self.languageLabel = QLabel(self.centralwidget)
        self.languageLabel.setObjectName(u"languageLabel")

        self.gridLayout_2.addWidget(self.languageLabel, 2, 0, 1, 1)

        self.serverRegionComboBox = QComboBox(self.centralwidget)
        self.serverRegionComboBox.addItem("")
        self.serverRegionComboBox.addItem("")
        self.serverRegionComboBox.addItem("")
        self.serverRegionComboBox.addItem("")
        self.serverRegionComboBox.addItem("")
        self.serverRegionComboBox.addItem("")
        self.serverRegionComboBox.setObjectName(u"serverRegionComboBox")
        self.serverRegionComboBox.setEditable(False)

        self.gridLayout_2.addWidget(self.serverRegionComboBox, 3, 1, 1, 1)

        self.languageComboBox = QComboBox(self.centralwidget)
        self.languageComboBox.addItem("")
        self.languageComboBox.addItem("")
        self.languageComboBox.setObjectName(u"languageComboBox")

        self.gridLayout_2.addWidget(self.languageComboBox, 2, 1, 1, 1)

        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout_2.addWidget(self.label_2, 5, 0, 1, 1)

        self.delayMaxSpin = QDoubleSpinBox(self.centralwidget)
        self.delayMaxSpin.setObjectName(u"delayMaxSpin")
        self.delayMaxSpin.setDecimals(1)
        self.delayMaxSpin.setMinimum(1.600000000000000)
        self.delayMaxSpin.setMaximum(10.000000000000000)
        self.delayMaxSpin.setSingleStep(0.200000000000000)

        self.gridLayout_2.addWidget(self.delayMaxSpin, 5, 1, 1, 1)

        self.delayMinSpin = QDoubleSpinBox(self.centralwidget)
        self.delayMinSpin.setObjectName(u"delayMinSpin")
        self.delayMinSpin.setDecimals(1)
        self.delayMinSpin.setMinimum(1.500000000000000)
        self.delayMinSpin.setSingleStep(0.200000000000000)

        self.gridLayout_2.addWidget(self.delayMinSpin, 4, 1, 1, 1)

        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.gridLayout_2.addWidget(self.label, 4, 0, 1, 1)

        self.gridLayout_2.setColumnStretch(0, 1)
        self.gridLayout_2.setColumnStretch(1, 5)

        self.appLayout.addLayout(self.gridLayout_2)

        self.frame = QFrame(self.centralwidget)
        self.frame.setObjectName(u"frame")
        self.frame.setStyleSheet(u"QFrame {\n"
"    border: 1px solid gray;\n"
"    border-radius: 4px;\n"
"    padding: 5px;\n"
"}\n"
"")
        self.frame.setFrameShape(QFrame.Shape.StyledPanel)
        self.frame.setFrameShadow(QFrame.Shadow.Raised)
        self.verticalLayout_4 = QVBoxLayout(self.frame)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.groupBox = QGroupBox(self.frame)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_2 = QVBoxLayout(self.groupBox)
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.verticalSpacer = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer)

        self.radioButton_2 = QRadioButton(self.groupBox)
        self.radioButton_2.setObjectName(u"radioButton_2")

        self.verticalLayout_2.addWidget(self.radioButton_2)

        self.radioButton = QRadioButton(self.groupBox)
        self.radioButton.setObjectName(u"radioButton")

        self.verticalLayout_2.addWidget(self.radioButton)

        self.radioButton_3 = QRadioButton(self.groupBox)
        self.radioButton_3.setObjectName(u"radioButton_3")

        self.verticalLayout_2.addWidget(self.radioButton_3)

        self.verticalSpacer_2 = QSpacerItem(20, 40, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding)

        self.verticalLayout_2.addItem(self.verticalSpacer_2)


        self.horizontalLayout.addWidget(self.groupBox)

        self.stackedWidgetPages = QStackedWidget(self.frame)
        self.stackedWidgetPages.setObjectName(u"stackedWidgetPages")
        self.pageDataCollection = QWidget()
        self.pageDataCollection.setObjectName(u"pageDataCollection")
        self.verticalLayout = QVBoxLayout(self.pageDataCollection)
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.groupBox_2 = QGroupBox(self.pageDataCollection)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.verticalLayout_3 = QVBoxLayout(self.groupBox_2)
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.crawl_players_btn = QRadioButton(self.groupBox_2)
        self.crawl_players_btn.setObjectName(u"crawl_players_btn")

        self.verticalLayout_3.addWidget(self.crawl_players_btn)

        self.crawl_64_32_btn = QRadioButton(self.groupBox_2)
        self.crawl_64_32_btn.setObjectName(u"crawl_64_32_btn")

        self.verticalLayout_3.addWidget(self.crawl_64_32_btn)

        self.crawl_32_16_btn = QRadioButton(self.groupBox_2)
        self.crawl_32_16_btn.setObjectName(u"crawl_32_16_btn")

        self.verticalLayout_3.addWidget(self.crawl_32_16_btn)

        self.crawl_16_8_btn = QRadioButton(self.groupBox_2)
        self.crawl_16_8_btn.setObjectName(u"crawl_16_8_btn")

        self.verticalLayout_3.addWidget(self.crawl_16_8_btn)

        self.crawl_8_4_btn = QRadioButton(self.groupBox_2)
        self.crawl_8_4_btn.setObjectName(u"crawl_8_4_btn")

        self.verticalLayout_3.addWidget(self.crawl_8_4_btn)

        self.crawl_4_2_btn = QRadioButton(self.groupBox_2)
        self.crawl_4_2_btn.setObjectName(u"crawl_4_2_btn")

        self.verticalLayout_3.addWidget(self.crawl_4_2_btn)

        self.crawl_2_1_btn = QRadioButton(self.groupBox_2)
        self.crawl_2_1_btn.setObjectName(u"crawl_2_1_btn")

        self.verticalLayout_3.addWidget(self.crawl_2_1_btn)


        self.verticalLayout.addWidget(self.groupBox_2)

        self.stackedWidgetPages.addWidget(self.pageDataCollection)
        self.pageScreenshot = QWidget()
        self.pageScreenshot.setObjectName(u"pageScreenshot")
        self.label_4 = QLabel(self.pageScreenshot)
        self.label_4.setObjectName(u"label_4")
        self.label_4.setGeometry(QRect(120, 80, 41, 16))
        self.stackedWidgetPages.addWidget(self.pageScreenshot)

        self.horizontalLayout.addWidget(self.stackedWidgetPages)

        self.horizontalLayout.setStretch(1, 1)

        self.verticalLayout_4.addLayout(self.horizontalLayout)


        self.appLayout.addWidget(self.frame)

        self.startBtn = QPushButton(self.centralwidget)
        self.startBtn.setObjectName(u"startBtn")

        self.appLayout.addWidget(self.startBtn)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 820, 33))
        self.helpMenu = QMenu(self.menubar)
        self.helpMenu.setObjectName(u"helpMenu")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.helpMenu.menuAction())
        self.helpMenu.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        self.stackedWidgetPages.setCurrentIndex(0)


        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"NIKKE Data Collector", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Server", None))
        self.languageLabel.setText(QCoreApplication.translate("MainWindow", u"Language", None))
        self.serverRegionComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"JP", None))
        self.serverRegionComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"KR", None))
        self.serverRegionComboBox.setItemText(2, QCoreApplication.translate("MainWindow", u"GLOBAL", None))
        self.serverRegionComboBox.setItemText(3, QCoreApplication.translate("MainWindow", u"SEA", None))
        self.serverRegionComboBox.setItemText(4, QCoreApplication.translate("MainWindow", u"NA", None))
        self.serverRegionComboBox.setItemText(5, QCoreApplication.translate("MainWindow", u"HK_MO_TW", None))

        self.languageComboBox.setItemText(0, QCoreApplication.translate("MainWindow", u"English", None))
        self.languageComboBox.setItemText(1, QCoreApplication.translate("MainWindow", u"\u4e2d\u6587\u7b80\u4f53", None))

        self.label_2.setText(QCoreApplication.translate("MainWindow", u"MAX", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"MIN", None))
        self.groupBox.setTitle("")
        self.radioButton_2.setText(QCoreApplication.translate("MainWindow", u"Collect Data", None))
        self.radioButton.setText(QCoreApplication.translate("MainWindow", u"Tools", None))
        self.radioButton_3.setText(QCoreApplication.translate("MainWindow", u"Settings", None))
        self.groupBox_2.setTitle("")
        self.crawl_players_btn.setText(QCoreApplication.translate("MainWindow", u"64 Players", None))
        self.crawl_64_32_btn.setText(QCoreApplication.translate("MainWindow", u"Round of 64 \u2192 32", None))
        self.crawl_32_16_btn.setText(QCoreApplication.translate("MainWindow", u"Round of 32 \u2192 16", None))
        self.crawl_16_8_btn.setText(QCoreApplication.translate("MainWindow", u"Round of 16 \u2192 8", None))
        self.crawl_8_4_btn.setText(QCoreApplication.translate("MainWindow", u"Round of  8 \u2192 4", None))
        self.crawl_4_2_btn.setText(QCoreApplication.translate("MainWindow", u"Round of  4 \u2192 2", None))
        self.crawl_2_1_btn.setText(QCoreApplication.translate("MainWindow", u"Round of  2 \u2192 1", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"empty", None))
        self.startBtn.setText(QCoreApplication.translate("MainWindow", u"Link Start", None))
        self.helpMenu.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

