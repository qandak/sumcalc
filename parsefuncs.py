# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2, or (at your option)
# any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.


import common
import mathdocs

from PyQt5 import QtWidgets
from difflib import SequenceMatcher, ndiff
from math import isfinite
from functools import wraps
from builtins import round as _round

translate = QtWidgets.QApplication.translate


dict_secondary = ['help',]


class Quickhelp(TypeError):

    def __init__(self, funcname, argnames, text):
        self.funcname = funcname
        self.argnames = argnames
        self.text = text


def _strdiff(first, second):
    'Get the differenc of chars in two strings.'
    count = 0
    for i, s in enumerate(ndiff(first, second)):
        if s[0] == '-':
            count += 1
    return count


def _is_pointZero(x):
    'Check if decimal equal to its integer (8.0 == 8)'
    if x == int(x):
        return True
    else:
        return False


def is_number(expr):
    'Check if string expression is a number.'
    try:
        float(expr)
        return True
    except ValueError:
        return False


def suggest(name, dict_keys):
    'Find suggestions in safeeval_dict if function name is misstyped.'

    def matching(n, match_lst):
        saved_n = n
        if '_' in n:
            n = n.replace('_', '')
        if len(name) == 2:
            if len(n) - len(name) == 0 and\
                    SequenceMatcher(None, name.lower(), n).ratio() >= 0.5:
                match_lst.append('<font color=green>' + saved_n + '</font>')
            elif len(n) - len(name) <= 2 and\
                    SequenceMatcher(None, name.lower(), n).ratio() > 0.6:
                match_lst.append('<font color=green>' + saved_n + '</font>')
        elif len(name) == 3:
            if len(n) - len(name) <= 2 and\
                    SequenceMatcher(None, name.lower(), n).ratio() > 0.57:
                match_lst.append('<font color=green>' + saved_n + '</font>')
            elif len(name) - len(n) <= 1 and\
                    SequenceMatcher(None, name.lower(), n).ratio() > 0.8:
                match_lst.append('<font color=green>' + saved_n + '</font>')
        elif 8 >= len(name) > 3:
            if abs(len(n) - len(name)) <= 2 and\
                    SequenceMatcher(None, name.lower(), n).ratio() > 0.5:
                match_lst.append('<font color=green>' + saved_n + '</font>')

    suggs = ''

    new_dict = list(dict_keys)
    for e in dict_secondary:
        new_dict.remove(e)
    new_dict.remove('__builtins__')

    if name == name.lower():
        if name in new_dict:
            return suggs
    else:
        name = name.lower()

    fmatch = []         # function match
    cmatch = []         # converter match

    for key in new_dict:
        if '_' in key:    # converter
            matching(key, cmatch)
        else:
            matching(key, fmatch)

    if fmatch or cmatch:
        suggs = '<b>|</b> {f}{comma}{c}'.format(
            f=', '.join(sorted(fmatch, key=len)) if fmatch else '',
            c=', '.join(sorted(cmatch, key=len)) if cmatch else '',
            comma=', ' if fmatch and cmatch else ''
            )
    return suggs


