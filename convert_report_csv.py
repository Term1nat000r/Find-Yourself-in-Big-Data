"""
Конвертер отчёта report_noocr.csv (из pd_scanner.py) в result.csv
Формат входного CSV: путь,категории_ПДн,количество_находок,УЗ,формат_файла
Выходной формат: size,time,name
"""

import csv
import os
from pathlib import Path
from datetime import datetime

MONTH_ABBR = [
    'jan', 'feb', 'mar', 'apr', 'may', 'jun',
    'jul', 'aug', 'sep', 'oct', 'nov', 'dec'
]

def format_time(timestamp: float) -> str:
    dt = datetime.fromtimestamp(timestamp)
    month = MONTH_ABBR[dt.month - 1]
    return f"{month} {dt.day:2d} {dt.hour:02d}:{dt.minute:02d}"

def convert_from_csv(input_csv: str, output_csv: str):
    rows = []
    with open(input_csv, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        header = next(reader, None)
        for row in reader:
            if not row:
                continue
            file_path = row[0].strip()
            try:
                stat = os.stat(file_path)
                size = stat.st_size
                mtime = stat.st_mtime
            except FileNotFoundError:
                print(f"Предупреждение: файл не найден – {file_path}")
                continue

            name = Path(file_path).name
            rows.append({
                'size': size,
                'time': format_time(mtime),
                'name': name
            })

    rows.sort(key=lambda r: r['name'])

    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        f.write("size,time,name\n")
        for r in rows:
            f.write(f"{r['size']},{r['time']},{r['name']}\n")

    print(f"Создан файл {output_csv} с {len(rows)} записями.")

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('input_csv', help='Путь к report_noocr.csv')
    parser.add_argument('output_csv', nargs='?', default='result.csv', help='Имя выходного файла')
    args = parser.parse_args()
    convert_from_csv(args.input_csv, args.output_csv)
