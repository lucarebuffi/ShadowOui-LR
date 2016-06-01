import numpy

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowPlot
from orangecontrib.shadow.widgets.plots import ow_plot_xy

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui
from oasys.widgets import congruence

import PyMca5.PyMcaGui.plotting.PlotWindow as PlotWindow

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.colorbar as colorbar
import matplotlib.cm as cmx

class WavefrontPlotXY(ow_plot_xy.PlotXY):

    name = "Wavefront Plot XY"
    description = "Wavefront Tools: Wavefront Plot XY"
    icon = "icons/plot_xy.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 5
    category = "Wavefront Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    spectro_number_of_bins = Setting(0)
    spectro_plot_canvas = None

    plotted_beam = None

    def __init__(self):
        super().__init__()

        tab_spe = oasysgui.createTabPage(self.tabs_setting, "Spectroscopy Settings")

        spectro_box = oasysgui.widgetBox(tab_spe, "Spectroscopy settings", addSpace=True, orientation="vertical", height=100)

        gui.comboBox(spectro_box, self, "spectro_number_of_bins", label="Number of Bins",labelWidth=350,
                     items=["1",
                            "2",
                            "3",
                            "4",
                            "5",
                            "6",
                            "7",
                            "8",
                            "9",
                            "10"],
                     sendSelectedValue=False, orientation="horizontal")

        spectro_plot_tab = oasysgui.widgetBox(self.main_tabs, addToLayout=0, margin=4)
        self.main_tabs.insertTab(1, spectro_plot_tab, "Spectroscopy Plots")

        self.spectro_image_box = gui.widgetBox(spectro_plot_tab, "Spectroscopy Plot Result", addSpace=True, orientation="vertical")
        self.spectro_image_box.setFixedHeight(self.IMAGE_HEIGHT)
        self.spectro_image_box.setFixedWidth(self.IMAGE_WIDTH)

        self.color_map = plt.cm.get_cmap('Blues')


    def plot_results(self):
        self.plotted_beam = None

        if super().plot_results():
            if self.spectro_plot_canvas is None:
                self.spectro_plot_canvas = PlotWindow.PlotWindow(roi=False, control=False, position=False, plugins=False, logx=False, logy=False)
                self.spectro_plot_canvas.setDefaultPlotLines(False)
                self.spectro_plot_canvas.setMinimumWidth(673)
                self.spectro_plot_canvas.setMaximumWidth(673)
                self.spectro_plot_canvas.setZoomModeEnabled(True)
                pos = self.spectro_plot_canvas._plot.graph.ax.get_position()
                self.spectro_plot_canvas._plot.graph.ax.set_position([pos.x0, pos.y0 , pos.width*0.86, pos.height])
                pos = self.spectro_plot_canvas._plot.graph.ax2.get_position()
                self.spectro_plot_canvas._plot.graph.ax2.set_position([pos.x0, pos.y0 , pos.width*0.86, pos.height])
                ax3 = self.spectro_plot_canvas._plot.graph.fig.add_axes([.82, .15, .05, .75])

                self.spectro_image_box.layout().addWidget(self.spectro_plot_canvas)
            else:
                self.spectro_plot_canvas.clear()
                ax3 = self.spectro_plot_canvas._plot.graph.fig.axes[-1]
                ax3.cla()


            number_of_bins = self.spectro_number_of_bins + 1

            x, y, auto_x_title, auto_y_title, xum, yum = self.get_titles()

            if self.plotted_beam is None: self.plotted_beam = self.input_beam

            xrange, yrange = self.get_ranges(self.plotted_beam._beam, x, y)

            min_k = numpy.min(self.plotted_beam._beam.rays[:, 10])
            max_k = numpy.max(self.plotted_beam._beam.rays[:, 10])

            bins = min_k + numpy.arange(0, number_of_bins + 1)*((max_k-min_k)/number_of_bins)

            normalization = colors.Normalize(vmin=min_k, vmax=max_k)
            scalarMap = cmx.ScalarMappable(norm=normalization, cmap=self.color_map)

            cb1 = colorbar.ColorbarBase(ax3,
                                        cmap=self.color_map,
                                        norm=normalization,
                                        orientation='vertical')
            cb1.set_label('Wavevector modulus |k| [Å-1]')

            go = numpy.where(self.plotted_beam._beam.rays[:, 9] == 1)
            lo = numpy.where(self.plotted_beam._beam.rays[:, 9] != 1)

            rays_to_plot = self.plotted_beam._beam.rays

            if self.rays == 1:
                rays_to_plot = self.plotted_beam._beam.rays[go]
            elif self.rays == 2:
                rays_to_plot = self.plotted_beam._beam.rays[lo]

            factor_x = ShadowPlot.get_factor(x, self.workspace_units_to_cm)
            factor_y = ShadowPlot.get_factor(y, self.workspace_units_to_cm)

            for index in range (0, number_of_bins):
                min_value = bins[index]
                max_value = bins[index+1]

                if index < number_of_bins-1:
                    cursor = numpy.where((numpy.round(rays_to_plot[:, 10], 4) >= numpy.round(min_value, 4)) &
                                         (numpy.round(rays_to_plot[:, 10], 4) < numpy.round(max_value, 4)))
                else:
                    cursor = numpy.where((numpy.round(rays_to_plot[:, 10], 4) >= numpy.round(min_value, 4)) &
                                         (numpy.round(rays_to_plot[:, 10], 4) <= numpy.round(max_value, 4)))

                color = scalarMap.to_rgba((bins[index] + bins[index+1])/2)

                if index == 0: self.spectro_plot_canvas.setActiveCurveColor(color=color)

                self.replace_spectro_fig(rays_to_plot[cursor], x, y, factor_x, factor_y,
                                         title=self.title + str(index), color=color)

            self.spectro_plot_canvas.setGraphXLimits(xrange[0]*factor_x, xrange[1]*factor_x)
            self.spectro_plot_canvas.setGraphYLimits(yrange[0]*factor_y, yrange[1]*factor_y)
            self.spectro_plot_canvas.setGraphXLabel(auto_x_title)
            self.spectro_plot_canvas.setGraphYLabel(auto_y_title)
            self.spectro_plot_canvas.replot()

    def replace_spectro_fig(self, rays_to_plot, var_x, var_y,  factor_x, factor_y, title, color):
        try:
            col1 = rays_to_plot[:, var_x-1]*factor_x
            col2 = rays_to_plot[:, var_y-1]*factor_y

            self.spectro_plot_canvas.addCurve(col1, col2, title, symbol='.', color=color, replace=False) #'+', '^', ','
        except Exception as e:
            print(e)
            raise Exception("Data not plottable: No good rays or bad content")

    def clearResults(self):
        if super().clearResults():
            if not self.spectro_plot_canvas is None:
                self.spectro_plot_canvas.clear()

    def retrace_beam(self, new_shadow_beam, dist):
        for index in range(0, len(new_shadow_beam._beam.rays)):
            new_shadow_beam._beam.rays[index, 0] = new_shadow_beam._beam.rays[index, 0] + dist*new_shadow_beam._beam.rays[index, 3]
            new_shadow_beam._beam.rays[index, 1] = new_shadow_beam._beam.rays[index, 1] + dist*new_shadow_beam._beam.rays[index, 4]
            new_shadow_beam._beam.rays[index, 2] = new_shadow_beam._beam.rays[index, 2] + dist*new_shadow_beam._beam.rays[index, 5]
            new_shadow_beam._beam.rays[index, 12] = new_shadow_beam._beam.rays[index, 12] + dist

        self.plotted_beam = new_shadow_beam

