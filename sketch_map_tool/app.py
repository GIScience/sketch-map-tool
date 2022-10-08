"""
Configuration of the Flask app routes and, thus, the interface between backend and frontend
"""
import json
import os
from typing import List, Union, Tuple

from multiprocessing import Process

from flask import Flask, Response, redirect, render_template, request
from wtforms import Form, TextAreaField, validators

from sketch_map_tool.analyses import run_analyses
from sketch_map_tool.analyses.helpers import get_result_path
from sketch_map_tool.constants import (
    ANALYSES_OUTPUT_PATH,
    BBOX_TOO_BIG,
    ERROR_MSG_FOR_CODE,
    INVALID_STATUS_LINK_MESSAGE,
    NR_OF_ANALYSES_STEPS,
    TEMPLATE_ANALYSES,
    TEMPLATE_ANALYSES_RESULTS,
    ErrorCode,
    TEMPLATE_GENERATION, 
    GENERATION_OUTPUT_PATH,
    STATUS_UPDATES_GENERATION,
)
from sketch_map_tool.helper_modules.bbox_utils import (
    Bbox,
    BboxTooLargeException,
    is_bbox_str,
)
from sketch_map_tool.helper_modules.progress import (
    NoStatusFileException,
    get_nr_of_completed_steps,
    get_status_updates,
)
from sketch_map_tool.printer import generate_sketchmap
from sketch_map_tool.printer.modules.paper_formats.paper_formats import PaperFormat



class BboxForm(Form):  # type: ignore
    """
    Enables access to the input field bbox-input of the HTML template
    """

    bbox_input = TextAreaField(
        id="bbox-input",
        validators=[validators.InputRequired(), is_bbox_str],
        render_kw={"placeholder": "E.g.: 8.69142561,49.4102821,8.69372067,49.4115517;"},
    )


