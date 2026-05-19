# ==============================================================
# FINAL FORM TEXT NORMALIZATION ENGINE
# deterministic numeric -> spoken language converter
# ============================================================== 

from __future__ import annotations

from decimal import Decimal, getcontext
from fractions import Fraction
import datetime
import re

getcontext().prec = 500

ONES = [
    'zero', 'one', 'two', 'three', 'four', 'five', 'six', 'seven', 'eight', 'nine',
    'ten', 'eleven', 'twelve', 'thirteen', 'fourteen', 'fifteen',
    'sixteen', 'seventeen', 'eighteen', 'nineteen'
]

TENS = [
    '', '', 'twenty', 'thirty', 'forty', 'fifty', 'sixty', 'seventy', 'eighty', 'ninety'
]

SCALES = [
    '', 'thousand', 'million', 'billion', 'trillion',
    'quadrillion', 'quintillion', 'sextillion', 'septillion',
    'octillion', 'nonillion', 'decillion', 'undecillion',
    'duodecillion', 'tredecillion', 'quattuordecillion',
    'quindecillion', 'sexdecillion', 'septendecillion',
    'octodecillion', 'novemdecillion', 'vigintillion'
]

FRACTIONS = {
    2: 'half', 3: 'third', 4: 'quarter', 5: 'fifth', 6: 'sixth',
    7: 'seventh', 8: 'eighth', 9: 'ninth', 10: 'tenth',
    12: 'twelfth', 16: 'sixteenth', 32: 'thirty-second'
}

ROMAN = [
    (1000, 'M'), (900, 'CM'), (500, 'D'), (400, 'CD'),
    (100, 'C'), (90, 'XC'), (50, 'L'), (40, 'XL'),
    (10, 'X'), (9, 'IX'), (5, 'V'), (4, 'IV'), (1, 'I')
]

MONTHS = [
    'January', 'February', 'March', 'April', 'May', 'June',
    'July', 'August', 'September', 'October', 'November', 'December'
]

UNITS = {
    'km': 'kilometers',
    'm': 'meters',
    'cm': 'centimeters',
    'mm': 'millimeters',
    'kg': 'kilograms',
    'g': 'grams',
    'lb': 'pounds',
    'oz': 'ounces',
    'm/s': 'meters per second',
    'km/h': 'kilometers per hour',
}


def chunk_words(n: int) -> str:
    words: list[str] = []
    if n >= 100:
        words.append(ONES[n // 100] + ' hundred')
        n %= 100
        if n:
            words.append('and')
    if n >= 20:
        tens = TENS[n // 10]
        if n % 10:
            tens += '-' + ONES[n % 10]
        words.append(tens)
    elif n > 0:
        words.append(ONES[n])
    return ' '.join(words)


def int_words(n: int) -> str:
    if n == 0:
        return 'zero'
    parts: list[str] = []
    scale = 0
    while n:
        chunk = n % 1000
        if chunk:
            text = chunk_words(chunk)
            if scale < len(SCALES):
                if SCALES[scale]:
                    text += ' ' + SCALES[scale]
            else:
                text += f' times ten to the {scale * 3}'
            parts.append(text)
        n //= 1000
        scale += 1
    return ' '.join(reversed(parts))


def fraction_words(frac: Fraction) -> str | None:
    num, den = frac.numerator, frac.denominator
    if den in FRACTIONS:
        name = FRACTIONS[den]
        if num > 1:
            name += 's'
        return f'{int_words(num)} {name}'
    return None


def number_words(x: int | float | str | Decimal) -> str:
    x = Decimal(str(x))
    if x < 0:
        return 'minus ' + number_words(-x)
    whole = int(x)
    frac = x - whole
    base = int_words(whole)
    if frac == 0:
        return base
    f = Fraction(frac).limit_denominator(64)
    fw = fraction_words(f)
    if fw:
        if whole:
            return base + ' and ' + fw
        return fw
    decimal = str(x).split('.')[1]
    return base + ' point ' + ' '.join(ONES[int(d)] for d in decimal)


def ordinal(n: int) -> str:
    text = number_words(n)
    if text.endswith('one'):
        return text[:-3] + 'first'
    if text.endswith('two'):
        return text[:-3] + 'second'
    if text.endswith('three'):
        return text[:-5] + 'third'
    if text.endswith('y'):
        return text[:-1] + 'ieth'
    return text + 'th'


def scientific(x: int | float | str | Decimal) -> str:
    x = Decimal(str(x))
    tup = x.normalize().as_tuple()
    digits = ''.join(map(str, tup.digits))
    exponent = len(digits) + tup.exponent - 1
    mantissa = Decimal(digits) / (10 ** (len(digits) - 1))
    return number_words(mantissa) + ' times ten to the ' + ordinal(exponent)


def currency(amount: int | float | str | Decimal) -> str:
    x = Decimal(str(amount))
    dollars = int(x)
    cents = int((x - dollars) * 100)
    words = int_words(dollars) + ' dollars'
    if cents:
        words += ' and ' + int_words(cents) + ' cents'
    return words


def percent(x: int | float | str | Decimal) -> str:
    return number_words(x) + ' percent'


def ratio(a: int | float | str | Decimal, b: int | float | str | Decimal) -> str:
    return number_words(a) + ' to ' + number_words(b)


def roman(n: int) -> str:
    result = ''
    for val, sym in ROMAN:
        while n >= val:
            result += sym
            n -= val
    return result


def phone(number: str) -> str:
    digits = re.sub(r'\D', '', number)
    return ' '.join(ONES[int(d)] for d in digits)


def date_words(date_str: str) -> str:
    d = datetime.datetime.strptime(date_str, '%Y-%m-%d')
    return f'{MONTHS[d.month - 1]} {ordinal(d.day)}, {int_words(d.year)}'


def time_words(time_str: str) -> str:
    t = datetime.datetime.strptime(time_str, '%H:%M')
    h = t.hour
    m = t.minute
    if m == 0:
        return int_words(h) + " o'clock"
    return int_words(h) + ' ' + int_words(m)


def units(number: int | float | str | Decimal, unit: str) -> str:
    if unit in UNITS:
        return number_words(number) + ' ' + UNITS[unit]
    return number_words(number) + ' ' + unit


NUMBER_PATTERN = r'\d+(\.\d+)?'


def normalize_numbers(text: str) -> str:
    return re.sub(NUMBER_PATTERN, lambda m: number_words(m.group()), text)


def normalize_currency(text: str) -> str:
    return re.sub(r'\$(\d+(\.\d+)?)', lambda m: currency(m.group(1)), text)


def normalize_percent(text: str) -> str:
    return re.sub(r'(\d+(\.\d+)?)%', lambda m: percent(m.group(1)), text)


def normalize_units(text: str) -> str:
    pattern = r'(\d+(\.\d+)?)(km|m|cm|kg|g|lb|oz)'

    def repl(match: re.Match[str]) -> str:
        return units(match.group(1), match.group(3))

    return re.sub(pattern, repl, text)


def normalize_all(text: str) -> str:
    text = normalize_currency(text)
    text = normalize_percent(text)
    text = normalize_units(text)
    text = normalize_numbers(text)
    return text


def batch(numbers: list[int | float | str | Decimal]) -> list[str]:
    return [number_words(n) for n in numbers]








