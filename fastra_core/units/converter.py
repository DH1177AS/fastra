import math
import logging
from .validator import normalize_unit, are_units_compatible, get_quantity_type
from .exceptions import ConversionError

logger = logging.getLogger(__name__)

LENGTH_TO_M = {'m':1,'mm':0.001,'cm':0.01,'km':1000,'inch':0.0254,'foot':0.3048,'yard':0.9144}
AREA_TO_M2 = {'m²':1,'cm²':1e-4,'ha':10000}
VOLUME_TO_M3 = {'m³':1,'cm³':1e-6,'l':0.001}
MASS_TO_KG = {'kg':1,'g':0.001,'ton':1000}

def convert(value, from_unit, to_unit):
    nf = normalize_unit(from_unit)
    nt = normalize_unit(to_unit)
    if nf == nt: return value
    if not are_units_compatible(nf, nt): raise ConversionError(from_unit, to_unit, "tidak kompatibel")
    qtype = get_quantity_type(nf)
    if qtype == 'length': table = LENGTH_TO_M
    elif qtype == 'area': table = AREA_TO_M2
    elif qtype == 'volume': table = VOLUME_TO_M3
    elif qtype == 'mass': table = MASS_TO_KG
    elif qtype == 'angle':
        rad = value * (math.pi/180) if nf=='deg' else value
        return rad if nt=='rad' else rad * (180/math.pi)
    elif qtype == 'time':
        to_s = {'s':1,'min':60,'h':3600,'day':86400}
        sec = value * to_s[nf]
        return sec / to_s[nt]
    elif qtype == 'temperature':
        if nf in ('°c','c'): k = value + 273.15
        elif nf in ('°f','f'): k = (value - 32)*5/9 + 273.15
        else: k = value
        if nt in ('°c','c'): return k - 273.15
        elif nt in ('°f','f'): return (k - 273.15)*9/5 + 32
        return k
    else: raise ConversionError(from_unit, to_unit)
    canonical = value * table[nf]
    result = canonical / table[nt]
    logger.info(f"[UNIT CONVERSION] {value} {nf} -> {result} {nt}")
    return result
