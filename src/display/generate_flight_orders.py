import random
import urllib
import urllib.request
from io import BytesIO
from tempfile import NamedTemporaryFile
from typing import List
import matplotlib.pyplot as plt
from PIL import Image, ImageDraw, ImageFont
from cartopy import geodesic

from cartopy.io.img_tiles import GoogleTiles
from fpdf import FPDF, HTMLMixin
from pylatex.base_classes import Environment, Options, Arguments
from pylatex.utils import bold
from shapely.geometry import Polygon

from display.coordinate_utilities import utm_from_lat_lon, normalise_bearing
from display.map_constants import LANDSCAPE, A4
from display.map_plotter import plot_route
from display.map_plotter_shared_utilities import qr_code_image
from display.models import Scorecard, Contestant
from display.waypoint import Waypoint
import cartopy.crs as ccrs

from display.wind_utilities import calculate_wind_correction_angle
from live_tracking_map.settings import AZURE_ACCOUNT_NAME
from pylatex import (
    Document,
    PageStyle,
    Head,
    MiniPage,
    NoEscape,
    StandAloneGraphic,
    LongTabu,
    Section,
    HugeText,
    Center,
    LineBreak,
    LargeText,
    Package,
    TextColor,
    Tabu,
    VerticalSpace,
    Figure,
    Command,
    SubFigure,
    Foot,
    NewPage,
    HorizontalSpace,
    UnsafeCommand,
    Label,
    Marker,
)


class MyFPDF(FPDF, HTMLMixin):
    pass


def generate_turning_point_image(
    waypoints: List[Waypoint], index, unknown_leg: bool = False
):
    waypoint = waypoints[index]
    imagery = GoogleTiles(style="satellite")
    plt.figure(figsize=(10, 10))
    ax = plt.axes(projection=imagery.crs)
    ax.add_image(imagery, 15)
    ax.set_aspect("auto")
    plt.plot(waypoint.longitude, waypoint.latitude, transform=ccrs.PlateCarree())
    if not unknown_leg:
        if index > 0:
            plt.plot(
                [waypoints[index - 1].longitude, waypoints[index].longitude],
                [waypoints[index - 1].latitude, waypoints[index].latitude],
                transform=ccrs.PlateCarree(),
                color="blue",
                linewidth=2,
            )
        if index < len(waypoints) - 1:
            print(waypoints[index])
            print(waypoints[index + 1])
            plt.plot(
                [waypoints[index].longitude, waypoints[index + 1].longitude],
                [waypoints[index].latitude, waypoints[index + 1].latitude],
                transform=ccrs.PlateCarree(),
                color="blue",
                linewidth=2,
            )
    proj = ccrs.PlateCarree()
    utm = utm_from_lat_lon(waypoint.latitude, waypoint.longitude)
    centre_x, centre_y = utm.transform_point(
        waypoint.longitude, waypoint.latitude, proj
    )
    range = 700
    x0, y0 = proj.transform_point(centre_x - range, centre_y - range, utm)
    x1, y1 = proj.transform_point(centre_x + range, centre_y + range, utm)
    extent = [x0, x1, y0, y1]
    ax.set_extent(extent, crs=ccrs.PlateCarree())
    circle_points = geodesic.Geodesic().circle(
        lon=waypoint.longitude,
        lat=waypoint.latitude,
        radius=200,
        n_samples=50,
        endpoint=False,
    )
    geom = Polygon(circle_points)
    ax.add_geometries(
        (geom,), crs=ccrs.PlateCarree(), facecolor="none", edgecolor="red", linewidth=3
    )
    figdata = BytesIO()
    plt.savefig(figdata, format="png", dpi=200, transparent=True)
    # plt.savefig(
    #     "temporary", format="png", dpi=100, transparent=True
    # )
    figdata.seek(0)
    img = Image.open(figdata, formats=["PNG"])
    if index > 0:
        img2 = img.rotate(waypoint.bearing_from_previous)
    else:
        img2 = img.rotate(waypoint.bearing_next)
    width, height = img2.size
    overlap = 500
    cropped = img2.crop((overlap, overlap, width - overlap, height - overlap))
    draw = ImageDraw.Draw(cropped)
    if unknown_leg:
        fnt = ImageFont.truetype("/src/OpenSans-Bold.ttf", 100)
        draw.text(
            (10, 10),
            f"{int(round(waypoint.bearing_next))}",
            font=fnt,
            fill=(255, 0, 0, 0),
        )
    image_data = BytesIO()
    cropped.save(image_data, "PNG")
    image_data.seek(0)
    return image_data