def create_app() -> Flask:  # noqa: C901
    """
    Create the Flask app
    """
    app = Flask(__name__)

    @app.route("/", methods=["GET", "POST"])
    def index() -> str:
        return render_template("index.html")

    @app.route("/analyses", methods=["GET", "POST"])
    def analyses() -> str:
        query_bbox = request.args.get("bbox")
        bbox_form = BboxForm(request.form)
        error_nr = request.args.get("error")
        if error_nr is not None and bbox_form.bbox_input.data is None:
            error_msg = ERROR_MSG_FOR_CODE.get(
                ErrorCode(int(error_nr)), "Unknown Error Code"
            )
            return render_template(
                TEMPLATE_ANALYSES, bbox_form=BboxForm(), outputs=dict(), msg=error_msg
            )
        if (
            query_bbox is not None
            and (bbox_form.bbox_input.data is None or bbox_form.bbox_input.data == "")
            and is_bbox_str(query_bbox)
        ):
            bbox_form.bbox_input.data = query_bbox
        if request.method == "POST":
            bbox_str = bbox_form.bbox_input.data
            if not is_bbox_str(bbox_str):
                return render_template(
                    TEMPLATE_ANALYSES,
                    bbox_form=bbox_form,
                    outputs=dict(),
                    msg="Invalid input. Please take a look at the bounding "
                    "box/-es you entered.",
                )
            try:
                return load_analyses(
                    bbox_form, bbox_str.split(";"), ANALYSES_OUTPUT_PATH
                )
            except BboxTooLargeException:
                return render_template(
                    TEMPLATE_ANALYSES,
                    bbox_form=bbox_form,
                    outputs=dict(),
                    msg=BBOX_TOO_BIG,
                )
        return render_template(
            TEMPLATE_ANALYSES, bbox_form=bbox_form, outputs=dict(), msg=""
        )

    @app.route("/generation", methods=["GET", "POST"])
    def generation() -> str:
        query_bbox = request.args.get("bbox")
        bbox_form = BboxForm(request.form)
        error_nr = request.args.get("error")
        if error_nr is not None and bbox_form.bbox_input.data is None:
            error_msg = ERROR_MSG_FOR_CODE.get(ErrorCode(int(error_nr)), "Unknown Error Code")
            return render_template(TEMPLATE_GENERATION, bbox_form=BboxForm(), outputs=dict(),
                                   msg=error_msg)
        if (query_bbox is not None and (bbox_form.bbox_input.data is None or
                                        bbox_form.bbox_input.data == "") and
                is_bbox_str(query_bbox)):
            bbox_form.bbox_input.data = query_bbox
        if request.method == "POST":
            bbox_str = bbox_form.bbox_input.data
            if not is_bbox_str(bbox_str):
                return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=dict(),
                                       msg="Invalid input. Please take a look at the bounding "
                                           "box/-es you entered.")
            if "format" in request.form.keys() and "height" in request.form.keys():
                paper_format_str = request.form["format"]
                try:
                    resolution = (int(request.form["width"].strip()),
                                  int(request.form["height"].strip()))
                except ValueError:
                    return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=dict(),
                                           msg="Invalid resolution. Only integer values are "
                                               "allowed.")
            else:
                return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=dict(),
                                       msg="The paper format selection and/or resolution seem to "
                                           "be missing.")
            try:
                bboxes = [Bbox.bbox_from_str(bbox) for bbox in bbox_str.split(";") if len(bbox) > 0]
                paper_format = PaperFormat.from_str(paper_format_str)
                if paper_format is None:
                    return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=dict(),
                                           msg="Invalid paper format selection, try 'a4'.")
                return load_printing(bbox_form,
                                     bboxes,
                                     GENERATION_OUTPUT_PATH,
                                     paper_format,
                                     resolution)
            except BboxTooLargeException:
                return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=dict(),
                                       msg=BBOX_TOO_BIG)
        return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=dict(), msg="")

    @app.route("/status")
    def status() -> Union[str, Response]:
        """
        Show status page for process specified by given parameters

        :return: HTML code of the status page
        """
        query_mode = request.args.get("mode")
        if query_mode == "analyses":
            name = "OSM Analyses"
            query_bbox = request.args.get("bbox")
            if query_bbox is None:
                return render_template(
                    TEMPLATE_ANALYSES,
                    bbox_form=BboxForm(),
                    outputs=dict(),
                    msg=INVALID_STATUS_LINK_MESSAGE,
                )
            result_path = get_result_path(
                Bbox.bbox_from_str(query_bbox), ANALYSES_OUTPUT_PATH
            )
            nr_of_steps = NR_OF_ANALYSES_STEPS + 1  # +1 because link is in last line
            try:
                steps_completed = get_nr_of_completed_steps(result_path)
                percentage = str(round(steps_completed / nr_of_steps * 100, 2)) + "%"
                outputs = get_status_updates(result_path)
                error = None
                download_link = None
                for output in outputs:
                    if "ERROR:" in output:
                        error = output
                        break
                    if ANALYSES_OUTPUT_PATH in output:
                        download_link = output
                        break
                results = []
                if download_link is not None:
                    result = {
                        "name": "Open your analyses' results",
                        "link": download_link,
                    }
                    results.append(result)
                bbox = query_bbox
            except ValueError:
                return redirect(
                    f"../../analyses?error={ErrorCode.INVALID_STATUS_LINK_MESSAGE.value}"
                )
            except NoStatusFileException:
                return redirect(
                    f"../../analyses?error={ErrorCode.NO_STATUS_FILE_MESSAGE.value}"
                )
        elif query_mode == "generation":
            name = "Sketch Map Generation"
            query_bbox = request.args.get("bbox")
            query_format = request.args.get("format")
            query_date = request.args.get("d")
            if query_bbox is None or query_date is None or query_format is None:
                return render_template(TEMPLATE_GENERATION, bbox_form=BboxForm(), outputs=dict(),
                                       msg=INVALID_STATUS_LINK_MESSAGE)
            paper_format = PaperFormat.from_str(query_format)
            if paper_format is None:
                return render_template(TEMPLATE_GENERATION, bbox_form=BboxForm(), outputs=dict(),
                                       msg=INVALID_STATUS_LINK_MESSAGE)
            result_path = generate_sketchmap.get_result_path(
                paper_format,
                Bbox.bbox_from_str(query_bbox),
                GENERATION_OUTPUT_PATH,
                query_date
            )
            nr_of_steps = len(STATUS_UPDATES_GENERATION) + 1  # +1 because link is in last line
            try:
                steps_completed = get_nr_of_completed_steps(result_path)
                percentage = str(round(steps_completed / nr_of_steps * 100, 2)) + "%"
                outputs = get_status_updates(result_path)
                error = None
                download_link = None
                for output in outputs:
                    if "ERROR:" in output:
                        error = output
                        break
                    if GENERATION_OUTPUT_PATH in output:
                        download_link = output
                        break
                results = []
                if download_link is not None:
                    result = {"name": "Open your Sketch Map", "link": download_link}
                    results.append(result)
                bbox = query_bbox
            except ValueError:
                return redirect(
                    f"../../generation?error={ErrorCode.INVALID_STATUS_LINK_MESSAGE.value}")
            except NoStatusFileException:
                return redirect(f"../../generation?error={ErrorCode.NO_STATUS_FILE_MESSAGE.value}")
        else:
            return redirect(
                f"../../analyses?error={ErrorCode.INVALID_STATUS_LINK_MESSAGE.value}"
            )
        return render_template(
            "progress.html",
            NAME=name,
            BBOX=bbox,
            NR_OF_STEPS=nr_of_steps,
            STEPS_COMPLETED=steps_completed,
            PERCENTAGE=percentage,
            OUTPUTS=outputs,
            RESULTS=results,
            ERROR=error,
        )

    @app.route(f"/{ANALYSES_OUTPUT_PATH}/<output_name>.html")
    def result(output_name: str) -> Union[str, Response]:
        """
        Render analyses result page based on JSON contents stored under 'output_name'

        :param output_name: Name of the JSON file stored in 'ANALYSES_OUTPUT_PATH' containing the
                            results that should be displayed
        :return: HTML code of the result page or, in case the JSON could not be found, a redirection
                 to the analyses page with a fitting error message
        """
        try:
            with open(
                f"{ANALYSES_OUTPUT_PATH}{os.sep}{output_name}.json",
                "r",
                encoding="utf8",
            ) as fr:
                results = json.load(fr)
        except FileNotFoundError:
            return redirect(
                f"../../analyses?error={ErrorCode.RESULT_COULD_NOT_BE_LOADED.value}"
            )
        return render_template(TEMPLATE_ANALYSES_RESULTS, **results)

    return app


