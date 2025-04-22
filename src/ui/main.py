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
from PySide6.QtWidgets import (QApplication, QDoubleSpinBox, QGridLayout, QGroupBox,
    QLabel, QMainWindow, QMenu, QMenuBar,
    QPushButton, QRadioButton, QSizePolicy, QSpacerItem,
    QVBoxLayout, QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(330, 440)
        sizePolicy = QSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Preferred)
        sizePolicy.setHorizontalStretch(0)
        sizePolicy.setVerticalStretch(0)
        sizePolicy.setHeightForWidth(MainWindow.sizePolicy().hasHeightForWidth())
        MainWindow.setSizePolicy(sizePolicy)
        MainWindow.setMinimumSize(QSize(330, 440))
        MainWindow.setMaximumSize(QSize(330, 440))
        self.actionAbout = QAction(MainWindow)
        self.actionAbout.setObjectName(u"actionAbout")
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setEnabled(True)
        self.appLayout = QVBoxLayout(self.centralwidget)
        self.appLayout.setObjectName(u"appLayout")
        self.groupBox_2 = QGroupBox(self.centralwidget)
        self.groupBox_2.setObjectName(u"groupBox_2")
        self.gridLayout = QGridLayout(self.groupBox_2)
        self.gridLayout.setObjectName(u"gridLayout")
        self.gridLayout.setContentsMargins(9, 5, -1, 5)
        self.delayMinSpin = QDoubleSpinBox(self.groupBox_2)
        self.delayMinSpin.setObjectName(u"delayMinSpin")
        self.delayMinSpin.setDecimals(1)
        self.delayMinSpin.setMinimum(1.500000000000000)

        self.gridLayout.addWidget(self.delayMinSpin, 0, 1, 1, 1)

        self.label = QLabel(self.groupBox_2)
        self.label.setObjectName(u"label")

        self.gridLayout.addWidget(self.label, 0, 0, 1, 1)

        self.label_2 = QLabel(self.groupBox_2)
        self.label_2.setObjectName(u"label_2")

        self.gridLayout.addWidget(self.label_2, 1, 0, 1, 1)

        self.delayMaxSpin = QDoubleSpinBox(self.groupBox_2)
        self.delayMaxSpin.setObjectName(u"delayMaxSpin")
        self.delayMaxSpin.setDecimals(1)
        self.delayMaxSpin.setMinimum(1.600000000000000)
        self.delayMaxSpin.setMaximum(10.000000000000000)

        self.gridLayout.addWidget(self.delayMaxSpin, 1, 1, 1, 1)

        self.horizontalSpacer = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer, 0, 2, 1, 1)

        self.horizontalSpacer_2 = QSpacerItem(40, 20, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum)

        self.gridLayout.addItem(self.horizontalSpacer_2, 1, 2, 1, 1)


        self.appLayout.addWidget(self.groupBox_2)

        self.groupBox = QGroupBox(self.centralwidget)
        self.groupBox.setObjectName(u"groupBox")
        self.verticalLayout_4 = QVBoxLayout(self.groupBox)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.crawl_players_btn = QRadioButton(self.groupBox)
        self.crawl_players_btn.setObjectName(u"crawl_players_btn")

        self.verticalLayout_4.addWidget(self.crawl_players_btn)

        self.crawl_64_32_btn = QRadioButton(self.groupBox)
        self.crawl_64_32_btn.setObjectName(u"crawl_64_32_btn")

        self.verticalLayout_4.addWidget(self.crawl_64_32_btn)

        self.crawl_32_16_btn = QRadioButton(self.groupBox)
        self.crawl_32_16_btn.setObjectName(u"crawl_32_16_btn")

        self.verticalLayout_4.addWidget(self.crawl_32_16_btn)

        self.crawl_16_8_btn = QRadioButton(self.groupBox)
        self.crawl_16_8_btn.setObjectName(u"crawl_16_8_btn")

        self.verticalLayout_4.addWidget(self.crawl_16_8_btn)

        self.crawl_8_4_btn = QRadioButton(self.groupBox)
        self.crawl_8_4_btn.setObjectName(u"crawl_8_4_btn")

        self.verticalLayout_4.addWidget(self.crawl_8_4_btn)

        self.crawl_4_2_btn = QRadioButton(self.groupBox)
        self.crawl_4_2_btn.setObjectName(u"crawl_4_2_btn")

        self.verticalLayout_4.addWidget(self.crawl_4_2_btn)

        self.crawl_2_1_btn = QRadioButton(self.groupBox)
        self.crawl_2_1_btn.setObjectName(u"crawl_2_1_btn")

        self.verticalLayout_4.addWidget(self.crawl_2_1_btn)


        self.appLayout.addWidget(self.groupBox)

        self.startBtn = QPushButton(self.centralwidget)
        self.startBtn.setObjectName(u"startBtn")

        self.appLayout.addWidget(self.startBtn)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 330, 33))
        self.helpMenu = QMenu(self.menubar)
        self.helpMenu.setObjectName(u"helpMenu")
        MainWindow.setMenuBar(self.menubar)

        self.menubar.addAction(self.helpMenu.menuAction())
        self.helpMenu.addAction(self.actionAbout)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"NIKKE Data Collector", None))
        self.actionAbout.setText(QCoreApplication.translate("MainWindow", u"About", None))
        self.groupBox_2.setTitle(QCoreApplication.translate("MainWindow", u"Configure Delay", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"MIN", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"MAX", None))
        self.groupBox.setTitle(QCoreApplication.translate("MainWindow", u"Select Tasks", None))
        self.crawl_players_btn.setText(QCoreApplication.translate("MainWindow", u"64 Players", None))
        self.crawl_64_32_btn.setText(QCoreApplication.translate("MainWindow", u"Round of 64 \u2192 32", None))
        self.crawl_32_16_btn.setText(QCoreApplication.translate("MainWindow", u"Round of 32 \u2192 16", None))
        self.crawl_16_8_btn.setText(QCoreApplication.translate("MainWindow", u"Round of 16 \u2192 8", None))
        self.crawl_8_4_btn.setText(QCoreApplication.translate("MainWindow", u"Round of  8 \u2192 4", None))
        self.crawl_4_2_btn.setText(QCoreApplication.translate("MainWindow", u"Round of  4 \u2192 2", None))
        self.crawl_2_1_btn.setText(QCoreApplication.translate("MainWindow", u"Round of  2 \u2192 1", None))
        self.startBtn.setText(QCoreApplication.translate("MainWindow", u"Link Start", None))
        self.helpMenu.setTitle(QCoreApplication.translate("MainWindow", u"Help", None))
    # retranslateUi

