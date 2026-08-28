from types import SimpleNamespace

from workers.cpu_worker import CpuTempWorker


def test_cpu_temperature_from_powershell(monkeypatch):
    """Температура должна быть получена из WMI Windows-хоста."""

    monkeypatch.setattr(
        "workers.cpu_worker.shutil.which",
        lambda command: "powershell.exe",
    )

    monkeypatch.setattr(
        "workers.cpu_worker.subprocess.run",
        lambda *args, **kwargs: SimpleNamespace(
            stdout="3000\n",
            stderr="",
            returncode=0,
        ),
    )

    worker = CpuTempWorker()

    result = worker.fetch_data()

    assert result == "Температура CPU (Host WMI): 26.8 °C"

def test_cpu_temperature_from_linux_sensor(monkeypatch):
    """При недоступности PowerShell worker использует Linux-датчик."""

    monkeypatch.setattr(
        "workers.cpu_worker.shutil.which",
        lambda command: None,
    )

    fake_temperatures = {
        "k10temp": [
            SimpleNamespace(current=57.5),
        ]
    }

    monkeypatch.setattr(
        "workers.cpu_worker.psutil.sensors_temperatures",
        lambda: fake_temperatures,
    )

    worker = CpuTempWorker()

    result = worker.fetch_data()

    assert result == "Температура CPU: 57.5 °C"

from workers.cpu_worker import CpuTempWorker


def test_cpu_temperature_fallback_from_cpu_load(monkeypatch):
    """При отсутствии датчиков выводится оценка температуры по нагрузке."""

    monkeypatch.setattr(
        "workers.cpu_worker.shutil.which",
        lambda command: None,
    )

    monkeypatch.setattr(
        "workers.cpu_worker.psutil.sensors_temperatures",
        lambda: {},
    )

    monkeypatch.setattr(
        "workers.cpu_worker.psutil.cpu_percent",
        lambda interval=None: 50.0,
    )

    worker = CpuTempWorker()

    result = worker.fetch_data()

    assert result == "Температура CPU: 60.0 °C (WSL эмуляция | Загрузка: 50.0%)"