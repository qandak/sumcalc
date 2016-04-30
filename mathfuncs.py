# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


from PyQt5.QtWidgets import QApplication

import common

from mathdocs import errors as _errors

from parsefuncs import dict_secondary as _dict_secondary
from parsefuncs import _function_handler as _handler
from parsefuncs import _is_pointZero

from builtins import round as _round
from builtins import abs as _abs
from builtins import bin as _bin, oct as _oct, hex as _hex
from builtins import min as _min, max as _max

from functools import reduce as _reduce

from math import acosh as _acosh
from math import asinh as _asinh
from math import atanh as _atanh
from math import cosh as _cosh
from math import sinh as _sinh
from math import tanh as _tanh

from math import acos as _acos
from math import asin as _asin
from math import atan as _atan
from math import atan2 as _atan2
from math import cos as _cos
from math import sin as _sin
from math import tan as _tan
from math import log as _log

from math import fsum as _fsum
from math import fmod as _fmod
from math import ceil as _ceil
from math import degrees as _deg
from math import exp as _exp
from math import factorial as _factorial
from math import floor as _floor
from math import hypot as _hypot
from math import log10 as _log10
from math import log2 as _log2
from math import pow as _pow
from math import radians as _rad
from math import sqrt as _sqrt
from math import erf as _erf
from math import erfc as _erfc
from math import gamma as _gamma
from math import lgamma as _lgamma


# for MathErrors raising
translate = QApplication.translate


# --------------------------
# START Functions
# --------------------------

@_handler
def sum(*numbers):
    return _fsum(numbers)


@_handler
def mod(dividend, divisor):
    return _fmod(dividend, divisor)


@_handler
def ceil(x):
    return _ceil(x)


@_handler
def exp(x):
    return _exp(x)


@_handler
def fact(n):
    if _is_pointZero(n):
        if 0 <= n <= 64:
            return _factorial(n)
        elif n < 0:
            raise MathError('<font color=red>fact()</font> ' +\
                            translate('MathErrors', _errors['nv']))
        else:
            raise MathError('<font color=red>fact()</font> ' +\
                            translate('MathErrors', _errors['fac64']))
    else:
        raise MathError('<font color=red>fact()</font> ' +\
                        translate('MathErrors', _errors['oiv']))


@_handler
def sqrt(x):
    if x > 0:
        return _sqrt(x)
    else:
        raise MathError(translate('MathErrors', _errors['mde']))


@_handler
def floor(x):
    return _floor(x)


@_handler
def pow(x, y):
    return _pow(x, y)


@_handler
def deg(radians):
    return _deg(radians)


@_handler
def rad(degrees):
    return _rad(degrees)


@_handler
def hyp(x, y):
    return _hypot(x, y)


@_handler
def log10(x):
    return _log10(x)


@_handler
def log2(x):
    return _log2(x)


# Extending LOGARITHMIC function
@_handler
def log(x, y):
    return _log(x, y)


@_handler
def lg(x):
    return _log10(x)


@_handler
def ln(x):
    return _log(x)


# Redefining TRIGONOMETRIC functions to switch betweeen Degrees and Radians
@_handler
def acosh(x):
    return _acosh(x) if common._use_radians else _deg(_acosh(x))


@_handler
def asinh(x):
    return _asinh(x) if common._use_radians else _deg(_asinh(x))


@_handler
def atanh(x):
    return _atanh(x) if common._use_radians else _deg(_atanh(x))


@_handler
def cosh(x):
    return _cosh(x) if common._use_radians else _cosh(_rad(x))


@_handler
def sinh(x):
    return _sinh(x) if common._use_radians else _sinh(_rad(x))


@_handler
def tanh(x):
    return _tanh(x) if common._use_radians else _tanh(_rad(x))


@_handler
def acos(x):
    return _acos(x) if common._use_radians else _deg(_acos(x))


@_handler
def asin(x):
    return _asin(x) if common._use_radians else _deg(_asin(x))