def _function_handler(func):

    'Error handling and Quickhelp decorator for Functions.'

    used_optlist = [
                    'dig',
                    'seconds',
                ]
    varargs = {
                'numbers': 'x',
            }

    @wraps(func)
    def inner(*args):
        func_argcount = func.__code__.co_argcount
        func_arg_names = func.__code__.co_varnames
        passed_argcount = len(args)
        optionals = 0

        for v in func.__code__.co_varnames:
            if v in used_optlist:
                optionals += 1

        if any(isinstance(x, tuple) for x in args):
            raise TypeError(translate('ParseError',
                                      '<font color=red>{0}( )</font> does not take sequences '
                                      'or tuples as an argument').format(func.__name__))

        elif passed_argcount == 1 and args[0] == 'quickhelp':
            text = []
            # varargs
            if func_argcount == 0:  # func_arg_names[0] must be in varargs
                for i in ['1', '2', '3', 'N']:
                    text.append('<font color=green> {el}{0}{1} </font>{comma}'.format(
                                varargs[func_arg_names[0]],
                                i,
                                el='</font>...<font color=green>' if i == 'N' else '',
                                comma='' if i == 'N' else ' , '))
                raise Quickhelp(func.__name__, ''.join(text),
                                translate('Mathdocs',
                                          mathdocs.docs[func.__name__]))
            # usual case
            else:
                for a in range(len(func_arg_names)):
                    if func_arg_names[a].startswith('_'):
                        continue
                    elif func_arg_names[a] in used_optlist:
                        text.append('</b><i><font color=green> {0} </font></i><b>{comma}'.format(
                            func_arg_names[a],
                            comma='' if a == func_argcount + optionals - 1 else ' , '))
                    else:
                        text.append('<font color=green> {0} </font>{comma}'.format(
                            func_arg_names[a],
                            comma='' if a == func_argcount + optionals - 1 else ' , '))
                raise Quickhelp(func.__name__, ''.join(text),
                                translate('Mathdocs',
                                          mathdocs.docs[func.__name__]))

        elif func_argcount == 0 and func_arg_names[0] in varargs:
            if passed_argcount <= 1:
                raise TypeError(translate('ParseError',
                                          '<font color=red>{0}( )</font> takes at least 2 arguments').format(func.__name__))
        elif passed_argcount == 1 and args[0] == {}:
            raise NameError('name \'__builtins__\' error')  # to truncate '__builtins__' by quots

        elif func_argcount == passed_argcount or\
                func_argcount == passed_argcount - optionals:
            return func(*args)  # Successfuly return
        elif func_argcount > passed_argcount:
            raise TypeError(translate('ParseError',
                                      '<font color=red>{0}( )</font> missing {least} {1} {a}{op}').format(
                            func.__name__,
                            func_argcount - passed_argcount,
                            least='' if not optionals else translate('ParseError', 'at least'),
                            op='' if not optionals else translate('ParseError', ' (has also {0} optional)').format(optionals),
                            a=translate('ParseError_', 'argument')\
                                if func_argcount - passed_argcount == 1\
                                else translate('ParseError', 'arguments')))
        elif func_argcount + optionals < passed_argcount:
            raise TypeError(translate('ParseError',
                                      '<font color=red>{0}( )</font> takes {most} {1} {a}, {2} were given').format(
                            func.__name__,
                            func_argcount + optionals,
                            passed_argcount,
                            most=translate('ParseError', 'at most') if optionals else '',
                            a=translate('ParseError', 'argument')\
                                if func_argcount + optionals == 1\
                                else translate('ParseError', 'arguments')))
        return func(*args)
    return inner


def reformat(rawtext):
    '''
    Reformat input expression for better representation in history,
    i.e. '2*(2**8-186)/sin(32)' --> '2 * (2**8 - 186) / sin(32).'
    '''
    if common._reformat_on:
        stack = []
        s = ''.join(rawtext.split())
        n = 0
        for i in s:
            if i in '+-':
                if n == 0:
                    stack.append('{0}'.format(i))
                elif s[n-1] == '(':
                    stack.append('{0}'.format(i))
                elif s[n-1] in '+-*/,eE':
                    stack.append(' {0}'.format(i))
                else:
                    stack.append(' {0} '.format(i))
            elif i == '/':
                stack.append(' {0} '.format(i))
            elif i == '.':
                if n == 0 or not s[n-1].isdigit():
                    stack.append('0.')
                else:
                    stack.append(i)
            elif i == ',':
                stack.append(', ')
            elif i is not ' ':
                stack.append(i)
            n += 1
        if '//' in s:
            return ''.join(stack).replace('/  /', '//')
        elif '**' in s:
            return ''.join(stack).replace(' *  * ', '**')
        else:
            return ''.join(stack)
    else:
        return rawtext


