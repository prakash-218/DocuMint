"""
Currency formatting and amounts in words.

INR uses Indian digit grouping (20,63,000) and lakh/crore words; everything
else uses international grouping (2,063,000) and thousand/million words.
"""

from decimal import Decimal, ROUND_HALF_UP

SYMBOLS = {'INR': '₹', 'USD': '$', 'EUR': '€', 'GBP': '£', 'AUD': 'A$', 'CAD': 'C$', 'SGD': 'S$', 'AED': 'AED '}

# Main unit / fractional unit names for amount-in-words
UNITS = {
    'INR': ('Rupees', 'Paise'),
    'USD': ('Dollars', 'Cents'),
    'EUR': ('Euros', 'Cents'),
    'GBP': ('Pounds', 'Pence'),
    'AUD': ('Dollars', 'Cents'),
    'CAD': ('Dollars', 'Cents'),
    'SGD': ('Dollars', 'Cents'),
    'AED': ('Dirhams', 'Fils'),
}

_ONES = ('', 'One', 'Two', 'Three', 'Four', 'Five', 'Six', 'Seven', 'Eight', 'Nine', 'Ten', 'Eleven',
         'Twelve', 'Thirteen', 'Fourteen', 'Fifteen', 'Sixteen', 'Seventeen', 'Eighteen', 'Nineteen')
_TENS = ('', '', 'Twenty', 'Thirty', 'Forty', 'Fifty', 'Sixty', 'Seventy', 'Eighty', 'Ninety')


def _to_decimal(value) -> Decimal:
    try:
        return Decimal(str(value if value is not None else 0)).quantize(Decimal('0.01'), ROUND_HALF_UP)
    except Exception:
        return Decimal('0.00')


def group_digits(integer_part: str, indian: bool) -> str:
    if not indian or len(integer_part) <= 3:
        return f'{int(integer_part):,}'
    head, tail = integer_part[:-3], integer_part[-3:]
    pairs = []
    while len(head) > 2:
        pairs.insert(0, head[-2:])
        head = head[:-2]
    if head:
        pairs.insert(0, head)
    return ','.join(pairs + [tail])


def format_money(value, currency: str = 'USD', decimals: bool = True) -> str:
    """₹20,63,000.00 / $4,957.00 / -₹500.00"""
    currency = (currency or 'USD').upper()
    amount = _to_decimal(value)
    negative = amount < 0
    amount = abs(amount)
    integer, _, fraction = f'{amount:.2f}'.partition('.')
    text = group_digits(integer, indian=currency == 'INR')
    if decimals:
        text += '.' + fraction
    symbol = SYMBOLS.get(currency, currency + ' ')
    return ('-' if negative else '') + symbol + text


def _below_hundred(n: int) -> str:
    if n < 20:
        return _ONES[n]
    return (_TENS[n // 10] + (' ' + _ONES[n % 10] if n % 10 else '')).strip()


def _below_thousand(n: int) -> str:
    hundreds, rest = divmod(n, 100)
    parts = []
    if hundreds:
        parts.append(_ONES[hundreds] + ' Hundred')
    if rest:
        parts.append(_below_hundred(rest))
    return ' '.join(parts)


def _international(n: int) -> str:
    if n == 0:
        return 'Zero'
    parts = []
    for size, name in ((10 ** 12, 'Trillion'), (10 ** 9, 'Billion'), (10 ** 6, 'Million'), (1000, 'Thousand')):
        if n >= size:
            parts.append(_below_thousand(n // size) + ' ' + name)
            n %= size
    if n:
        parts.append(_below_thousand(n))
    return ' '.join(parts)


def _indian(n: int) -> str:
    if n == 0:
        return 'Zero'
    parts = []
    crore, n = divmod(n, 10 ** 7)
    if crore:
        # Large amounts: "One Hundred Twenty Crore" (crore count spelled out recursively)
        parts.append(_indian(crore) + ' Crore')
    for size, name in ((10 ** 5, 'Lakh'), (1000, 'Thousand')):
        count, n = divmod(n, size)
        if count:
            parts.append(_below_hundred(count) + ' ' + name)
    if n:
        parts.append(_below_thousand(n))
    return ' '.join(parts)


def number_in_words(n: int, indian: bool) -> str:
    return _indian(n) if indian else _international(n)


def amount_in_words(value, currency: str = 'USD') -> str:
    """'INR Ten Lakh Thirty One Thousand Five Hundred Rupees Only'
       'USD Four Thousand Nine Hundred Fifty Seven Dollars and Fifty Cents Only'"""
    currency = (currency or 'USD').upper()
    amount = abs(_to_decimal(value))
    whole = int(amount)
    fraction = int((amount - whole) * 100)
    indian = currency == 'INR'
    main, sub = UNITS.get(currency, ('', 'Cents'))
    words = number_in_words(whole, indian)
    text = f'{currency} {words}' + (f' {main}' if main else '')
    if fraction:
        text += f' and {number_in_words(fraction, indian)} {sub}'
    return text + ' Only'