@_handler
def atan(x):
    return _atan(x) if common._use_radians else _deg(_atan(x))


@_handler
def atan2(y, x):
    return _atan2(y, x) if common._use_radians else _deg(_atan2(x))


@_handler
def cos(x):
    return _cos(x) if common._use_radians else _cos(_rad(x))


@_handler
def sin(x):
    return _sin(x) if common._use_radians else _sin(_rad(x))


@_handler
def tan(x):
    return _tan(x) if common._use_radians else _tan(_rad(x))


# Special functions
@_handler
def erf(x):
    return _erf(x)


@_handler
def erfc(x):
    return _erfc(x)


@_handler
def gamma(x):
    return _gamma(x)


@_handler
def lgamma(x):
    return _lgamma(x)


@_handler
def cdf(x):
    return (1.0 + _erf(x / _sqrt(2.0))) / 2.0


# Redefining BUILTIN functions
@_handler
def bin(x):
    if isinstance(x, int):
        return _bin(x)
    else:
        if _is_pointZero(x):
            return _bin(int(x))
        else:
            return x


@_handler
def oct(x):
    if isinstance(x, int):
        return _oct(x)
    else:
        if _is_pointZero(x):
            return _oct(int(x))
        else:
            return x


@_handler
def hex(x):
    if isinstance(x, int):
        return _hex(x)
    else:
        if _is_pointZero(x):
            return _hex(int(x))
        else:
            raise x


@_handler               # 'digits' optional argument must be declared
def round(x, *dig):     # in parsefuncs.function_handler.used_optlist
    if len(dig) == 0:
        return _round(x)
    else:
        if not _is_pointZero(dig[0]):
            raise MathError('<font color=red>round( )</font> ' +\
                            translate('MathErrors', _errors['oivDig']))
        else:
            return _round(x, int(dig[0]))


@_handler
def abs(x):
    return _abs(x)


@_handler
def min(*numbers):
    return _min(*numbers)


@_handler
def max(*numbers):
    return _max(*numbers)


# --------------------------
# USER-DEFINED Functions
# --------------------------


@_handler
def rt(x, N):
    if _is_pointZero(N) and N >= 2:
        if x < 0:
            if N % 2:
                return _abs(x)**(1/N) * -1
            else:
                raise MathError(translate('MathErrors', _errors['mde']))
        else:
            return x**(1/N)
    else:
        raise MathError(translate('MathErrors', _errors['mde']))


@_handler
def cbrt(x):
    if x < 0:
        return _abs(x)**(1/3) * -1
    else:
        return x**(1/3)


@_handler
def pc(x, percent):
    return (x / 100) * percent


@_handler
def perc(x, percent):
    if percent < 0:
        return x - (x / 100) * _abs(percent)
    else:
        return x + (x / 100) * _abs(percent)


@_handler
def dperc(old, new):
    return _round((new - old) / old * 100, 2)


@_handler
def gcd(x, y):
    if all(isinstance(i, int) for i in (x, y)):
        while y:
            x, y = y, x % y
        return x
    else:
        raise MathError('<font color=red>gcd( )</font> ' +\
                        translate('MathErrors', _error['oiv']))


@_handler
def dms(degrees, minutes, *seconds):  # Args may be negative, and may be subtracted
    if all(isinstance(x, int) for x in [degrees, minutes]):
        if not seconds:
            return degrees + minutes/60
        else:
            if isinstance(seconds[0], int):
                return degrees + minutes/60 + seconds[0]/3600
            else:
                raise MathError('<font color=red>dms( )</font> ' +\
                                translate('MathErrors', _error['oiv']))
    else:
        raise MathError('<font color=red>dms( )</font> ' +\
                        translate('MathErrors', _error['oiv']))


@_handler
def dd(degrees):
    _deg = int(_abs(degrees))
    _min = int((_abs(degrees) - _deg) * 60)
    _sec = _round((_abs(degrees) - _deg - _min/60) * 3600)
    return '{s}dms({0}, {1}, {2})'.format(_deg, _min, _sec,
                                          s='-' if degrees < 0 else '')


