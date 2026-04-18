import csv
import json
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

def generate_csv_report(results: list, output_path: str):
    with open(output_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(["путь", "категории_ПДн", "количество_находок", "УЗ", "формат_файла"])
        for r in results:
            categories_str = "; ".join([f"{k}:{v}" for k, v in r['categories'].items()])
            writer.writerow([
                r['path'],
                categories_str,
                sum(r['categories'].values()),
                r['protection_level'],
                r['format']
            ])

def generate_json_report(results: list, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

def generate_markdown_report(results: list, output_path: str):
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write("# Отчёт об обнаружении персональных данных\n\n")
        f.write(f"Дата генерации: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("| Путь | Категории ПДн | Количество находок | УЗ | Формат |\n")
        f.write("|------|---------------|---------------------|----|--------|\n")
        for r in results:
            categories_str = "<br>".join([f"{k}: {v}" for k, v in r['categories'].items()])
            f.write(f"| {r['path']} | {categories_str} | {sum(r['categories'].values())} | УЗ-{r['protection_level']} | {r['format']} |\n")
