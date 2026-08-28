from collections import namedtuple
from unittest.mock import mock_open

import workers.fan_worker as fan_worker_module
from workers.fan_worker import FanWorker


FanEntry = namedtuple("FanEntry", ["label", "current"])


def test_fetch_data_returns_psutil_fan_value(monkeypatch):
    """Должен вернуть RPM первого вентилятора с положительной скоростью."""

    fans_data = {
        "cpu_fan": [
            FanEntry(label="CPU Fan", current=1450),
        ]
    }

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: fans_data
    )

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор (CPU Fan): 1450 RPM"


def test_fetch_data_uses_fan_name_when_label_is_empty(monkeypatch):
    """Если label пустой, должен использоваться ключ словаря sensors_fans."""

    fans_data = {
        "nct6798": [
            FanEntry(label="", current=1200),
        ]
    }

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: fans_data
    )

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор (nct6798): 1200 RPM"


def test_fetch_data_skips_zero_rpm_psutil_fans(monkeypatch):
    """Вентиляторы с current <= 0 должны игнорироваться."""

    fans_data = {
        "cpu_fan": [
            FanEntry(label="Stopped fan", current=0),
            FanEntry(label="Active fan", current=1800),
        ]
    }

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: fans_data
    )

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор (Active fan): 1800 RPM"


def test_fetch_data_reads_linux_hwmon_file_when_psutil_has_no_fans(
    monkeypatch
):
    """Если sensors_fans вернул пустые данные, должен использоваться hwmon."""

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: {}
    )

    monkeypatch.setattr(
        fan_worker_module.glob,
        "glob",
        lambda pattern: ["/sys/class/hwmon/hwmon0/fan1_input"]
    )

    mocked_open = mock_open(read_data="2100\n")
    monkeypatch.setattr(fan_worker_module, "open", mocked_open, raising=False)

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор (hwmon): 2100 RPM"

    mocked_open.assert_called_once_with(
        "/sys/class/hwmon/hwmon0/fan1_input",
        "r"
    )


def test_fetch_data_uses_first_positive_hwmon_value(monkeypatch):
    """Должен пропустить невалидный/нулевой RPM и вернуть первый положительный."""

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: None
    )

    fan_files = [
        "/sys/class/hwmon/hwmon0/fan1_input",
        "/sys/class/hwmon/hwmon0/fan2_input",
        "/sys/class/hwmon/hwmon0/fan3_input",
    ]

    monkeypatch.setattr(
        fan_worker_module.glob,
        "glob",
        lambda pattern: fan_files
    )

    values = iter([
        "0\n",
        "unknown\n",
        "1850\n",
    ])

    def fake_open(*args, **kwargs):
        return mock_open(read_data=next(values))()

    monkeypatch.setattr(fan_worker_module, "open", fake_open, raising=False)

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор (hwmon): 1850 RPM"


def test_fetch_data_falls_back_to_wsl_when_sensors_fans_raises_error(
    monkeypatch
):
    """При ошибке psutil и отсутствии файлов hwmon должен использоваться WSL-расчёт."""

    def raise_psutil_error():
        raise RuntimeError("Не удалось получить данные датчиков")

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        raise_psutil_error
    )

    monkeypatch.setattr(
        fan_worker_module.glob,
        "glob",
        lambda pattern: []
    )

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "cpu_percent",
        lambda interval=None: 50.0
    )

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор CPU: 2000 RPM (WSL | Нагрузка: 50.0%)"


def test_fetch_data_falls_back_to_wsl_when_linux_file_reading_fails(
    monkeypatch
):
    """Если hwmon-файл не читается, метод должен вернуть имитацию WSL."""

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: {}
    )

    monkeypatch.setattr(
        fan_worker_module.glob,
        "glob",
        lambda pattern: ["/sys/class/hwmon/hwmon0/fan1_input"]
    )

    def raise_open_error(*args, **kwargs):
        raise OSError("Нет доступа к файлу вентилятора")

    monkeypatch.setattr(
        fan_worker_module,
        "open",
        raise_open_error,
        raising=False
    )

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "cpu_percent",
        lambda interval=None: 25.0
    )

    worker = FanWorker()

    result = worker.fetch_data()

    assert result == "Вентилятор CPU: 1550 RPM (WSL | Нагрузка: 25.0%)"


def test_fetch_data_calculates_wsl_rpm_from_cpu_load(monkeypatch):
    """Должен правильно вычислять RPM по формуле 1100 + load * 18."""

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: None
    )

    monkeypatch.setattr(
        fan_worker_module.glob,
        "glob",
        lambda pattern: []
    )

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "cpu_percent",
        lambda interval=None: 73.5
    )

    worker = FanWorker()

    result = worker.fetch_data()

    # int(1100 + 73.5 * 18.0) = int(2423.0) = 2423
    assert result == "Вентилятор CPU: 2423 RPM (WSL | Нагрузка: 73.5%)"


def test_fetch_data_passes_none_to_cpu_percent(monkeypatch):
    """cpu_percent должен вызываться с interval=None."""

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "sensors_fans",
        lambda: {}
    )

    monkeypatch.setattr(
        fan_worker_module.glob,
        "glob",
        lambda pattern: []
    )

    received_intervals = []

    def fake_cpu_percent(interval=None):
        received_intervals.append(interval)
        return 10.0

    monkeypatch.setattr(
        fan_worker_module.psutil,
        "cpu_percent",
        fake_cpu_percent
    )

    worker = FanWorker()

    result = worker.fetch_data()

    assert received_intervals == [None]
    assert result == "Вентилятор CPU: 1280 RPM (WSL | Нагрузка: 10.0%)"