def insert_turning_point_images_latex(contestant, document: Document):
    navigation = contestant.navigation_task  # type: NavigationTask
    render_waypoints = [
        waypoint
        for waypoint in navigation.route.waypoints
        if waypoint.type not in ("secret", "ul")
        and (waypoint.gate_check or waypoint.time_check)
    ]
    rows_per_page = 2
    number_of_images = len(render_waypoints)
    number_of_pages = 1 + ((number_of_images - 1) // (2 * rows_per_page))
    current_page = -1
    document.append(Label(Marker("firstpagetocount")))
    for index in range(0, len(render_waypoints), 2):
        if index % (rows_per_page * 2) == 0:
            document.append(NewPage())
            page_text = (
                f"Turning point images {current_page + 2}/{number_of_pages}"
                if number_of_pages > 1
                else ""
            )
            document.append(Section(page_text, numbering=False))
            current_page += 1
        figure_width = 0.4
        with document.create(Figure(position="!ht")):
            with document.create(MiniPage(width=fr"{figure_width}\textwidth")):
                image_file = get_turning_point_image(render_waypoints, index)
                document.append(
                    StandAloneGraphic(
                        image_options=r"width=\linewidth",
                        filename=image_file.name,
                    )
                )
                document.append(Command("caption*", render_waypoints[index].name))
            document.append(Command("hfill"))
            if index < len(render_waypoints) - 1:
                image_file = get_turning_point_image(render_waypoints, index + 1)
                with document.create(MiniPage(width=fr"{figure_width}\textwidth")):
                    document.append(
                        StandAloneGraphic(
                            image_options=r"width=\linewidth",
                            filename=image_file.name,
                        )
                    )
                    document.append(
                        Command("caption*", render_waypoints[index + 1].name)
                    )
    document.append(Label(Marker("lastpagetocount")))


def insert_turning_point_images(contestant, pdf: FPDF):
    navigation = contestant.navigation_task  # type: NavigationTask
    accounted_waypoints = []
    render_waypoints = []
    for index, waypoint in enumerate(navigation.route.waypoints):
        object = {"waypoint": waypoint, "index": index}
        accounted_waypoints.append(waypoint)
        if waypoint.type not in ("secret", "ul") and (
            waypoint.gate_check or waypoint.time_check
        ):
            render_waypoints.append(object)
    rows_per_page = 3
    number_of_images = len(render_waypoints)
    number_of_pages = 1 + ((number_of_images - 1) // (2 * rows_per_page))
    current_page = -1
    image_height = 230 / rows_per_page
    title_offset = 5
    row_step = image_height + title_offset
    row_start = 30
    for index in range(number_of_images):
        waypoint_object = render_waypoints[index]
        if index % (rows_per_page * 2) == 0:
            if index > 0:
                pdf.image("static/img/AirSportsLiveTracking.png", x=65, y=280, w=80)
            pdf.add_page()
            page_text = (
                f" {current_page + 2}/{number_of_pages}" if number_of_pages > 1 else ""
            )
            pdf.write_html(f"<font size=14>Turning point images{page_text}</font>")
            current_page += 1
        if index % 2 == 0:  # left column
            x = 18
        else:
            x = 118
        row_number = (index - (current_page * rows_per_page * 2)) // 2
        y = row_start + row_number * row_step
        pdf.text(x, y, render_waypoints[index]["waypoint"].name)
        image = generate_turning_point_image(
            accounted_waypoints, waypoint_object["index"]
        )
        file = NamedTemporaryFile(suffix=".png")
        file.write(image.read())
        file.seek(0)
        pdf.image(file.name, x=x, y=y + 1, h=image_height)
    pdf.image("static/img/AirSportsLiveTracking.png", x=65, y=280, w=80)


def insert_unknown_leg_images(contestant, pdf: FPDF):
    navigation = contestant.navigation_task  # type: NavigationTask
    accounted_waypoints = []
    render_waypoints = []
    for index, waypoint in enumerate(navigation.route.waypoints):
        object = {"waypoint": waypoint, "index": index}
        accounted_waypoints.append(waypoint)
        if waypoint.type == "ul":
            render_waypoints.append(object)
    # Randomise the images to make things more difficult
    random.shuffle(render_waypoints)
    rows_per_page = 3
    number_of_images = len(render_waypoints)
    number_of_pages = 1 + ((number_of_images - 1) // (2 * rows_per_page))
    current_page = -1
    image_height = 230 / rows_per_page
    title_offset = 5
    row_step = image_height + title_offset
    row_start = 30
    for index in range(number_of_images):
        waypoint_object = render_waypoints[index]
        if index % (rows_per_page * 2) == 0:
            if index > 0:
                pdf.image("static/img/AirSportsLiveTracking.png", x=65, y=280, w=80)
            pdf.add_page()
            page_text = (
                f" {current_page + 2}/{number_of_pages}" if number_of_pages > 1 else ""
            )
            pdf.write_html(f"<font size=14>Unknown leg images{page_text}</font>")
            current_page += 1
        if index % 2 == 0:  # left column
            x = 18
        else:
            x = 118
        row_number = (index - (current_page * rows_per_page * 2)) // 2
        y = row_start + row_number * row_step
        # pdf.text(x, y, render_waypoints[index]["waypoint"].name)
        image = generate_turning_point_image(
            accounted_waypoints, waypoint_object["index"], unknown_leg=True
        )
        file = NamedTemporaryFile(suffix=".png")
        file.write(image.read())
        file.seek(0)
        pdf.image(file.name, x=x, y=y + 1, h=image_height)
    pdf.image("static/img/AirSportsLiveTracking.png", x=65, y=280, w=80)


def recode_text(text: str):
    return text.encode("latin-1", "replace").decode("latin-1")


class WrapFigure(Environment):
    _latex_name = "wrapfigure"
    packages = [Package("wrapfig")]

    def __init__(self, left_or_right: str, width_string, data=None):
        super().__init__(
            arguments=Arguments(left_or_right, width_string),
            data=data,
        )


def generate_flight_orders_latex(contestant: "Contestant") -> bytes:
    flight_order_configuration = contestant.navigation_task.flightorderconfiguration
    starting_point_time_string = (
        f'{contestant.starting_point_time_local.strftime("%H:%M:%S")}'
    )
    tracking_start_time_string = (
        f'{contestant.tracker_start_time_local.strftime("%H:%M:%S")}'
    )
    finish_tracking_time = f'{contestant.finished_by_time_local.strftime("%H:%M:%S")}'
    facebook_share_url = "https://www.facebook.com/sharer/sharer.php?u="
    url = (
        facebook_share_url
        + "https://airsports.no"
        + contestant.navigation_task.tracking_link
    )
    qr = qr_code_image(url, "static/img/facebook_logo.png")
    qr_file = NamedTemporaryFile(suffix=".png")
    qr.save(qr_file)
    qr_file.seek(0)

    starting_point_text = starting_point_time_string
    if contestant.adaptive_start:
        starting_point_text = f"After {tracking_start_time_string}"

    if contestant.navigation_task.contest.logo:
        logo_url = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/media/{contestant.navigation_task.contest.logo}"
        logo = f"/tmp/{contestant.navigation_task.contest.logo}"
        urllib.request.urlretrieve(logo_url, logo)
    else:
        logo = "/src/static/img/airsports_no_text.png"

    geometry_options = {
        "a4paper": True,
        "head": "40pt",
        "margin": "0.5in",
        "bottom": "0.6in",
        "includeheadfoot": False,
    }
    document = Document(geometry_options=geometry_options, indent=False)
    document.preamble.append(Command("usepackage", "caption"))
    document.preamble.append(Command("usepackage", "xassoccnt"))
    document.preamble.append(Command("usepackage", "zref", "abspage,user,lastpage"))
    document.preamble.append(Command("usepackage", "hyperref"))
    # document.preamble.append(Command("newcounter", "turningpointimagepages"))
    # document.preamble.append(Command("makeatletter"))
    # count_command = UnsafeCommand(
    #     "newcommand",
    #     "totalimagepages",
    #     extra_arguments=r"\setcounter{turningpointimagepages}{\numexpr\zref@extract{lastpagetocount}{abspage} -\zref@extract{firstpagetocount}{abspage}+1\relax}\theturningpointimagepages",
    # )
    # document.preamble.append(count_command)
    # document.preamble.append(Command("makeatother"))
    # document.preamble.append(Command("newcounter", "realpage"))
    # document.preamble.append(Command("DeclareAssociatedCounters", ["page", "realpage"]))
    # document.preamble.append(
    #     Command("AtBeginDocument", NoEscape(r"\stepcounter{realpage}"))
    # )
    document.preamble.append(Command("captionsetup", "font=Large", "figure"))
    header = PageStyle("header")
    with header.create(Foot("C")):
        header.append(
            StandAloneGraphic(
                image_options=r"width=0.4\linewidth",
                filename="/src/static/img/AirSportsLiveTracking.png",
            )
        )
    document.preamble.append(header)
    # Map header
    map_header = PageStyle("mapheader")
    with map_header.create(Foot("R")):
        map_header.append(
            StandAloneGraphic(
                image_options=r"width=0.3\linewidth",
                filename="/src/static/img/AirSportsLiveTracking.png",
            )
        )
    document.preamble.append(map_header)
    # turning_point_header = PageStyle("turningpointheader")
    # with turning_point_header.create(Head("C")):
    #     turning_point_header.append(
    #         NoEscape(r"Turning point images \therealpage \totalimagepages")
    #     )
    # document.preamble.append(turning_point_header)
    document.change_document_style("header")
    with document.create(MiniPage()):
        with document.create(WrapFigure("r", "80pt")):
            document.append(
                StandAloneGraphic(image_options=r"width=\linewidth", filename=logo)
            )
        with document.create(Section("", numbering=False)):
            with document.create(Center()):
                document.append(LargeText("Welcome to"))
                document.append(LineBreak())
                document.append(HugeText(f"{contestant.navigation_task.contest.name}"))
                document.append(LineBreak())
                document.append(
                    TextColor("red", LargeText(f"{contestant.navigation_task.name}"))
                )
    document.append(LineBreak())
    with document.create(MiniPage()):
        document.append(VerticalSpace("50pt"))
        with document.create(WrapFigure("r", "150pt")):
            document.append(
                StandAloneGraphic(
                    image_options=r"width=\linewidth", filename=qr_file.name
                )
            )
            document.append(
                Command(
                    "caption*",
                    NoEscape(fr"\protect\href{{{url}}}{{Share on Facebook}}"),
                )
            )
        with document.create(Section("", numbering=False)):
            with document.create(Tabu("ll")) as data_table:
                data_table.add_row("Contestant:", str(contestant))
                data_table.add_row(
                    "Task type:",
                    f"{contestant.navigation_task.scorecard.get_calculator_display()}",
                )
                data_table.add_row(
                    "Competition date:",
                    f'{contestant.starting_point_time_local.strftime("%Y-%m-%d")}',
                )
                data_table.add_row(
                    "Airspeed:", f'{"{:.0f}".format(contestant.air_speed)} knots'
                )
                data_table.add_row(
                    "Tasks wind:",
                    f'{"{:03.0f}".format(contestant.wind_direction)}@{"{:.0f}".format(contestant.wind_speed)}',
                )
                data_table.add_row(
                    "Departure:",
                    f"{contestant.takeoff_time.astimezone(contestant.navigation_task.contest.time_zone).strftime('%Y-%m-%d %H:%M:%S') if not contestant.adaptive_start else 'Take-off time is not measured'}",
                )
                data_table.add_row("Start point:", f"{starting_point_text}")
                data_table.add_row(
                    "Finish by:", f"{finish_tracking_time} (tracking will stop)"
                )

            document.append(
                f"Using adaptive start, your start time will be set to the nearest whole minute you cross the infinite line going through the starting gate anywhere between one hour before and one hour after the selected starting point time (https://home.airsports.no/faq/#adaptiv-start)."
                if contestant.adaptive_start
                else ""
            )
    document.append(VerticalSpace("50pt"))
    with document.create(Section("Rules", numbering=False)):
        document.append(contestant.get_formatted_rules_description().replace("\n", ""))
    with document.create(Center()):
        document.append(HugeText(bold("Good luck")))
    document.append(VerticalSpace("30pt"))
    waypoints = list(
        filter(
            lambda waypoint: waypoint.type != "dummy",
            contestant.navigation_task.route.waypoints,
        )
    )
    starting_point_image_file = get_turning_point_image(waypoints, 0)
    finish_point_image_file = get_turning_point_image(waypoints, len(waypoints) - 1)
    with document.create(Figure(position="!ht")):
        with document.create(MiniPage(width=r"0.45\textwidth")):
            document.append(
                StandAloneGraphic(
                    image_options=r"width=\linewidth",
                    filename=starting_point_image_file.name,
                )
            )
            document.append(Command("caption*", "Starting point"))
        document.append(Command("hfill"))
        with document.create(MiniPage(width=r"0.45\textwidth")):
            document.append(
                StandAloneGraphic(
                    image_options=r"width=\linewidth",
                    filename=finish_point_image_file.name,
                )
            )
            document.append(Command("caption*", "Finish point"))
    document.append(NewPage())
    with document.create(Section("Turning point times", numbering=False)):
        with document.create(MiniPage(width=r"\textwidth")):
            document.append(Command("Large"))
            with document.create(Tabu("X[l] X[l] X[l] X[l] X[l]")) as data_table:
                data_table.add_row(
                    ["Turning point", "Distance", "TT", "TH", "Time"], mapper=[bold]
                )
                data_table.add_hline()
                first_line = True
                local_time = "-"
                if contestant.navigation_task.route.first_takeoff_gate:
                    local_time = contestant.gate_times.get(
                        contestant.navigation_task.route.first_takeoff_gate.name, None
                    )
                    if local_time:
                        local_time = local_time.astimezone(
                            contestant.navigation_task.contest.time_zone
                        ).strftime("%H:%M:%S")
                data_table.add_row(["Takeoff gate", "-", "-", "-", local_time])

                accumulated_distance = 0
                for (
                    waypoint
                ) in contestant.navigation_task.route.waypoints:  # type: Waypoint
                    if not first_line:
                        accumulated_distance += waypoint.distance_previous
                    if (
                        waypoint.type not in ("secret", "dummy", "ul")
                        and waypoint.time_check
                    ):
                        bearing = waypoint.bearing_from_previous
                        wind_correction_angle = calculate_wind_correction_angle(
                            bearing,
                            contestant.air_speed,
                            contestant.wind_speed,
                            contestant.wind_direction,
                        )
                        wind_bearing = normalise_bearing(
                            bearing - wind_correction_angle
                        )
                        gate_time = contestant.gate_times.get(waypoint.name, None)
                        local_waypoint_time = gate_time.astimezone(
                            contestant.navigation_task.contest.time_zone
                        )
                        if gate_time is not None:
                            data_table.add_row(
                                [
                                    waypoint.name,
                                    f"{accumulated_distance / 1852:.2f} NM"
                                    if not first_line
                                    else "-",
                                    f"{bearing:.0f}" if not first_line else "-",
                                    f"{wind_bearing:.0f}" if not first_line else "-",
                                    local_waypoint_time.strftime("%H:%M:%S"),
                                ]
                            )
                            accumulated_distance = 0
                            first_line = False
                local_time = "-"
                if contestant.navigation_task.route.first_landing_gate:
                    local_time = contestant.gate_times.get(
                        contestant.navigation_task.route.first_landing_gate.name, None
                    )
                    if local_time:
                        local_time = local_time.astimezone(
                            contestant.navigation_task.contest.time_zone
                        ).strftime("%H:%M:%S")
                data_table.add_row(["Landing gate", "-", "-", "-", local_time])

    map_image, pdf_image = plot_route(
        contestant.navigation_task,
        A4,  # flight_order_configuration.document_size,
        zoom_level=flight_order_configuration.map_zoom_level,
        landscape=flight_order_configuration.map_orientation == LANDSCAPE,
        contestant=contestant,
        annotations=flight_order_configuration.map_include_annotations,
        waypoints_only=not flight_order_configuration.map_include_waypoints,
        dpi=flight_order_configuration.map_dpi,
        scale=flight_order_configuration.map_scale,
        map_source=flight_order_configuration.map_source,
        user_map_source=str(flight_order_configuration.map_user_source.map_file)
        if flight_order_configuration.map_user_source
        else "",
        line_width=flight_order_configuration.map_line_width,
        minute_mark_line_width=flight_order_configuration.map_minute_mark_line_width,
        colour=flight_order_configuration.map_line_colour,
    )
    mapimage_file = NamedTemporaryFile(suffix=".png")
    mapimage_file.write(map_image.read())
    mapimage_file.seek(0)
    document.append(NewPage())
    document.append(Command("newgeometry", "left=0pt,bottom=0pt,top=0pt,right=0pt"))
    document.change_document_style("mapheader")
    document.append(
        StandAloneGraphic(mapimage_file.name, "")
    )  # f"resolution={flight_order_configuration.map_dpi}"))
    document.append(NewPage())
    document.append(Command("restoregeometry"))

    document.change_document_style("header")
    # document.change_document_style("turningpointheader")
    insert_turning_point_images_latex(contestant, document)

    # Produce the output
    pdf_file = NamedTemporaryFile()
    document.generate_tex(pdf_file.name)
    with open(pdf_file.name + ".tex", "r") as f:
        print(f.read())
    document.generate_pdf(pdf_file.name, clean=False, compiler_args=["-f"])
    pdf_file.close()
    with open(pdf_file.name + ".pdf", "rb") as f:
        return f.read()


def get_turning_point_image(waypoints: List, index: int) -> NamedTemporaryFile:
    turning_point = generate_turning_point_image(waypoints, index)
    temporary_file = NamedTemporaryFile(suffix=".png", delete=False)
    temporary_file.write(turning_point.read())
    temporary_file.seek(0)
    return temporary_file


def generate_flight_orders(contestant: "Contestant") -> bytes:
    """
    Returns a PDF report

    :param contestant:
    :return:
    """
    from display.forms import SCALE_TO_FIT

    flight_order_configuration = contestant.navigation_task.flightorderconfiguration
    starting_point_time_string = (
        f'{contestant.starting_point_time_local.strftime("%H:%M:%S")}'
    )
    tracking_start_time_string = (
        f'{contestant.tracker_start_time_local.strftime("%H:%M:%S")}'
    )
    finish_tracking_time = f'{contestant.finished_by_time_local.strftime("%H:%M:%S")}'
    facebook_share_url = "https://www.facebook.com/sharer/sharer.php?u="
    url = facebook_share_url + urllib.parse.quote(
        "https://airsports.no" + contestant.navigation_task.tracking_link
    )
    qr = qr_code_image(url, "static/img/facebook_logo.png")
    qr_file = NamedTemporaryFile(suffix=".png")
    qr.save(qr_file)
    qr_file.seek(0)

    starting_point_text = starting_point_time_string
    if contestant.adaptive_start:
        starting_point_text = f"After {tracking_start_time_string}"

    if contestant.navigation_task.contest.logo:
        logo = f"https://{AZURE_ACCOUNT_NAME}.blob.core.windows.net/media/{contestant.navigation_task.contest.logo}"
    else:
        logo = "static/img/airsports_no_text.png"
        # pdf.image("static/img/airsports_no_text.png", x=170, y=10, w=30)
    # pdf.image(qr_file.name, x=160, y=45, w=30)
    # pdf.text()
    heading = f"""
    <table width="100%">
    <thead><tr><th width="20%"></th><th width="60%"></th><th width="20%"></th></tr></thead>
    <tbody>
    <tr><td>&nbsp;</td><td align="center"><font size=18>Welcome to</font></td><td rowspan=5><img src="{logo}" width=80 /></td></tr>
    <tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr><td>&nbsp;</td><td align="center"><font color="#000000" size=24 font-weight="bold">{contestant.navigation_task.contest.name}</font></td></tr>
    <tr><td>&nbsp;</td><td>&nbsp;</td><td>&nbsp;</td></tr>
    <tr><td>&nbsp;</td><td align="center"><font color="#FF0000" size=16>{contestant.navigation_task.name}</font></td></tr>
    </tbody>
    </table>
<table width="100%">
<thead><tr><th width="20%"></th><th width="50%"></th><th width="30%"></th></tr></thead>
<tbody>
<tr><td><b>Contestant:</b></td><td>{contestant}</td><td rowspan=6><a href="{url}"><img src="{qr_file.name}" width=100 /></a></td></tr>
<tr><td><b>Task type:</b></td><td>{contestant.navigation_task.scorecard.get_calculator_display()}</td><td></td></tr>
<tr><td><b>Competition date:</b></td><td>{contestant.starting_point_time_local.strftime("%Y-%m-%d")}</td><td></td></tr>
<tr><td><b>Airspeed:</b></td><td>{"{:.0f}".format(contestant.air_speed)} knots</td><td></td></tr>
<tr><td><b>Task wind:</b></td><td>{"{:03.0f}".format(contestant.wind_direction)}@{"{:.0f}".format(contestant.wind_speed)}</td><td></td></tr>
<tr><td><b>Departure:</b></td><td>{contestant.takeoff_time.astimezone(contestant.navigation_task.contest.time_zone).strftime('%Y-%m-%d %H:%M:%S') if not contestant.adaptive_start else 'Take-off time is not measured'}</td><td></td></tr>
<tr><td><b>Start point:</b></td><td>{starting_point_text}</td><td></td></tr>
<tr><td><b>Finish by:</b></td><td>{finish_tracking_time} (tracking will stop)</td><td></td></tr>
</tbody>
</table>{f"<p>Using adaptive start, your start time will be set to the nearest whole minute you cross the infinite line going through the starting gate anywhere between one hour before and one hour after the selected starting point time (https://home.airsports.no/faq/#adaptiv-start)." if contestant.adaptive_start else ""}
<p></p><p></p><b>Rules</b><br/>{contestant.get_formatted_rules_description()}<p><center><h2>Good luck</h2></center></p>
"""

    pdf = MyFPDF(
        orientation="P", unit="mm", format=A4
    )  # TODO: flight_order_configuration.document_size)
    # 210 x 297 mm
    pdf.add_page()
    pdf.set_font("Times", "B", 12)

    pdf.write_html(recode_text(heading))
    pdf.set_text_color(0, 0, 255)
    pdf.set_xy(136, 90)
    pdf.write(10, "Share flight on Facebook", url)
    pdf.set_text_color(0, 0, 0)
    starting_point = generate_turning_point_image(
        contestant.navigation_task.route.waypoints, 0
    )
    starting_point_file = NamedTemporaryFile(suffix=".png")
    starting_point_file.write(starting_point.read())
    starting_point_file.seek(0)
    pdf.set_font("Arial", "B", 14)
    pdf.text(10, 178, "Starting point")
    pdf.text(110, 178, "Finish point")
    pdf.set_font("Arial", "B", 12)
    pdf.image(starting_point_file.name, x=10, y=180, w=90)
    waypoints = list(
        filter(
            lambda waypoint: waypoint.type != "dummy",
            contestant.navigation_task.route.waypoints,
        )
    )
    finish_point = generate_turning_point_image(
        waypoints,
        len(waypoints) - 1,
    )
    finish_point_file = NamedTemporaryFile(suffix=".png")
    finish_point_file.write(finish_point.read())
    finish_point_file.seek(0)
    pdf.image(finish_point_file.name, x=110, y=180, w=90)

    pdf.image("static/img/AirSportsLiveTracking.png", x=65, y=280, w=80)
    pdf.add_page()

    table = """<h1>Turning point times</h1><table width='100%' border="1" align="left">
    <thead><tr><th width="25%">Turning point</th><th width="25%">Distance</th><th width="15%">TT</th><th width="15%">TH</th><th width="20%">Time</th></tr></thead><tbody>
    """
    first_line = True
    local_time = "-"
    if contestant.navigation_task.route.first_takeoff_gate:
        local_time = contestant.gate_times.get(
            contestant.navigation_task.route.first_takeoff_gate.name, None
        )
        if local_time:
            local_time = local_time.astimezone(
                contestant.navigation_task.contest.time_zone
            ).strftime("%H:%M:%S")
    table += f"<tr><td>Takeoff gate</td><td>-</td><td>-</td><td>-</td><td>{local_time}</td></tr>"
    accumulated_distance = 0
    for waypoint in contestant.navigation_task.route.waypoints:  # type: Waypoint
        if not first_line:
            accumulated_distance += waypoint.distance_previous
        if waypoint.type not in ("secret", "dummy", "ul") and waypoint.time_check:
            bearing = waypoint.bearing_from_previous
            wind_correction_angle = calculate_wind_correction_angle(
                bearing,
                contestant.air_speed,
                contestant.wind_speed,
                contestant.wind_direction,
            )
            wind_bearing = normalise_bearing(bearing - wind_correction_angle)
            gate_time = contestant.gate_times.get(waypoint.name, None)
            local_waypoint_time = gate_time.astimezone(
                contestant.navigation_task.contest.time_zone
            )
            if gate_time is not None:
                table += f"<tr><td>{waypoint.name}</td><td>{f'{accumulated_distance / 1852:.2f} NM' if not first_line else '-'}</td><td>{f'{bearing:.0f}' if not first_line else '-'}</td><td>{f'{wind_bearing:.0f}' if not first_line else '-'}</td><td>{local_waypoint_time.strftime('%H:%M:%S')}</td></tr>"
                accumulated_distance = 0
                first_line = False
    local_time = "-"
    if contestant.navigation_task.route.first_landing_gate:
        local_time = contestant.gate_times.get(
            contestant.navigation_task.route.first_landing_gate.name, None
        )
        if local_time:
            local_time = local_time.astimezone(
                contestant.navigation_task.contest.time_zone
            ).strftime("%H:%M:%S")
    table += f"<tr><td>Landing gate</td><td>-</td><td>-</td><td>-</td><td>{local_time}</td></tr>"
    table += "</tbody></table>"
    pdf.set_font("Times", "B", 18)

    pdf.write_html(recode_text(table))

    pdf.set_font("Times", "B", 12)

    pdf.image("static/img/AirSportsLiveTracking.png", x=65, y=280, w=80)

    pdf.add_page()
    map_image, pdf_image = plot_route(
        contestant.navigation_task,
        A4,  # flight_order_configuration.document_size,
        zoom_level=flight_order_configuration.map_zoom_level,
        landscape=flight_order_configuration.map_orientation == LANDSCAPE,
        contestant=contestant,
        annotations=flight_order_configuration.map_include_annotations,
        waypoints_only=not flight_order_configuration.map_include_waypoints,
        dpi=flight_order_configuration.map_dpi,
        scale=flight_order_configuration.map_scale,
        map_source=flight_order_configuration.map_source,
        user_map_source=str(flight_order_configuration.map_user_source.map_file)
        if flight_order_configuration.map_user_source
        else "",
        line_width=flight_order_configuration.map_line_width,
        minute_mark_line_width=flight_order_configuration.map_minute_mark_line_width,
        colour=flight_order_configuration.map_line_colour,
    )
    mapimage_file = NamedTemporaryFile(suffix=".png")
    mapimage_file.write(map_image.read())
    mapimage_file.seek(0)
    # Negative values to account for margins
    pdf.image(mapimage_file.name, x=0, y=0, h=297)
    pdf.image("static/img/AirSportsLiveTrackingWhiteBG.png", x=150, y=288, w=50)
    if (
        contestant.navigation_task.scorecard.calculator != Scorecard.ANR_CORRIDOR
        and flight_order_configuration.include_turning_points
    ):
        insert_turning_point_images(contestant, pdf)
    if any(
        waypoint.type == "ul" for waypoint in contestant.navigation_task.route.waypoints
    ):
        insert_unknown_leg_images(contestant, pdf)
    return pdf.output()
