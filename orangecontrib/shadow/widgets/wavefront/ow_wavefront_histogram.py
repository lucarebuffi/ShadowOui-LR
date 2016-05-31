import numpy

from orangecontrib.shadow.util.shadow_objects import ShadowBeam
from orangecontrib.shadow.widgets.plots.ow_histogram import Histogram

class WavefrontHistogram(Histogram):
    name = "Wavefront Histogram"
    description = "Wavefront Tools: Wavefront Histogram"
    icon = "icons/histogram.png"
    maintainer = "Luca Rebuffi"
    maintainer_email = "luca.rebuffi(@at@)elettra.eu"
    priority = 4
    category = "Display Data Tools"
    keywords = ["data", "file", "load", "read"]

    inputs = [("Input Beam", ShadowBeam, "setBeam")]

    def __init__(self):
        super().__init__()

    def retrace_beam(self, new_shadow_beam, dist):
        reference_distance_along_y = dist # form origin point of image plane to origin point of new image plane
    
        for index in range(0, len(new_shadow_beam._beam.rays)): 
          
            distance_along_ray_direction = numpy.abs(reference_distance_along_y/new_shadow_beam._beam.rays[index, 4])
            sign = numpy.sign(reference_distance_along_y)
              
            new_shadow_beam._beam.rays[index, 0] = new_shadow_beam._beam.rays[index, 0] + sign*distance_along_ray_direction*new_shadow_beam._beam.rays[index, 3]
            new_shadow_beam._beam.rays[index, 1] = new_shadow_beam._beam.rays[index, 1] + sign*distance_along_ray_direction*new_shadow_beam._beam.rays[index, 4]
            new_shadow_beam._beam.rays[index, 2] = new_shadow_beam._beam.rays[index, 2] + sign*distance_along_ray_direction*new_shadow_beam._beam.rays[index, 5]
            new_shadow_beam._beam.rays[index, 12] = new_shadow_beam._beam.rays[index, 12] + sign*distance_along_ray_direction
