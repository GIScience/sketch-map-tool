import os
from pathlib import Path

import geopandas
import matplotlib.patches as mpatches
import numpy as np
from approvaltests import Reporter
from matplotlib import pyplot as plt
from matplotlib.widgets import Button
from numpy.typing import NDArray
from PIL import Image


class ImageApprover:
    def __init__(self, approved_path: Path, received_path: Path):
        self.approved_path = approved_path
        self.received_path = received_path
        if not self.approved_path.exists():
            img = Image.open(self.received_path)
            i = Image.new(mode="RGB", size=img.size)
            i.save(self.approved_path)

    def approve(self, *_):
        self.received_path.replace(self.approved_path)
        plt.close()

    def open(self):
        """Open dialog for visual comparison."""
        fig, axs = plt.subplots(1, 2)
        fig.subplots_adjust(bottom=0.2)
        img = Image.open(self.received_path)
        axs[0].imshow(img)
        axs[0].title.set_text("Received")
        axs[0].axis("off")
        img = Image.open(self.approved_path)
        axs[1].imshow(img)
        axs[1].title.set_text("Approved")
        axs[1].axis("off")

        ax2 = fig.add_axes((0.45, 0.05, 0.1, 0.075))
        button = Button(ax2, "Approve")
        button.on_clicked(self.approve)

        nodeid = os.environ["PYTEST_CURRENT_TEST"]
        nodeid_without_dir = nodeid.split("/")[-1]
        description = nodeid_without_dir.replace(" (call)", "")
        plt.figtext(
            0.5,
            0.01,
            description,
            wrap=True,
            horizontalalignment="center",
            fontsize=12,
        )
        plt.show()


class NDArrayApprover:
    def __init__(self, approved_path: Path, received_path: Path):
        self.approved_path = approved_path
        self.received_path = received_path
        if not self.approved_path.exists():
            self._save_ndarray(np.zeros((2, 2)), approved_path)

    @staticmethod
    def _load_ndarray(path) -> NDArray:
        with open(path, mode="rb") as file:
            return np.load(file)

    @staticmethod
    def _save_ndarray(array: NDArray, path):
        with open(path, mode="wb") as file:
            np.save(file, array)

    def approve(self, *_):
        self.received_path.replace(self.approved_path)
        plt.close()

    def open(self):
        """Open dialog for visual comparison."""
        fig, axs = plt.subplots(1, 2)
        fig.subplots_adjust(bottom=0.2)

        img = self._load_ndarray(self.received_path)
        axs[0].imshow(img, cmap="Greys")
        axs[0].title.set_text("Received")
        img = self._load_ndarray(self.approved_path)
        axs[1].imshow(img, cmap="Greys")
        axs[1].title.set_text("Approved")

        ax2 = fig.add_axes((0.45, 0.05, 0.1, 0.075))
        button = Button(ax2, "Approve")
        button.on_clicked(self.approve)
        plt.show()


class SketchMapToolApprover:
    def __init__(self, approved_path: Path, received_path: Path, sketch_map: Path):
        self.approved_path: Path = approved_path  # geojson
        self.received_path: Path = received_path  # geojson
        self.sketch_map: Path = sketch_map  # jpg

    def plot_difference(self, ax):
        """Plot difference between approved and received GeoJSON features."""
        if self.approved_path.exists() and self.approved_path.stat().st_size != 0:
            df_approved = geopandas.read_file(self.approved_path)
            df_approved.plot(ax=ax, facecolor="none", edgecolor="blue")
        df_received = geopandas.read_file(self.received_path)
        df_received.plot(ax=ax, facecolor="none", edgecolor="red")

    def plot_sketch_map(self, ax):
        """Plot sketch map image."""
        image = np.asarray(Image.open(self.sketch_map))
        ax.imshow(image)

    def approve(self, *_):
        self.received_path.replace(self.approved_path)
        plt.close()

    def open(self):
        """Open dialog for visual comparison."""
        fig, axs = plt.subplots(1, 2)
        fig.subplots_adjust(bottom=0.2)
        self.plot_sketch_map(axs[0])
        self.plot_difference(axs[1])

        blue_patch = mpatches.Patch(color="blue", label="Approved")
        red_patch = mpatches.Patch(color="red", label="Received")
        axs[1].legend(handles=[blue_patch, red_patch])

        ax_approve = fig.add_axes((0.45, 0.05, 0.1, 0.075))
        button = Button(ax_approve, "Approve")
        button.on_clicked(self.approve)
        plt.show()


class ImageReporter(Reporter):
    def report(
        self,
        received_path: str,
        approved_path: str,
    ) -> bool:
        ImageApprover(Path(approved_path), Path(received_path)).open()
        return True


class NDArrayReporter(Reporter):
    def report(self, received_path: str, approved_path: str) -> bool:
        NDArrayApprover(Path(approved_path), Path(received_path)).open()
        return True


class SketchMapToolReporter(Reporter):
    def __init__(self, sketch_map: Path):
        self.sketch_map: Path = sketch_map

    def report(self, received_path: str, approved_path: str) -> bool:
        SketchMapToolApprover(
            Path(approved_path),
            Path(received_path),
            self.sketch_map,
        ).open()
        return True
