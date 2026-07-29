from __future__ import annotations

from collector.core.enums import StorageDirectory
from collector.storage import configure_storage
from collector.storage.local import LocalStorage
from collector.storage.models import StorageFile


def test_save_e_read(tmp_path):
    storage = LocalStorage(str(tmp_path))
    files = [
        StorageFile(name="SP.csv", content=b"a"),
        StorageFile(name="RJ.csv", content=b"b"),
    ]
    storage.save(StorageDirectory.CAIXA_DOWNLOAD, files)

    lidos = storage.read(StorageDirectory.CAIXA_DOWNLOAD)
    nomes = sorted(f.name for f in lidos)
    assert nomes == ["RJ.csv", "SP.csv"]
    conteudo = {f.name: f.content for f in lidos}
    assert conteudo["SP.csv"] == b"a"


def test_save_substitui_conteudo_anterior(tmp_path):
    storage = LocalStorage(str(tmp_path))
    storage.save(StorageDirectory.CAIXA_DOWNLOAD, [StorageFile(name="SP.csv", content=b"antigo")])
    storage.save(StorageDirectory.CAIXA_DOWNLOAD, [StorageFile(name="SP.csv", content=b"novo")])

    lidos = storage.read(StorageDirectory.CAIXA_DOWNLOAD)
    assert len(lidos) == 1
    assert lidos[0].content == b"novo"


def test_read_diretorio_inexistente_retorna_vazio(tmp_path):
    storage = LocalStorage(str(tmp_path))
    assert storage.read(StorageDirectory.CAIXA_DOWNLOAD) == []


def test_configure_storage_local_por_padrao(settings):
    storage = configure_storage(settings)
    assert isinstance(storage, LocalStorage)
