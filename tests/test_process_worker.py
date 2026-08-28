from types import SimpleNamespace

import psutil

from workers.process_worker import ProcessWorker

class DeniedProcess:
    @property
    def info(self):
        raise psutil.AccessDenied(pid=999, name="protected")

def make_process(pid: int, name: str, memory_bytes: int):
    """Создаёт тестовый объект процесса для psutil.process_iter()."""

    return SimpleNamespace(
        info={
            "pid": pid,
            "name": name,
            "memory_info": SimpleNamespace(rss=memory_bytes),
        }
    )

def test_process_worker_selects_process_with_maximum_ram(monkeypatch):
    """Worker должен выбрать процесс с наибольшим RSS."""

    processes = [
        make_process(100, "python", 100 * 1024 * 1024),
        make_process(200, "code", 750 * 1024 * 1024),
        make_process(300, "chrome", 300 * 1024 * 1024),
    ]

    monkeypatch.setattr(
        "workers.process_worker.psutil.process_iter",
        lambda attrs: processes,
    )

    worker = ProcessWorker()

    result = worker.fetch_data()

    assert worker.fetch_data() == "Процессы: 3 | RAM-лидер: code (PID 200, 750 МБ)"


def test_process_worker_skips_access_denied_process(monkeypatch):
    """Недоступный процесс не должен ломать весь мониторинг."""

    processes = [
        DeniedProcess(),
        make_process(10, "python", 128 * 1024 * 1024),
    ]

    monkeypatch.setattr(
        "workers.process_worker.psutil.process_iter",
        lambda attrs: processes,
    )

    worker = ProcessWorker()

    result = worker.fetch_data()

    assert worker.fetch_data() == "Процессы: 1 | RAM-лидер: python (PID 10, 128 МБ)"

def test_process_worker_returns_message_when_no_processes(monkeypatch):
    """При пустом списке процессов worker должен вернуть понятный текст."""

    monkeypatch.setattr(
        "workers.process_worker.psutil.process_iter",
        lambda attrs: [],
    )

    worker = ProcessWorker()

    result = worker.fetch_data()

    assert result == "Процессы: данные недоступны"