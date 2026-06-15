from collections import Counter, defaultdict
from datetime import datetime
from itertools import accumulate

import pandas
import pygal
from dateutil.relativedelta import relativedelta
from flask_babel import _
from pygal.graph.graph import Graph

FMT = "%Y-%m"


def create_monthly_bins(start: datetime, end: datetime) -> dict:
    start = start.replace(day=1)
    end = end.replace(day=1) + relativedelta(months=1)
    date_range = pandas.date_range(start=start, end=end, freq="M", normalize=True)
    month_series = pandas.Series(0, index=date_range.strftime(FMT))
    return month_series.to_dict()


def created_and_downloaded_sketch_maps(stats: list[dict]) -> Graph:
    created_timestamps = [row["created"] for row in stats]
    monthly_bins = create_monthly_bins(min(created_timestamps), max(created_timestamps))

    created = [1] * len(stats)
    downloaded = []
    for row in stats:
        if row["downloaded"] is not None:
            downloaded.append(1)
        else:
            downloaded.append(0)

    created_by_month = defaultdict(int, monthly_bins)
    downloaded_by_month = defaultdict(int, monthly_bins)

    for ts, c, d in zip(created_timestamps, created, downloaded):
        month = ts.strftime(FMT)
        created_by_month[month] += c
        downloaded_by_month[month] += d

    created_accumulated = list(accumulate(created_by_month.values()))
    downloaded_accumulated = list(accumulate(downloaded_by_month.values()))
    timestamps = list(monthly_bins.keys())

    line_chart = pygal.Line()
    line_chart.title = _("How many sketch maps have been created and downloaded?")
    line_chart.x_labels = timestamps
    line_chart.add(_("Created"), created_accumulated)
    line_chart.add(_("Downloaded"), downloaded_accumulated)

    return line_chart


def uploads_and_downloads(stats: list[dict]) -> Graph:
    created_timestamps = [row["created"] for row in stats]
    monthly_bins = create_monthly_bins(min(created_timestamps), max(created_timestamps))

    downloads = [row["downloads"] for row in stats]
    uploads = []
    for row in stats:
        if row["uploads"] > 0:
            uploads.append(1)
        else:
            uploads.append(0)

    uploads_per_month = defaultdict(int, monthly_bins)
    downloads_per_month = defaultdict(int, monthly_bins)

    for ts, u, d in zip(created_timestamps, uploads, downloads):
        month = ts.strftime(FMT)
        uploads_per_month[month] += u
        downloads_per_month[month] += d

    uploads_accumulated = list(accumulate(uploads_per_month.values()))
    downloads_accumulated = list(accumulate(downloads_per_month.values()))
    timestamps = list(monthly_bins.keys())

    line_chart = pygal.Line()
    line_chart.title = _(
        (
            "For how many sketch maps have markings been "
            "uploaded and results been download?"
        )
    )
    line_chart.x_labels = timestamps
    line_chart.add(_("Uploads"), uploads_accumulated)
    line_chart.add(_("Downloads"), downloads_accumulated)

    return line_chart


def layer_distribution(stats: list[dict]) -> Graph:
    layers = [row["layer"] for row in stats]
    layers = list(
        map(
            lambda layer: "oam" if layer.startswith("oam") else layer,
            layers,
        )
    )
    counts = dict(Counter(layers))

    bar_chart = pygal.HorizontalBar()
    bar_chart.title = _("For which layers have sketch maps been created?")
    for key, value in counts.items():
        bar_chart.add(key, value)

    return bar_chart


def format_distribution(stats: list[dict]) -> Graph:
    formats = [row["format"] for row in stats]
    counts = dict(Counter(formats))

    bar_chart = pygal.HorizontalBar()
    bar_chart.title = _("For which format have sketch maps been created?")
    for key, value in counts.items():
        bar_chart.add(key, value)

    return bar_chart


def result_download_distribution(stats: list[dict]) -> Graph:
    uploads = []
    downloads = []
    downloads_raster = []
    downloads_vector = []

    for row in stats:
        if row["uploads"] > 0:
            uploads.append(1)
        else:
            uploads.append(0)
        downloads.append(row["downloads"])
        downloads_raster.append(row["downloads_raster"])
        downloads_vector.append(row["downloads_vector"])

    bar_chart = pygal.HorizontalBar()
    bar_chart.title = _("Which result types have been downloaded?")
    bar_chart.add("None", sum(uploads) - sum(downloads))
    bar_chart.add("Any", sum(downloads))
    bar_chart.add("Raster", sum(downloads_raster))
    bar_chart.add("Vector", sum(downloads_vector))

    return bar_chart


def consent_distribution(stats: list[dict]):
    consensus = [row["consenses"] for row in stats]
    counts = dict(Counter(consensus))

    bar_chart = pygal.HorizontalBar()
    bar_chart.title = _(
        (
            "How many sketch maps with markings have been uploaded where the user "
            "agreed to let them be used for improvement of the Sketch Map Tool?"
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
