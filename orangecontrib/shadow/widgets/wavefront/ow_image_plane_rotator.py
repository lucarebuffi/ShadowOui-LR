import sys, numpy
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from oasys.widgets import gui as oasysgui

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

class ImagePlaneRotator(AutomaticElement):

    name = "Image Plane Rotator"
    description = "Wavefront Tools: Image Plane Rotator"
    icon = "icons/rotation.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 3
    category = "Wavefront Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam" , ShadowBeam, "setBeam" ),
              ("Rotation Angle" , float, "setRotationAngle" ),
              ]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Beam",
                "id":"beam"}]

    want_main_area=0
    want_control_area = 1

    input_beam=None
    rotation_angle = -999
    displayed_rotation_angle = -999

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box)

        self.setFixedWidth(420)
        self.setFixedHeight(250)

        gen_box = gui.widgetBox(self.controlArea, "Image Plane Rotator", addSpace=True, orientation="vertical")

        button_box = oasysgui.widgetBox(gen_box, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Rotate Image Plane", callback=self.rotate_image_plane)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        result_box = oasysgui.widgetBox(gen_box, "Result", addSpace=False, orientation="horizontal")

        le_angle = oasysgui.lineEdit(result_box, self, "displayed_rotation_angle", "Rotation Angle",
                                     labelWidth=250, valueType=float, orientation="horizontal")
        le_angle.setReadOnly(True)

    def setBeam(self, beam):
        self.input_beam = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam
                if self.is_automatic_run:
                    self.rotate_image_plane()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Input Beam not usable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def setRotationAngle(self, rotation_angle):
        self.rotation_angle = rotation_angle
        self.displayed_rotation_angle = numpy.round(numpy.degrees(self.rotation_angle), 4)

        if self.is_automatic_run:
            self.rotate_image_plane()


    def rotate_image_plane(self):
        if self.input_beam is None or self.rotation_angle == -999: return

        beam_out = self.input_beam.duplicate()

        for index in range(0, len(beam_out._beam.rays)):
            y_new = beam_out._beam.rays[index, 1]*numpy.cos(self.rotation_angle) - beam_out._beam.rays[index, 2]*numpy.sin(self.rotation_angle)
            z_new = beam_out._beam.rays[index, 1]*numpy.sin(self.rotation_angle) + beam_out._beam.rays[index, 2]*numpy.cos(self.rotation_angle)

            beam_out._beam.rays[index, 1] = y_new
            beam_out._beam.rays[index, 2] = z_new

            y_prime_new = beam_out._beam.rays[index, 4]*numpy.cos(self.rotation_angle) - beam_out._beam.rays[index, 5]*numpy.sin(self.rotation_angle)
            z_prime_new = beam_out._beam.rays[index, 4]*numpy.sin(self.rotation_angle) + beam_out._beam.rays[index, 5]*numpy.cos(self.rotation_angle)

            beam_out._beam.rays[index, 4] = y_prime_new
            beam_out._beam.rays[index, 5] = z_prime_new

        self.send("Beam", beam_out)

if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = ImagePlaneRotator()
    ow.show()
    a.exec_()
    ow.saveSettings()