def load_analyses(bbox_form: BboxForm, bboxes: List[str], output_path: str) -> str:
    """
    Execute the sketch map fitness analyses and load a page containing
    links to the status pages.

    :param bbox_form: The input form, where the bbox (-list) has been entered (to keep the input
                      when reloading the page)
    :param bboxes: List of bboxes to analyse
    :param output_path: The location where the analyses' results will be saved
    :return: The generated HTML code including links to the analyses' status pages
    :raises BboxTooLargeException: Selected bounding box is bigger than 50 km^2
    """
    print("Loading analyses...")
    bbox_objects = []
    for bbox_str in bboxes:
        if len(bbox_str.strip()) == 0:
            continue
        bbox = Bbox.bbox_from_str(bbox_str)
        if bbox.get_area() > 50:
            raise BboxTooLargeException()
        bbox_objects.append(bbox)
    outputs = run_analyses.run(bbox_objects, output_path)
    return render_template(
        TEMPLATE_ANALYSES, bbox_form=bbox_form, outputs=outputs, msg=""
    )


def load_printing(bbox_form: BboxForm,
                  bboxes: List[Bbox],
                  output_path: str,
                  paper_format: PaperFormat,
                  resolution: Tuple[int, int]) -> str:
    """
    Execute the sketch map fitness (PDF) generation and load a page containing
    links to the status pages.

    :param bbox_form: The input form, where the bbox (-list) has been entered (to keep the input
                      when reloading the page)
    :param bboxes: List of bboxes to generate sketch maps of
    :param output_path: The location where the sketch maps will be stored
    :param paper_format: Paper format of the generated PDF(s)
    :param resolution: Resolution of the map image(s) to be added to the sketch map PDF(s)
    :return: The generated HTML code including links to the status pages
    :raises BboxTooLargeException: Selected bounding box is bigger than 50 km^2
    """
    print("Loading generation...")
    outputs = {}
    for bbox in bboxes:
        if bbox.get_area() > 50:
            raise BboxTooLargeException()
        p_printing = Process(target=generate_sketchmap.generate,
                             args=(paper_format, bbox, resolution, output_path))
        p_printing.start()
        name = f"Sketch Map for area {bbox}"
        outputs[name] = generate_sketchmap.get_status_link(paper_format, bbox)
    return render_template(TEMPLATE_GENERATION, bbox_form=bbox_form, outputs=outputs, msg="")


if __name__ == "__main__":
    flask_app = create_app()
    flask_app.run()
