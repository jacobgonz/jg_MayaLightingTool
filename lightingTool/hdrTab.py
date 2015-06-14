import os
import datetime

import subprocess
import sys

from PySide import QtGui, QtCore

from lm_utils import util as lm_util
reload(lm_util)

class TabContent():
    def __init__(self, ui):
        self.ui = ui

        self._addTabContent()

        # Signal - Explore Folder
        self.ui.connect(self.ui.btnPathExplore,
                    QtCore.SIGNAL('clicked()'),
                    self._exploreFolder)

        self.hdrSel = None

        self.ui.connect(self.ui.btnLoad,
                    QtCore.SIGNAL('clicked()'),
                    self._loadHDRI)

        ## Fill Load Preset Combo
        self.loadPresets = ["aiSkyDomeLight", "aiAreaLight", "areaLight"]
        self.ui.cbLoadPreset.addItems(self.loadPresets)

        self.ui.connect(self.ui.btnExplore,
                    QtCore.SIGNAL('clicked()'),
                    self._exploreHdri)

        self.ui.connect(self.ui.btnRefreshHdr,
                    QtCore.SIGNAL('clicked()'),
                    self._addTabContent)

        self.ui.lePath.returnPressed.connect(self._addTabContent)

    ############################################################################
    #### HDRI FOLDERS

    def _hdrFoldersLayout(self):
        if not self.mainFolder:
            return False

        self.hdriFiles = self._getHdriDict(self.mainFolder)
        if not self.hdriFiles:
            return False

        self._hdrFolderContents()

        return True

    def _hdrFolderContents(self):
        # Clear the layout first
        self._clearLayout(self.ui.lyHdr)

        ### VARIABLES
        self.folderViewBtn = {}
        self.folderBtn = {}
        self.thumbIcon = {}
        self.folderGrid = {}
        self.thumbsWg = {}

        ## Loop through Hdr Folder to add images
        for hdrFolder in sorted(self.hdriFiles):
            ### Add Folder
            self.folderGrid[hdrFolder] = QtGui.QGridLayout(self.ui.scrlyHdr)
            self.ui.lyHdr.addLayout(self.folderGrid[hdrFolder])

            folderWg = QtGui.QWidget(self.ui.scrlyHdr)
            self.folderGrid[hdrFolder].addWidget(folderWg)

            hboxFolder = QtGui.QHBoxLayout(folderWg)

            # Folder View Icon Button
            self.folderViewBtn[hdrFolder] = QtGui.QPushButton(folderWg)
            self.folderViewBtn[hdrFolder].setFixedSize(20, 20)
            self.folderViewBtn[hdrFolder].setStyleSheet("background-color:#6a7071")
            self.folderViewBtn[hdrFolder].isCheckable()

            # View Button Icon
            self.folderViewBtn[hdrFolder].setIcon(QtGui.QIcon(':/showHistory.png'))
            self.folderViewBtn[hdrFolder].setIconSize(QtCore.QSize(20, 20))

            # Signal - Explore Folder
            self.ui.connect(self.folderViewBtn[hdrFolder],
                        QtCore.SIGNAL('clicked()'),
                        lambda hdrFolder = hdrFolder:
                        self._showHideFolder(hdrFolder))

            hboxFolder.addWidget(self.folderViewBtn[hdrFolder])

            # Folder Button
            self.folderBtn[hdrFolder] = QtGui.QPushButton(folderWg)
            self.folderBtn[hdrFolder].setFixedSize(len(hdrFolder)*10, 20)
            self.folderBtn[hdrFolder].setStyleSheet("background-color:#3e6d74")
            self.folderBtn[hdrFolder].setText(hdrFolder)

            folderPath = os.path.join(self.mainFolder, hdrFolder)

            # Signal - Explore Folder
            self.ui.connect(self.folderBtn[hdrFolder],
                        QtCore.SIGNAL('clicked()'),
                        lambda folderPath = folderPath:
                        self._exploreFolder(folderPath))

            hboxFolder.addWidget(self.folderBtn[hdrFolder])

            # Line
            line = QtGui.QFrame(folderWg)
            line.setFrameShape(QtGui.QFrame.HLine)
            line.setFrameShadow(QtGui.QFrame.Sunken)
            line.setFixedSize(520-(len(hdrFolder)*10), 15)
            hboxFolder.addWidget(line)

            # Add Hdri Thumbnails for this HDR Folder Row
            self._uiFolderContent(hdrFolder)
            self.thumbsWg[hdrFolder].hide()

        spacerContent = QtGui.QSpacerItem(1,
                                        1,
                                        QtGui.QSizePolicy.Expanding,
                                        QtGui.QSizePolicy.Expanding)

        self.ui.lyHdr.addItem(spacerContent)

        return None

    def _uiFolderContent(self, hdrFolder):
        rowIndex = 1
        rowLength = 7

        self.thumbsWg[hdrFolder] = QtGui.QWidget(self.ui.scrlyHdr)
        self.folderGrid[hdrFolder].addWidget(self.thumbsWg[hdrFolder])

        grid = QtGui.QGridLayout(self.thumbsWg[hdrFolder])

        frame = QtGui.QFrame()
        grid.addWidget(frame)
        hBox = QtGui.QHBoxLayout(frame)

        newRow = 1
        for hdrFile in self.hdriFiles[hdrFolder]:
            thumbPath = self._getHdriThumbPath(hdrFolder, hdrFile)

            if newRow > rowLength:
                rowIndex += rowIndex
                self._addRowSpacer(hBox)

                frame = QtGui.QFrame()
                grid.addWidget(frame)

                hBox = QtGui.QHBoxLayout(frame)

                newRow = 1

            ## Add Thumbanail
            thumbW = 70
            thumbH = 35

            ### HDR Thumbanail Button
            self.thumbIcon[hdrFile] = QtGui.QPushButton()
            self.thumbIcon[hdrFile].setAutoFillBackground(True)

            self.thumbIcon[hdrFile].setFixedSize(thumbW, thumbH)
            hBox.addWidget(self.thumbIcon[hdrFile])

            ### Set image Thumbnail Icon
            self.thumbIcon[hdrFile].setIcon(QtGui.QIcon(thumbPath))
            self.thumbIcon[hdrFile].setIconSize(QtCore.QSize(thumbW-4, thumbH-4))
            self.thumbIcon[hdrFile].setStyleSheet("background-color: #52869e")

            # Signal
            filePath = os.path.join(self.mainFolder, hdrFolder, hdrFile)
            self.thumbIcon[hdrFile].clicked.connect(lambda thumbPath=thumbPath,
                                                    filePath=filePath,
                                                    selBtn=self.thumbIcon[hdrFile]:
                                                    self._setLoadImage(thumbPath, filePath, selBtn))

            newRow += 1

        self._addRowSpacer(hBox)
        spacerFolders = QtGui.QSpacerItem(1,
                                              25,
                                              QtGui.QSizePolicy.Fixed,
                                              QtGui.QSizePolicy.Fixed)
        self.ui.lyHdr.addItem(spacerFolders)

        return None

    def _addTabContent(self):
        self.mainFolder = self.ui.lePath.text()
        self._hdrFoldersLayout()

        return None

    def _addRowSpacer(self, hBox):

        spacerRow = QtGui.QSpacerItem(500,
                    1,
                    QtGui.QSizePolicy.Maximum,
                    QtGui.QSizePolicy.Fixed)

        hBox.addItem(spacerRow)

        return None

    ############################################################################
    ### MAIN FUNCTIONS

    def _getFileData(self, filePath):
        dateCreated, dateModified = self._getFileTime(filePath)
        fileSize = os.path.getsize(filePath)
        fileSize = (fileSize/(1024*1024.0))
        docType = (os.path.splitext(filePath)[-1]).replace(".", "").upper()
        fileData = {"dateCreated": dateCreated,
                    "dateModified": dateModified,
                    "fileSize": "%.2f MB" % fileSize,
                    "fileRes": None,
                    "docType": docType}

        return fileData

    def _getFileTime(self, filePath):
        t = int(os.stat(filePath).st_mtime)
        t = datetime.datetime.fromtimestamp(t)
        dateCreated = t.strftime("%Y/%m/%d %H:%M")

        t = int(os.stat(filePath).st_ctime)
        t = datetime.datetime.fromtimestamp(t)
        dateModified = t.strftime("%Y/%m/%d %H:%M")

        return dateCreated, dateModified

    def _getHdriDict(self, mainFolder):
        if not os.path.exists(mainFolder):
            return

        hdriDict = {}

        for typeFolder in os.listdir(mainFolder):
            folderPath = os.path.join(mainFolder, typeFolder)
            if os.path.isfile(folderPath):
                continue

            # Catch Windows error when accesing acces denied dirs
            try:
                hdrFiles = [x for x in os.listdir(folderPath) \
                            if x.endswith(".exr") or x.endswith(".hdr")]
            except:
                print "File acces denied: %s" % folderPath

            hdriDict[typeFolder] = hdrFiles

        return hdriDict

    def _getHdriThumbPath(self, hdrFolder, hdrFile):
        folderPath = os.path.join(self.mainFolder, hdrFolder)

        thumbFile = None
        for myFile in os.listdir(folderPath):
            fileName = os.path.splitext(hdrFile)[0]
            if os.path.splitext(myFile)[0] == "%s_Thumb" % (fileName):
                thumbFile = myFile

        if not thumbFile:
            thumbFile = 'hdr_noThumb.jpg'

        thumbPath = os.path.join(folderPath, thumbFile)

        return thumbPath

    def _clearLayout(self, layout):

        if layout is not None:
            while layout.count():
                child = layout.takeAt(0)
                if child.widget() is not None:
                    child.widget().deleteLater()
                elif child.layout() is not None:
                    self._clearLayout(child.layout())

        return None

    ##########################################################################################
    ### MAIN SIGNALS

    def _exploreFolder(self, folderPath=None):
        if folderPath is None:
            folderPath = self.mainFolder

        if not os.path.exists(folderPath):
            print '%s does not exist' % folderPath
            return None

        if sys.platform == "darwin":
            subprocess.call(["open", "-R", folderPath])
        elif sys.platform == "win32":
            os.system('start %s' % folderPath)
        elif sys.platform == "linux2":
            subprocess.Popen(["nautilus", folderPath])
        else:
            print "Explore folder not implemented for this OS"

        return None

    def _showHideFolder(self, hdrFolder):
        if self.thumbsWg[hdrFolder].isVisible() is True:
            self.thumbsWg[hdrFolder].hide()
        else:
            self.thumbsWg[hdrFolder].show()

        return None

    def _exploreHdri(self):
        if self.hdrSel is None:
            return None

        hdriFolder = os.path.dirname(self.hdrSel)
        self._exploreFolder(hdriFolder)

        return None

    def _setLoadImage(self, thumbPath, filePath, selBtn):
        for hdrFile in sorted(self.thumbIcon):
            self.thumbIcon[hdrFile].setStyleSheet("background-color: #52869e")

        selBtn.setStyleSheet("background-color: #d93939")

        self.hdrSel = filePath

        self.ui.btnImage.setIcon(QtGui.QIcon(thumbPath))
        self.ui.btnImage.setIconSize(QtCore.QSize(320, 160))

        fileData = self._getFileData(filePath)
        fileName = os.path.basename(filePath)

        self.ui.leFileName.setText(fileName)
        self.ui.leDocTYpe.setText(fileData["docType"])
        self.ui.leDateCreated.setText(fileData["dateCreated"])
        self.ui.leDateMod.setText(fileData["dateModified"])
        self.ui.leFileSize.setText(fileData["fileSize"])
        self.ui.leResolution.setText(fileData["fileRes"])

        self.ui.btnLoad.setEnabled(True)
        self.ui.btnLoad.setStyleSheet("background-color: #005500")

        return None

    def _loadHDRI(self):
        filePath = self.hdrSel
        if not filePath or not os.path.exists(filePath):
            print "%s does not exist" % filePath
            return None

        lightPreset = self.ui.cbLoadPreset.currentText()
        validTypes = self.loadPresets

        newLight, loadLight = lm_util.loadFileToLight(filePath,
                                                      lightPreset,
                                                      validTypes)
        if newLight:
            lm_util.displayMessageBox("Maya Lighting Tool",
                "Image Loaded to new CREATED Light - [ %s ]" % loadLight)
        else:
            lm_util.displayMessageBox("Maya Lighting Tool",
                "Image Loaded to existing SELECTED Light - [ %s ]" % loadLight)

        return None
