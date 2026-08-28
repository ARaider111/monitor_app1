import os
from types import SimpleNamespace
import pytest
from workers.disk_worker import DiskWorker


def test_disk_worker_calculates_usage_and_speed(monkeypatch):
    """Проверка расчета использования диска и вычисления скорости I/O."""
    # Мок времени
    time_mock_values = [100.0, 102.0]
    monkeypatch.setattr("workers.disk_worker.time.time", lambda: time_mock_values.pop(0))

    # Мок IO
    io_initial = SimpleNamespace(read_bytes=100 * 1024 * 1024, write_bytes=50 * 1024 * 1024)
    io_current = SimpleNamespace(read_bytes=120 * 1024 * 1024, write_bytes=60 * 1024 * 1024)
    io_mock_values = [io_initial, io_current]
    monkeypatch.setattr(
        "workers.disk_worker.psutil.disk_io_counters",
        lambda: io_mock_values.pop(0),
    )

    usage_mock = SimpleNamespace(
        used=50 * (1024**3),
        total=100 * (1024**3),
        percent=50.0,
    )
    monkeypatch.setattr("workers.disk_worker.psutil.disk_usage", lambda path: usage_mock)

    # Задаем имя ОС как POSIX (Linux)
    monkeypatch.setattr("workers.disk_worker.os.name", "posix")

    worker = DiskWorker()
    result = worker.fetch_data()

    expected = "Диск (/): 50.0/100.0 ГБ (50.0%) | R: 10.0 МБ/с, W: 5.0 МБ/с"
    assert result == expected


@pytest.mark.parametrize(
    "os_name, expected_path",
    [
        ("nt", "C:\\"),
        ("posix", "/"),
    ],
)
def test_disk_worker_root_path_selection(monkeypatch, os_name, expected_path):
    """Проверка выбора корневого пути для Windows и Linux."""
    monkeypatch.setattr("workers.disk_worker.os.name", os_name)
    monkeypatch.setattr("workers.disk_worker.time.time", lambda: 100.0)
    monkeypatch.setattr(
        "workers.disk_worker.psutil.disk_io_counters",
        lambda: SimpleNamespace(read_bytes=0, write_bytes=0),
    )

    passed_paths = []

    def mock_disk_usage(path):
        passed_paths.append(path)
        return SimpleNamespace(used=0, total=1024**3, percent=0.0)

    monkeypatch.setattr("workers.disk_worker.psutil.disk_usage", mock_disk_usage)

    worker = DiskWorker()
    result = worker.fetch_data()

    assert passed_paths[-1] == expected_path
    assert f"Диск ({expected_path})" in result


def test_disk_worker_handles_none_io_counters(monkeypatch):
    """Если счетчики ввода-вывода недоступны (None), скорости должны быть 0.0."""
    monkeypatch.setattr("workers.disk_worker.time.time", lambda: 100.0)
    monkeypatch.setattr("workers.disk_worker.psutil.disk_io_counters", lambda: None)
    monkeypatch.setattr(
        "workers.disk_worker.psutil.disk_usage",
        lambda path: SimpleNamespace(used=20 * (1024**3), total=100 * (1024**3), percent=20.0),
    )

    worker = DiskWorker()
    result = worker.fetch_data()

    assert "R: 0.0 МБ/с, W: 0.0 МБ/с" in result


def test_disk_worker_state_updates_between_calls(monkeypatch):
    """Проверка обновления внутренних переменных _last_io и _last_time."""
    time_mock = [10.0, 20.0]
    monkeypatch.setattr("workers.disk_worker.time.time", lambda: time_mock.pop(0))

    io_1 = SimpleNamespace(read_bytes=100, write_bytes=100)
    io_2 = SimpleNamespace(read_bytes=200, write_bytes=200)
    io_mock = [io_1, io_2]
    monkeypatch.setattr("workers.disk_worker.psutil.disk_io_counters", lambda: io_mock.pop(0))
    monkeypatch.setattr(
        "workers.disk_worker.psutil.disk_usage",
        lambda path: SimpleNamespace(used=0, total=1024**3, percent=0),
    )

    worker = DiskWorker()
    assert worker._last_time == 10.0
    assert worker._last_io == io_1

    worker.fetch_data()
    assert worker._last_time == 20.0
    assert worker._last_io == io_2