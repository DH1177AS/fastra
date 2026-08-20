from fastra_core.tolerance import approximately_equal, approximately_greater, approximately_less

def test_approximately_equal():
    assert approximately_equal(1.0000001, 1.0, 1e-6)
    assert not approximately_equal(1.01, 1.0, 1e-6)

def test_approximately_greater():
    assert approximately_greater(1.0, 0.9999, 1e-6)
    assert not approximately_greater(1.0, 1.1, 1e-6)

def test_approximately_less():
    assert approximately_less(0.9999, 1.0, 1e-6)
    assert not approximately_less(1.1, 1.0, 1e-6)
