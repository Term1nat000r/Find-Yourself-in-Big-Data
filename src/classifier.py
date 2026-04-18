from detectors import CATEGORY_MAP
GOV_ID_LARGE_VOLUME = 10     
ORDINARY_LARGE_VOLUME = 50   


def determine_protection_level(categories_counts: dict) -> int:
    has_special = False
    has_biometric = False
    has_payment = False
    gov_id_count = 0
    ordinary_count = 0

    for name, count in categories_counts.items():
        cat = CATEGORY_MAP.get(name, "ordinary")
        if cat == "special":
            has_special = True
        elif cat == "biometric":
            has_biometric = True
        elif cat == "payment":
            has_payment = True
        elif cat == "government_id":
            gov_id_count += count
        elif cat == "ordinary":
            ordinary_count += count

    if has_special or has_biometric:
        return 1
    if has_payment or gov_id_count > GOV_ID_LARGE_VOLUME:
        return 2
    if gov_id_count > 0 or ordinary_count > ORDINARY_LARGE_VOLUME:
        return 3
    return 4


def describe_level(level: int) -> str:
    descriptions = {
        1: "УЗ-1: специальные категории ПДн или биометрия (высокий риск)",
        2: "УЗ-2: платёжная информация или гос.идентификаторы в больших объёмах",
        3: "УЗ-3: гос.идентификаторы или обычные ПДн в больших объёмах",
        4: "УЗ-4: только обычные ПДн в небольших объёмах (базовый уровень)",
    }
    return descriptions.get(level, f"УЗ-{level}")
