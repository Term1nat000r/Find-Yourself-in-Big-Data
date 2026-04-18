import json
import os
import argparse
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

def convert_report(json_path: str, output_csv: str):
    with open(json_path, 'r', encoding='utf-8') as f:
        records = json.load(f)

    rows = []
    for rec in records:
        file_path = rec['path']
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
    parser = argparse.ArgumentParser(description='Конвертация JSON-отчёта сканера в result.csv')
    parser.add_argument('json_report', help='Путь к JSON-файлу от pd_scanner.py')
    parser.add_argument('output', nargs='?', default='result.csv', help='Имя выходного CSV (по умолчанию result.csv)')
    args = parser.parse_args()
    convert_report(args.json_report, args.output)
