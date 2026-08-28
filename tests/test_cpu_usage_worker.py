import pytest
from workers.cpu_usage_worker import CpuUsageWorker


def test_cpu_usage_worker_normal_cores(monkeypatch):
    """Проверка расчета среднего и формата для системы с 4 ядрами."""
    cores_data = [10.0, 20.0, 30.0, 40.0] 

    monkeypatch.setattr(
        "workers.cpu_usage_worker.psutil.cpu_percent",
        lambda *args, **kwargs: cores_data,
    )

    worker = CpuUsageWorker()
    result = worker.fetch_data()

    expected = "Загрузка CPU: 25.0% [C1: 10%, C2: 20%, C3: 30%, C4: 40%]"
    assert result == expected


def test_cpu_usage_worker_more_than_six_cores(monkeypatch):
    """Проверка усечения вывода и счетчика оставшихся ядер при > 6 ядрах."""
    cores_data = [50.0] * 8

    monkeypatch.setattr(
        "workers.cpu_usage_worker.psutil.cpu_percent",
        lambda *args, **kwargs: cores_data,
    )

    worker = CpuUsageWorker()
    result = worker.fetch_data()

    expected = "Загрузка CPU: 50.0% [C1: 50%, C2: 50%, C3: 50%, C4: 50%, C5: 50%, C6: 50%, +2 ядер]"
    assert result == expected


def test_cpu_usage_worker_empty_cores(monkeypatch):
    """Проверка корректной обработки при пустом списке ядер."""
    monkeypatch.setattr(
        "workers.cpu_usage_worker.psutil.cpu_percent",
        lambda *args, **kwargs: [],
    )

    worker = CpuUsageWorker()
    result = worker.fetch_data()

    assert result == "Загрузка CPU: 0.0% []"


def test_cpu_usage_worker_initialization_calls_psutil(monkeypatch):
    """Проверка вызова psutil.cpu_percent(percpu=True) при инициализации."""
    calls = []

    def mock_cpu_percent(*args, **kwargs):
        calls.append(kwargs)
        return [0.0]

    monkeypatch.setattr(
        "workers.cpu_usage_worker.psutil.cpu_percent",
        mock_cpu_percent,
    )

    CpuUsageWorker()

    assert len(calls) == 1
    assert calls[0].get("percpu") is True