@_handler
def amn(*numbers):
    return sum(numbers) / len(numbers)


@_handler
def gmn(*numbers):
    if any(x < 0 for x in numbers):
        raise MathError('<font color=red>gmn( )</font> ' +\
                        translate('MathErrors', _errors['nv']))
    else:
        return rt(_reduce(lambda x, y: x * y, numbers), len(numbers))


@_handler
def hmn(*numbers):
    if any(x < 0 for x in numbers):
        raise MathError('<font color=red>hmn( )</font> ' +\
                        translate('MathErrors', _errors['nv']))
    else:
        return len(numbers) / sum(1/x for x in numbers)


# --------------------------
# CONVERSION Functions
# --------------------------

# LENGTH

# ---- imperial

@_handler
def in_mm(inch):
    return inch * 25.4


@_handler
def in_cm(inch):
    return inch * 2.54


@_handler
def in_m(inch):
    return inch * 0.0254


@_handler
def ft_in(foot):
    return foot * 12


@_handler
def ft_mm(foot):
    return foot * 304.8


@_handler
def ft_cm(foot):
    return foot * 30.48


@_handler
def ft_m(foot):
    return foot * 0.3048


@_handler
def ftin_cm(foot, inch):    # Args may be negative, and may be subtracted
    if isinstance(foot, int):
        return ft_cm(foot) + in_cm(inch)
    else:
        raise MathError('<b>foot</b> ' +\
                        translate('MathErrors', _error['oiv']))


@_handler
def ftin_m(foot, inch):     # Args may be negative, and may be subtracted
    if isinstance(foot, int):
        return ft_m(foot) + in_m(inch)
    else:
        raise MathError('<b>foot</b> ' +\
                        translate('MathErrors', _error['oiv']))


@_handler
def yd_in(yard):
    return yard * 36


@_handler
def yd_ft(yard):
    return yard * 3


@_handler
def yd_mm(yard):
    return yard * 914.4


@_handler
def yd_cm(yard):
    return yard * 91.44


@_handler
def yd_m(yard):
    return yard * 0.9144


@_handler
def yd_km(yard):
    return yard * 0.0009144


@_handler
def mi_yd(mile):
    return mile * 1760


@_handler
def mi_m(mile):
    return mile * 1609.344


@_handler
def mi_km(mile):
    return mile * 1.609344


# ---- metric

@_handler
def mm_in(mm):
    return mm * 0.0393700787401575


@_handler
def cm_in(cm):
    return cm * 0.3937007874015748


@_handler
def cm_ft(cm):
    return cm * 0.0328083989501312


@_handler
def cm_ftin(cm):
    _foot = int(_abs(cm_ft(cm)))
    _inch = _round(ft_in(_abs(cm_ft(cm)) - _foot), 2)
    if _inch == int(_inch):
        _inch = int(_inch)
    return '{s}ftin_cm({0}, {1})'.format(_foot, _inch,
                                        s='-' if cm < 0 else '')


@_handler
def m_ftin(m):
    _foot = int(_abs(m_ft(m)))
    _inch = _round(ft_in(_abs(m_ft(m)) - _foot), 2)
    if _inch == int(_inch):
        _inch = int(_inch)
    return '{s}ftin_m({0}, {1})'.format(_foot, _inch,
                                        s='-' if m < 0 else '')


@_handler
def m_in(m):
    return m * 39.3700787401574803


@_handler
def m_ft(m):
    return m * 3.2808398950131234


@_handler
def m_yd(m):
    return m * 1.0936132983377078


@_handler
def m_mi(m):
    return m * 0.0006213711922373


@_handler
def km_mi(km):
    return km * 0.621371192237334


# AREA

@_handler
def sqcm_sqin(sqcm):
    return sqcm * 0.15500031000062


@_handler
def sqm_sqft(sqm):
    return sqm * 10.763910417


