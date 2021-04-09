import glob
from io import BytesIO
import utm
import pytz
import datetime
import os
import sys
from typing import Optional, Tuple, List

from cartopy.io.img_tiles import OSM, GoogleWTS
import matplotlib.pyplot as plt
import numpy as np
import cartopy.crs as ccrs
from matplotlib import patheffects
from matplotlib.transforms import Bbox
from shapely.geometry import Polygon

from display.coordinate_utilities import calculate_distance_lat_lon, calculate_bearing, \
    calculate_fractional_distance_point_lat_lon, get_heading_difference, project_position_lat_lon, \
    create_perpendicular_line_at_end_lonlat
from display.wind_utilities import calculate_ground_speed_combined, calculate_wind_correction_angle

if __name__ == "__main__":
    sys.path.append("../")
    os.environ.setdefault("DJANGO_SETTINGS_MODULE", "live_tracking_map.settings")
    import django

    django.setup()

from display.models import Route, Contestant, NavigationTask
from display.waypoint import Waypoint

LINEWIDTH = 0.5


def get_course_position(start: Tuple[float, float], finish: Tuple[float, float], left_side: bool, distance_nm: float) -> \
        Tuple[float, float]:
    centre = calculate_fractional_distance_point_lat_lon(start, finish, 0.5)
    return centre
    # positions = create_perpendicular_line_at_end(*reversed(start), *reversed(centre), distance_nm * 1852)
    # if left_side:
    #     return tuple(reversed(positions[0]))
    # return tuple(reversed(positions[1]))


def create_minute_lines(start: Tuple[float, float], finish: Tuple[float, float], air_speed: float, wind_speed: float,
                        wind_direction: float, gate_start_time: datetime.datetime, route_start_time: datetime.datetime,
                        resolution_seconds: int = 60,
                        line_width_nm=0.5) -> List[
    Tuple[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float], datetime.datetime]]:
    """

    :param start:
    :param finish:
    :param air_speed:
    :param wind_speed:
    :param wind_direction:
    :param gate_start_time: The time of the contestant crosses out from the gate (so remember to factor in procedure turns in that time)
    :param route_start_time:
    :param resolution_seconds:
    :param line_width_nm:
    :return:
    """
    bearing = calculate_bearing(start, finish)
    ground_speed = calculate_ground_speed_combined(bearing, air_speed, wind_speed,
                                                   wind_direction)
    length = calculate_distance_lat_lon(start, finish) / 1852  # NM
    leg_time = length / ground_speed * 3600  # seconds

    def time_to_position(seconds):
        return calculate_fractional_distance_point_lat_lon(start, finish, seconds / leg_time)

    lines = []
    gate_start_elapsed = (gate_start_time - route_start_time).total_seconds()
    time_to_next_line = resolution_seconds - gate_start_elapsed % resolution_seconds
    if time_to_next_line == 0:
        time_to_next_line += resolution_seconds
    while time_to_next_line < leg_time:
        line_position = time_to_position(time_to_next_line)
        lines.append((create_perpendicular_line_at_end_lonlat(*reversed(start), *reversed(line_position),
                                                              line_width_nm * 1852), line_position,
                      gate_start_time + datetime.timedelta(seconds=time_to_next_line)))
        time_to_next_line += resolution_seconds
    return lines


