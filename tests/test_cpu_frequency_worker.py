from types import SimpleNamespace
import pytest
from workers.cpu_frequency_worker import CpuFrequencyWorker


def test_cpu_frequency_worker_ghz_format(monkeypatch):
    """Частота >= 1000 МГц должна форматироваться в ГГц."""
    mock_freq = SimpleNamespace(current=2450.0, min=800.0, max=4200.0)

    monkeypatch.setattr(
        "workers.cpu_frequency_worker.psutil.cpu_freq",
        lambda: mock_freq,
    )

    worker = CpuFrequencyWorker()
    result = worker.fetch_data()

    assert result == "Частота CPU: 2.45 ГГц"


def test_cpu_frequency_worker_mhz_format(monkeypatch):
    """Частота < 1000 МГц должна форматироваться в МГц."""
    mock_freq = SimpleNamespace(current=800.0, min=400.0, max=1200.0)

    monkeypatch.setattr(
        "workers.cpu_frequency_worker.psutil.cpu_freq",
        lambda: mock_freq,
    )

    worker = CpuFrequencyWorker()
    result = worker.fetch_data()

    assert result == "Частота CPU: 800 МГц"


@pytest.mark.parametrize("invalid_freq", [None, SimpleNamespace(current=0.0), SimpleNamespace(current=-100.0)])
def test_cpu_frequency_worker_unavailable_data(monkeypatch, invalid_freq):
    """При None или значении <= 0 должно возвращаться сообщение о недоступности."""
    monkeypatch.setattr(
        "workers.cpu_frequency_worker.psutil.cpu_freq",
        lambda: invalid_freq,
    )

    worker = CpuFrequencyWorker()
    result = worker.fetch_data()

    assert result == "Частота CPU: данные недоступны"


def test_cpu_frequency_worker_handles_exception(monkeypatch):
    """Исключения при вызове psutil.cpu_freq должны корректно перехватываться."""
    def raise_error():
        raise PermissionError("Access denied")

    monkeypatch.setattr(
        "workers.cpu_frequency_worker.psutil.cpu_freq",
        raise_error,
    )

    worker = CpuFrequencyWorker()
    result = worker.fetch_data()

    assert result == "Частота CPU: ошибка (Access denied)"


@pytest.mark.parametrize(
    "mhz, expected",
    [
        (1000.0, "1.00 ГГц"),
        (3599.9, "3.60 ГГц"),
        (999.0, "999 МГц"),
        (500.4, "500 МГц"),
    ],
)
def test_format_frequency_static_method(mhz, expected):
    """Прямое тестирование вспомогательного метода форматирования."""
    assert CpuFrequencyWorker._format_frequency(mhz) == expected