"""
ACES-000 §6.12: Matrix4x4
Matriks transformasi affine 4×4 dalam koordinat homogen.
Column-major order (konsisten dengan OpenGL/IFC).
"""

import math
from dataclasses import dataclass
from typing import List

@dataclass(frozen=True)
class Matrix4x4:
    """Matriks 4×4 column-major."""
    elements: List[float]  # 16 elemen dalam column-major: [col0, col1, col2, col3]

    def __post_init__(self):
        if len(self.elements) != 16:
            raise ValueError("Matrix4x4 harus memiliki 16 elemen")
        if any(math.isnan(e) for e in self.elements):
            raise ValueError("Elemen matriks tidak boleh NaN")

    @classmethod
    def identity(cls) -> 'Matrix4x4':
        return cls([
            1, 0, 0, 0,
            0, 1, 0, 0,
            0, 0, 1, 0,
            0, 0, 0, 1
        ])

    @classmethod
    def from_rows(cls, r0, r1, r2, r3) -> 'Matrix4x4':
        """Buat dari 4 baris (masing-masing 4 elemen). Disimpan column-major."""
        return cls([
            r0[0], r1[0], r2[0], r3[0],
            r0[1], r1[1], r2[1], r3[1],
            r0[2], r1[2], r2[2], r3[2],
            r0[3], r1[3], r2[3], r3[3]
        ])

    def get_element(self, row: int, col: int) -> float:
        """Akses elemen berdasarkan baris dan kolom (0-indexed)."""
        return self.elements[col * 4 + row]

    def to_row_major(self) -> List[float]:
        """Konversi ke row-major list."""
        return [
            self.get_element(0,0), self.get_element(0,1), self.get_element(0,2), self.get_element(0,3),
            self.get_element(1,0), self.get_element(1,1), self.get_element(1,2), self.get_element(1,3),
            self.get_element(2,0), self.get_element(2,1), self.get_element(2,2), self.get_element(2,3),
            self.get_element(3,0), self.get_element(3,1), self.get_element(3,2), self.get_element(3,3),
        ]

    def transpose(self) -> 'Matrix4x4':
        m = self.elements
        return Matrix4x4([
            m[0], m[4], m[8], m[12],
            m[1], m[5], m[9], m[13],
            m[2], m[6], m[10], m[14],
            m[3], m[7], m[11], m[15]
        ])

    def __mul__(self, other):
        """Perkalian matriks atau matriks * vektor."""
        if isinstance(other, Matrix4x4):
            return self._multiply_matrix(other)
        elif hasattr(other, 'x') and hasattr(other, 'y') and hasattr(other, 'z'):
            # Asumsikan vektor/koordinat
            return self._multiply_vector(other)
        raise TypeError(f"Tidak dapat mengalikan Matrix4x4 dengan {type(other)}")

    def _multiply_matrix(self, other: 'Matrix4x4') -> 'Matrix4x4':
        result = []
        for col in range(4):
            for row in range(4):
                s = 0.0
                for k in range(4):
                    s += self.get_element(row, k) * other.get_element(k, col)
                result.append(s)
        return Matrix4x4(result)

    def _multiply_vector(self, v):
        """Kalikan matriks dengan vektor 3D (asumsikan w=1)."""
        x = self.get_element(0,0)*v.x + self.get_element(0,1)*v.y + self.get_element(0,2)*v.z + self.get_element(0,3)
        y = self.get_element(1,0)*v.x + self.get_element(1,1)*v.y + self.get_element(1,2)*v.z + self.get_element(1,3)
        z = self.get_element(2,0)*v.x + self.get_element(2,1)*v.y + self.get_element(2,2)*v.z + self.get_element(2,3)
        w = self.get_element(3,0)*v.x + self.get_element(3,1)*v.y + self.get_element(3,2)*v.z + self.get_element(3,3)
        # Asumsikan w=1 untuk vektor posisi, normalisasi jika perlu
        if abs(w) > 1e-12:
            return type(v)(x/w, y/w, z/w)
        return type(v)(x, y, z)

    def inverse(self) -> 'Matrix4x4':
        """Menghitung invers matriks 4x4 (Gauss-Jordan)."""
        m = [list(row) for row in [self.to_row_major()[i:i+4] for i in range(0,16,4)]]
        # Augment dengan identitas
        aug = [row + [1 if i==j else 0 for j in range(4)] for i,row in enumerate(m)]
        # Eliminasi Gauss
        for i in range(4):
            pivot = aug[i][i]
            if abs(pivot) < 1e-12:
                raise ValueError("Matriks singular, tidak dapat di-inverse")
            for j in range(8):
                aug[i][j] /= pivot
            for k in range(4):
                if k != i:
                    factor = aug[k][i]
                    for j in range(8):
                        aug[k][j] -= factor * aug[i][j]
        # Ekstrak hasil
        inv_rows = [row[4:] for row in aug]
        return Matrix4x4.from_rows(inv_rows[0], inv_rows[1], inv_rows[2], inv_rows[3])

    def approximately_equal(self, other: 'Matrix4x4', epsilon: float = 1e-6) -> bool:
        if not isinstance(other, Matrix4x4):
            return False
        return all(abs(a-b) <= epsilon for a,b in zip(self.elements, other.elements))

    def __eq__(self, other):
        if not isinstance(other, Matrix4x4):
            return False
        return self.elements == other.elements

    def __repr__(self):
        return f"Matrix4x4({self.elements})"