@_handler
def sqm_sqyd(sqm):
    return sqm * 1.19599004630108


@_handler
def sqm_ac(sqm):
    return sqm * 0.000247105


@_handler
def sqm_ha(sqm):
    return sqm * 0.0001


@_handler
def sqkm_sqmi(sqkm):
    return sqkm * 0.386102159


@_handler
def sqin_sqcm(sqin):
    return sqin * 6.4516


@_handler
def sqft_sqm(sqft):
    return sqft * 0.09290304


@_handler
def sqyd_sqm(sqyd):
    return sqyd * 0.83612736


@_handler
def sqmi_sqkm(sqmi):
    return sqmi * 2.58998811


@_handler
def sqmi_ac(sqmi):
    return sqmi * 640


@_handler
def sqmi_ha(sqmi):
    return sqmi * 258.9988110336


@_handler
def ac_ha(ac):
    return ac * 0.404685642


@_handler
def ha_ac(ha):
    return ha * 2.471053815


# VOLUME

@_handler
def l_usgal(l):
    return l * 0.264172052


@_handler
def l_ukgal(l):
    return l * 0.219969248


@_handler
def gal_pt(gal):
    return gal * 8


@_handler
def ukgal_l(ukgal):
    return ukgal * 4.54609


@_handler
def usgal_l(usgal):
    return usgal * 3.785411784


# WEIGHT

@_handler
def oz_g(ounce):
    return ounce * 28.349523125


@_handler
def lb_oz(pound):
    return pound * 16


@_handler
def lb_g(pound):
    return pound * 453.59237


@_handler
def lb_kg(pound):
    return pound * 0.45359237


@_handler
def g_oz(gram):
    return gram * 0.035273961949580414


@_handler
def g_lb(gram):
    return gram * 0.002204622621848776


@_handler
def kg_oz(kg):
    return kg * 35.273961949580414


@_handler
def kg_lb(kg):
    return kg * 2.2046226218487757


@_handler
def ct_g(ct):
    return ct * 0.2


@_handler
def ct_oz(ct):
    return ct * 0.00705479238991608


@_handler
def g_ct(g):
    return g * 5


@_handler
def oz_ct(oz):
    return oz * 141.747615625


# ENERGY

@_handler
def wh_cl(watt):
    return watt * 860.421


@_handler
def wh_j(watt_h):
    return watt * 3600


@_handler
def cl_j(calorie):

    return calorie * 4.184


@_handler
def cl_wh(calorie):
    return calorie * 0.0011622217495854


@_handler
def j_cl(joule):
    return joule * 0.2390057361376673


@_handler
def j_wh(joule):
    return joule * 0.0002777777777777


# TEMPERATURE

@_handler
def c_f(c):
    return c * 9/5 + 32


@_handler
def c_k(c):
    return c + 273.15


@_handler
def f_c(f):
    return (f - 32) * 5/9


@_handler
def f_k(f):
    return (f + 459.67) * 5/9


@_handler
def k_c(k):
    return k - 273.15


@_handler
def k_f(k):
    return k * 9/5 - 459.67


# POWER

@_handler
def kw_hp(kw):
    return kw * 1.3410220895955138


@_handler
def hp_kw(hp):
    return hp * 0.745699871582

# --------------------------
# END of CONVERSION
# --------------------------


class MathError(ValueError):

    def __init__(self, *args):
        self.args = args


# Creating eval()'s safe dict
safeeval_dict = {'__builtins__': {}}

safeeval_dict_EXCL = ['safeeval_dict', 'common', 'MathError',
                      'QApplication', 'translate', 'utfCodec']

# Assign an empty dict to secondary items,
# and ad to safeeval_dict see parsfuncs module
for s in _dict_secondary:
    safeeval_dict[s] = 'quickhelp'
del s

# Add math functions
for x in dir():
    if not x.startswith('_') and not x in safeeval_dict_EXCL:
        exec('{0}[\'{1}\'] = {2}'.format('safeeval_dict', x, x))
del x