def create_minute_lines_track(track: List[Tuple[float, float]], air_speed: float, wind_speed: float,
                              wind_direction: float, gate_start_time: datetime.datetime,
                              route_start_time: datetime.datetime,
                              resolution_seconds: int = 60,
                              line_width_nm=0.5) -> List[
    Tuple[Tuple[Tuple[float, float], Tuple[float, float]], Tuple[float, float], datetime.datetime]]:
    """
    Generates a track that goes through the centre of the route (or corridor if it exists)

    :param track: List of positions that represents the path between two gates
    :param air_speed:
    :param wind_speed:
    :param wind_direction:
    :param gate_start_time: The time of the contestant crosses out from the gate (so remember to factor in procedure turns in that time)
    :param route_start_time:
    :param resolution_seconds:
    :param line_width_nm:
    :return:
    """
    gate_start_elapsed = (gate_start_time - route_start_time).total_seconds()
    time_to_next_line = resolution_seconds - gate_start_elapsed % resolution_seconds
    if time_to_next_line == 0:
        time_to_next_line += resolution_seconds
    accumulated_time = 0
    lines = []
    for index in range(0, len(track) - 1):
        start = track[index]
        finish = track[index + 1]
        bearing = calculate_bearing(start, finish)
        ground_speed = calculate_ground_speed_combined(bearing, air_speed, wind_speed,
                                                       wind_direction)
        length = calculate_distance_lat_lon(start, finish) / 1852
        leg_time = 3600 * length / ground_speed  # seconds
        while time_to_next_line < leg_time + accumulated_time:
            internal_leg_time = time_to_next_line - accumulated_time
            line_position = calculate_fractional_distance_point_lat_lon(start, finish, internal_leg_time / leg_time)
            lines.append((create_perpendicular_line_at_end_lonlat(*reversed(start), *reversed(line_position),
                                                                  line_width_nm * 1852), line_position,
                          gate_start_time + datetime.timedelta(seconds=time_to_next_line)))
            time_to_next_line += resolution_seconds
        accumulated_time += leg_time
    for line in lines:
        print(line)
    return lines


A4 = "A4"
A3 = "A3"

OSM_MAP = 0
N250_MAP = 1
M517_BERGEN_MAP = 2
GERMANY1 = 3
TILE_MAP = {
    N250_MAP: "Norway_N250",
    M517_BERGEN_MAP: "m517_bergen",
    GERMANY1: "germany_map"
}


def folder_map_name(folder: str) -> str:
    actual_map = folder.split("/")[-1]
    elements = actual_map.split("_")
    return " ".join([item.capitalize() for item in elements])


MAP_FOLDERS = glob.glob("/maptiles/*")
MAP_CHOICES = [(item, folder_map_name(item)) for item in MAP_FOLDERS] + [("osm", "OSM")]


class OpenAIP(GoogleWTS):
    def _image_url(self, tile):
        x, y, z = tile
        s = '1'
        ext = 'png'
        return f"http://{s}.tile.maps.openaip.net/geowebcache/service/tms/1.0.0/openaip_basemap@EPSG%3A900913@png/{z}/{x}/{y}.{ext}"


class LocalImages(GoogleWTS):
    def __init__(self, folder: str):
        super().__init__()
        self.folder = folder

    def _image_url(self, tile):
        x, y, z = tile
        return "file://{}/{}/{}/{}.png".format(self.folder, z, x, y)

    def tileextent(self, x_y_z):
        """Return extent tuple ``(x0,x1,y0,y1)`` in Mercator coordinates."""
        x, y, z = x_y_z
        x_lim, y_lim = self.tile_bbox(x, y, z, y0_at_north_pole=False)
        return tuple(x_lim) + tuple(y_lim)

    _tileextent = tileextent

    # def subtiles(self, x_y_z):
    #     x, y, z = x_y_z
    #     # Google tile specific (i.e. up->down).
    #     for xi in range(0, 2):
    #         for yi in range(0, 2):
    #             ry=y * 2 + yi
    #             result = x * 2 + xi, (ry*2) + yi, z + 1
    #             print(result)
    #             yield result
    #
    # _subtiles = subtiles
    # def tileextent(self, x_y_z):
    #     """Return extent tuple ``(x0,x1,y0,y1)`` in Mercator coordinates."""
    #     x, y, z = x_y_z
    #     x_lim, y_lim = self.tile_bbox(x, y, z, y0_at_north_pole=True)
    #     # return [-1.70230674884, 32.2907623616, 57.5458684362, 71.7652057932]
    #     return [577671.47,475230.47,6378894.33, 7962889.13]
    #     # return [57.5458684362, 32.2907623616], [71.7652057932, -1.70230674884]
    #     # return tuple(x_lim) + tuple(y_lim)


def utm_from_lon(lon):
    """
    utm_from_lon - UTM zone for a longitude
    Not right for some polar regions (Norway, Svalbard, Antartica)
    :param float lon: longitude
    :return: UTM zone number
    :rtype: int
    """

    return np.floor((lon + 180) / 6) + 1


def utm_from_lat_lon(lat, lon) -> ccrs.CRS:
    """
    utm_from_lon - UTM zone for a longitude
    Not right for some polar regions (Norway, Svalbard, Antartica)
    :param float lon: longitude
    :return: UTM zone number
    :rtype: int
    """
    _, _, zone, letter = utm.from_latlon(lat, lon)
    print(zone)
    print(letter)
    return ccrs.UTM(zone, southern_hemisphere=lat < 0)


