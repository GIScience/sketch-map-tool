from collections import Counter, defaultdict
from datetime import datetime
from itertools import accumulate

import pandas
import pygal
from dateutil.relativedelta import relativedelta
from flask_babel import _
from pygal.graph.bar import Bar
from pygal.graph.graph import Graph
from pygal.style import Style
from pygal_maps_world.maps import COUNTRIES, World

FMT = "%Y-%m"
STYLE = Style(
    background="transparent",
    plot_background="#fff",
)


def create_monthly_bins(start: datetime, end: datetime) -> dict:
    start = start.replace(day=1)
    end = end.replace(day=1) + relativedelta(months=1)
    date_range = pandas.date_range(start=start, end=end, freq="M", normalize=True)
    month_series = pandas.Series(0, index=date_range.strftime(FMT))
    return month_series.to_dict()


def get_created_sketch_maps_number(stats):
    # Sketch maps which has been created AND downloaded
    downloaded = []
    for row in stats:
        if row["downloaded"] is not None:
            downloaded.append(1)
        else:
            downloaded.append(0)
    return sum(downloaded)


def get_created_sketch_maps(stats: list[dict]) -> Graph:
    # Sketch maps which has been created AND downloaded
    created_timestamps = [row["created"] for row in stats]
    monthly_bins = create_monthly_bins(min(created_timestamps), max(created_timestamps))
    downloaded = []
    for row in stats:
        if row["downloaded"] is not None:
            downloaded.append(1)
        else:
            downloaded.append(0)
    downloaded_by_month = defaultdict(int, monthly_bins)
    for ts, d in zip(created_timestamps, downloaded):
        month = ts.strftime(FMT)
        downloaded_by_month[month] += d
    downloaded_accumulated = list(accumulate(downloaded_by_month.values()))
    timestamps = list(monthly_bins.keys())

    # x.size = y
    assert len(timestamps) == len(downloaded_accumulated)
    line_chart = pygal.Line(
        style=STYLE,
        show_legend=False,
        x_label_rotation=20,
        x_labels_major_every=3,
    )
    line_chart.title = _("How many Sketch Maps have been created?")
    line_chart.x_labels = timestamps
    line_chart.add(_(""), downloaded_accumulated)

    return line_chart


def get_detected_markings_number(stats: list[dict]) -> int:
    return sum([row["downloads"] for row in stats])


def get_detected_markings(stats: list[dict]) -> Graph:
    # only look at sketch maps for which download happened
    created_timestamps = [row["created"] for row in stats]
    monthly_bins = create_monthly_bins(min(created_timestamps), max(created_timestamps))
    downloads = [row["downloads"] for row in stats]
    downloads_per_month = defaultdict(int, monthly_bins)
    for ts, d in zip(created_timestamps, downloads):
        month = ts.strftime(FMT)
        downloads_per_month[month] += d
    downloads_accumulated = list(accumulate(downloads_per_month.values()))
    timestamps = list(monthly_bins.keys())

    # x.size = y
    assert len(timestamps) == len(downloads_accumulated)
    line_chart = pygal.Line(
        style=STYLE,
        show_legend=False,
        x_label_rotation=20,
        x_labels_major_every=3,
    )
    line_chart.title = _("For how many Sketch Maps did we detect markings?")
    line_chart.x_labels = timestamps
    line_chart.add(_(""), downloads_accumulated)

    return line_chart


def layer_distribution(stats: list[dict]) -> Graph:
    # only look at sketch maps for which downloads happened
    layers = [row["layer"] for row in stats if row["downloaded"] is not None]
    layers = list(
        map(
            lambda layer: "oam" if layer.startswith("oam") else layer,
            layers,
        )
    )
    counts = dict(Counter(layers))

    bar_chart = pygal.HorizontalBar(
        style=STYLE,
        print_values=True,
        print_zeroes=False,
    )
    bar_chart.title = _(
        "Which baselayers were chosen most frequently for map generation?"
    )
    for key, value in counts.items():
        bar_chart.add(key.upper(), value)

    return bar_chart


