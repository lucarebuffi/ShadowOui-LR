import sys, numpy
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

class RotationAngleCalculator(AutomaticElement):

    name = "Rotation Angle Calculator"
    description = "Wavefront Tools: Rotation Angle Calculator"
    icon = "icons/angle.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 2
    category = "Wavefront Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam # 1" , ShadowBeam, "setBeam1" ),
              ("Input Beam # 2" , ShadowBeam, "setBeam2" ),
              ]

    outputs = [{"name":"Rotation Angle",
                "type":float,
                "doc":"Rotation Angle",
                "id":"rotation_angle"}]

    want_main_area=0
    want_control_area = 1

    input_beam1=None
    input_beam2=None

    rotation_angle = 0.0

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box)

        self.setFixedWidth(420)
        self.setFixedHeight(250)

        gen_box = gui.widgetBox(self.controlArea, "Rotation Angle Calculator", addSpace=True, orientation="vertical")

        button_box = oasysgui.widgetBox(gen_box, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Calculate Rotation Angle", callback=self.calculate_rotation_angle)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        result_box = oasysgui.widgetBox(gen_box, "Result", addSpace=False, orientation="horizontal")

        le_angle = oasysgui.lineEdit(result_box, self, "rotation_angle", "Calculated Rotation Angle",
                                     labelWidth=250, valueType=float, orientation="horizontal")
        le_angle.setReadOnly(True)

    def setBeam1(self, beam):
        self.input_beam1 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam1 = beam
                if self.is_automatic_run:
                    self.calculate_rotation_angle()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #1 not usable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setBeam2(self, beam):
        self.input_beam2 = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam2 = beam
                if self.is_automatic_run:
                    self.calculate_rotation_angle()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Data #2 not usable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)


    def calculate_rotation_angle(self):
        if self.input_beam1 is None or self.input_beam2 is None: return

        self.rotation_angle = 0.0

        # Beam 1 : last 2 elements

        first_grating  = self.input_beam1.getOEHistory()[-2]
        second_grating = self.input_beam1.getOEHistory()[-1]

        alpha_1 = first_grating._shadow_oe_end._oe.T_INCIDENCE
        beta_1  = first_grating._shadow_oe_end._oe.T_REFLECTION

        alpha_2 = second_grating._shadow_oe_end._oe.T_INCIDENCE
        beta_2  = second_grating._shadow_oe_end._oe.T_REFLECTION

        total_angle_1 = (alpha_1 + beta_1) - (alpha_2 - beta_2)

        # Beam 2 : last 3 elements

        first_grating  = self.input_beam2.getOEHistory()[-3]
        second_grating = self.input_beam2.getOEHistory()[-2]
        mirror         = self.input_beam2.getOEHistory()[-1]

        alpha_1 = first_grating._shadow_oe_end._oe.T_INCIDENCE
        beta_1  = first_grating._shadow_oe_end._oe.T_REFLECTION

        alpha_2 = second_grating._shadow_oe_end._oe.T_INCIDENCE
        beta_2  = second_grating._shadow_oe_end._oe.T_REFLECTION

        alpha_3 = mirror._shadow_oe_end._oe.T_INCIDENCE
        beta_3  = mirror._shadow_oe_end._oe.T_REFLECTION

        total_angle_2 = (alpha_1 + beta_1) - (alpha_2 + beta_2) +  (alpha_3 + beta_3)

        calculated_rotation_angle = total_angle_2 - total_angle_1

        self.rotation_angle = numpy.round(numpy.degrees(calculated_rotation_angle), 4)

        self.send("Rotation Angle", calculated_rotation_angle)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = RotationAngleCalculator()
    ow.show()
    a.exec_()
    ow.saveSettings()