def scale_bar(ax, proj, length, location=(0.5, 0.05), linewidth=3,
              units='km', m_per_unit=1000, scale=0):
    """
    http://stackoverflow.com/a/35705477/1072212
    ax is the axes to draw the scalebar on.
    proj is the projection the axes are in
    location is center of the scalebar in axis coordinates ie. 0.5 is the middle of the plot
    length is the length of the scalebar in km.
    linewidth is the thickness of the scalebar.
    units is the name of the unit
    m_per_unit is the number of meters in a unit
    """
    # find lat/lon center to find best UTM zone
    x0, x1, y0, y1 = ax.get_extent(proj.as_geodetic())
    # Projection in metres
    utm = utm_from_lat_lon((y0 + y1) / 2, (x0 + x1) / 2)
    # Get the extent of the plotted area in coordinates in metres
    x0, x1, y0, y1 = ax.get_extent(utm)
    # Turn the specified scalebar location into coordinates in metres
    sbcx, sbcy = x0 + (x1 - x0) * location[0], y0 + (y1 - y0) * location[1]
    # Generate the x coordinate for the ends of the scalebar
    ruler_scale = 100 * 1852 * length / (scale * 1000)  # cm
    bar_length = 10 * scale * 1000 / (100 * 1852)  # NM (10 is cm)
    x_offset = bar_length * m_per_unit
    bar_xs = [sbcx - x_offset / 2, sbcx + x_offset / 2]
    # buffer for scalebar
    buffer = [patheffects.withStroke(linewidth=5, foreground="w")]
    # Plot the scalebar with buffer
    x0, y = proj.transform_point(bar_xs[0], sbcy, utm)
    x1, _ = proj.transform_point(bar_xs[1], sbcy, utm)
    xc, yc = proj.transform_point(sbcx, sbcy + 200, utm)
    ax.plot([x0, x1], [y, y], transform=proj, color='k',
            linewidth=linewidth, path_effects=buffer, solid_capstyle="butt")
    # buffer for text
    buffer = [patheffects.withStroke(linewidth=3, foreground="w")]
    # Plot the scalebar label
    t0 = ax.text(xc, yc, "1:{:,d} {:.2f} {} = {:.0f} cm".format(int(scale * 1000), bar_length, units, 10),
                 transform=proj,
                 horizontalalignment='center', verticalalignment='bottom',
                 path_effects=buffer, zorder=2)
    # left = x0 + (x1 - x0) * 0.05
    # Plot the N arrow
    # t1 = ax.text(left, sbcy, u'\u25B2\nN', transform=utm,
    #              horizontalalignment='center', verticalalignment='bottom',
    #              path_effects=buffer, zorder=2)

    # Plot the scalebar without buffer, in case covered by text buffer
    ax.plot([x0, x1], [y, y], transform=proj, color='k',
            linewidth=linewidth, zorder=3, solid_capstyle="butt")


