import numpy

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.util.shadow_util import ShadowPlot, ShadowPhysics
from orangecontrib.shadow.widgets.plots import ow_histogram

from orangewidget import gui
from orangewidget.settings import Setting
from oasys.widgets import gui as oasysgui

import PyMca5.PyMcaGui.plotting.PlotWindow as PlotWindow

import matplotlib.pyplot as plt
import matplotlib.colors as colors
import matplotlib.colorbar as colorbar
import matplotlib.cm as cmx

class WavefrontHistogram(ow_histogram.Histogram):
    name = "Wavefront Histogram"
    description = "Wavefront Tools: Wavefront Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Wavefront Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    spectro_variable = Setting(0)
    spectro_number_of_bins = Setting(9)
    spectro_plot_canvas = None

    plotted_beam = None

    def __init__(self):
        super().__init__()

        tab_spe = oasysgui.createTabPage(self.tabs_setting, "Spectroscopy Settings")

        spectro_box = oasysgui.widgetBox(tab_spe, "Spectroscopy settings", addSpace=True, orientation="vertical", height=100)

        gui.comboBox(spectro_box, self, "spectro_variable", label="Spectroscopy Variable", labelWidth=300,
                     items=["Energy",
                            "Wavelength"],
                     sendSelectedValue=False, orientation="horizontal")

        gui.comboBox(spectro_box, self, "spectro_number_of_bins", label="Number of Bins", labelWidth=350,
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
                self.spectro_plot_canvas.setDefaultPlotLines(True)
                self.spectro_plot_canvas.setDefaultPlotPoints(False)
                self.spectro_plot_canvas.setZoomModeEnabled(True)
                self.spectro_plot_canvas.setMinimumWidth(673)
                self.spectro_plot_canvas.setMaximumWidth(673)
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

            x, auto_title, xum = self.get_titles()

            if self.plotted_beam is None: self.plotted_beam = self.input_beam

            xrange  = self.get_range(self.plotted_beam._beam, x)

            min_k = numpy.min(self.plotted_beam._beam.rays[:, 10])
            max_k = numpy.max(self.plotted_beam._beam.rays[:, 10])

            if self.spectro_variable == 0: #Energy
                energy_min = ShadowPhysics.getEnergyFromShadowK(min_k)
                energy_max = ShadowPhysics.getEnergyFromShadowK(max_k)

                bins = energy_min + numpy.arange(0, number_of_bins + 1)*((energy_max-energy_min)/number_of_bins)
                normalization = colors.Normalize(vmin=energy_min, vmax=energy_max)
            else: #wavelength
                wavelength_min = ShadowPhysics.getWavelengthfromShadowK(max_k)
                wavelength_max = ShadowPhysics.getWavelengthfromShadowK(min_k)

                bins = wavelength_min + numpy.arange(0, number_of_bins + 1)*((wavelength_max-wavelength_min)/number_of_bins)
                normalization = colors.Normalize(vmin=wavelength_min, vmax=wavelength_max)

            scalarMap = cmx.ScalarMappable(norm=normalization, cmap=self.color_map)

            cb1 = colorbar.ColorbarBase(ax3,
                                        cmap=self.color_map,
                                        norm=normalization,
                                        orientation='vertical')

            if self.spectro_variable == 0: #Energy
                cb1.set_label('Energy [eV]')
            else:
                cb1.set_label('Wavelength [Å]')

            go = numpy.where(self.plotted_beam._beam.rays[:, 9] == 1)
            lo = numpy.where(self.plotted_beam._beam.rays[:, 9] != 1)

            rays_to_plot = self.plotted_beam._beam.rays

            if self.rays == 1:
                rays_to_plot = self.plotted_beam._beam.rays[go]
            elif self.rays == 2:
                rays_to_plot = self.plotted_beam._beam.rays[lo]

            factor_x = ShadowPlot.get_factor(x, self.workspace_units_to_cm)

            for index in range (0, number_of_bins):
                min_value = bins[index]
                max_value = bins[index+1]

                if index < number_of_bins-1:
                    if self.spectro_variable == 0: #Energy
                        cursor = numpy.where((numpy.round(ShadowPhysics.getEnergyFromShadowK(rays_to_plot[:, 10]), 4) >= numpy.round(min_value, 4)) &
                                             (numpy.round(ShadowPhysics.getEnergyFromShadowK(rays_to_plot[:, 10]), 4) < numpy.round(max_value, 4)))
                    else:
                        cursor = numpy.where((numpy.round(ShadowPhysics.getWavelengthfromShadowK(rays_to_plot[:, 10]), 4) >= numpy.round(min_value, 4)) &
                                             (numpy.round(ShadowPhysics.getWavelengthfromShadowK(rays_to_plot[:, 10]), 4) < numpy.round(max_value, 4)))
                else:
                    if self.spectro_variable == 0: #Energy
                        cursor = numpy.where((numpy.round(ShadowPhysics.getEnergyFromShadowK(rays_to_plot[:, 10]), 4) >= numpy.round(min_value, 4)) &
                                             (numpy.round(ShadowPhysics.getEnergyFromShadowK(rays_to_plot[:, 10]), 4) <= numpy.round(max_value, 4)))
                    else:
                        cursor = numpy.where((numpy.round(ShadowPhysics.getWavelengthfromShadowK(rays_to_plot[:, 10]), 4) >= numpy.round(min_value, 4)) &
                                             (numpy.round(ShadowPhysics.getWavelengthfromShadowK(rays_to_plot[:, 10]), 4) <= numpy.round(max_value, 4)))

                color = scalarMap.to_rgba((bins[index] + bins[index+1])/2)

                if index == 0: self.spectro_plot_canvas.setActiveCurveColor(color=color)

                self.replace_spectro_fig(rays_to_plot[cursor], x, factor_x, xrange,
                                         title=self.title + str(index), color=color)

            self.spectro_plot_canvas.setDrawModeEnabled(True, 'rectangle')
            self.spectro_plot_canvas.setGraphXLimits(xrange[0]*factor_x, xrange[1]*factor_x)
            self.spectro_plot_canvas.setGraphXLabel(auto_title)
            self.spectro_plot_canvas.replot()

    def replace_spectro_fig(self, rays_to_plot, var_x, factor_x, xrange, title, color):
        try:
            beam = ShadowBeam()
            beam._beam.rays = rays_to_plot

            ticket = beam._beam.histo1(var_x, nbins=self.number_of_bins, xrange=xrange, nolost=self.rays, ref=self.weight_column_index)

            if self.weight_column_index != 0:
                self.spectro_plot_canvas.setGraphYLabel("Number of rays weighted by " + ShadowPlot.get_shadow_label(self.weight_column_index))
            else:
                self.spectro_plot_canvas.setGraphYLabel("Number of Rays")

            histogram = ticket['histogram_path']
            bins = ticket['bin_path']*factor_x

            self.spectro_plot_canvas.addCurve(bins, histogram, title, symbol='', color=color, replace=False) #'+', '^', ','
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

