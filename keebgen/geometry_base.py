from abc import ABC, abstractmethod
import solid as sl
import numpy as np
from functools import partialmethod

from . import geometry_utils as utils

# base class for all solids
class Solid(ABC):
    @abstractmethod
    def __init__(self):
        # check if defined
        try:
            self._anchors
        except AttributeError:
            # not defined
            # define arbitrary anchors for compatibility
            self._anchors = Hull(((0, 0, 0),
                                  (1, 0, 0),
                                  (1, 1, 0),
                                  (0, 1, 0),
                                  (0, 0, 1),
                                  (1, 0, 1),
                                  (1, 1, 1),
                                  (0, 1, 1)))
        # check if defined
        try:
            self._solid
        except AttributeError:
            # not defined
            # define arbitrary solid for compatibility
            self._solid = sl.part()


    # child __init__() functions responsible for populating self._solid and self._anchors
    def solid(self):
        return self._solid

    def translate(self, x=0, y=0, z=0):
        self._solid = sl.translate([x,y,z])(self._solid)
        self._anchors.translate(x,y,z)

    def rotate(self, x=0, y=0, z=0, degrees=True):
        if degrees == False:
            x = utils.rad2deg(x)
            y = utils.rad2deg(y)
            z = utils.rad2deg(z)
        self._solid = sl.rotate([x, y, z])(self._solid)
        self._anchors.rotate(x,y,z)

    def anchors(self):
        return self._anchors


class Assembly(ABC):
    @abstractmethod
    def __init__(self):
        pass

    # child __init__() functions responsible for populating self._solid and self._anchors
    def solid(self):
        out_solid = sl.part()
        for part in self._parts.values():
            out_solid += part.solid()
        return out_solid

    def translate(self, x=0, y=0, z=0):
        self._anchors.translate(x,y,z)
        for part in self._parts.values():
            part.translate(x, y, z)

    def rotate(self, x=0, y=0, z=0, degrees=True):
        self._anchors.rotate(x, y, z, degrees)
        for part in self._parts.values():
            part.rotate(x, y, z, degrees)

    def anchors(self, part_name=None):
        # return assembly anchors if no part specified
        if part_name == None:
            return self._anchors
        # return the anchors of the requested part
        if self._parts.get(part_name):
            return self._parts[part_name].anchors()
        return None

    def part(self, part_name):
        return self._parts.get(part_name)


# top, bottom, left, right are relative to the user sitting at the keyboard
class Hull(object):
    def __init__(self, corners):
        # assumes a volume. No more than 4 corners should be in plane or behavior is undefined
        """
        sorted corner ordering
           3-------7
          /|      /|
         / |     / | Z
        2--|----6  |
        |  1----|--5
        | /     | / Y
        0-------4
            X
        """
        assert len(corners) == 8
        self.corners = np.array(self._sort_corners(corners)).reshape((2,2,2,3))
        self._output_shape = (4,3)

    def _sort_corners(self, corners):
        assert len(corners) == 8
        top_corners = sorted(corners, key = lambda x: x[2])[:4]
        bottom_corners = sorted(corners, key = lambda x: x[2], reverse=True)[:4]
        front_top_corners = sorted(top_corners, key = lambda x: x[1])[:2]
        back_top_corners = sorted(top_corners, key = lambda x: x[1], reverse=True)[:2]
        front_bottom_corners = sorted(bottom_corners, key = lambda x: x[1])[:2]
        back_bottom_corners = sorted(bottom_corners, key = lambda x: x[1], reverse=True)[:2]

        # sorted corners match indices in __init__ ascii art
        sorted_corners = []
        # left
        sorted_corners.append(sorted(back_bottom_corners, key=lambda x: x[0])[0])
        sorted_corners.append(sorted(front_bottom_corners, key=lambda x: x[0])[0])
        sorted_corners.append(sorted(back_top_corners, key=lambda x: x[0])[0])
        sorted_corners.append(sorted(front_top_corners, key=lambda x: x[0])[0])
        # right
        sorted_corners.append(sorted(back_bottom_corners, key=lambda x: x[0])[1])
        sorted_corners.append(sorted(front_bottom_corners, key=lambda x: x[0])[1])
        sorted_corners.append(sorted(back_top_corners, key=lambda x: x[0])[1])
        sorted_corners.append(sorted(front_top_corners, key=lambda x: x[0])[1])
        return sorted_corners

    def _get_side(self, slice):
        coords =  self.corners[slice].reshape(self._output_shape)
        return set(tuple(x) for x in coords)

    def translate(self, x=0, y=0, z=0):
        for i in range(len(self.corners)):
            for j in range(len(self.corners[i])):
                for k in range(len(self.corners[i][j])):
                    self.corners[i,j,k] = utils.translate_point(self.corners[i,j,k], (x,y,z))

    def rotate(self, x=0, y=0, z=0, degrees=True):
        for i in range(len(self.corners)):
            for j in range(len(self.corners[i])):
                for k in range(len(self.corners[i][j])):
                    self.corners[i,j,k] = np.array(utils.rotate_point(self.corners[i,j,k], (x,y,z), degrees))

    right  = partialmethod(_get_side, np.s_[1,:,:])
    left   = partialmethod(_get_side, np.s_[0,:,:])
    bottom    = partialmethod(_get_side, np.s_[:,1,:])
    top = partialmethod(_get_side, np.s_[:,0,:])
    back  = partialmethod(_get_side, np.s_[:,:,1])
    front = partialmethod(_get_side, np.s_[:,:,0])