def scale_bar_y(ax, proj, length, location=(0.03, 0.5), linewidth=3,
                units='km', m_per_unit=1000, scale=0):
    """
    http://stackoverflow.com/a/35705477/1072212
    ax is the axes to draw the scalebar on.
    proj is the projection the axes are in
    location is center of the scalebar in axis coordinates ie. 0.5 is the middle of the plot
    length is the length of the scalebar in km.
    linewidth is the thickness of the scalebar.
    units is the name of the unit
    m_per_unit is the number of meters in a unit
    """
    print("Scale y")
    # find lat/lon center to find best UTM zone
    x0, x1, y0, y1 = ax.get_extent(proj.as_geodetic())
    # Projection in metres
    utm = utm_from_lat_lon((y0 + y1) / 2, (x0 + x1) / 2)
    # Get the extent of the plotted area in coordinates in metres
    x0, x1, y0, y1 = ax.get_extent(utm)
    # Turn the specified scalebar location into coordinates in metres
    sbcx, sbcy = x0 + (x1 - x0) * location[0], y0 + (y1 - y0) * location[1]
    # Generate the x coordinate for the ends of the scalebar
    ruler_scale = 100 * 1852 * length / (scale * 1000)  # cm
    bar_length = 10 * scale * 1000 / (100 * 1852)  # NM (10 is cm)
    y_offset = bar_length * m_per_unit
    bar_ys = [sbcy - y_offset / 2, sbcy + y_offset / 2]
    # buffer for scalebar
    buffer = [patheffects.withStroke(linewidth=5, foreground="w")]
    # Plot the scalebar with buffer
    x, y0 = proj.transform_point(sbcx, bar_ys[0], utm)
    _, y1 = proj.transform_point(sbcx, bar_ys[1], utm)
    xc, yc = proj.transform_point(sbcx + 400, sbcy, utm)
    ax.plot([x, x], [y0, y1], transform=proj, color='k',
            linewidth=linewidth, path_effects=buffer, solid_capstyle="butt")
    # buffer for text
    buffer = [patheffects.withStroke(linewidth=3, foreground="w")]
    # Plot the scalebar label
    t0 = ax.text(xc, yc, "1:{:,d} {:.2f} {} = {:.0f} cm".format(int(scale * 1000), bar_length, units, 10),
                 transform=proj,
                 horizontalalignment='center', verticalalignment='bottom',
                 path_effects=buffer, zorder=2, rotation=-90, ha='center', va='center')
    # left = x0 + (x1 - x0) * 0.05
    # Plot the N arrow
    # t1 = ax.text(left, sbcy, u'\u25B2\nN', transform=utm,
    #              horizontalalignment='center', verticalalignment='bottom',
    #              path_effects=buffer, zorder=2)

    # Plot the scalebar without buffer, in case covered by text buffer
    ax.plot([x, x], [y0, y1], transform=proj, color='k',
            linewidth=linewidth, zorder=3, solid_capstyle="butt")


# if __name__ == '__main__':
#     ax = plt.axes(projection=ccrs.Mercator())
#     plt.title('Cyprus')
#     ax.set_extent([31, 35.5, 34, 36], ccrs.Geodetic())
#     ax.stock_img()
#     ax.coastlines(resolution='10m')
#     scale_bar(ax, ccrs.Mercator(), 100)  # 100 km scale bar
#     # or to use m instead of km
#     # scale_bar(ax, ccrs.Mercator(), 100000, m_per_unit=1, units='m')
#     # or to use miles instead of km
#     # scale_bar(ax, ccrs.Mercator(), 60, m_per_unit=1609.34, units='miles')
#     plt.show()
def inch2cm(inch: float) -> float:
    return inch * 2.54


def cm2inch(cm: float) -> float:
    return cm / 2.54


def calculate_extent(width: float, height: float, centre: Tuple[float, float]):
    left_edge = project_position_lat_lon(centre, 270, width / 2)[1]
    right_edge = project_position_lat_lon(centre, 90, width / 2)[1]
    top_edge = project_position_lat_lon(centre, 0, height / 2)[0]
    bottom_edge = project_position_lat_lon(centre, 180, height / 2)[0]
    return [left_edge, right_edge, bottom_edge, top_edge]


def plot_leg_bearing(current_waypoint, next_waypoint, air_speed, wind_speed, wind_direction, character_offset: int = 4,
                     fontsize: int = 14):
    bearing = current_waypoint.bearing_next
    wind_correction_angle = calculate_wind_correction_angle(bearing, air_speed, wind_speed, wind_direction)
    bearing_difference_next = get_heading_difference(next_waypoint.bearing_from_previous,
                                                     next_waypoint.bearing_next)
    bearing_difference_previous = get_heading_difference(current_waypoint.bearing_from_previous,
                                                         current_waypoint.bearing_next)
    course_position = get_course_position((current_waypoint.latitude, current_waypoint.longitude),
                                          (next_waypoint.latitude,
                                           next_waypoint.longitude),
                                          True, 3)
    course_text = "{:03.0f}".format(current_waypoint.bearing_next - wind_correction_angle)
    # Try to keep it out of the way of the next leg
    if bearing_difference_next > 60 or bearing_difference_previous > 60:  # leftSide
        label = "" + course_text + " " * len(course_text) + " " * character_offset
    else:  # Right-sided is preferred
        label = "" + " " * len(course_text) + " " * character_offset + course_text
    plt.text(course_position[1], course_position[0], label,
             verticalalignment="center", color="red",
             horizontalalignment="center", transform=ccrs.PlateCarree(), fontsize=fontsize,
             rotation=-bearing,
             linespacing=2, family="monospace")


