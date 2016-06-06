import sys, numpy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

from PyQt4 import QtGui
from PyQt4.QtGui import QPalette, QColor, QFont

from orangecontrib.shadow.widgets.gui import ow_generic_element
from orangecontrib.shadow.util.shadow_objects import EmittingStream, TTYGrabber, ShadowTriggerIn, ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowCongruence

class WavefrontViewer(ow_generic_element.GenericElement):
    name = "Wavefront Viewer"
    description = "Wavefront Tools: Wavefront Viewer"
    icon = "icons/viewer.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 1
    category = "Wavefront Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    outputs = [{"name": "Beam",
                "type": ShadowBeam,
                "doc": "Shadow Beam",
                "id": "beam"},
               {"name": "Trigger",
                "type": ShadowTriggerIn,
                "doc": "Feedback signal to start a new beam simulation",
                "id": "Trigger"}]

    input_beam = None

    NONE_SPECIFIED = "NONE SPECIFIED"

    element_before = Setting(1)

    delta_angle_calculated = 0.0
    delta_angle_shadow = 0.0

    want_main_area = 1

    def __init__(self):
        super().__init__()

        button_box = oasysgui.widgetBox(self.controlArea, "", addSpace=False, orientation="horizontal")

        button = gui.button(button_box, self, "Reconstruct Wavefront", callback=self.reconstructWavefront)
        font = QFont(button.font())
        font.setBold(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Blue'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)

        button = gui.button(button_box, self, "Reset Fields", callback=self.callResetSettings)
        font = QFont(button.font())
        font.setItalic(True)
        button.setFont(font)
        palette = QPalette(button.palette())  # make a copy of the palette
        palette.setColor(QPalette.ButtonText, QColor('Dark Red'))
        button.setPalette(palette)  # assign new palette
        button.setFixedHeight(45)
        button.setFixedWidth(100)

        tabs_setting = oasysgui.tabWidget(self.controlArea)
        tabs_setting.setFixedHeight(self.TABS_AREA_HEIGHT)
        tabs_setting.setFixedWidth(self.CONTROL_AREA_WIDTH-5)

        tab_bas = oasysgui.createTabPage(tabs_setting, "Wavefront Viewer Setting")

        input_box = oasysgui.widgetBox(tab_bas, "Input Parameters", addSpace=False, orientation="vertical", width=375)

        oasysgui.lineEdit(input_box, self, "element_before", "Number of OEs before", labelWidth=300, valueType=int, orientation="horizontal")

        gui.separator(input_box, height=30)

        le_delta_angle_calculated = oasysgui.lineEdit(input_box, self, "delta_angle_calculated", "Delta Angle - Calculated  (deg)", labelWidth=250, valueType=float, orientation="horizontal")
        le_delta_angle_shadow = oasysgui.lineEdit(input_box, self, "delta_angle_shadow", "Delta Angle - From Shadow (deg)", labelWidth=250, valueType=float, orientation="horizontal")

        le_delta_angle_calculated.setReadOnly(True)
        le_delta_angle_shadow.setReadOnly(True)

    def callResetSettings(self):
        super().callResetSettings()
        self.setupUI()

    def checkFields(self):
        congruence.checkStrictlyPositiveNumber(self.element_before, "Number of OEs before")

    def reconstructWavefront(self):
        try:
            self.error(self.error_id)
            self.setStatusMessage("")
            self.progressBarInit()

            if ShadowCongruence.checkEmptyBeam(self.input_beam):
                if ShadowCongruence.checkGoodBeam(self.input_beam):
                    sys.stdout = EmittingStream(textWritten=self.writeStdOut)

                    self.progressBarSet(10)

                    self.checkFields()

                    self.setStatusMessage("Modifing coordinates to equal optical paths")

                    if self.trace_shadow:
                        grabber = TTYGrabber()
                        grabber.start()

                    self.progressBarSet(50)

                    beam_out = self.input_beam.duplicate()

                    reference_distance = 0.0

                    for history_element in beam_out.getOEHistory():
                        if not history_element._shadow_oe_end is None:
                            reference_distance += history_element._shadow_oe_end._oe.SSOUR + history_element._shadow_oe_end._oe.SIMAG

                    for index in range(0, len(beam_out._beam.rays)):
                        optical_path_difference = beam_out._beam.rays[index, 12] - reference_distance

                        beam_out._beam.rays[index, 0] = beam_out._beam.rays[index, 0] + optical_path_difference*beam_out._beam.rays[index, 3]
                        beam_out._beam.rays[index, 1] = beam_out._beam.rays[index, 1] + optical_path_difference*beam_out._beam.rays[index, 4]
                        beam_out._beam.rays[index, 2] = beam_out._beam.rays[index, 2] + optical_path_difference*beam_out._beam.rays[index, 5]
                        beam_out._beam.rays[index, 12] = reference_distance

                    last_element = beam_out.getOEHistory()[-self.element_before]

                    alpha = last_element._shadow_oe_end._oe.T_INCIDENCE
                    beta = last_element._shadow_oe_end._oe.T_REFLECTION

                    delta_calculated = numpy.round(numpy.degrees(numpy.arctan(numpy.tan(beta) - (numpy.sin(alpha)/numpy.cos(beta)))), 4)

                    # y max
                    cursor_1 = numpy.where(beam_out._beam.rays[:, 1]==numpy.max(beam_out._beam.rays[:, 1]))
                    cursor_2 = numpy.where(beam_out._beam.rays[:, 1]==numpy.min(beam_out._beam.rays[:, 1]))

                    point_1 = [beam_out._beam.rays[cursor_1, 2][0][0], beam_out._beam.rays[cursor_1, 1][0][0]]
                    point_2 = [beam_out._beam.rays[cursor_2, 2][0][0], beam_out._beam.rays[cursor_2, 1][0][0]]


                    delta_shadow = numpy.round(numpy.degrees(numpy.arctan((point_1[1]-point_2[1])/(point_1[0]-point_2[0]))), 4)

                    self.delta_angle_calculated = delta_calculated
                    self.delta_angle_shadow = delta_shadow

                    if self.trace_shadow:
                        grabber.stop()

                        for row in grabber.ttyData:
                            self.writeStdOut(row)

                    self.setStatusMessage("Plotting Results")

                    self.plot_results(beam_out)

                    self.setStatusMessage("")

                    self.send("Beam", beam_out)
                    self.send("Trigger", ShadowTriggerIn(new_beam=True))
                else:
                    raise Exception("Input Beam with no good rays")
            else:
                raise Exception("Empty Input Beam")

        except Exception as exception:
            QtGui.QMessageBox.critical(self, "QMessageBox.critical()",
                                       str(exception),
                                       QtGui.QMessageBox.Ok)

            self.error_id = self.error_id + 1
            self.error(self.error_id, "Exception occurred: " + str(exception))

        self.progressBarFinished()

    def setBeam(self, beam):
        self.onReceivingInput()

        if ShadowCongruence.checkEmptyBeam(beam):
            self.input_beam = beam

            if self.is_automatic_run:
                self.reconstructWavefront()


    def getVariablestoPlot(self):
        return [[3, 2], [1, 2], [1, 3], [4, 6], 13]

    def getTitles(self):
        return ["Z,Y", "X,Y", "X,Z", "X',Z'", "Optical Path"]

    def getXTitles(self):
        return ["Z [" + self.workspace_units_label + "]",
                "X [" + self.workspace_units_label + "]",
                "X [" + self.workspace_units_label + "]",
                "X' [rad]", "Optical Path [" + self.workspace_units_label + "]"]

    def getYTitles(self):
        return ["Y [" + self.workspace_units_label + "]",
                "Y [" + self.workspace_units_label + "]",
                "Z [" + self.workspace_units_label + "]",
                "Z' [rad]",
                "Number of Rays"]

    def getXUM(self):
        return ["Z [" + self.workspace_units_label + "]",
                "X [" + self.workspace_units_label + "]",
                "X [" + self.workspace_units_label + "]",
                "X' [rad]", "Optical Path [" + self.workspace_units_label + "]"]

    def getYUM(self):
        return ["Y [" + self.workspace_units_label + "]",
                "Y [" + self.workspace_units_label + "]",
                "Z [" + self.workspace_units_label + "]",
                "Z' [rad]",
                None]

    def getConversionActive(self):
        return False


