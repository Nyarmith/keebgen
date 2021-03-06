from abc import abstractmethod
import numpy as np
import solid as sl

from .geometry_base import Assembly, Hull
from . import geometry_utils as utils
from . import key_assy
from .connector import Connector

class KeyColumn(Assembly):
    @abstractmethod
    def __init__(self):
        super(KeyColumn, self).__init__()

class ConcaveOrtholinearColumn(KeyColumn):
    def __init__(self, config, key_config, socket_config):
        super(ConcaveOrtholinearColumn, self).__init__()

        radius = config.getfloat('radius')
        gap = config.getfloat('key_gap')
        num_keys = config.getint('num_keys')
        home_index = config.getint('home_index')
        key_lean = config.getfloat('key_side_lean')
        home_angle = config.getfloat('home_tiltback_angle')

        self._parts = {}
        prev_anchors = None
        first_key_name = None
        last_key_name = None
        for i in range(num_keys):
            r = 4-i + (home_index-1)
            rotation_index = i - home_index
            if r <= 0:
                r = 1
            if r > 4:
                r = 4

            # for alignment across rows, name keys by index from the home row. negative is below home
            key_name = rotation_index
            if first_key_name is None:
                first_key_name = key_name
            last_key_name = key_name


            # add a key_assy to the parts
            self._parts[key_name] = (key_assy.FaceAlignedKey(key_config, socket_config, r))
            self._parts[key_name].rotate(0, key_lean, 0)
            self._parts[key_name].translate(0, 0, -radius)

            # get y values from top face of the key
            anchors = self._parts[key_name].anchors()
            center_top_front_anchor = utils.mean_point(anchors.top() & anchors.front())
            center_top_back_anchor = utils.mean_point(anchors.top() & anchors.back())
            y_front = center_top_front_anchor[1]
            y_back = center_top_back_anchor[1]

            # find rotation angle to create one gap width between adjacent keys
            one_offset = np.arctan(abs(y_front)/radius) + np.arctan(abs(y_back)/radius) + 2 * np.arctan(gap/(2*radius))

            rotation_angle = one_offset * -rotation_index
            self._parts[key_name].rotate(-rotation_angle, 0, 0, degrees=False)
            self._parts[key_name].translate(0, 0, radius)

            if prev_anchors is not None:
                connector_name = 'connector'+str(i-1)+'to'+str(i)
                self._parts[connector_name] = Connector(self._parts[key_name].anchors('socket').back(), prev_anchors)

            # remember where to connect the next key
            prev_anchors = self._parts[key_name].anchors('socket').front()

        self._anchors = Hull(self._parts[first_key_name].anchors('socket').back() | self._parts[last_key_name].anchors('socket').front())
        self.rotate(home_angle, 0, 0, degrees=True)
