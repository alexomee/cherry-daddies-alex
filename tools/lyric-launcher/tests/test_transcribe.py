import importlib

import pytest


def module():
    return importlib.import_module("transcribe_lyrics")


def test_repeats_and_offset_are_preserved():
    rows, notes = module().timed_lines({"segments": [
        {"start": 1, "end": 3, "text": "Это припев"},
        {"start": 10, "end": 12, "text": "Это припев"},
    ]}, offset=2.5)
    assert rows == [(3.5, "Это припев"), (12.5, "Это припев")]
    assert notes == []


def test_word_timing_splits_long_segment_without_inventing_times():
    words = [{"start": i, "end": i + .5, "word": f" слово{i}"}
             for i in range(20)]
    rows, _ = module().timed_lines({"segments": [{
        "start": 0, "end": 20, "text": "ignored", "words": words,
    }]}, offset=0)
    assert len(rows) > 1
    assert all(t in range(20) for t, _ in rows)
    assert " ".join(text for _, text in rows) == " ".join(f"слово{i}" for i in range(20))


def test_uncertain_recognition_is_reported_for_human_review():
    rows, notes = module().timed_lines({"segments": [
        {"start": 1, "end": 3, "text": "Сомнительные слова", "avg_logprob": -1.5},
        {"start": 5, "end": 7, "text": "Спасибо за просмотр", "no_speech_prob": .9},
    ]}, offset=0)
    assert rows == [(1, "Сомнительные слова")]
    assert len(notes) == 2


def test_empty_or_negative_output_cannot_become_a_stage_clip():
    with pytest.raises(ValueError):
        module().timed_lines({"segments": []}, offset=0)
    with pytest.raises(ValueError):
        module().timed_lines({"segments": [{"start": 1, "end": 2, "text": "x"}]}, offset=-5)
