import json
import os

import hdrTab
reload(hdrTab)

import lightsTab
reload(lightsTab)

from PySide import QtGui, QtCore

from lm_utils import util as lm_util
reload(lm_util)

import lightingTool_form as lt_form
reload(lt_form)

class PublishDialog(QtGui.QDialog, lt_form.Ui_LightManagerForm):
# class PublishDialog(QtGui.QDialog, form_class):
    def __init__(self, parent=None, hdrPath=None):
        super(PublishDialog, self).__init__(parent)
        self.setupUi(self)
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
                    "btnRefresh": self.btnRefresh.isEnabled()
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

        return None

    def _tabMainChanged(self):
        tabIndex = self.tabMain.currentIndex()
        tabLabel = self.tabMain.tabText(tabIndex)
        self._loadTabContent(tabLabel)

        return

    def _loadTabContent(self, tabLabel):
        if tabLabel in self.tabsLoaded:
            return

        if tabLabel == "HDRI":
            ## HDRI Tab Content
            self.tbHdr = hdrTab.TabContent(self)
        elif tabLabel == "LIGHTS":
            ### Light Tab Content
            self.tbLights = lightsTab.TabContent(self)

        self.tabsLoaded.append(tabLabel)

        return None

    def _autoRefreshToggled(self):
        autoRefresh = self.cbxRefresh.isChecked()
        btnRef = (autoRefresh is False)
        self.btnRefresh.setEnabled(btnRef)

        return None

    def enterEvent(self, event):
        if "LIGHTS" not in self.tabsLoaded:
            return

        if self.cbxRefresh.isChecked():
            self.tbLights._refreshWidgets()

        return None

    def closeEvent(self, event):
        self._saveWindowPrefs()
        self.tbLights.onClose()

        global ui
        ui = None

def main(hdrPath=None):
    if lm_util.arnoldIsRenderer() is False:
        return

    global ui
    if 'ui' in globals():
        if ui is not None:
            ui.close()

    ui = PublishDialog(parent=lm_util.getMayaWindow(), hdrPath=hdrPath)
    ui.show()
