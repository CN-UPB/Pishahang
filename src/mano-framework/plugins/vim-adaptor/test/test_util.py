from vim_adaptor.util import convert_size

import bitmath


def test_convert_size():
    assert 1024 == convert_size(1, "GiB", bitmath.MiB)
    assert 1 == convert_size(1.0, "GiB", bitmath.GiB)
    assert 1 == convert_size("1", "GiB", bitmath.GiB)
    assert 1 == convert_size(1, "Gi", bitmath.GiB)
