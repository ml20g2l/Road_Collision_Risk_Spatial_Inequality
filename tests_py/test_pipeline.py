from src.pipeline import STAGES, selected_stages


def test_pipeline_stage_names_are_unique() -> None:
    names = [stage.name for stage in STAGES]
    assert len(names) == len(set(names))


def test_pipeline_download_is_first() -> None:
    assert STAGES[0].name == "download"


def test_skip_download_preserves_remaining_order() -> None:
    assert [stage.name for stage in selected_stages(True)] == [stage.name for stage in STAGES[1:]]


def test_every_stage_declares_an_output() -> None:
    assert all(stage.outputs for stage in STAGES)
