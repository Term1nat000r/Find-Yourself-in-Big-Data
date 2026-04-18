import re
import logging

logger = logging.getLogger(__name__)

def luhn_check(card_number: str) -> bool:
    digits = [int(d) for d in card_number if d.isdigit()]
    if len(digits) != 16:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0

def validate_snils(snils: str) -> bool:
    digits = re.sub(r'\D', '', snils)
    if len(digits) != 11:
        return False
    nums = [int(d) for d in digits[:9]]
    control = int(digits[9:])
    sum_val = sum((9 - i) * num for i, num in enumerate(nums))
    if sum_val < 100:
        check = sum_val
    elif sum_val == 100 or sum_val == 101:
        check = 0
    else:
        check = sum_val % 101
        if check == 100:
            check = 0
    return check == control

def validate_inn(inn: str, is_legal: bool = False) -> bool:
    digits = re.sub(r'\D', '', inn)
    if is_legal and len(digits) == 10:
        coeffs1 = [2, 4, 10, 3, 5, 9, 4, 6, 8]
        n = sum(int(d) * c for d, c in zip(digits[:9], coeffs1)) % 11 % 10
        return n == int(digits[9])
    elif not is_legal and len(digits) == 12:
        coeffs1 = [7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        coeffs2 = [3, 7, 2, 4, 10, 3, 5, 9, 4, 6, 8]
        n1 = sum(int(d) * c for d, c in zip(digits[:10], coeffs1)) % 11 % 10
        n2 = sum(int(d) * c for d, c in zip(digits[:11], coeffs2)) % 11 % 10
        return n1 == int(digits[10]) and n2 == int(digits[11])
    return False

def validate_passport_rf(series: str, number: str) -> bool:
    series_clean = re.sub(r'\D', '', series)
    number_clean = re.sub(r'\D', '', number)
    return len(series_clean) == 4 and len(number_clean) == 6

def validate_driver_license(series: str, number: str) -> bool:
    pattern = re.compile(r'^\d{2}\s?[А-ЯA-Z]{2}\s?\d{6}$', re.IGNORECASE)
    return bool(pattern.match(f"{series} {number}".strip()))

patterns = {
    "ФИО": re.compile(
        r'\b[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\b',
        re.IGNORECASE
    ),
    "Телефон": re.compile(
        r'(?:\+7|8)[\s\-]?\(?\d{3}\)?[\s\-]?\d{3}[\s\-]?\d{2}[\s\-]?\d{2}\b'
    ),
    "Email": re.compile(
        r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
    ),
    "Дата рождения": re.compile(
        r'\b(?:0[1-9]|[12][0-9]|3[01])[\.\-](?:0[1-9]|1[012])[\.\-](?:19|20)\d{2}\b'
    ),
    "Адрес": re.compile(
        r'\b(?:ул\.|улица|пр-т|проспект|пер\.|переулок|пл\.|площадь|б-р|бульвар|наб\.|набережная)\s+[А-Яа-я0-9\s\.,\-]+\b',
        re.IGNORECASE
    ),

    "Паспорт РФ": re.compile(
        r'\b\d{2}\s?\d{2}\s?\d{6}\b'
    ),
    "СНИЛС": re.compile(
        r'\b\d{3}[\s\-]?\d{3}[\s\-]?\d{3}[\s\-]?\d{2}\b'
    ),
    "ИНН": re.compile(
        r'\b\d{10}(?:\d{2})?\b'
    ),
    "Водительское удостоверение": re.compile(
        r'\b\d{2}\s?[А-ЯA-Z]{2}\s?\d{6}\b', re.IGNORECASE
    ),
    "MRZ": re.compile(
        r'P<[A-Z]{3}[A-Z<]+\n?[A-Z0-9<]{30,}'
    ),

    "Банковская карта": re.compile(
        r'\b(?:\d[ -]*?){13,19}\b'
    ),
    "Банковский счёт": re.compile(
        r'\b\d{20}\b'
    ),
    "БИК": re.compile(
        r'\b04\d{7}\b'
    ),
    "CVV": re.compile(
        r'\bCVV[:\s]*\d{3,4}\b', re.IGNORECASE
    ),

    "Биометрия": re.compile(
        r'\b(?:биометри[яи]|отпечат[ок|ки] пальц[а|ев]|радужн[ая|ой] оболочк[а|и]|голосов[ой|ые] образ[ец|цы])\b',
        re.IGNORECASE
    ),
    "Здоровье": re.compile(
        r'\b(?:диагноз|болезнь|заболевание|медицинск[ая|ий|ое]|поликлиника|больница|пациент|анализ|кровь|рентген|МРТ|КТ)\b',
        re.IGNORECASE
    ),
    "Религия/политика": re.compile(
        r'\b(?:православ|ислам|мусульман|католик|иудаизм|буддизм|полит[ическая|ический]|партия|выборы|голосование)\b',
        re.IGNORECASE
    ),
    "Расовая/национальная принадлежность": re.compile(
        r'\b(?:русский|татарин|украинец|белорус|еврей|армянин|казах|узбек|таджик|чеченец|дагестан|национальность|раса)\b',
        re.IGNORECASE
    ),
}

CATEGORY_MAP = {
    "ФИО": "ordinary",
    "Телефон": "ordinary",
    "Email": "ordinary",
    "Дата рождения": "ordinary",
    "Адрес": "ordinary",
    "Паспорт РФ": "government_id",
    "СНИЛС": "government_id",
    "ИНН": "government_id",
    "Водительское удостоверение": "government_id",
    "MRZ": "government_id",
    "Банковская карта": "payment",
    "Банковский счёт": "payment",
    "БИК": "payment",
    "CVV": "payment",
    "Биометрия": "biometric",
    "Здоровье": "special",
    "Религия/политика": "special",
    "Расовая/национальная принадлежность": "special",
}

def detect_pd(text: str) -> dict:
    results = {}
    for name, pattern in patterns.items():
        matches = pattern.findall(text)
        if matches:
            if name == "Банковская карта":
                valid = [m for m in matches if luhn_check(m)]
                count = len(valid)
            elif name == "СНИЛС":
                valid = [m for m in matches if validate_snils(m)]
                count = len(valid)
            elif name == "ИНН":
                valid = [m for m in matches if validate_inn(m, is_legal=False) or validate_inn(m, is_legal=True)]
                count = len(valid)
            elif name == "Паспорт РФ":
                count = 0
                for m in matches:
                    parts = re.findall(r'\d+', m)
                    if len(parts) >= 2 and validate_passport_rf(parts[0], parts[1]):
                        count += 1
            elif name == "Водительское удостоверение":
                count = sum(1 for m in matches if validate_driver_license(m[:2], m[2:]))
            else:
                count = len(matches)
            if count > 0:
                results[name] = count
    return results
