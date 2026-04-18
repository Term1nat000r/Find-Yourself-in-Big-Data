import argparse
import logging
from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from tqdm import tqdm
from extractor import get_extractor
from detectors import detect_pd
from classifier import determine_protection_level
from reporter import generate_csv_report, generate_json_report, generate_markdown_report

def setup_logging(verbose: bool):
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[logging.StreamHandler()]
    )

def process_file(file_path: Path, use_ocr: bool) -> dict | None:
    logger = logging.getLogger(__name__)
    ext = file_path.suffix.lower()
    logger.debug(f"Processing: {file_path}")
    extractor = get_extractor(str(file_path), use_ocr)
    if extractor is None:
        logger.debug(f"Skipping unsupported format: {ext}")
        return None
    try:
        text = extractor.extract(str(file_path))
        if not text:
            logger.debug(f"No text extracted from {file_path}")
            return None
        categories = detect_pd(text)
        if categories:
            level = determine_protection_level(categories)
            logger.info(f"Found PD in {file_path}, categories: {categories}, УЗ-{level}")
            return {
                'path': str(file_path),
                'categories': categories,
                'protection_level': level,
                'format': ext[1:] if ext else 'unknown'
            }
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}", exc_info=True)
    return None

def scan_directory(root_dir: str, use_ocr: bool = False, max_workers: int = None) -> list:
    root_path = Path(root_dir)
    logger = logging.getLogger(__name__)
    files = [p for p in root_path.rglob('*') if p.is_file()]
    logger.info(f"Found {len(files)} files to process")
    results = []

    found_pd = 0
    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        future_to_file = {executor.submit(process_file, f, use_ocr): f for f in files}
        with tqdm(total=len(files), desc="Сканирование", unit="файл",
                  bar_format="{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}] ПДн найдено: {postfix}") as pbar:
            pbar.set_postfix_str(str(found_pd))
            for future in as_completed(future_to_file):
                result = future.result()
                if result:
                    results.append(result)
                    found_pd += 1
                    pbar.set_postfix_str(str(found_pd))
                pbar.update(1)
    return results

def main():
    parser = argparse.ArgumentParser(description='Сканер персональных данных в файловом хранилище')
    parser.add_argument('directory', help='Путь к сканируемой директории')
    parser.add_argument('-o', '--output', default='report.csv', help='Путь к выходному файлу отчёта')
    parser.add_argument('-f', '--format', choices=['csv', 'json', 'md'], default='csv',
                        help='Формат отчёта (csv, json, md)')
    parser.add_argument('--ocr', action='store_true', help='Включить OCR для изображений')
    parser.add_argument('-w', '--workers', type=int, default=None,
                        help='Количество параллельных процессов (по умолчанию — число ядер CPU)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Подробный вывод')
    args = parser.parse_args()

    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)

    logger.info(f"Starting scan of directory: {args.directory}")
    results = scan_directory(args.directory, use_ocr=args.ocr, max_workers=args.workers)
    logger.info(f"Scan completed. Found PD in {len(results)} files.")

    if args.format == 'csv':
        generate_csv_report(results, args.output)
    elif args.format == 'json':
        generate_json_report(results, args.output)
    elif args.format == 'md':
        generate_markdown_report(results, args.output)

    logger.info(f"Report saved to {args.output}")

if __name__ == '__main__':
    main()
