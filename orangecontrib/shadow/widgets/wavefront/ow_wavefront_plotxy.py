import numpy

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.widgets.plots import ow_plot_xy

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

    def __init__(self):
        super().__init__()

    def retrace_beam(self, new_shadow_beam, dist):
        for index in range(0, len(new_shadow_beam._beam.rays)):
            new_shadow_beam._beam.rays[index, 0] = new_shadow_beam._beam.rays[index, 0] + dist*new_shadow_beam._beam.rays[index, 3]
            new_shadow_beam._beam.rays[index, 1] = new_shadow_beam._beam.rays[index, 1] + dist*new_shadow_beam._beam.rays[index, 4]
            new_shadow_beam._beam.rays[index, 2] = new_shadow_beam._beam.rays[index, 2] + dist*new_shadow_beam._beam.rays[index, 5]
            new_shadow_beam._beam.rays[index, 12] = new_shadow_beam._beam.rays[index, 12] + dist
