from hypothesis import given
from hypothesis.strategies import text, binary

from arxiv.files import (
    BinaryMinimalFile,
    FileDoesNotExist,
    MockStringFileObj,
    FileTransform,
)

class BinaryMinimalFileExample(BinaryMinimalFile):
    pass                        # ?

def test_binary_minimal_file() -> None:
    bmf = BinaryMinimalFileExample()
    assert str(bmf)
    assert not bmf.read()
    assert not bmf.readline()
    assert not bmf.seek(0)
    with bmf as should_be_null:
        assert not should_be_null
    #
    # for c in bmf: # throws
    # assert False
    #
    assert not bmf.close()

def test_file_does_not_exist() -> None:
    fdne = FileDoesNotExist("xyzzy")
    # with FileDoesNotExist("xyzzy") as fdne:
    assert fdne.item
    assert not fdne.exists()
    # open, etag, size, updated all should fail
    assert str(fdne)

@given(text())
def test_filetransform(data: str) -> None:
    orig_file = MockStringFileObj("no_name.data", data=data)
    assert orig_file.name
    assert orig_file.exists()
    assert orig_file.etag
    assert orig_file.size >= 0  # careful!
    assert orig_file.updated
    assert str(orig_file)

    def transform(xx: bytes) -> bytes:
        return xx.decode('utf-8').lower().encode("utf-8")

    expected = transform(data.encode("utf-8"))
    new_file = FileTransform(orig_file, transform)
    transformed_data = new_file.open('rb').read()
    assert transformed_data == expected



@given(text())
def test_filetransform_fakeurls(data: str) -> None:
    orig_file = MockStringFileObj("no_name.data", data=data)

    def letters_to_fake_urls(xx: bytes) -> bytes:
        out = b""
        for byte in xx:
            if byte > 0x40 and byte < 0x5b:
                out += f'<a href="https://arxiv.org/abs/{byte}">{byte}</a>'.encode('utf-8')
        return out

    expected = letters_to_fake_urls(data.encode('utf-8'))
    new_file = FileTransform(orig_file, letters_to_fake_urls)
    transformed_data = new_file.open('rb').read()
    assert transformed_data == expected