def waypoint_bearing(waypoint, index) -> float:
    bearing = waypoint.bearing_from_previous
    if index == 0:
        bearing = waypoint.bearing_next
    return bearing


def plot_prohibited_zones(route: Route, target_projection, ax):
    for prohibited in route.prohibited_set.all():
        line = []
        for element in prohibited.path:
            line.append(target_projection.transform_point(*list(reversed(element)), ccrs.PlateCarree()))
        polygon = Polygon(line)
        centre = polygon.centroid
        ax.add_geometries([polygon], crs=target_projection, facecolor="red", alpha=0.4)
        plt.text(centre.x, centre.y, prohibited.name, horizontalalignment="center")


def plot_waypoint_name(route: Route, waypoint: Waypoint, bearing: float, annotations: bool, waypoints_only: bool,
                       contestant: Optional[Contestant], line_width: float, colour: str, character_padding: int = 4):
    text = "{}".format(waypoint.name)
    if contestant is not None and annotations:
        waypoint_time = contestant.gate_times.get(waypoint.name)  # type: datetime.datetime
        if waypoint_time is not None:
            local_waypoint_time = waypoint_time.astimezone(route.navigationtask.contest.time_zone)
            text += " {}".format(local_waypoint_time.strftime("%H:%M:%S"))
    bearing_difference = get_heading_difference(waypoint.bearing_from_previous, waypoint.bearing_next)
    if bearing_difference > 0:
        text = "\n" + text + " " * len(text) + " " * character_padding  # Padding to get things aligned correctly
    else:
        text = "\n" + " " * (len(text) + character_padding) + text  # Padding to get things aligned correctly
    if waypoints_only:
        bearing = 0
    plt.text(waypoint.longitude, waypoint.latitude, text, verticalalignment="center", color=colour,
             horizontalalignment="center", transform=ccrs.PlateCarree(), fontsize=8, rotation=-bearing,
             linespacing=2, family="monospace", clip_on=True)


def plot_anr_corridor_track(route: Route, contestant: Optional[Contestant], annotations, line_width: float,
                            colour: str):
    inner_track = []
    outer_track = []
    for index, waypoint in enumerate(route.waypoints):
        ys, xs = np.array(waypoint.gate_line).T
        bearing = waypoint_bearing(waypoint, index)

        if waypoint.type in ("sp", "fp"):
            plot_waypoint_name(route, waypoint, bearing, annotations, False, contestant, line_width, colour,
                               character_padding=5)
        if route.rounded_corners and waypoint.left_corridor_line is not None:
            inner_track.extend(waypoint.left_corridor_line)
            outer_track.extend(waypoint.right_corridor_line)
        else:
            plt.plot(xs, ys, transform=ccrs.PlateCarree(), color=colour, linewidth=line_width)
            inner_track.append(waypoint.gate_line[0])
            outer_track.append(waypoint.gate_line[1])
        if index < len(route.waypoints) - 1 and annotations and contestant is not None:
            plot_minute_marks(waypoint, contestant, route.waypoints, index, line_width, colour, mark_offset=4,
                              line_width_nm=contestant.navigation_task.scorecard.get_corridor_width(contestant))
            plot_leg_bearing(waypoint, route.waypoints[index + 1], contestant.air_speed, contestant.wind_speed,
                             contestant.wind_direction, 2, 10)
        # print(inner_track)
    path = np.array(inner_track)
    ys, xs = path.T
    plt.plot(xs, ys, transform=ccrs.PlateCarree(), color=colour, linewidth=line_width)
    path = np.array(outer_track)
    ys, xs = path.T
    plt.plot(xs, ys, transform=ccrs.PlateCarree(), color=colour, linewidth=line_width)
    return path


