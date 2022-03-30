from flask import Flask, render_template, request
from wtforms import Form, TextAreaField, validators
from typing import List
from helper_modules.bbox_utils import (is_bbox_str, BboxTooLargeException, Bbox)
from analyses import run_analyses
from constants import (ANALYSES_OUTPUT_PATH, INVALID_STATUS_LINK_MESSAGE,
                       TEMPLATE_ANALYSES, NO_STATUS_FILE_MESSAGE, NR_OF_ANALYSES_STEPS)
from analyses.helpers import get_result_path
from helper_modules.progress import get_status_updates, get_nr_of_completed_steps, \
    NoStatusFileException


class BboxForm(Form):
    """
    Enables access to the input field bbox_input of the HTML template
    """
    bbox_input = TextAreaField(id='bbox_input', validators=[validators.InputRequired(), is_bbox_str],
                               render_kw=
                               {"placeholder": "E.g.: 8.69142561,49.4102821,8.69372067,49.4115517;"}
                               )


def create_app():
    app = Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return render_template('index.html')

    @app.route('/analyses', methods=['GET', 'POST'])
    def analyses():
        bbox_form = BboxForm(request.form)
        if request.method == 'POST':
            bbox_str = bbox_form.bbox_input.data
            if not is_bbox_str(bbox_str):
                return render_template(TEMPLATE_ANALYSES, bbox_form=bbox_form, outputs=dict(),
                                       msg="Invalid input. Please take a look at the bounding box/-es "
                                           "you entered.")
            return load_analyses(bbox_form, bbox_str.split(";"), ANALYSES_OUTPUT_PATH)
        return render_template(TEMPLATE_ANALYSES, bbox_form=bbox_form, outputs=dict(), msg="")

    @app.route('/status')
    def status():
        """
        Show status page for process specified by given parameters

        :return: HTML code of the status page
        """
        query_mode = request.args.get("mode")
        if query_mode == "analyses":
            name = "OSM Analyses"
            query_bbox = request.args.get("bbox")
            if query_bbox is None:
                return render_template(TEMPLATE_ANALYSES, bbox_form=BboxForm(), outputs=dict(),
                                       msg=INVALID_STATUS_LINK_MESSAGE)
            result_path = get_result_path(Bbox.bbox_from_str(query_bbox), ANALYSES_OUTPUT_PATH)
            nr_of_steps = NR_OF_ANALYSES_STEPS+1  # +1 because link is in last line
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
                    result = {"name": "Open your analyses' results", "link": download_link}
                    results.append(result)
                bbox = query_bbox
            except ValueError:
                return render_template(TEMPLATE_ANALYSES, bbox_form=BboxForm(), outputs=dict(),
                                       msg=INVALID_STATUS_LINK_MESSAGE)
            except NoStatusFileException:
                return render_template(TEMPLATE_ANALYSES, bbox_form=BboxForm(), outputs=dict(),
                                       msg=NO_STATUS_FILE_MESSAGE)
        else:
            return render_template(TEMPLATE_ANALYSES, bbox_form=BboxForm(), outputs=dict(),
                                   msg=INVALID_STATUS_LINK_MESSAGE)
        return render_template('progress.html', NAME=name, BBOX=bbox, NR_OF_STEPS=nr_of_steps,
                               STEPS_COMPLETED=steps_completed, PERCENTAGE=percentage, OUTPUTS=outputs,
                               RESULTS=results, ERROR=error)
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
    return render_template(TEMPLATE_ANALYSES, bbox_form=bbox_form, outputs=outputs, msg="")


if __name__ == "__main__":
    app = create_app()
    app.run()



