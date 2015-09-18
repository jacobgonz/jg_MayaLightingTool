import maya.cmds as cmds

import pymel.core as pm

from PySide import QtGui
import pysideuic
import xml.etree.ElementTree as xml
from cStringIO import StringIO

import shiboken
import maya.OpenMayaUI as apiUI

def loadUi(uiFile):
    parsed = xml.parse(uiFile)
    widget_class = parsed.find('widget').get('class')
    form_class = parsed.find('class').text

    with open(uiFile, 'r') as f:
        o = StringIO()
        frame = {}

        pysideuic.compileUi(f, o, indent=0)
        pyc = compile(o.getvalue(), '<string>', 'exec')
        exec pyc in frame

        form_class = frame['Ui_%s' % form_class]
        base_class = eval('QtGui.%s' % widget_class)

    return form_class, base_class

def mayaWindowExists(mayaDialog):

    return cmds.window(mayaDialog, exists=True)

def deleteMayawindow(mayaDialog):
    if mayaWindowExists(mayaDialog):
        cmds.deleteUI(mayaDialog)

    return None

def getMayaWindowByName(mayaDialog):
    if cmds.window(mayaDialog, exists=True):
        cmds.deleteUI(mayaDialog, window=True)

    maya_win_name = cmds.window(mayaDialog)

    parent_win_pointer = apiUI.MQtUtil.findWindow(maya_win_name)
    parent_win = shiboken.wrapInstance(long(parent_win_pointer), QtGui.QWidget)

    return parent_win

def toQtObject(mayaName):
    '''
    Given the name of a Maya UI element of any type,
    return the corresponding QWidget or QAction.
    If the object does not exist, returns None
    '''
    ptr = apiUI.MQtUtil.findControl(mayaName)
    if ptr is None:
        ptr = apiUI.MQtUtil.findLayout(mayaName)
    if ptr is None:
        ptr = apiUI.MQtUtil.findMenuItem(mayaName)
    if ptr is not None:
        return shiboken.wrapInstance(long(ptr), QtGui.QWidget)

def createLocator(locatorType, asLight=False):
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

def getLightShapeNode(node):
    shapeNodes = cmds.listRelatives(node,
                                    allDescendents=True,
                                    fullPath=True,
                                    shapes=True) or []

    shapeNodes = filter(lambda x: cmds.nodeType(x) in getLightTypes(),
                        shapeNodes) or []

    if not len(shapeNodes):
        return False

    # TODO: Review - Return only 1 shape node (keep an eye for multiple shapeNodes)
    lightShape = shapeNodes[0]

    return lightShape

def lightOnCurrentLayer(myLight):
    currLayer = cmds.editRenderLayerGlobals(query= True, crl = True)
    currLy_objs = cmds.editRenderLayerMembers(currLayer,
                                              query=True,
                                              fullNames=True)

    if not currLy_objs:
        return False

    lightShape = getLightShapeNode(myLight)

    if myLight in currLy_objs or lightShape in currLy_objs:
        return True

    return False

def getSelectedLightShape(lightType, validTypes):
    userSel = cmds.ls(sl=True)

    if not userSel:
        return False

    lightShape = getLightShapeNode(userSel[0])

    if not lightShape:
        return False

    return lightShape

def loadFileToLight(filePath, lightType, validTypes):
    # If Light selected: load file to this light (ony valid Types)
    lightShape = getSelectedLightShape(lightType, validTypes)

    #If not create a light based on lightType preset
    if not lightShape:
        lightShape, lightName = createLocator(lightType, asLight=False)
        newLight = True
    else:
        newLight = False

    fileNode = cmds.shadingNode("file", asTexture=True)
    placeNode = cmds.shadingNode("place2dTexture", asUtility=True)

    conPlace2File = ["coverage", "translateFrame", "rotateFrame", "mirrorU",
                    "mirrorV", "stagger", "wrapU", "wrapV", "repeatUV", "offset",
                    "rotateUV", "noiseUV", "vertexUvOne", "vertexUvTwo",
                    "vertexUvThree", "vertexCameraOne"]

    for value in conPlace2File:
        cmds.connectAttr("%s.%s" % (placeNode, value),
                         "%s.%s" % (fileNode, value),
                         force=True)

    cmds.connectAttr("%s.outUV" % placeNode,  "%s.uv" % fileNode)
    cmds.connectAttr("%s.outUvFilterSize" % placeNode,  "%s.uvFilterSize" % fileNode)
    cmds.connectAttr("%s.outColor" % fileNode, "%s.color" % lightShape, force=True)

    cmds.setAttr("%s.fileTextureName" % fileNode, filePath, type="string")

    # Set resolution if Skydome
    if lightType == "aiSkyDomeLight":
        fileRes = int(cmds.getAttr('%s.outSizeX' % fileNode))
        # FIXME: Some files return 0 as resolution. Needs to be looked at
        if fileRes > 0:
            cmds.setAttr("%s.resolution" % lightShape, fileRes)

    # Select the new Light
    loadLight = cmds.listRelatives(lightShape, parent =True)[0]
    cmds.select(loadLight)

    return newLight, loadLight

