import pytest
from fastra_core.spatial.matrix4x4 import Matrix4x4
from fastra_core.spatial.coordinate import Coordinate

class TestMatrix4x4:
    def test_identity(self):
        I = Matrix4x4.identity()
        assert I.get_element(0,0) == 1
        assert I.get_element(1,1) == 1

    def test_multiply_identity_vector(self):
        I = Matrix4x4.identity()
        p = Coordinate(3,4,5)
        result = I * p
        assert result.approximately_equal(p)

    def test_inverse_identity(self):
        I = Matrix4x4.identity()
        inv = I.inverse()
        assert inv.approximately_equal(I)

    def test_inverse_product(self):
        T = Matrix4x4.from_rows(
            [1,0,0,5],
            [0,1,0,3],
            [0,0,1,2],
            [0,0,0,1]
        )
        inv = T.inverse()
        product = T * inv
        assert product.approximately_equal(Matrix4x4.identity())
