import pytest
from fastra_core.primitives.length import Length
from fastra_core.spatial.coordinate import Coordinate
from fastra_core.ccm.physical import Wall, Column, Beam, Slab, Foundation
from fastra_core.ccm.spatial import Site, Building, Storey, Room
from fastra_core.ccm.resource import Material, Equipment, Labor
from fastra_core.ccm.economic import WorkItem, BOQItem, CostItem, RABItem

class TestWall:
    def test_create_valid_wall(self):
        axis = [Coordinate(0,0,0), Coordinate(5,0,0)]
        w = Wall(name="Dinding Test", axis_line=axis, height=Length(3.5))
        assert w.gross_area.value == 17.5

    def test_zero_height_raises(self):
        with pytest.raises(ValueError):
            Wall(name="Dinding Invalid", height=Length(0))

    def test_area_with_openings(self):
        axis = [Coordinate(0,0,0), Coordinate(5,0,0)]
        from fastra_core.ccm.common import Opening
        w = Wall(name="Dinding+Jendela", axis_line=axis, height=Length(3.5),
                 openings=[Opening(Length(1.5), Length(1.2), Length(1.0), "WINDOW")])
        assert w.gross_area.value == 17.5  # gross tetap

class TestColumn:
    def test_volume_calculation(self):
        c = Column(name="K1", width=Length(0.3), depth=Length(0.4), height=Length(3.0))
        assert c.volume.value == 0.36

    def test_bekisting_area(self):
        c = Column(name="K1", width=Length(0.3), depth=Length(0.4), height=Length(3.0))
        assert c.bekisting_area.value == 2 * (0.3+0.4) * 3.0

class TestBeam:
    def test_volume(self):
        b = Beam(name="B1", width=Length(0.25), depth=Length(0.4), length=Length(5.0))
        assert b.volume.value == 0.5

class TestSlab:
    def test_area(self):
        boundary = [Coordinate(0,0,0), Coordinate(5,0,0), Coordinate(5,4,0), Coordinate(0,4,0), Coordinate(0,0,0)]
        s = Slab(name="Plat Lantai", boundary=boundary, thickness=Length(0.12), supports=["col-001"])
        assert s.area.value == 20.0
        assert s.volume.value == 2.4

class TestRoom:
    def test_closed_room(self):
        boundary = [Coordinate(0,0,0), Coordinate(4,0,0), Coordinate(4,3,0), Coordinate(0,3,0), Coordinate(0,0,0)]
        r = Room(name="Kamar", boundary=boundary)
        assert r.is_closed
        assert r.area.value == 12.0

class TestMaterial:
    def test_create(self):
        m = Material(name="Beton K-250", material_class="CONCRETE", material_type="BETON", unit="m³", strength_grade="K-250")
        assert m.unit == "m³"

class TestWorkItem:
    def test_create(self):
        wi = WorkItem(name="Pasangan Bata", work_item_code="PEK.DIND.001", unit="m²", quantity=100.0)
        assert wi.quantity == 100.0