#NEW getSceneLights

def getLightTypes():
    lightTypes = ['aiAreaLight',
              'aiPhotometricLight',
              'aiSkyDomeLight',
              'areaLight',
              'pointLight',
              'spotLight',
              'volumeLight']
    return lightTypes

def getSceneLights(layer=False):
    '''
        This function returns:
    - [0] a dict of lights and their group parent (if any) inside the scene : l_dict
    - [1] l_dict but filered by lights inside the current Layer: layer_l_dict
    - [2] a list of lights used on the current layer: rl_lights
    - [3] a list of all lights inside the scene: scnLights

    - Need to look at simplyfing this code
    '''

    ## Variables
    l_dict = {}
    layer_l_dict = {}
    rl_lights = []
    scn_Lights = []

    lightTypes = getLightTypes()

    scn_Lights = cmds.ls(type=["light"] + lightTypes, long=True)

    ## Add mesh Lights to scn_Lights list
    ## FIXME: review this - is making the updates really slow!!!
    for meshNode in cmds.ls(type="mesh", long=True):
        if cmds.getAttr("%s.aiTranslator" % meshNode) == "mesh_light":
            scn_Lights.append(meshNode)

    currLayer = cmds.editRenderLayerGlobals(query= True, crl=True)
    currLy_objs = cmds.editRenderLayerMembers(currLayer,
                                              query=True,
                                              fullNames=True) or []

    for l in scn_Lights:
        l_obj = "|".join(l.split("|")[0:-1])
        l_parent = "|".join(l.split("|")[0:-2]) or 'Root'

        if l_parent not in l_dict.keys():
            l_dict[l_parent] = [l]
        else:
            l_dict[l_parent].append(l)

        if l_obj in currLy_objs or l in currLy_objs:
            rl_lights.append(l_obj)

            if l_parent not in layer_l_dict.keys():
                layer_l_dict[l_parent] = [l]
            else:
                layer_l_dict[l_parent].append(l)

    return l_dict, layer_l_dict, rl_lights, scn_Lights

def removeAddLightFromLayer(transform, layer, remove=False):
    cmds.editRenderLayerMembers(layer,
                                transform,
                                remove = remove,
                                noRecurse=True)

    # Remove light Shape nodes if inside the layer
    lightShapeNode = getLightShapeNode(transform)

    if lightShapeNode and remove:
        cmds.editRenderLayerMembers(layer,
                                    lightShapeNode,
                                    r= remove,
                                    nr= True)

    return None

def createLightGrpAttr(lightShape):
    attrName = "mtoa_constant_lightGroup"

    if not cmds.attributeQuery(attrName, node=lightShape, exists=True):
        cmds.addAttr(lightShape,
                     ln=attrName,
                     at="long",
                     defaultValue=1,
                     minValue=1,
                     maxValue=8)

    grpAttr = "%s.%s" % (lightShape, attrName)

    return grpAttr

def displayMessageBox(windowTitle,
                      text,
                      infoText = None,
                      detailText = None,
                      icon = QtGui.QMessageBox.Information,
                      buttons = QtGui.QMessageBox.Ok,
                      parent = None):

    msgBox = QtGui.QMessageBox(parent)
    msgBox.setIcon(icon)
    msgBox.setWindowTitle(windowTitle+"\t\t\t\t")
    msgBox.setText(text)
    if infoText is not None:
        msgBox.setInformativeText(infoText)
    if detailText is not None:
        msgBox.setDetailedText(detailText)
    msgBox.setStandardButtons(buttons)

    return msgBox.exec_()

def arnoldIsRenderer():
    if cmds.getAttr('defaultRenderGlobals.currentRenderer') == 'arnold':
        return True
    else:
        displayMessageBox("Maya Lighting Tool",
                          "Lighting Tool only available for ARNOLD. Check scene render engine!")
        return False
