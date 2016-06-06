import sys, numpy
from PyQt4 import QtGui
from PyQt4.QtGui import QApplication
from PyQt4.QtGui import QPalette, QColor, QFont

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence, ShadowPhysics

from orangecontrib.shadow.widgets.gui.ow_automatic_element import AutomaticElement

class EnergyCirp(AutomaticElement):

    name = "Energy Cirp"
    description = "Wavefront Tools: Energy Cirp"
    icon = "icons/energy_cirp.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 6
    category = "Wavefront Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam" , ShadowBeam, "setBeam" )]

    outputs = [{"name":"Beam",
                "type":ShadowBeam,
                "doc":"Beam",
                "id":"beam"}]

    want_main_area=0
    want_control_area = 1

    input_beam=None
    units = Setting(0)
    kind_of_calculation = Setting(0)
    central_value = Setting(0.0)
    factor = Setting(1.0)
    user_file = Setting("NONE SPECIFIED")
    user_distribution_values = None

    def __init__(self, show_automatic_box=True):
        super().__init__(show_automatic_box)

        self.setFixedWidth(420)
        self.setFixedHeight(350)

        gen_box = gui.widgetBox(self.controlArea, "Energy Cirp", addSpace=True, orientation="vertical")

        button_box = oasysgui.widgetBox(gen_box, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Generate Energy Spectrum", callback=self.generate_energy_spectrum)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette()) # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette) # assign new palette
        button.setFixedHeight(45)

        gui.separator(gen_box, height=10)

        result_box = oasysgui.widgetBox(gen_box, "Energy Cirp Setting", addSpace=True, orientation="vertical")


        gui.comboBox(result_box, self, "units", label="Units", labelWidth=260,
                     items=["Energy",
                            "Wavelength"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(result_box, self, "kind_of_calculation", label="Kind of calculation", labelWidth=110,
                     items=["Energy/Wavelength = C + k*Y", "User File (Energy/Wavelength vs. Y)"],
                     sendSelectedValue=False, orientation="horizontal", callback=self.set_KindOfCalculation)

        self.kind_box_1 = oasysgui.widgetBox(result_box, "", addSpace=True, orientation="vertical", height=50)

        oasysgui.lineEdit(self.kind_box_1, self, "factor", "Proportionality factor (k) [to eV/Å]",
                                     labelWidth=240, valueType=float, orientation="horizontal")

        oasysgui.lineEdit(self.kind_box_1, self, "central_value", "Central Energy/Wavelength Value [eV/Å]",
                                     labelWidth=240, valueType=float, orientation="horizontal")

        self.kind_box_2 = oasysgui.widgetBox(result_box, "", addSpace=True, orientation="horizontal", height=50)

        self.le_user_file = oasysgui.lineEdit(self.kind_box_2, self, "user_file", "File Name",
                                     labelWidth=60, valueType=str, orientation="horizontal")

        gui.button(self.kind_box_2, self, "...", callback=self.selectUserFile)

        self.set_KindOfCalculation()

    def setBeam(self, beam):
        self.input_beam = None

        if ShadowCongruence.checkEmptyBeam(beam):
            if ShadowCongruence.checkGoodBeam(beam):
                self.input_beam = beam
                if self.is_automatic_run:
                    self.generate_energy_spectrum()
            else:
                QtGui.QMessageBox.critical(self, "Error",
                                           "Input Beam not usable: No good rays or bad content",
                                           QtGui.QMessageBox.Ok)

    def generate_energy_spectrum(self):
        if self.input_beam is None: return

        try:
            if self.input_beam.getOEHistory(oe_number=0)._shadow_source_end.src.FSOURCE_DEPTH == 1:
                raise Exception("Source has no depth, calcution could be inconsistent")

            if self.kind_of_calculation == 1:
                congruence.checkFile(self.user_file)
            else:
                congruence.checkStrictlyPositiveNumber(self.factor, "Proportionality factor (k) [to eV/Å]")
                congruence.checkStrictlyPositiveNumber(self.central_value, "Central Energy/Wavelength Value [eV/Å]")

            beam_out = self.input_beam.duplicate()

            if self.kind_of_calculation == 0:
                for index in range(0, len(beam_out._beam.rays)):
                    if self.units == 0:
                        beam_out._beam.rays[index, 10] =  ShadowPhysics.getShadowKFromEnergy(self.central_value + self.factor*beam_out._beam.rays[index, 1])
                    else:
                        beam_out._beam.rays[index, 10] =  ShadowPhysics.getShadowKFromWavelength(self.central_value + self.factor*beam_out._beam.rays[index, 1])
            else:
                self.load_energy_distribution()

                for index in range(0, len(beam_out._beam.rays)):
                    if self.units == 0:
                        beam_out._beam.rays[index, 10] = ShadowPhysics.getShadowKFromEnergy(self.get_value_from_y(beam_out._beam.rays[index, 1]))
                    else:
                        beam_out._beam.rays[index, 10] =  ShadowPhysics.getShadowKFromWavelength(self.get_value_from_y(beam_out._beam.rays[index, 1]))

            self.send("Beam", beam_out)
        except Exception as exception:
                QtGui.QMessageBox.critical(self, "Error", str(exception), QtGui.QMessageBox.Ok)

                #raise exception

    def set_KindOfCalculation(self):
        self.kind_box_1.setVisible(self.kind_of_calculation==0)
        self.kind_box_2.setVisible(self.kind_of_calculation==1)

    def selectUserFile(self):
        self.le_user_file.setText(oasysgui.selectFileFromDialog(self, self.user_file, "Open External File With Energy/Wavelength vs. Y"))

    def get_value_from_y(self, y_value):
        return numpy.interp(y_value, self.user_distribution_values[0], self.user_distribution_values[1])

    def load_energy_distribution(self):
        self.user_distribution_values = numpy.loadtxt(self.user_file, unpack=True)


if __name__ == "__main__":
    a = QApplication(sys.argv)
    ow = EnergyCirp()
    ow.show()
    a.exec_()
    ow.saveSettings()
