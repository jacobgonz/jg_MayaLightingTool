import os

import maya.cmds as cmds
import pymel.core as pm

from PySide import QtGui, QtCore

from lm_utils import util as lm_util
reload(lm_util)

class TabContent():
    def __init__(self, ui):
        self.ui = ui

        # Variables
        self.lightAttrW = {}
        self.attrGrid = {}
        self.currentLightAttr = None

        self.lightLayersW = {}
        self.lightLayerBtn = {}
        self.lightLayerLabel = {}

        # Render Layers Combo
        self._renderLayersCombo()
        self.ui.connect(self.ui.cbLayers,
                    QtCore.SIGNAL("currentIndexChanged(int)"),
                    self._rLayerSwitch)

        self.scn_lights, self.rl_lights, self.rl_lights_list, self.scn_lights_list = lm_util.getSceneLights()

        self.sel_lbt, lightShape, self.allSelLights = self._getSelectedLight()

        ### Fill Lights Tab
        self._activeLightsLayout()
        self._lightPresets()
        self._lightsOutliner()

        if self.sel_lbt:
            self._updateAttrEditor(lightShape)
            self._lightLayersTab(lightShape)
            self._highlightSelLight(lightShape, self.allSelLights)

        currLayer = cmds.editRenderLayerGlobals(currentRenderLayer =True,
                                                query = True)

        # Add to Layer Button signal
        self.ui.btnAddLayer.clicked.connect(lambda btName ='add' : \
                                            self._rlLayer_bt(btName))
        self.ui.btnAddLayer.setEnabled(currLayer != 'defaultRenderLayer')

        # Remove from  Layer Button signal
        self.ui.btnRemoveLayer.clicked.connect(lambda btName ='remove': \
                                               self._rlLayer_bt(btName))
        self.ui.btnRemoveLayer.setEnabled(currLayer != 'defaultRenderLayer')

        # Refresh button signal
        self.ui.btnRefresh.clicked.connect(self._refreshWidgets)

        # Resfresh UI Signal on tabSide Channel(Outliner/Attr/Layers)
        self.ui.connect(self.ui.tabSide,
                    QtCore.SIGNAL('currentChanged(int)'),
                    lambda : self._refreshWidgets(False))

        # Add Script Job
        self._createScriptJobs()

        selTreeLights = self.ui.trOutliner.selectedItems(), 'here'

    def _displayContextMenu(self, myLight, lightShape):
        btn = self.light_bt[lightShape]
        self.addActions = {}

        # set button context menu policy
        btn.setContextMenuPolicy(QtCore.Qt.CustomContextMenu)
        self.ui.connect(btn, QtCore.SIGNAL('customContextMenuRequested(const QPoint&)'),
                    lambda point,
                    lightShape = lightShape,
                    myLight = myLight:
                    self.on_context_menu(point, lightShape, myLight))

        # create context menu
        self.ui.popMenu = QtGui.QMenu(self.ui)
        self.add_Action = QtGui.QAction(self.ui.popMenu)

        self.add_Action.setText("Add to All Layers")
        self.ui.popMenu.addAction(self.add_Action)

        self.remove_Action = QtGui.QAction(self.ui.popMenu)
        self.ui.popMenu.addAction(self.remove_Action)
        self.remove_Action.setText("Remove from All Layers")

        return None

    def on_context_menu(self, point, lightShape, myLight):
        self.add_Action.triggered.connect(lambda myLight = myLight,
                                                rL=None,
                                                remove = False,
                                                allLayers= True:
                                                self._addRemoveFromLayers(myLight,
                                                                          rL,
                                                                          remove,
                                                                          allLayers))

        self.remove_Action.triggered.connect(lambda myLight = myLight,
                                                rL=None,
                                                remove = True,
                                                allLayers= True:
                                                self._addRemoveFromLayers(myLight,
                                                                          rL,
                                                                          remove,
                                                                          allLayers))

        # show context menu
        self.ui.popMenu.exec_(self.light_bt[lightShape].mapToGlobal(point))

        self.add_Action.triggered.disconnect()
        self.remove_Action.triggered.disconnect()

        return None

    ############################################################################
    #### RENDER LAYERS COMBO

    def _getRenderLayers(self):
        # TODO: review avoiding more than one defaultRenderLayer
        rLayers = [x for x in cmds.ls(type='renderLayer') \
                    if "defaultRenderLayer" not in x]

        rLayers.append("defaultRenderLayer")

        return rLayers

    def _renderLayersCombo(self):
        rLayers = self._getRenderLayers()
        currLayer = cmds.editRenderLayerGlobals(currentRenderLayer =True,
                                                query = True)
        crlIndex = rLayers.index(currLayer)

        self.ui.cbLayers.clear()

        self.ui.cbLayers.addItems(rLayers)
        self.ui.cbLayers.setCurrentIndex(crlIndex)

        return None

    ############################################################################
    ###SIGNAL FUNCTIONS - RENDER LAYERS COMBO

    def _rLayerSwitch(self):
        self.ui.cbLayers.blockSignals(True)
        rLayer = str(self.ui.cbLayers.currentText())

        if not cmds.objExists(rLayer) or cmds.nodeType(rLayer) != "renderLayer":
            cmds.warning("The %s render Layes does not exist" % rLayer)
            return False

        cmds.editRenderLayerGlobals(currentRenderLayer = rLayer)
        self._refreshWidgets()
        self.ui.cbLayers.blockSignals(False)

        return rLayer

    ############################################################################
    #### ACTIVE LIGHTS

    def _activeLightsLayout(self):

        # Variables to store UI widgets
        self.remove_bt = {}
        self.light_bt = {}

        ### ACTIVE LIGHTS CONTENT
        self.spacerActive = None
        self._activeLightsContents()

        return None

    def _activeLightsContents(self):
        ### VARIABLES
        self.grpW = {}
        self.grpGrid = {}
        self.hboxLight = {}
        self.lightW = {}
        self.light_label = {}

        ## Make sure 'Root' is the first element in the list
        groupList = list(self.scn_lights.keys())

        if 'Root' in groupList:
            groupList.remove('Root')
            groupList.insert(0, 'Root')

        ## Loop through Groups to add Lights
        for myGr in groupList:
            self._addGroupToActive(myGr)

            # Add lights for this group
            for lightShape in self.scn_lights[myGr]:
                myLight = "|".join(lightShape.split("|")[0:-1])

                self._addLightToActive(myLight, lightShape, myGr)

        self._addSpacerToActivefunction()

        return None

    def _addGroupToActive(self, myGr):
        self.grpGrid[myGr] = QtGui.QGridLayout(self.ui.scrlyActive)
        self.ui.lyActive.addLayout(self.grpGrid[myGr])

        self.grpW[myGr] = QtGui.QWidget()
        self.grpGrid[myGr].addWidget(self.grpW[myGr])

        # GRP Label
        hbox = QtGui.QHBoxLayout(self.grpW[myGr])
        grLabel = QtGui.QLabel(self.grpW[myGr])
        grLabel.setText(myGr)
        grLabel.setFixedSize(len(myGr)*8, 15)
        hbox.addWidget(grLabel)

        # Grp Line
        line = QtGui.QFrame(self.grpW[myGr])
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        line.setFixedSize(690-(len(myGr)*8), 15)
        hbox.addWidget(line)

        return None

    def _addLightToActive(self, myLight, lightShape, myGr):
        if myGr not in sorted(self.grpW):
            self._addGroupToActive(myGr)
            self._addSpacerToActivefunction()

        lightName = cmds.listRelatives(lightShape, parent=True)[0]

        self.lightW[lightShape] = QtGui.QWidget(self.ui)
        self.hboxLight[lightShape] = QtGui.QHBoxLayout(self.lightW[lightShape])

        ### Light Remove Button
        self.remove_bt[lightShape] = QtGui.QPushButton(self.ui.scrActive)
        self.remove_bt[lightShape].setFixedSize(20, 20)

        self.hboxLight[lightShape].addWidget(self.remove_bt[lightShape])

        currLayer = cmds.editRenderLayerGlobals(query= True, crl = True)
        if currLayer == 'defaultRenderLayer':
            self.remove_bt[lightShape].setEnabled(False)

        iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         'icons',
                         'removeIcon.png')

        self.remove_bt[lightShape].setIcon(QtGui.QIcon(iconPath))

        # Signal
        self.remove_bt[lightShape].clicked.connect(lambda myLight=myLight \
                                                   : self._addRemoveFromLayers(myLight))

        ### Light Icon Button
        self.light_bt[lightShape] = QtGui.QPushButton(self.ui.scrActive)
        self.light_bt[lightShape].setFixedSize(30, 30)
        self.hboxLight[lightShape].addWidget(self.light_bt[lightShape])

        ## Set Icon Image
        lightType = cmds.objectType(lightShape)
        self._setLihgtIcon(lightType, self.light_bt[lightShape], [25, 25])

        # Signal
        self.light_bt[lightShape].clicked.connect(lambda values =lightShape \
                                                  : self._lightIcon_bt(values))

        self._displayContextMenu(myLight, lightShape)

        ### Light Name
        self.light_label[lightShape] = QtGui.QLabel(self.ui.scrActive)
        self.light_label[lightShape].setText(lightName)
        self.hboxLight[lightShape].addWidget(self.light_label[lightShape])
        self.light_label[lightShape].setFixedSize(150, 20)

        ### Highlight Channel Box Light
        if myLight == self.sel_lbt:
            light_font = QtGui.QFont(self.light_label[lightShape].font())
            light_font.setBold(True)
            light_font.setWeight(100)
            self.light_label[lightShape].setFont(light_font)

        ### Light Controls
        vis_values = ['%s.visibility' % lightShape, 'Visibility']
        color_values = ['%s.color' % lightShape, 'C']
        int_values = ['%s.intensity' % lightShape, 'I']
        exp_values = ['%s.aiExposure' % lightShape, 'E']

        self._addAttrWidget(self.hboxLight[lightShape],
                            self.ui.scrActive,
                            vis_values)

        self._addAttrWidget(self.hboxLight[lightShape], self.ui.scrActive,
                                    color_values,
                                    attr_type='color')

        if lightType == "mesh":
            self._addAttrWidget(self.hboxLight[lightShape], self.ui.scrActive,
                                        int_values,
                                        attr_type='float2Col',
                                        size=[10, 125])

            self._addAttrWidget(self.hboxLight[lightShape], self.ui.scrActive,
                        exp_values,
                        attr_type='floatSliderMesh', size=[10, 60, 62])
        else:
            self._addAttrWidget(self.hboxLight[lightShape], self.ui.scrActive,
                                        int_values,
                                        attr_type='floatSlider')

            self._addAttrWidget(self.hboxLight[lightShape], self.ui.scrActive,
                                        exp_values,
                                        attr_type='floatSlider')

        self.grpGrid[myGr].addWidget(self.lightW[lightShape])

        if myGr not in sorted(self.rl_lights):
            self.lightW[lightShape].hide()
            self.grpW[myGr].hide()
            return None

        else:
            self.grpW[myGr].show()

        if lightShape not in self.rl_lights[myGr]:
            self.lightW[lightShape].hide()
            return None

        self.lightW[lightShape].show()

        return None

    def _addSpacerToActivefunction(self):
        if not self.spacerActive is None:
            self.ui.lyActive.removeItem(self.spacerActive)

        self.spacerActive = QtGui.QSpacerItem(1,
                                              185,
                                              QtGui.QSizePolicy.Fixed,
                                              QtGui.QSizePolicy.Minimum)

        self.ui.lyActive.addItem(self.spacerActive)

        return None

    def _setLihgtIcon(self, lightType, uiObject, size):
        iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                 'icons',
                                 '%s.png' % lightType.lower())

        if os.path.exists(iconPath):
            uiObject.setIcon(QtGui.QIcon(iconPath))
        else:
            uiObject.setIcon(QtGui.QIcon(':/%s.png' % lightType.lower()))

        uiObject.setIconSize(QtCore.QSize(size[0], size[1]))

        return None

    ############################################################################
    ## SIGNAL FUNCTIONS - ACTIVE LIGHTS

    def _addRemoveFromLayers(self, myLight, rL=None, remove=True, allLayers=False):
        if myLight == "selected":
            myLight = self._getSelectedLight()[0]

        if not cmds.objExists(myLight):
            ## Refresh UI Widgets
            cmds.warning("Light %s does not exist in the scene. UI updated" % myLight)
            self._refreshWidgets()
            return None

        rLayers = [x for x in cmds.ls(type='renderLayer') \
                                if x != 'defaultRenderLayer']

        if rL is None:
            rL = cmds.editRenderLayerGlobals(query= True,
                                              currentRenderLayer = True)

        # Check if the renderLayer exists
        if not cmds.objExists(rL) or cmds.nodeType(rL) != "renderLayer":
            cmds.warning("Render Layer %s does not exist. Upade UI first" % rL)
            return None

        if remove == "check":
            remove = (myLight in (cmds.editRenderLayerMembers(rL,
                                    q=True,
                                    fullNames=True) or []))

        if not allLayers:
            rLayers = [rL]

        for rL in rLayers:
            cmds.editRenderLayerMembers(rL,
                                        myLight,
                                        remove = remove,
                                        noRecurse=True)

        ## Refresh UI Widgets
        # TODO: update lights variables internally to gain speed
        self._refreshWidgets()

        return None

    def _lightIcon_bt(self, lightShape):
        if lightShape not in sorted(self.hboxLight):
            return None
        myLight = "|".join(lightShape.split("|")[0:-1])

        if not cmds.objExists(myLight):
            cmds.warning("%s does not exist.UI Updated" % lightShape)
            self._refreshWidgets()
            return

        ## Select Light
        cmds.select(myLight)

        self._updateAttrEditor(lightShape)
        self._lightLayersTab(lightShape)
        self.sel_lbt = myLight

        for treeLight in self.treeItems.keys():
            lightSel = (treeLight == myLight)
            self.treeItems[treeLight].setSelected(lightSel)

        self._highlightSelLight(lightShape, self.allSelLights)

        return None

    def _highlightSelLight(self, lightShape, allSelLights):
        ### Highlight label on selected light
        myLight = cmds.listRelatives(lightShape, parent =True, fullPath= True)[0]
        for light_label in self.light_label.keys():
            if light_label == lightShape and self._lightOnCurrentLayer(myLight) is True:
                light_font = QtGui.QFont(self.light_label[light_label].font())
                light_font.setBold(True)
                light_font.setWeight(100)
                self.light_label[light_label].setFont(light_font)
                self.light_label[light_label].setStyleSheet("background-color: #52869e")
            elif light_label in allSelLights and self._lightOnCurrentLayer(myLight) is True:
                light_font = QtGui.QFont(self.light_label[light_label].font())
                light_font.setBold(True)
                light_font.setWeight(100)
                self.light_label[light_label].setFont(light_font)
                self.light_label[light_label].setStyleSheet("background-color: #5f7681")
            else:
                light_font = QtGui.QFont(self.light_label[light_label].font())
                light_font.setBold(False)
                light_font.setWeight(1)
                self.light_label[light_label].setFont(light_font)
                self.light_label[light_label].setStyleSheet("background-color: none")

        return None

    ############################################################################
    ###### CHANNEL BOX

    def _attrEditor(self, lightShape):
        attrGrid = QtGui.QGridLayout(self.ui.scrlyAttr)
        self.ui.lyAttr.addLayout(attrGrid)

        self.lightAttrW[lightShape] = QtGui.QWidget()
        attrGrid.addWidget(self.lightAttrW[lightShape])

        lyAttrLight = QtGui.QVBoxLayout(self.lightAttrW[lightShape])

        self.ui.lblAttr.setText(lightShape.split("|")[-2])
        lightType = cmds.objectType(lightShape)
        lightTrans = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]

        emit_values = [["%s.emitDiffuse" % lightShape, 'Emit Diffuse'],
                       ["%s.emitSpecular" % lightShape, 'Emit Specular']]

        scaleX = ['%s.scaleX' % lightTrans, 'Scale X']
        scaleY = ['%s.scaleY' % lightTrans, 'Scale Y']

        max_values = ['%s.aiMaxBounces' % lightShape, 'Max Bounces']

        contr_values = [['%s.aiDiffuse' % lightShape, 'Diffuse'],
                        ['%s.aiSpecular' % lightShape, 'Specular'],
                        ['%s.aiSss' % lightShape, 'SSS'],
                        ['%s.aiIndirect' % lightShape, 'Indirect']]

        for param in emit_values:
            self._addAttrWidget(lyAttrLight,
                                self.ui.scrAttr,
                                param,
                                attr_type='cbx')

        if lightType == "mesh":

            self._addLine(lyAttrLight)
            samp_values = ["%s.aiSamples" % lightShape, 'Samples']
            self._addAttrWidget(lyAttrLight, self.ui.scrlyAttr, samp_values,
                                attr_type='float2Col',
                                size=[40, 40])

            self._addLine(lyAttrLight)

            for param in contr_values:
                self._addAttrWidget(lyAttrLight, None, param,
                                    attr_type='floatSliderMesh',
                                    size=[40, 40, 5])

            self._addAttrWidget(lyAttrLight, self.ui.scrlyAttr,
                                max_values,
                                attr_type='float2Col',
                                size=[80, 45])

        else:
            self._addLine(lyAttrLight)

            if lightType == "areaLight" or lightType == "aiAreaLight":
                self._addAttrWidget(lyAttrLight,
                                    self.ui.scrlyAttr,
                                    scaleX,
                                    attr_type='float2Col',
                                    size=[40, 40])

                self._addAttrWidget(lyAttrLight,
                                    self.ui.scrlyAttr,
                                    scaleY,
                                    attr_type='float2Col',
                                    size=[40, 40])

            res_values = ["%s.resolution" % lightShape, 'Resolution']
            self._addAttrWidget(lyAttrLight, self.ui.scrlyAttr, res_values,
                                attr_type='floatSlider', size=[80, 40, 5, 5])

            self._addLine(lyAttrLight)
            angle_values = ["%s.aiAngle" % lightShape, 'Angle']
            self._addAttrWidget(lyAttrLight, self.ui.scrlyAttr, angle_values,
                                attr_type='floatSlider',
                                size=[40, 40, 30, 5])

            samp_values = ["%s.aiSamples" % lightShape, 'Samples']
            self._addAttrWidget(lyAttrLight, self.ui.scrlyAttr, samp_values,
                                attr_type = 'floatSlider',
                                size=[40, 40, 30, 5])

            self._addLine(lyAttrLight)

            for param in contr_values:
                self._addAttrWidget(lyAttrLight,
                                    self.ui.scrlyAttr,
                                    param,
                                    attr_type='floatSlider',
                                    size=[40, 40, 30, 5])

            self._addAttrWidget(lyAttrLight,
                                self.ui.scrlyAttr,
                                max_values,
                                attr_type='floatSlider',
                                size=[80, 45, 5, 5])

        self._addLine(lyAttrLight)
        norm_values = ["%s.aiNormalize" % lightShape, 'Normalize']
        self._addAttrWidget(lyAttrLight,
                            self.ui.scrlyAttr,
                            norm_values,
                            attr_type='cbx')

        shad_values = ["%s.aiCastShadows" % lightShape, 'Cast Shadows']
        self._addAttrWidget(lyAttrLight,
                            self.ui.scrlyAttr,
                            shad_values,
                            attr_type='cbx')
        self._addLine(lyAttrLight)

        # Add LightGrp Attr to lightShape if not existing

        grpAttr = lm_util.createLightGrpAttr(lightShape)
        if lightType == "mesh":
            self._addAttrWidget(lyAttrLight,
                                None,
                                [grpAttr, "Mtoa_lightGroup"],
                                attr_type='floatSliderMesh',
                                size=[80, 20, 5])

        else:
            self._addAttrWidget(lyAttrLight,
                                self.ui.scrlyAttr,
                                [grpAttr, "Mtoa_lightGroup"],
                                attr_type='floatSlider',
                                size=[80, 15, 5, 5])

        lightName = "|".join(lightShape.split("|")[0:-1])

        if lightName in self.rl_lights_list:
            self.ui.scrlyAttr.setVisible(True)
        else:
            self.ui.scrlyAttr.setVisible(False)

        self.spacerAttr = QtGui.QSpacerItem(1, 80,
                                            QtGui.QSizePolicy.Fixed,
                                            QtGui.QSizePolicy.Minimum)

        lyAttrLight.addItem(self.spacerAttr)

        self.currentLightAttr = lightShape

        return None

    def _addLine(self, layout):
        line = QtGui.QFrame(self.ui.scrAttr)
        line.setFrameShape(QtGui.QFrame.HLine)
        line.setFrameShadow(QtGui.QFrame.Sunken)
        layout.addWidget(line)

        return line

    ############################################################################
    #### LIGHT LAYERS TAB

    def _lightLayersTab(self, lightShape):
        lightName = cmds.listRelatives(lightShape, parent=True)[0]
        myLight = cmds.listRelatives(lightShape, parent=True, fullPath=True)[0]

        self.ui.lblLayers.setText(lightName)

        rLayers = [x for x in cmds.ls(type='renderLayer') \
                    if x != "defaultRenderLayer"]

        for rL in rLayers:
            self._createLightLayerWg(rL, myLight, lightName, rLayers.index(rL))
            self._updateLightLayersWidgets(rL,
                                           myLight,
                                           lightName,
                                           rLayers.index(rL))

        return None

    def _createLightLayerWg(self, rL, myLight, lightName, rlIndex):
        if rL in sorted(self.lightLayerBtn):
            return

        self.lightLayersW[myLight] = QtGui.QWidget(self.ui.scrlyLayers)
        self.ui.scrlyLayers.layout().insertWidget(rlIndex,
                                                  self.lightLayersW[myLight])

        hLayout = QtGui.QHBoxLayout(self.lightLayersW[myLight])

        self.lightLayerBtn[rL] = QtGui.QPushButton(self.lightLayersW[myLight])

        self.lightLayerBtn[rL].setFixedSize(20, 20)
        sizePolicy = QtGui.QSizePolicy(QtGui.QSizePolicy.Fixed,
                                       QtGui.QSizePolicy.Fixed)

        sizePolicy.setHorizontalStretch(0)

        self.lightLayerBtn[rL].setSizePolicy(sizePolicy)

        ### Layer Name
        self.lightLayerLabel[rL] = QtGui.QLabel(self.lightLayersW[myLight])
        self.lightLayerLabel[rL].setText(rL)

        hLayout.addWidget(self.lightLayerBtn[rL])
        hLayout.addWidget(self.lightLayerLabel[rL])

        #SIGNAL
        self.lightLayerBtn[rL].clicked.connect(lambda myLight="selected",
                                        rL=rL,
                                        remove="check",
                                        allLayers= False:
                                        self._addRemoveFromLayers(myLight,
                                                                  rL,
                                                                  remove,
                                                                  allLayers))

        return None

    def _updateLightLayersWidgets(self, rL, myLight, lightName, rlIndex):
        inconName = "addIcon.png"
        bgColor = "background-color: #c95758"

        if myLight in (cmds.editRenderLayerMembers(rL, q=True, fullNames=True) or []):
            inconName = "removeIcon.png"
            bgColor = "background-color: #587b99"

        if not rL in sorted(self.lightLayerBtn):
            self._createLightLayerWg(rL, myLight, lightName, rlIndex)

        iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'icons',
                        inconName)

        self.lightLayerBtn[rL].setIcon(QtGui.QIcon(iconPath))

        font = QtGui.QFont(self.lightLayerLabel[rL].font())
        font.setBold(True)
        font.setWeight(100)

        self.lightLayerLabel[rL].setFont(font)
        self.lightLayerLabel[rL].setStyleSheet(bgColor)

        return None

    ############################################################################
    #### LIGHT PRESETS

    def _lightPresets(self):
        self.lightPr_bt = {}

        prDict = {
                    'Mtoa': [
                            'meshLight',
                            'aiPhotometricLight',
                            'aiAreaLight',
                            'aiSkyDomeLight'
                            ],
                    'Maya': [
                            'directionalLight',
                            'pointLight',
                            'spotLight',
                            'areaLight'
                            ]
                 }

        for prType in sorted(prDict):
            for lightName in prDict[prType]:
                iconPath = ':/%s.png' % lightName.lower()

                # Set custom path for arnold light Presets
                if prType == 'Mtoa':
                    iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                        'icons', '%s.png' % lightName.lower())
                lightPr = len(self.lightPr_bt.keys())

                self.lightPr_bt[lightPr] = QtGui.QPushButton(self.ui.frPresets)
                self.lightPr_bt[lightPr].setFixedSize(40, 40)
                self.lightPr_bt[lightPr].setIcon(QtGui.QIcon(iconPath))
                self.lightPr_bt[lightPr].setIconSize(QtCore.QSize(40, 40))

                self.ui.lyPresets.addWidget(self.lightPr_bt[lightPr])
                self.lightPr_bt[lightPr].setObjectName(lightName)

                # signal
                self.lightPr_bt[lightPr].clicked.connect(lambda values = [lightName, prType] \
                                                        : self._createLight_bt(values))

        return None

    ############################################################################
    #### SIGNALS - LIGHT PRESETS
    def _createLight_bt(self, values):
        lightName = values[0]
        prType = values[1]

        newLight = False
        ## Create Light as per preset Type
        if prType == 'Maya':
            if lightName == 'directionalLight':
                cmds.CreateDirectionalLight()
                newLight = cmds.ls(sl=True)[0]
            if lightName == 'pointLight':
                cmds.CreatePointLight()
                newLight = cmds.ls(sl=True)[0]
            if lightName == 'spotLight':
                cmds.CreateSpotLight()
                newLight = cmds.ls(sl=True)[0]
            if lightName == 'areaLight':
                cmds.CreateAreaLight()
                newLight = cmds.ls(sl=True)[0]

        if prType == 'Mtoa':
            if lightName == "meshLight":
                userSel = cmds.ls(selection=True,
                                  exactType='transform',
                                  long=True)

                if not userSel:
                    cmds.confirmDialog(title='Error',
                                       message='No transform is selected!',
                                       button='Ok')
                    return None

                meshShape = cmds.listRelatives(userSel[0], type='mesh')

                if not meshShape:
                    cmds.confirmDialog(title='Error',
                               message='The selected transform has no meshes',
                               button='Ok')
                    return None

                if not cmds.objExists('%s.aiTranslator' % meshShape[0]):
                    print 'Shape has not aiTranslator attribute'
                    return None

                cmds.setAttr("%s.aiTranslator" % meshShape[0],
                             'mesh_light',
                             type="string")
                newLight = userSel[0]

            else:
                newLight = self._createLocator(lightName, asLight=True)[1]

        ## Add new light to render layer and selected
        if not newLight:
            return None

        self._lightToLayer(newLight)
        cmds.select(newLight)
        lightShape = cmds.listRelatives(allDescendents=True, fullPath=True)[0]

        ## Create lightGrp Attr on new light
        lm_util.createLightGrpAttr(lightShape)

        ## Add Light to UI
        # Update rl_lights variable - revise if needed

        self.rl_lights = lm_util.getSceneLights()[1]

        self._addLightToActive(newLight, lightShape, 'Root')

        self._refreshWidgets()

        return newLight

    def _createLocator(self, locatorType, asLight=False):
        ## Used to create Arnold Lights (Copied from mtoa.utils)
        lNode = pm.createNode('transform', name='%s1' % locatorType)
        lName = lNode.name()
        lId = lName[len(locatorType):]
        shapeName = '%sShape%s' % (locatorType, lId)
        pm.createNode(locatorType, name=shapeName, parent=lNode)

        if asLight:
            cmds.connectAttr('%s.instObjGroups' % lName,
                             'defaultLightSet.dagSetMembers',
                             nextAvailable=True)

        return (shapeName, lName)

    def _lightToLayer(self, newLight):
        ### Add new light to current layer
        currLayer = cmds.editRenderLayerGlobals(query= True,
                                                  currentRenderLayer = True)
        if currLayer == 'defaultRenderLayer' or not newLight:
            return False
        cmds.editRenderLayerMembers(currLayer, newLight, noRecurse=True)

        return None

    ############################################################################
    #### LIGHTS OUTLINER

    def _lightsOutliner(self):
        self._lightsOutlinerContent()
        __sortingEnabled = self.ui.trOutliner.isSortingEnabled()
        self.ui.trOutliner.setSortingEnabled(__sortingEnabled)

        return None

    def _lightsOutlinerContent(self):

        if not self.scn_lights:
            self.scn_lights['Root'] = []

        # First clear the tree
        self.ui.trOutliner.clear()
        self.treeItems = {}
        self.treeLightShapes = []

        # SIGNAL
        self.ui.connect(self.ui.trOutliner.selectionModel(),
                        QtCore.SIGNAL('selectionChanged(QItemSelection, QItemSelection)'),
                        self._selectLightsFromTree)

        # Make sure 'Root' is the first element in the list
        groupList = list(self.scn_lights.keys())
        if 'Root' in groupList:
            groupList.remove('Root')
            groupList.insert(0, 'Root')

        for myGrp in groupList:
            item_0 = QtGui.QTreeWidgetItem(self.ui.trOutliner)
            self.ui.trOutliner.topLevelItem(groupList.index(myGrp)).setText(0, myGrp)
            item_0.setFlags(QtCore.Qt.ItemIsDragEnabled | QtCore.Qt.ItemIsUserCheckable | QtCore.Qt.ItemIsEnabled)
            self.ui.trOutliner.expandItem(item_0)

            for lightShape in self.scn_lights[myGrp]:

                lightName = cmds.listRelatives(lightShape, parent=True)[0]
                myLight = "|".join(lightShape.split("|")[0:-1])

                self.treeItems[myLight] = QtGui.QTreeWidgetItem(item_0)
                self.treeLightShapes.append(lightShape)

                self.ui.trOutliner.topLevelItem(groupList.index(myGrp)).child(self.scn_lights[myGrp].index(lightShape)).setText(0, lightName)
                lightType = cmds.objectType(lightShape)
                iconPath = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                            'icons',
                                            '%s.png' % lightType.lower())

                if os.path.exists(iconPath):
                    self.treeItems[myLight].setIcon(0, QtGui.QIcon(iconPath))
                else:
                    self.treeItems[myLight].setIcon(0,QtGui.QIcon(':/%s.png' % lightType.lower()))

                if not self._lightOnCurrentLayer(myLight):
                    self._setTreeEntryColor(myLight, self.treeItems[myLight])

                self.treeItems[myLight].setData(0, QtCore.Qt.UserRole, lightShape)

        return None

    def _setTreeEntryColor(self, myLight, treeItem):
        if not self._lightOnCurrentLayer(myLight):
            brush = QtGui.QBrush(QtGui.QColor(170, 0, 0))
        else:
            brush = QtGui.QBrush(QtGui.QColor(200, 200, 200))
        brush.setStyle(QtCore.Qt.NoBrush)
        treeItem.setForeground(0, brush)

        return None

    ############################################################################
    ### SIGNAL FUNCTIONS - LIGHTS OUTLINER
    def _selectLightsFromTree(self):
        selItems = self.ui.trOutliner.selectedItems()
        selLights = []
        selLightShapes = []

        myLightFullName = None

        for item in selItems:
            grp = item.parent()
            grpName = str(grp.text(0))
            grpName = "" if grpName == "Root" else grpName
            myLight = str(item.text(0))
            myLightFullName = "%s|%s" % (grpName, myLight)
            if cmds.objExists(myLightFullName):
                lightShape = cmds.listRelatives(myLightFullName,
                                                allDescendents=True,
                                                fullPath=True)[0]
                selLightShapes.append(lightShape)
                selLights.append(myLightFullName)

        if not len(selLights):
            return None

        self.allSelLights = selLightShapes
        lastSelLight = self.allSelLights[-1]

        self._highlightSelLight(lastSelLight, self.allSelLights)

        cmds.select(selLights)

        return selLights

    def _rlLayer_bt(self, btName, allLayers = False):
        selItems = self.ui.trOutliner.selectedItems()

        for item in selItems:
            grp = item.parent()
            grpNanme = str(grp.text(0))
            myLight = str(item.text(0))

            if grpNanme != "Root":
                myLight = ("%s|%s" % (grpNanme, myLight))
            else:
                myLight = "|" + myLight

            if not cmds.objExists(myLight):
                cmds.warning("%s does not exist in the scene" % myLight)
                continue

            currLayer = cmds.editRenderLayerGlobals(query= True, crl = True)
            rLayers = [x for x in cmds.ls(type='renderLayer') \
                                     if 'defaultRenderLayer' not in x]

            if currLayer == 'defaultRenderLayer':
                return False

            rmLight = (btName == 'remove')
            if allLayers:
                for rL in rLayers:
                    cmds.editRenderLayerMembers(rL,
                                                myLight,
                                                r= rmLight,
                                                nr= True)
            else:
                cmds.editRenderLayerMembers(currLayer,
                                            myLight,
                                            r= rmLight,
                                            nr= True)

        ## Refresh UI Widgets
        self._refreshWidgets()

        return None

    # ##########################################################################
    ### MAIN FUNCTIONS

    def _lightOnCurrentLayer(self, myLight):
        currLayer = cmds.editRenderLayerGlobals(query= True, crl = True)
        currLy_objs = cmds.editRenderLayerMembers(currLayer, query=True,
                                                  fullNames=True)

        if not currLy_objs:
            return False
        if not myLight in currLy_objs:
            return False

        return True

    def _getSelectedLight(self):
        userSel = cmds.ls(sl=True, long=True)
        sel_light = False
        sel_lightShape = False
        allSelLights = []

        if not userSel:
            return sel_light, sel_lightShape, allSelLights

        lastObj = cmds.ls(sl=True, long=True)[-1]

        for lightShape in self.scn_lights_list:
            lightTrans = cmds.listRelatives(lightShape,
                                            parent=True,
                                            fullPath=True)[0]
            if lightTrans in userSel:
                allSelLights.append(lightShape)

            if lightTrans == lastObj:
                sel_light = lastObj
                sel_lightShape = lightShape

        return sel_light, sel_lightShape, allSelLights

    def _addAttrWidget(self, layout, lyParent, values, attr_type='cbx',
                            size=[10, 60, 40, 80]):

        myAttr, label = values

        if not cmds.objExists(myAttr):
            return False

        if not cmds.window('lmTmpWin', exists=True):
            cmds.window('lmTmpWin')

        cmds.columnLayout(adjustableColumn=True)

        if attr_type == 'cbx':
            ui_item = cmds.checkBox(label=label, v=False, rs=False, w=60)
            cmds.checkBox(ui_item,
                          changeCommand = lambda attr: self._onAttrChanged(myAttr),
                          edit=True)
            cmds.connectControl(ui_item, myAttr)

        if attr_type == 'color':
            ui_item = cmds.attrColorSliderGrp(label=label, attribute=myAttr,
                cl4=['left', 'left', 'left', 'left'], cw4=[10, 15, 50, 80])

        if attr_type == 'floatSlider':
            ui_item = cmds.attrFieldSliderGrp(label=label, attribute=myAttr,
                cl4=['left', 'left', 'left', 'left'], cw4=size, pre=2)
            cmds.attrFieldSliderGrp(ui_item,
                                changeCommand = lambda *args: self._onAttrChanged(myAttr),
                                edit=True)

        if attr_type == 'floatSliderMesh':
            ui_item = cmds.attrFieldSliderGrp(label=label, attribute=myAttr,
                cl3=["left", "left", "left"], cw3=size, pre=2)
            cmds.attrFieldSliderGrp(ui_item,
                                changeCommand = lambda *args: self._onAttrChanged(myAttr),
                                edit=True)

        if attr_type == 'float2Col':
            ui_item = cmds.attrFieldSliderGrp(label=label, attribute=myAttr,
                 cl2=["left", "left"], cw2=size, pre=2)
            cmds.attrFieldSliderGrp(ui_item,
                                changeCommand = lambda *args: self._onAttrChanged(myAttr),
                                edit=True)

        qtObj = lm_util.toQtObject(ui_item)
        qtObj.setParent(lyParent)
        layout.addWidget(qtObj)

        if cmds.window('lmTmpWin', exists=True):
            cmds.deleteUI('lmTmpWin')

        return qtObj

    def _onAttrChanged(self, changedAttr):
        selItems = self.ui.trOutliner.selectedItems()

        selLights = [x.data(0, QtCore.Qt.UserRole) for x in selItems]

        lightChanged = changedAttr.split(".")[0]

        if not selLights or lightChanged not in selLights:
            return

        currLayer = cmds.editRenderLayerGlobals(crl =True, q = True)

        if currLayer == "defaultRenderLayer":
                isOverride = False
        else:
            isOverride = (currLayer in (cmds.listConnections(changedAttr,
                                                        type="renderLayer") or []))

        attrValue = cmds.getAttr(changedAttr)
        myAttr = changedAttr.split(".")[-1]

        for lightShape in selLights:
            if not cmds.attributeQuery(myAttr, node=lightShape, exists=True):
                continue

            ligthAttr = "%s.%s" % (lightShape, myAttr)

            if isOverride is not False:
                cmds.editRenderLayerAdjustment(ligthAttr)
            elif currLayer != "defaultRenderLayer":
                cmds.editRenderLayerAdjustment(ligthAttr, remove=True)

            cmds.setAttr(ligthAttr, attrValue)

        return None

    ############################################################################
    ### UI UPDATE FUNCTIONS

    def _updateAttrEditor(self, lightShape):
        if self.currentLightAttr:
            self.lightAttrW[self.currentLightAttr].hide()

        selLight, selShape, self.allSelLights = self._getSelectedLight()

        if selShape not in sorted(self.lightAttrW):
            self._attrEditor(selShape)
        else:
            self.lightAttrW[selShape].show()
            self.ui.lblAttr.setText(selShape.split("|")[-2])
            self.currentLightAttr = selShape

        return None

    def _refreshWidgets(self, getLights=True):
        if getLights:
            self.scn_lights, self.rl_lights, self.rl_lights_list, self.scn_lights_list = lm_util.getSceneLights()

        #Update render Layers Combo
        self.ui.cbLayers.blockSignals(True)
        self._renderLayersCombo()
        self.ui.cbLayers.blockSignals(False)

        # Update Render Layer Buttons
        currLayer = cmds.editRenderLayerGlobals(crl =True, q = True)
        self.ui.btnAddLayer.setEnabled(currLayer != 'defaultRenderLayer')
        self.ui.btnRemoveLayer.setEnabled(currLayer != 'defaultRenderLayer')

        ## Show/Hide the Lights Params on the Active Tab if in/out the currlayer
        showLights = []
        showGrps = []

        for myGr, onLights in self.rl_lights.iteritems():
            showGrps.append(myGr)
            for light in onLights:
                showLights.append(light)

        ## Show/Hide Group Labels on Active Layout
        for myGr in sorted(self.grpW):
            if myGr in showGrps:
                self.grpW[myGr].show()
            else:
                self.grpW[myGr].hide()

        ## Show/Hide Lights on Active layout
        for lightShape in sorted(self.lightW):
            if lightShape in showLights:
                self.lightW[lightShape].show()
            else:
                self.lightW[lightShape].hide()

            btnOn = (currLayer != 'defaultRenderLayer')
            if btnOn:
                self.remove_bt[lightShape].setStyleSheet("background-color: red")
            else:
                self.remove_bt[lightShape].setStyleSheet("background-color: black")

            self.remove_bt[lightShape].setEnabled(btnOn)

        ## Check if they are new lights/Groups in the scene - add them to the UI
        newGrps = False
        for myGr, onLights in self.scn_lights.iteritems():
            if myGr not in sorted(self.grpW):
                # Add the group
                self._addGroupToActive(myGr)
                newGrps = True

            # Add the lights
            newLights = [x for x in onLights if x not in sorted(self.lightW)]
            for lightShape in newLights:
                myLight = "|".join(lightShape.split("|")[0:-1])
                self._addLightToActive(myLight, lightShape, myGr)

        if newGrps:
            self._addSpacerToActivefunction()

        ### Check scn lighs count against UI lights count
        # If not the same refresh UI Tree Outliner - !!
        if set(self.treeLightShapes) != set(self.scn_lights_list):
            self._lightsOutlinerContent()

        ### Refresh Entry Colors and selected Lighs
        scnSel = cmds.ls(sl=True, long=True)
        for myLight in self.treeItems.keys():
            self._setTreeEntryColor(myLight, self.treeItems[myLight])

            lightSel = myLight in scnSel
            self.treeItems[myLight].setSelected(lightSel)

        # Update selected Light on Active and Attr Editor
        self.sel_lbt, selShape, self.allSelLights = self._getSelectedLight()

        if selShape in sorted(self.hboxLight):
            self._highlightSelLight(selShape, self.allSelLights)

            self._updateAttrEditor(selShape)

        # Upate Light Layers Tab
        if selShape:
            self._lightLayersTab(selShape)

        return None

    ############################################################################
    ### SCRIPT JOBS

    def _createScriptJobs(self):
        self.scriptJobs = []

        #create script job for updating UI  when change Render Layer
        self.rlMJob = cmds.scriptJob(e= ["renderLayerManagerChange",
                                     self._updateRenderLayer],
                                     protected=True,
                                     killWithScene=False)

        self.scriptJobs.append(self.rlMJob)

        return self.scriptJobs

    def _updateRenderLayer(self):
        if not lm_util.mayaWindowExists('lightingTool_ui'):
            return None

        ## Refresh UI Widgets
        self._refreshWidgets()

        return None

    ############################################################################
    ### MAIN SIGNALS

    def onClose(self):
        ##Remove script jobs linked to the tool
        for sJob in self.scriptJobs :
            cmds.scriptJob(kill=sJob, force=True)
