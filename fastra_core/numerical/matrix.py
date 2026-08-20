from fastra_core.spatial.matrix4x4 import Matrix4x4

def inverse_matrix(m: Matrix4x4) -> Matrix4x4:
    a: list[float] = [float(m.get_element(i//4, i%4)) for i in range(16)]
    inv: list[float] = [0.0] * 16
    for i in range(4):
        inv[i*4 + i] = 1.0
    for i in range(4):
        pivot = abs(a[i*4 + i])
        maxrow = i
        for k in range(i+1, 4):
            if abs(a[k*4 + i]) > pivot:
                pivot = abs(a[k*4 + i])
                maxrow = k
        if pivot < 1e-12:
            raise ValueError("Matriks singular")
        if maxrow != i:
            for j in range(4):
                a[i*4+j], a[maxrow*4+j] = a[maxrow*4+j], a[i*4+j]
                inv[i*4+j], inv[maxrow*4+j] = inv[maxrow*4+j], inv[i*4+j]
        diag = a[i*4 + i]
        for j in range(4):
            a[i*4+j] /= diag
            inv[i*4+j] /= diag
        for k in range(4):
            if k != i:
                factor = a[k*4 + i]
                for j in range(4):
                    a[k*4+j] -= factor * a[i*4+j]
                    inv[k*4+j] -= factor * inv[i*4+j]
    col_major: list[float] = [0.0] * 16
    for col in range(4):
        for row in range(4):
            col_major[col*4 + row] = inv[row*4 + col]
    return Matrix4x4(col_major)
