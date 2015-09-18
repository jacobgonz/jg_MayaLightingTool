import json
import os
import sys

from PySide import QtGui, QtCore

import hdrTab
reload(hdrTab)

import lightsTab
reload(lightsTab)

from lm_utils import util as lm_util
reload(lm_util)

import lightingTool_form as lt_form
reload(lt_form)

class PublishDialog(QtGui.QDialog, lt_form.Ui_LightManagerForm):
    def __init__(self, parent=None, winFlag=False, hdrPath=None):
        super(PublishDialog, self).__init__(parent, winFlag)
        self.setupUi(self)

        # Force Close/Minimize button for linux window
        self.setWindowFlags(winFlag | QtCore.Qt.WindowCloseButtonHint | QtCore.Qt.WindowMinimizeButtonHint)

        self.prefsFolder = os.path.join(os.environ["MAYA_APP_DIR"],
                                        "lightingToolPrefs")
        self.prefsFile = os.path.join(self.prefsFolder,
                                      "lightingToolPrefs.pref")

        self.setWindowTitle("MAYA LIGHTING TOOL")

        # Load Window Preferences
        self._loadWindowPrefs()

        # Hdr Path defined as per variable or user input to UI
        if hdrPath:
            self.lePath.setText(hdrPath)
            self.lePath.setEnabled(False)

        self.connect(self.cbxRefresh,
                     QtCore.SIGNAL('clicked()'),
                     self._autoRefreshToggled)

        ## Tab Change Singal
        self.connect(self.tabMain,
                    QtCore.SIGNAL('currentChanged(int)'),
                    self._tabMainChanged)

        # GetCurrentTab Label
        tabIndex = self.tabMain.currentIndex()
        tabLabel = self.tabMain.tabText(tabIndex)

        self.tabsLoaded = []
        self._loadTabContent(tabLabel)

        ## Exit Signal
        self.connect(self, QtCore.SIGNAL('triggered()'), self.closeEvent)

    def _saveWindowPrefs(self):
        prefDict = {"tabMain": self.tabMain.currentIndex(),
                    "cbxRefresh": self.cbxRefresh.isChecked(),
                    "tabSide": self.tabSide.currentIndex(),
                    "lePath": self.lePath.text(),
                    "btnRefresh": self.btnRefresh.isEnabled(),
                    "posX": self.x(),
                    "posY": self.y(),
                    "width": self.width(),
                    "height": self.height()
                    }

        if not os.path.exists(self.prefsFolder):
            os.makedirs(self.prefsFolder)

        with open(self.prefsFile, 'w') as outfile:
            json.dump(prefDict, outfile)

        return None

    def _loadWindowPrefs(self):
        if not os.path.exists(self.prefsFile):
            return None

        with open(self.prefsFile) as data_file:
            prefDict = json.load(data_file)

        self.tabMain.setCurrentIndex(prefDict.get("tabMain", 0))
        self.cbxRefresh.setChecked(prefDict.get("cbxRefresh", True))
        self.tabSide.setCurrentIndex(prefDict.get("tabSide", 0))
        self.lePath.setText(prefDict.get("lePath", ""))
        self.btnRefresh.setEnabled(prefDict.get("btnRefresh", False))
        self.move(prefDict.get("posX", 740), prefDict.get("posY", 390))
        self.resize(prefDict.get("width", self.width()),
                    prefDict.get("height", self.height()))

        return None

    def _tabMainChanged(self):
        tabIndex = self.tabMain.currentIndex()
        tabLabel = self.tabMain.tabText(tabIndex)
        self._loadTabContent(tabLabel)

        return

    def _loadTabContent(self, tabLabel):
        if tabLabel in self.tabsLoaded:
            if tabLabel == "LIGHTS":
                self.tabLights._refreshWidgets()
            return

        if tabLabel == "HDRI":
            ## HDRI Tab Content
            self.tbHdr = hdrTab.TabContent(self)
        elif tabLabel == "LIGHTS":
            ### Light Tab Content
            self.tabLights = lightsTab.TabContent(self)

        self.tabsLoaded.append(tabLabel)

        return None

    def _autoRefreshToggled(self):
        autoRefresh = self.cbxRefresh.isChecked()
        btnRef = (autoRefresh is False)
        self.btnRefresh.setEnabled(btnRef)

        return None

    def keyPressEvent(self, event):
        # Workaround to stop Maya from stealing focus
        if event.key() in (QtCore.Qt.Key_Shift, QtCore.Qt.Key_Control):
            event.accept()
        else:
            event.ignore()

        return None

    def enterEvent(self, event):
        # GetCurrentTab Label
        tabIndex = self.tabMain.currentIndex()
        tabLabel = self.tabMain.tabText(tabIndex)
        if tabLabel != "LIGHTS":
            return

        if self.cbxRefresh.isChecked():
            self.tabLights._refreshWidgets()

        return None

    def closeEvent(self, event):
        self._saveWindowPrefs()
        self.tabLights.onClose()

        lm_util.deleteMayawindow('lightingTool_ui')

def main(hdrPath=None):
    if lm_util.arnoldIsRenderer() is False:
        return

    # If OSX we pass the tool flag to have the window parented to Maya as in Win
    if sys.platform == "darwin":
        winFlag = QtCore.Qt.Tool
    else:
        winFlag = QtCore.Qt.Window

    parent = lm_util.getMayaWindowByName("lightingTool_ui")
    ui = PublishDialog(parent=parent,
                       winFlag=winFlag,
                       hdrPath=hdrPath)
    ui.show()
