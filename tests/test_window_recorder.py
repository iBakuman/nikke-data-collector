import os

from nikke_arena.window_recorder import WindowRecorder


def test_window_recorder(manager):
    output_dir = os.path.join("testdata", "recordings")
    os.makedirs(output_dir, exist_ok=True)
    recorder = WindowRecorder(window_manager=manager)
    assert recorder.start_recording(filename="test_recording.mp4") is True
    recorder.stop_recording()