def plot_minute_marks(waypoint: Waypoint, contestant: Contestant, track, index, line_width: float, colour: str,
                      mark_offset=1,
                      line_width_nm: float = 0.5):
    gate_start_time = contestant.gate_times.get(waypoint.name)
    if waypoint.is_procedure_turn:
        gate_start_time += datetime.timedelta(minutes=1)
    first_segments = waypoint.get_centre_track_segments()
    last_segments = track[index + 1].get_centre_track_segments()
    track_points = first_segments[len(first_segments) // 2:] + last_segments[:(len(last_segments) // 2) + 1]
    # print(f"track_points: {track_points}")
    ys, xs = np.array(track_points).T
    plt.plot(xs, ys, transform=ccrs.PlateCarree(), color="green", linewidth=LINEWIDTH)
    minute_lines = create_minute_lines_track(track_points,
                                             contestant.air_speed, contestant.wind_speed,
                                             contestant.wind_direction,
                                             gate_start_time,
                                             contestant.gate_times.get(track[0].name), line_width_nm=line_width_nm)
    for mark_line, line_position, timestamp in minute_lines:
        xs, ys = np.array(mark_line).T  # Already comes in the format lon, lat
        plt.plot(xs, ys, transform=ccrs.PlateCarree(), color=colour, linewidth=line_width)
        time_format = "%M"
        if timestamp.second != 0:
            time_format = "%M:%S"
        time_string = timestamp.strftime(time_format)
        text = "\n" + " " * mark_offset + " " * len(time_string) + time_string
        plt.text(line_position[1], line_position[0], text, verticalalignment="center",
                 color=colour,
                 horizontalalignment="center", transform=ccrs.PlateCarree(), fontsize=8,
                 rotation=-waypoint.bearing_next,
                 linespacing=2, family="monospace")


def plot_precision_track(route: Route, contestant: Optional[Contestant], waypoints_only: bool, annotations: bool,
                         line_width: float, colour: str):
    tracks = [[]]
    for waypoint in route.waypoints:  # type: Waypoint
        if waypoint.type == "isp":
            tracks.append([])
        if waypoint.type in ("tp", "sp", "fp", "isp", "ifp"):
            tracks[-1].append(waypoint)
    for track in tracks:
        line = []
        for index, waypoint in enumerate(track):  # type: int, Waypoint
            if waypoint.type != "secret":
                bearing = waypoint_bearing(waypoint, index)
                ys, xs = np.array(waypoint.gate_line).T
                if not waypoints_only:
                    plt.plot(xs, ys, transform=ccrs.PlateCarree(), color=colour, linewidth=line_width)
                else:
                    plt.plot(waypoint.longitude, waypoint.latitude, transform=ccrs.PlateCarree(), color=colour,
                             marker="o", markersize=8, fillstyle="none")
                plot_waypoint_name(route, waypoint, bearing, annotations, waypoints_only, contestant, line_width,
                                   colour)
                if contestant is not None:
                    if index < len(track) - 1:
                        if annotations:
                            plot_leg_bearing(waypoint, track[index + 1], contestant.air_speed, contestant.wind_speed,
                                             contestant.wind_direction)
                            plot_minute_marks(waypoint, contestant, track, index, line_width, colour)

            if waypoint.is_procedure_turn:
                line.extend(waypoint.procedure_turn_points)
            else:
                line.append((waypoint.latitude, waypoint.longitude))
        path = np.array(line)
        if not waypoints_only:
            ys, xs = path.T
            plt.plot(xs, ys, transform=ccrs.PlateCarree(), color=colour, linewidth=line_width)
        return path


def plot_route(task: NavigationTask, map_size: str, zoom_level: Optional[int] = None, landscape: bool = True,
               contestant: Optional[Contestant] = None,
               waypoints_only: bool = False, annotations: bool = True, scale: int = 200, dpi: int = 300,
               map_source: str = "osm", line_width: float = 0.5, colour: str = "#0000ff"):
    route = task.route
    A4_width = 21.0
    A4_height = 29.7
    A3_height = 42
    A3_width = 29.7
    if map_source == "osm":
        imagery = OSM()
    else:
        imagery = LocalImages(map_source)
    if map_size == A3:
        if zoom_level is None:
            zoom_level = 12
        if landscape:
            figure_width = A3_height
            figure_height = A3_width
        else:
            figure_width = A3_width
            figure_height = A3_height
    else:
        if zoom_level is None:
            zoom_level = 11
        if landscape:
            figure_width = A4_height
            figure_height = A4_width
        else:
            figure_width = A4_width
            figure_height = A4_height

    plt.figure(figsize=(cm2inch(figure_width), cm2inch(figure_height)))
    ax = plt.axes(projection=imagery.crs)
    print(f"Figure projection: {imagery.crs}")
    ax.add_image(imagery, zoom_level)#, interpolation='spline36', zorder=10)
    # ax.add_image(OpenAIP(), zoom_level, interpolation='spline36', alpha=0.6, zorder=20)
    ax.set_aspect("auto")
    if "precision" in task.scorecard.task_type:
        path = plot_precision_track(route, contestant, waypoints_only, annotations, line_width, colour)
    elif "anr_corridor" in task.scorecard.task_type:
        path = plot_anr_corridor_track(route, contestant, annotations, line_width, colour)
    else:
        path = []
    plot_prohibited_zones(route, imagery.crs, ax)
    ax.gridlines(draw_labels=False, dms=True)
    buffer = [patheffects.withStroke(linewidth=3, foreground="w")]
    if contestant is not None:
        plt.title("Track: '{}' - Contestant: {} - Wind: {:03.0f}/{:02.0f}".format(route.name, contestant,
                                                                                  contestant.wind_direction,
                                                                                  contestant.wind_speed), y=1, pad=-20,
                  color="black", fontsize=10, path_effects=buffer)
    else:
        plt.title("Track: {}".format(route.navigationtask.name), y=1, pad=-20, path_effects=buffer)

    # plt.tight_layout()
    fig = plt.gcf()
    print(f"Figure size (cm): ({figure_width}, {figure_height})")
    minimum_latitude = np.min(path[:, 0])
    minimum_longitude = np.min(path[:, 1])
    maximum_latitude = np.max(path[:, 0])
    maximum_longitude = np.max(path[:, 1])
    print(f"minimum: {minimum_latitude}, {minimum_longitude}")
    print(f"maximum: {maximum_latitude}, {maximum_longitude}")
    if scale == 0:
        # Zoom to fit
        map_margin = 6000  # metres

        proj = ccrs.PlateCarree()
        x0, x1, y0, y1 = ax.get_extent(proj.as_geodetic())
        print(f"x0: {x0}, y0: {y0}")
        print(f"x1: {x1}, y1: {y1}")

        # Projection in metres
        utm = utm_from_lat_lon((y0 + y1) / 2, (x0 + x1) / 2)
        bottom_left = utm.transform_point(minimum_longitude, minimum_latitude, proj)
        top_left = utm.transform_point(minimum_longitude, maximum_latitude, proj)
        bottom_right = utm.transform_point(maximum_longitude, minimum_latitude, proj)
        top_right = utm.transform_point(maximum_longitude, maximum_latitude, proj)

        print(f"bottom_left: {bottom_left}")
        print(f"top_right: {top_right}")
        x0 = bottom_left[0] - map_margin
        y0 = bottom_left[1] - map_margin
        x1 = top_right[0] + map_margin
        y1 = top_right[1] + map_margin
        print(f"Width at top: {top_right[0] - top_left[0]}")
        print(f"Width at bottom: {bottom_right[0] - bottom_left[0]}")
        horizontal_metres = x1 - x0
        vertical_metres = y1 - y0
        x_centre = (x0 + x1) / 2
        y_centre = (y0 + y1) / 2
        vertical_scale = vertical_metres / figure_height  # m per cm
        horizontal_scale = horizontal_metres / figure_width  # m per cm

        if vertical_scale < horizontal_scale:
            # Increase vertical scale to match
            vertical_metres = horizontal_scale * figure_height
            y0 = y_centre - vertical_metres / 2
            y1 = y_centre + vertical_metres / 2
            x0 += 2000
            x1 -= 2000
            scale = horizontal_metres / (10 * figure_width)
        else:
            # Do not scale in the horizontal direction, just make sure that we do not step over the bounds
            horizontal_metres = vertical_scale * figure_width
            # x0 = x_centre - horizontal_metres / 2
            # x1 = x_centre + horizontal_metres / 2
            scale = vertical_metres / (10 * figure_height)
        print(f"x0: {x0}, y0: {y0}")
        print(f"x1: {x1}, y1: {y1}")
        x0, y0 = proj.transform_point(x0, y0, utm)
        x1, y1 = proj.transform_point(x1, y1, utm)
        print(f"x0: {x0}, y0: {y0}")
        print(f"x1: {x1}, y1: {y1}")
        extent = [x0, x1, y0, y1]
    else:
        proj = ccrs.PlateCarree()
        x0, x1, y0, y1 = ax.get_extent(proj.as_geodetic())
        # Projection in metres
        utm = utm_from_lat_lon((y0 + y1) / 2, (x0 + x1) / 2)
        centre_longitude = minimum_longitude + (maximum_longitude - minimum_longitude) / 2
        centre_latitude = minimum_latitude + (maximum_latitude - minimum_latitude) / 2
        centre_x, centre_y = utm.transform_point(centre_longitude, centre_latitude, proj)
        width_metres = (scale * 10) * figure_width
        height_metres = (scale * 10) * figure_height
        height_offset = 0
        width_offset = 2000
        lower_left = proj.transform_point(centre_x - width_metres / 2 + width_offset,
                                          centre_y - height_metres / 2 + height_offset, utm)
        upper_right = proj.transform_point(centre_x + width_metres / 2 - width_offset,
                                           centre_y + height_metres / 2 - height_offset, utm)
        extent = [lower_left[0], upper_right[0], lower_left[1], upper_right[1]]
    print(extent)
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    # scale_bar(ax, ccrs.PlateCarree(), 5, units="NM", m_per_unit=1852, scale=scale)
    scale_bar_y(ax, ccrs.PlateCarree(), 5, units="NM", m_per_unit=1852, scale=scale)
    ax.autoscale(False)
    fig.patch.set_visible(False)
    # lat lon lines
    longitude = np.ceil(extent[0])
    while longitude < extent[1]:
        plt.plot((longitude, longitude), (extent[2], extent[3]), transform=ccrs.PlateCarree(), color="black",
                 linewidth=0.5)
        longitude += 1
    latitude = np.ceil(extent[2])
    while latitude < extent[3]:
        plt.plot((extent[0], extent[1]), (latitude, latitude), transform=ccrs.PlateCarree(), color="black",
                 linewidth=0.5)
        latitude += 1
    # plt.savefig("map.png", dpi=600)
    fig.subplots_adjust(bottom=0)
    fig.subplots_adjust(top=1)
    fig.subplots_adjust(right=1)
    fig.subplots_adjust(left=0)

    # plot_margin = 1
    # plot_margin = plot_margin / 2.54
    #
    # x0, x1, y0, y1 = plt.axis()
    # plt.axis((x0 - plot_margin,
    #           x1 + plot_margin,
    #           y0 - plot_margin,
    #           y1 + plot_margin))

    figdata = BytesIO()
    plt.savefig(figdata, format='png', dpi=dpi)  # , bbox_inches="tight", pad_inches=margin_inches/2)
    figdata.seek(0)
    pdfdata = BytesIO()
    plt.savefig(pdfdata, format='pdf', dpi=dpi)  # , bbox_inches="tight", pad_inches=margin_inches/2)
    plt.close()
    pdfdata.seek(0)

    return figdata, pdfdata


def get_basic_track(positions: List[Tuple[float, float]]):
    """

    :param positions: List of (latitude, longitude) pairs
    :return:
    """
    imagery = OSM()
    ax = plt.axes(projection=imagery.crs)
    ax.add_image(imagery, 13)
    ax.set_aspect("auto")
    ys, xs = np.array(positions).T
    plt.plot(xs, ys, transform=ccrs.PlateCarree(), color="blue", linewidth=LINEWIDTH * 2)
    index = 1
    for latitude, longitude in positions[1:-1]:
        plt.text(longitude, latitude, f"TP {index}", verticalalignment="center", color="blue",
                 horizontalalignment="center", transform=ccrs.PlateCarree(), fontsize=6)
        index += 1
    plt.text(positions[0][1], positions[0][0], f"SP", verticalalignment="center", color="blue",
             horizontalalignment="center", transform=ccrs.PlateCarree(), fontsize=6)
    plt.text(positions[-1][1], positions[-1][0], f"FP", verticalalignment="center", color="blue",
             horizontalalignment="center", transform=ccrs.PlateCarree(), fontsize=6)
    figdata = BytesIO()
    plt.savefig(figdata, format='png', dpi=100, bbox_inches="tight", pad_inches=0)
    plt.close()
    figdata.seek(0)
    return figdata