def rd(res):
    '''
    If there is a base2 incorrect transforms like 1.000000000000001
    or trigonometry calculaion like 0.4999999999999994,
    rounds eval()'s result to 12th symbol after floating point.
    If result is decimal but equal to integer,
    turn to integer truncating [.0].
    '''

    if isinstance(res, str):
        return res
    elif isinstance(res, int):
        if common._scientific_on and len(str(res)) > 16:
            return eval('{:.15e}'.format(res))
        else:
            return res
    elif 'e' in str(res):
        if res == int(res):
            if common._scientific_on:
                return res
            else:
                return int(res)
        else:
            return res
    elif isinstance(res, float) and not isfinite(res):
        raise ValueError(mathdocs.errors['mde'])
    elif _is_pointZero(res):
        return int(res)
    else:
        f = _round(res, 12)
        if _is_pointZero(f):
            return int(f)
        elif f == _round(res, 10):
            return f
        else:
            return res


def turnFloat(expr):
    '''
    Add '/1' to element in input expression if it has a 'power' operator
    to add limitations to power operation and avoid overflows.
    '''
    signs = '+-/*,%('

    def isEven(i):
        return i % 2 == 0

    def numSplit(part):
        temp = part[::-1]
        index = 0
        for i in range(len(temp)):
            if temp[i] in signs:
                index = i * -1
                break
        return index

    if '**' in expr:
        temp = expr.split('**')
        for x in range(len(temp)):
            part = temp[x]
            if part and isEven(x) and not part[-1] in signs:
                try:
                    temp[x] = str(float(part))
                except ValueError:
                    if part.endswith(')'):
                        temp[x] = part[:-1] + '/1)'
                    else:
                        temp[x] = part[:numSplit(part)] + '(' + part[numSplit(part):] + '/1)'

        return '**'.join(temp)
    else:
        return expr


def turnBack(text, new, offset):
    '''
    Remove trailing '.0's and '(.../1)'s added by turnFloat() if exist
    to restore original indexing for error handling.
    '''
    if '**' in text:
        step = 0
        for i, s in enumerate(ndiff(text, new)):
            if i < offset:
                if s[0] == ' ':
                    continue
                elif s[0] == '+':
                    step += 1
                elif s[0] == '-':
                    step -= 1
            else:
                break
        return offset - step
    else:
        return offset


def binOctHex(expr, funcs, types):
    '''
    Check if there are bin-oct-hex elements or functions in expression.
    Raise an exception if there is more than one type,
    otherwise remove existing function name from expression
    and enclose by function of he same name.
    '''
    if any((x in expr.lower()) for x in types + funcs):

        error = translate('BinOctHex',
                          'only one of special types ({0}|{1}|{2}) is allowed in the same expression!').format(
            ' <b>binary</b> ',
            ' <b>octal</b> ',
            ' <b>hexadecimal</b> ')
        lowerexp = expr.lower()
        funcCount = []
        typeCount = []
        for f in funcs:
            if f in lowerexp:
                funcCount.append(f)
        for t in types:
            if t in lowerexp:
                typeCount.append(t)

        if len(funcCount) > 1 or len(typeCount) > 1:
            raise TypeError(error)
        elif len(funcCount) + len(typeCount) == 2 and\
                not funcs.index(funcCount[0]) == types.index(typeCount[0]):
            raise TypeError(error)
        elif len(funcCount) + len(typeCount) == 2:
            el = funcCount[0]
            return el + '(' + expr.replace(el, '') + ')'
        elif len(funcCount) > len(typeCount):
            el = funcCount[0]
            return el + '(' + expr.replace(el, '') + ')'
        else:
            el = funcs[types.index(typeCount[0])]
            return el + '(' + expr + ')'
    else:
        return expr
