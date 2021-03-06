from abc import abstractmethod
from keebgen.geometry_base import Assembly

# TODO remove this when configs updated
import configparser

from keebgen.key_column import ConcaveOrtholinearColumn
from keebgen.connector import Connector
from keebgen.geometry_base import Hull

class Keyboard(Assembly):
    @abstractmethod
    def __init__(self):
        super().__init__()


class DactylManuform(Keyboard):
    def __init__(self, config, col_config, key_config, socket_config):
        super().__init__()

        # TODO add config parsing. this is terrible right now
        # there should ideally be a different column config for each row, but this will do for proof of concept
        # all of these numbers should come from the config file or default config
        # TODO will want different spacing for end cols if they are tilted
        num_cols = 6
        index_radius = 56.4
        middle_radius = 65.0
        ring_radius = 64.0
        pinky_radius = 48.9
        section_name = 'column'
        col_configs = []
        for col in range(num_cols):
            new_conf = configparser.ConfigParser()
            new_conf.add_section(section_name)
            for key in col_config:
                new_conf.set(section_name, key, col_config.get(key))
            # add extra row a t bottom for middle and ring fingers

            if col == 2 or col == 3:
                new_conf.set(section_name, 'num_keys', str(5))
                new_conf.set(section_name, 'home_index', str(2))

            # set side lean
            if col == 0:
                new_conf.set(section_name, 'key_side_lean', str(25))
            elif col == num_cols-1:
                new_conf.set(section_name, 'key_side_lean', str(-25))

            # set radius by finger
            if col <= 1:
                new_conf.set(section_name, 'radius', str(index_radius))
            elif col == 2:
                new_conf.set(section_name, 'radius', str(middle_radius))
            elif col == 3:
                new_conf.set(section_name, 'radius', str(ring_radius))
            else:
                new_conf.set(section_name, 'radius', str(pinky_radius))

            col_configs.append(new_conf[section_name])

        col_x_spacing = 19.0 #mm

        sub_pointer_y_off = 0
        pointer_y_off = 0
        middle_y_off = 11
        ring_y_off = 3
        pinky_y_off = -19
        post_pinky_y_off = pinky_y_off

        sub_pointer_z_off = 3
        pointer_z_off = 0
        middle_z_off = 5
        ring_z_off = -2.5
        pinky_z_off = -6.5
        post_pinky_z_off = pinky_z_off + 3


        self._parts = {}
        prev_name = None
        connector_count = 0
        for col_num, col_config in enumerate(col_configs):
            name = col_num
            self._parts[name] = ConcaveOrtholinearColumn(col_config, key_config, socket_config)

            #TODO this should be part of the config
            col_fudge = 0
            if col_num < 1:
                col_fudge = 3.5
                y_off = sub_pointer_y_off
                z_off = sub_pointer_z_off
            elif col_num == 1:
                y_off = pointer_y_off
                z_off = pointer_z_off
            elif col_num == 2:
                y_off = middle_y_off
                z_off = middle_z_off
            elif col_num == 3:
                y_off = ring_y_off
                z_off = ring_z_off
            elif col_num == 4:
                y_off = pinky_y_off
                z_off = pinky_z_off
            else:
                col_fudge = -3.5
                y_off = post_pinky_y_off
                z_off = post_pinky_z_off

            # all column positioning must happen before the connectors are made
            shift = col_num - 1
            self._parts[name].translate(col_x_spacing*shift+col_fudge, y_off, z_off)

            def add_connector(*args):
                self._parts['connector'+str(connector_count)] = Connector(*args)
                connector_count += 1

            if prev_name is not None:
                # add connectors between previous col and this col
                # must check if row in this col existed in prev cal and vv.
                prev_col = self._parts[prev_name]
                cur_col = self._parts[name]

                #TODO make this prettier
                prev_col_prev_anchors = None
                cur_col_prev_anchors = None
                for row in range(-6, 6):
                    prev_col_key = prev_col.part(row)
                    cur_col_key = cur_col.part(row)

                    prev_col_anchors = None
                    if prev_col_key is not None:
                        prev_col_anchors = prev_col_key.anchors('socket')
                    cur_col_anchors = None
                    if cur_col_key is not None:
                        cur_col_anchors = cur_col_key.anchors('socket')

                    # TODO this is really annoying
                    # naming is bad too, "connect connectors"

                    # normal case, both connectors exist
                    # connect adjacent socket edges
                    if prev_col_anchors and cur_col_anchors:
                        self._parts['connector'+str(connector_count)] = Connector(
                                prev_col_anchors.right(),
                                cur_col_anchors.left())
                        connector_count += 1

                    # cur and prev rows exist for both cols
                    # connect the connectors that are between the cur and prev rows for each col
                    if prev_col_anchors and prev_col_prev_anchors and cur_col_anchors and cur_col_prev_anchors:
                        self._parts['connector'+str(connector_count)] = Connector(
                                prev_col_anchors.right() & prev_col_anchors.back(),
                                prev_col_prev_anchors.right() & prev_col_prev_anchors.front(),
                                cur_col_anchors.left() & cur_col_anchors.back(),
                                cur_col_prev_anchors.left() & cur_col_prev_anchors.front())
                        connector_count += 1


                    # these four conditionals handle the end conditions when one col is shorter than the other

                    # prev_col one longer on bottom
                    if prev_col_anchors and prev_col_prev_anchors and cur_col_anchors and not cur_col_prev_anchors:
                        self._parts['connector'+str(connector_count)] = Connector(
                                prev_col_anchors.right() & prev_col_anchors.back(),
                                prev_col_prev_anchors.right(),
                                cur_col_anchors.left() & cur_col_anchors.back())
                        connector_count += 1

                    # cur_col one longer on bottom
                    if prev_col_anchors and not prev_col_prev_anchors and cur_col_anchors and cur_col_prev_anchors:
                        self._parts['connector'+str(connector_count)] = Connector(
                                prev_col_anchors.right() & prev_col_anchors.bottom(),
                                cur_col_anchors.left() & cur_col_anchors.bottom(),
                                cur_col_prev_anchors.left())
                        connector_count += 1

                    # prev_col one longer on top
                    if prev_col_anchors and prev_col_prev_anchors and not cur_col_anchors and cur_col_prev_anchors:
                        self._parts['connector'+str(connector_count)] = Connector(
                                prev_col_anchors.right(),
                                prev_col_prev_anchors.right() & prev_col_prev_anchors.front(),
                                cur_col_prev_anchors.left() & cur_col_prev_anchors.front())
                        connector_count += 1

                    # cur_col one longer on top
                    if not prev_col_anchors and prev_col_prev_anchors and cur_col_anchors and cur_col_prev_anchors:
                        self._parts['connector'+str(connector_count)] = Connector(
                                prev_col_prev_anchors.right() & prev_col_prev_anchors.front(),
                                cur_col_anchors.left(),
                                cur_col_prev_anchors.left() & cur_col_prev_anchors.front())
                        connector_count += 1





                    prev_col_prev_anchors = prev_col_anchors
                    cur_col_prev_anchors = cur_col_anchors

            prev_name = name
#
#
#
#        colum
#
#        #TODO: add everything

