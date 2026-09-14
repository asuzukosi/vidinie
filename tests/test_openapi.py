"""
the spec is the input to sdk and cli generation, so the shapes generators
depend on are worth pinning.
"""

import pytest

from api.main import app


@pytest.fixture(scope="module")
def spec():
    return app.openapi()


def response_schema(spec, path, method):
    content = spec["paths"][path][method]["responses"]["200"]["content"]
    return content["application/json"]["schema"]["$ref"].split("/")[-1]


def test_operation_ids_are_method_names_not_path_fragments(spec):
    ids = [
        op["operationId"]
        for operations in spec["paths"].values()
        for op in operations.values()
    ]
    assert "create_video_pipeline_from_file" in ids
    # the fastapi default appends the path and the verb to the route name
    assert not any(i.endswith(("_post", "_get", "_delete")) for i in ids), ids
    assert len(ids) == len(set(ids)), "duplicate operation ids break generation"


@pytest.mark.parametrize("path", [
    "/video-pipelines/{video_pipeline_id}/process",
    "/video-pipelines/{video_pipeline_id}/generate-scripts",
    "/video-pipelines/{video_pipeline_id}/generate",
])
def test_stage_routes_declare_the_summary_they_actually_return(spec, path):
    assert response_schema(spec, path, "post") == "VideoPipelineSummary"


@pytest.mark.parametrize("path", [
    "/video-pipelines/{video_pipeline_id}/output/download",
    "/video-pipelines/{video_pipeline_id}/output/stream",
])
def test_video_routes_are_mp4_and_say_when_it_is_not_ready(spec, path):
    responses = spec["paths"][path]["get"]["responses"]
    assert list(responses["200"]["content"]) == ["video/mp4"]
    assert "409" in responses and "404" in responses


def test_progress_route_is_small_enough_to_poll(spec):
    name = response_schema(spec, "/video-pipelines/{video_pipeline_id}/progress", "get")
    assert name == "VideoPipelineProgress"
    fields = spec["components"]["schemas"][name]["properties"]
    assert "video_ready" in fields
    assert len(fields) < 12, "a poll target should stay small"
