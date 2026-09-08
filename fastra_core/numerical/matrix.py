# fastra_core\numerical\matrix.py

from __future__ import annotations

import logging
import math
from typing import Any, List

from fastra_core.spatial.matrix4x4 import Matrix4x4

logger = logging.getLogger("fastra.numerical.matrix")


def inverse_matrix(m: Any) -> Matrix4x4:
    """
    Computes the exact inverse of a 4x4 matrix using robust Gauss-Jordan elimination with partial pivoting.
    Strictly handles floating-point singularity constraints and prevents data type coercion hacks.
    """
    if not isinstance(m, Matrix4x4):
        logger.error("INVERSE_MATRIX_INPUT_TYPE_VIOLATION: %r", m)
        raise TypeError("MATRIX_TYPE_VIOLATION_INPUT_MUST_BE_A_PURE_MATRIX4X4_INSTANCE")

    # Extract original matrix into a raw flat row-major layout
    a: List[float] = []
    for i in range(16):
        elem = m.get_element(i // 4, i % 4)
        if isinstance(elem, bool):
            logger.error("INVERSE_MATRIX_ELEMENT_BOOLEAN at (%d,%d): %r", i // 4, i % 4, elem)
            raise TypeError("DATA_TYPE_COERCION_FORBIDDEN_BOOLEAN_NOT_ALLOWED")
        if not isinstance(elem, (int, float)):
            logger.error("INVERSE_MATRIX_ELEMENT_NON_NUMERIC at (%d,%d): %r", i // 4, i % 4, elem)
            raise TypeError("MATRIX_ELEMENT_MUST_BE_PURE_NUMERIC_TYPE")

        float_elem = float(elem)
        if math.isnan(float_elem) or math.isinf(float_elem):
            logger.error("INVERSE_MATRIX_ELEMENT_NAN_OR_INF at (%d,%d): %s", i // 4, i % 4, float_elem)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_MATRIX_CONTAINS_NAN_OR_INFINITE_VALUE")
        a.append(float_elem)

    # Initialize identity matrix context container in row-major layout
    inv: List[float] = [0.0] * 16
    for i in range(4):
        inv[i * 4 + i] = 1.0

    # Gauss-Jordan elimination pipeline with row-swapping partial pivoting
    for i in range(4):
        pivot = abs(a[i * 4 + i])
        max_row = i

        # Discover optimal pivot magnitude down the column matrix bounds
        for k in range(i + 1, 4):
            current_magnitude = abs(a[k * 4 + i])
            if current_magnitude > pivot:
                pivot = current_magnitude
                max_row = k

        # Verify mathematical matrix singularity constraints using strict threshold
        if pivot < 1e-12:
            logger.error("INVERSE_MATRIX_SINGULARITY at column %d, pivot=%s", i, pivot)
            raise ValueError("NUMERICAL_SINGULARITY_DETECTED_MATRIX_DETERMINANT_COLLAPSED_TO_ZERO")

        # Swap rows to secure matrix stability
        if max_row != i:
            for j in range(4):
                idx_i, idx_max = i * 4 + j, max_row * 4 + j
                a[idx_i], a[idx_max] = a[idx_max], a[idx_i]
                inv[idx_i], inv[idx_max] = inv[idx_max], inv[idx_i]

        # Normalize the primary pivot row
        diag = a[i * 4 + i]
        for j in range(4):
            idx = i * 4 + j
            a[idx] /= diag
            inv[idx] /= diag

        # Eliminate rows across remaining boundaries
        for k in range(4):
            if k != i:
                factor = a[k * 4 + i]
                for j in range(4):
                    idx_k, idx_i = k * 4 + j, i * 4 + j
                    a[idx_k] -= factor * a[idx_i]
                    inv[idx_k] -= factor * inv[idx_i]

    # Final conversion validation check on all computed indices
    for idx, val in enumerate(inv):
        if math.isnan(val) or math.isinf(val):
            logger.error("INVERSE_MATRIX_RESULT_NAN_OR_INF at index %d: %s", idx, val)
            raise ValueError("NUMERIC_ANOMALY_DETECTED_INVERSED_MATRIX_VALUES_CORRUPTED")

    # Map the row-major computed results into the internal column-major storage required by Matrix4x4
    col_major: List[float] = [0.0] * 16
    for col in range(4):
        for row in range(4):
            col_major[col * 4 + row] = inv[row * 4 + col]

    return Matrix4x4(col_major)