from PyQt4.QtGui import QApplication
from random import Random

if __name__ == "__main__":
    print(numpy.arange(1, 10))

    '''

    app = QApplication([])

    spectro_plot_canvas = PlotWindow.PlotWindow(roi=False, control=False, position=False, plugins=False, logx=False, logy=False)
    spectro_plot_canvas.setDefaultPlotLines(True)
    spectro_plot_canvas.setMinimumWidth(673)
    spectro_plot_canvas.setMaximumWidth(673)
    spectro_plot_canvas.setDrawModeEnabled(True, 'rectangle')
    spectro_plot_canvas.setZoomModeEnabled(True)

    color_map = plt.cm.get_cmap('Blues')
    normalization = colors.Normalize(vmin=0, vmax=100)
    scalarMap = cmx.ScalarMappable(norm=normalization, cmap=color_map)

    random = Random()

    for index in range (0, 100):
        if index == 0:  spectro_plot_canvas.setActiveCurveColor(color=scalarMap.to_rgba(0))

        spectro_plot_canvas.addCurve([index], [index+100], "ciao" + str(index), symbol='.', color=scalarMap.to_rgba(int(100*random.random())), replace=False)

    spectro_plot_canvas.show()

    spectro_plot_canvas.setGraphXLimits(-1, 100, replot=True)
    spectro_plot_canvas.setGraphYLimits(99, 200, replot=True)

    app.exec_()
    '''