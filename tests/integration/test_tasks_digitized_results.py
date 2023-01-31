from io import BytesIO

from numpy import ndarray

from sketch_map_tool import tasks


def test_t_read_file(file_ids):
    task = tasks.t_read_file.apply_async(args=[file_ids[0]])
    result = task.wait()
    assert isinstance(result, bytes)


def test_t_buffer_to_array(sketch_map_buffer):
    task = tasks.t_to_array.apply_async(args=[sketch_map_buffer.read()])
    result = task.wait()
    assert isinstance(result, ndarray)


def test_t_clip(sketch_map, map_frame):
    task = tasks.t_clip.apply_async(args=[sketch_map, map_frame])
    result = task.wait()
    assert isinstance(result, ndarray)


def test_t_detect(sketch_map_frame_markings, map_frame):
    task = tasks.t_detect.apply_async(
        args=[sketch_map_frame_markings, map_frame, "red"]
    )
    result = task.wait()
    assert isinstance(result, ndarray)


def test_t_georeference(sketch_map_frame_markings_detected, bbox):
    task = tasks.t_georeference.apply_async(
        args=[sketch_map_frame_markings_detected, bbox]
    )
    result = task.wait()
    assert isinstance(result, BytesIO)


def test_t_polygonize(sketch_map_frame_markings_detected_buffer):
    task = tasks.t_polygonize.apply_async(
        args=[sketch_map_frame_markings_detected_buffer, "red"]
    )
    result = task.wait()
    assert isinstance(result, BytesIO)


# TODO
# def test_t_merge(geojsons):
#     task = tasks.t_merge.apply_async(args=[geojsons])
#     result = task.wait()
#     assert isinstance(result, BytesIO)


# TODO: Not working because first a sketch map with its map frame has to be created
# def test_generate_digitized_results(file_ids):
#     workflow = tasks.generate_digitized_results(file_ids)
#     result = workflow.apply().get()
#     assert isinstance(result, BytesIO)
