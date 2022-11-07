from reportlab.graphics.shapes import Drawing

from sketch_map_tool.map_generation import generate_pdf


def test_get_globes(format_):
    globes = generate_pdf.get_globes(format_.globe_scale)
    for globe in globes:
        assert isinstance(globe, Drawing)


def test_get_compass(format_):
    compass = generate_pdf.get_compass(format_.compass_scale)
    assert isinstance(compass, Drawing)
