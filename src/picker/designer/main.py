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
from PySide6.QtGui import (QBrush, QColor, QConicalGradient, QCursor,
    QFont, QFontDatabase, QGradient, QIcon,
    QImage, QKeySequence, QLinearGradient, QPainter,
    QPalette, QPixmap, QRadialGradient, QTransform)
from PySide6.QtWidgets import (QApplication, QHBoxLayout, QHeaderView, QLabel,
    QListView, QMainWindow, QMenuBar, QPushButton,
    QSizePolicy, QStatusBar, QTreeView, QVBoxLayout,
    QWidget)

class Ui_MainWindow(object):
    def setupUi(self, MainWindow):
        if not MainWindow.objectName():
            MainWindow.setObjectName(u"MainWindow")
        MainWindow.resize(617, 454)
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.verticalLayout_4 = QVBoxLayout(self.centralwidget)
        self.verticalLayout_4.setObjectName(u"verticalLayout_4")
        self.horizontalLayout_8 = QHBoxLayout()
        self.horizontalLayout_8.setObjectName(u"horizontalLayout_8")
        self.verticalLayout = QVBoxLayout()
        self.verticalLayout.setObjectName(u"verticalLayout")
        self.label = QLabel(self.centralwidget)
        self.label.setObjectName(u"label")

        self.verticalLayout.addWidget(self.label)

        self.page_tree = QTreeView(self.centralwidget)
        self.page_tree.setObjectName(u"page_tree")

        self.verticalLayout.addWidget(self.page_tree)

        self.horizontalLayout = QHBoxLayout()
        self.horizontalLayout.setObjectName(u"horizontalLayout")
        self.btnAddPage = QPushButton(self.centralwidget)
        self.btnAddPage.setObjectName(u"btnAddPage")

        self.horizontalLayout.addWidget(self.btnAddPage)


        self.verticalLayout.addLayout(self.horizontalLayout)


        self.horizontalLayout_8.addLayout(self.verticalLayout)

        self.verticalLayout_2 = QVBoxLayout()
        self.verticalLayout_2.setObjectName(u"verticalLayout_2")
        self.label_2 = QLabel(self.centralwidget)
        self.label_2.setObjectName(u"label_2")

        self.verticalLayout_2.addWidget(self.label_2)

        self.identifier_list = QListView(self.centralwidget)
        self.identifier_list.setObjectName(u"identifier_list")

        self.verticalLayout_2.addWidget(self.identifier_list)

        self.horizontalLayout_2 = QHBoxLayout()
        self.horizontalLayout_2.setObjectName(u"horizontalLayout_2")
        self.pushButton = QPushButton(self.centralwidget)
        self.pushButton.setObjectName(u"pushButton")

        self.horizontalLayout_2.addWidget(self.pushButton)

        self.pushButton_2 = QPushButton(self.centralwidget)
        self.pushButton_2.setObjectName(u"pushButton_2")

        self.horizontalLayout_2.addWidget(self.pushButton_2)


        self.verticalLayout_2.addLayout(self.horizontalLayout_2)

        self.label_3 = QLabel(self.centralwidget)
        self.label_3.setObjectName(u"label_3")

        self.verticalLayout_2.addWidget(self.label_3)

        self.interactive_list = QListView(self.centralwidget)
        self.interactive_list.setObjectName(u"interactive_list")

        self.verticalLayout_2.addWidget(self.interactive_list)

        self.horizontalLayout_4 = QHBoxLayout()
        self.horizontalLayout_4.setObjectName(u"horizontalLayout_4")
        self.pushButton_5 = QPushButton(self.centralwidget)
        self.pushButton_5.setObjectName(u"pushButton_5")

        self.horizontalLayout_4.addWidget(self.pushButton_5)

        self.pushButton_6 = QPushButton(self.centralwidget)
        self.pushButton_6.setObjectName(u"pushButton_6")

        self.horizontalLayout_4.addWidget(self.pushButton_6)


        self.verticalLayout_2.addLayout(self.horizontalLayout_4)

        self.label_4 = QLabel(self.centralwidget)
        self.label_4.setObjectName(u"label_4")

        self.verticalLayout_2.addWidget(self.label_4)

        self.transition_tree = QTreeView(self.centralwidget)
        self.transition_tree.setObjectName(u"transition_tree")

        self.verticalLayout_2.addWidget(self.transition_tree)

        self.horizontalLayout_5 = QHBoxLayout()
        self.horizontalLayout_5.setObjectName(u"horizontalLayout_5")
        self.pushButton_7 = QPushButton(self.centralwidget)
        self.pushButton_7.setObjectName(u"pushButton_7")

        self.horizontalLayout_5.addWidget(self.pushButton_7)

        self.pushButton_8 = QPushButton(self.centralwidget)
        self.pushButton_8.setObjectName(u"pushButton_8")

        self.horizontalLayout_5.addWidget(self.pushButton_8)


        self.verticalLayout_2.addLayout(self.horizontalLayout_5)


        self.horizontalLayout_8.addLayout(self.verticalLayout_2)

        self.verticalLayout_3 = QVBoxLayout()
        self.verticalLayout_3.setObjectName(u"verticalLayout_3")
        self.label_5 = QLabel(self.centralwidget)
        self.label_5.setObjectName(u"label_5")

        self.verticalLayout_3.addWidget(self.label_5)

        self.treeView = QTreeView(self.centralwidget)
        self.treeView.setObjectName(u"treeView")

        self.verticalLayout_3.addWidget(self.treeView)

        self.btnAddPage_2 = QPushButton(self.centralwidget)
        self.btnAddPage_2.setObjectName(u"btnAddPage_2")

        self.verticalLayout_3.addWidget(self.btnAddPage_2)


        self.horizontalLayout_8.addLayout(self.verticalLayout_3)


        self.verticalLayout_4.addLayout(self.horizontalLayout_8)

        self.horizontalLayout_6 = QHBoxLayout()
        self.horizontalLayout_6.setObjectName(u"horizontalLayout_6")
        self.save_button = QPushButton(self.centralwidget)
        self.save_button.setObjectName(u"save_button")

        self.horizontalLayout_6.addWidget(self.save_button)

        self.cancel_button = QPushButton(self.centralwidget)
        self.cancel_button.setObjectName(u"cancel_button")

        self.horizontalLayout_6.addWidget(self.cancel_button)


        self.verticalLayout_4.addLayout(self.horizontalLayout_6)

        MainWindow.setCentralWidget(self.centralwidget)
        self.menubar = QMenuBar(MainWindow)
        self.menubar.setObjectName(u"menubar")
        self.menubar.setGeometry(QRect(0, 0, 617, 33))
        MainWindow.setMenuBar(self.menubar)
        self.statusbar = QStatusBar(MainWindow)
        self.statusbar.setObjectName(u"statusbar")
        MainWindow.setStatusBar(self.statusbar)

        self.retranslateUi(MainWindow)

        QMetaObject.connectSlotsByName(MainWindow)
    # setupUi

    def retranslateUi(self, MainWindow):
        MainWindow.setWindowTitle(QCoreApplication.translate("MainWindow", u"MainWindow", None))
        self.label.setText(QCoreApplication.translate("MainWindow", u"Pages:", None))
        self.btnAddPage.setText(QCoreApplication.translate("MainWindow", u"Add Page", None))
        self.label_2.setText(QCoreApplication.translate("MainWindow", u"Page Identifiers:", None))
        self.pushButton.setText(QCoreApplication.translate("MainWindow", u"Add Identifier", None))
        self.pushButton_2.setText(QCoreApplication.translate("MainWindow", u"Remove Identifier", None))
        self.label_3.setText(QCoreApplication.translate("MainWindow", u"Interactive Elements:", None))
        self.pushButton_5.setText(QCoreApplication.translate("MainWindow", u"Add Iterfactive", None))
        self.pushButton_6.setText(QCoreApplication.translate("MainWindow", u"Remove Iterfactive", None))
        self.label_4.setText(QCoreApplication.translate("MainWindow", u"Transitions:", None))
        self.pushButton_7.setText(QCoreApplication.translate("MainWindow", u"Add Transition", None))
        self.pushButton_8.setText(QCoreApplication.translate("MainWindow", u"Remove Transition", None))
        self.label_5.setText(QCoreApplication.translate("MainWindow", u"Page Elements:", None))
        self.btnAddPage_2.setText(QCoreApplication.translate("MainWindow", u"New Element", None))
        self.save_button.setText(QCoreApplication.translate("MainWindow", u"Save", None))
        self.cancel_button.setText(QCoreApplication.translate("MainWindow", u"Cancel", None))
    # retranslateUi