def format_distribution(stats: list[dict]) -> Graph:
    # only look at sketch maps for which downloads happened
    formats = [row["format"] for row in stats if row["downloaded"] is not None]
    counts = dict(Counter(formats))

    bar_chart = pygal.HorizontalBar(
        style=STYLE,
        print_values=True,
        print_zeroes=False,
    )
    bar_chart.title = _(
        "Which paper size was chosen most frequently for map generation?"
    )
    counts_sorted_by_key = dict(sorted(counts.items()))
    for key, value in counts_sorted_by_key.items():
        bar_chart.add(key.title(), value)

    return bar_chart


def result_download_distribution(stats: list[dict]) -> Graph:
    uploads = []
    downloads = []
    downloads_raster = []
    downloads_vector = []

    for row in stats:
        if row["downloaded"] is None:
            # Sketch Map never got downloaded after creation
            continue

        if row["uploads"] > 0:
            uploads.append(1)
        else:
            uploads.append(0)

        downloads.append(row["downloads"])
        downloads_raster.append(row["downloads_raster"])
        downloads_vector.append(row["downloads_vector"])

    bar_chart = pygal.HorizontalBar(
        style=STYLE,
        print_values=True,
        print_zeroes=False,
    )
    bar_chart.title = _("Which result types have been downloaded?")
    bar_chart.add("Any", sum(downloads))
    bar_chart.add("None", abs(sum(uploads) - sum(downloads)))
    bar_chart.add("Raster", sum(downloads_raster))
    bar_chart.add("Vector", sum(downloads_vector))

    return bar_chart


def consent_distribution(stats: list[dict]):
    # only look at sketch maps for which upload happened
    consensus = [row["consenses"] for row in stats if row["uploads"] > 0]
    counts = dict(Counter(consensus))

    bar_chart = pygal.HorizontalBar(
        style=STYLE,
        print_values=True,
        print_zeroes=False,
    )
    bar_chart.title = _(
        (
            "Consent: How many users agreed to let us use their "
            "marked sketch maps for further improvement of the Sketch Map Tool?"
        )
    )
    try:
        bar_chart.add("Agreed ", counts[1])
    except KeyError:
        bar_chart.add("Agreed ", 0)

    try:
        bar_chart.add("Rejected", counts[0])
    except KeyError:
        bar_chart.add("Rejected", 0)

    return bar_chart


def sketch_maps_by_country_map(stats: list[dict]):
    iso_a2 = [
        row["iso_a2"].lower()
        for row in stats
        if row["downloaded"] is not None and row["iso_a2"] is not None
    ]
    iso_a2_valid = [i for i in iso_a2 if i in COUNTRIES.keys()]
    iso_a2_count = dict(Counter(iso_a2_valid))
    iso_a2_count_over_1000 = {k: v for k, v in iso_a2_count.items() if v >= 1000}
    iso_a2_count_over_100 = {
        k: v for k, v in iso_a2_count.items() if v >= 100 and v < 1000
    }
    iso_a2_count_over_0 = {k: v for k, v in iso_a2_count.items() if v > 0 and v < 100}

    # https://colorbrewer2.org/#type=sequential&scheme=YlOrRd&n=3
    style = Style(
        background="transparent",
        plot_background="#fff",
        colors=(
            "#f03b20",
            "#feb24c",
            "#ffeda0",
        ),
    )
    worldmap_chart = World(legend=False, style=style)
    worldmap_chart.title = _("How many Sketch Maps have been created per country?")
    worldmap_chart.add(">=1000", iso_a2_count_over_1000)
    worldmap_chart.add(">=100", iso_a2_count_over_100)
    worldmap_chart.add(">=0", iso_a2_count_over_0)
    return worldmap_chart


def sketch_maps_by_country_table(stats: list[dict]):
    iso_a2 = [
        row["iso_a2"].lower()
        for row in stats
        if row["downloaded"] is not None and row["iso_a2"] is not None
    ]
    iso_a2_valid = [i for i in iso_a2 if i in COUNTRIES.keys()]
    iso_a2_count = dict(Counter(iso_a2_valid))

    bar_chart = Bar(legend=False, style=STYLE)
    bar_chart.title = _("How many Sketch Maps have been created per country?")
    bar_chart.x_labels = list(iso_a2_count.keys())
    bar_chart.add("Sketch Maps", list(iso_a2_count.values()))
    return bar_chart
