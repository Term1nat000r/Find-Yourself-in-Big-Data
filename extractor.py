import json
import logging
import subprocess
from pathlib import Path

import pandas as pd
from PIL import Image, ImageEnhance, ImageFilter
import pytesseract
from pypdf import PdfReader
import pdfplumber
from docx import Document
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text

logger = logging.getLogger(__name__)

CSV_CHUNK_SIZE = 50_000
CSV_MAX_CHARS = 5_000_000
JSON_MAX_ITEMS = 10_000
PARQUET_MAX_ROWS = 100_000
PDF_MAX_PAGES = 50
EXCEL_MAX_ROWS = 50_000
IMAGE_MAX_SIDE = 2000


class TextExtractor:
    def extract(self, file_path: str) -> str:
        raise NotImplementedError


class CSVExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            chunks = []
            total = 0
            for chunk in pd.read_csv(
                file_path,
                chunksize=CSV_CHUNK_SIZE,
                on_bad_lines='skip',
                low_memory=False,
                dtype=str
            ):
                s = chunk.to_string(index=False, header=False)
                chunks.append(s)
                total += len(s)
                if total > CSV_MAX_CHARS:
                    break
            return "\n".join(chunks)
        except Exception as e:
            logger.error(f"CSV read error {file_path}: {e}")
            return ""


class JSONExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                data = json.load(f)
            if isinstance(data, list):
                data = data[:JSON_MAX_ITEMS]
            return json.dumps(data, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"JSON read error {file_path}: {e}")
            return ""


class ParquetExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            import pyarrow.parquet as pq
            pf = pq.ParquetFile(file_path)
            rows_left = PARQUET_MAX_ROWS
            parts = []
            for batch in pf.iter_batches(batch_size=10_000):
                if rows_left <= 0:
                    break
                df = batch.to_pandas()
                if len(df) > rows_left:
                    df = df.head(rows_left)
                parts.append(df.to_string(index=False))
                rows_left -= len(df)
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"Parquet read error {file_path}: {e}")
            return ""


class PDFExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        text = ""
        try:
            with pdfplumber.open(file_path) as pdf:
                for page in pdf.pages[:PDF_MAX_PAGES]:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
        except Exception as e:
            logger.debug(f"pdfplumber failed {file_path}: {e}")

        if not text.strip():
            try:
                reader = PdfReader(file_path)
                for page in reader.pages[:PDF_MAX_PAGES]:
                    page_text = page.extract_text()
                    if page_text:
                        text += page_text + "\n"
            except Exception as e:
                logger.error(f"pypdf failed {file_path}: {e}")
        return text


class DOCXExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            doc = Document(file_path)
            parts = [p.text for p in doc.paragraphs if p.text]
            for table in doc.tables:
                for row in table.rows:
                    for cell in row.cells:
                        if cell.text:
                            parts.append(cell.text)
            return "\n".join(parts)
        except Exception as e:
            logger.error(f"DOCX read error {file_path}: {e}")
            return ""


class DOCExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        for tool in ('antiword', 'catdoc'):
            try:
                result = subprocess.run(
                    [tool, file_path],
                    capture_output=True,
                    timeout=60,
                    check=False,
                )
                if result.returncode == 0 and result.stdout:
                    return result.stdout.decode('utf-8', errors='ignore')
            except (FileNotFoundError, subprocess.TimeoutExpired) as e:
                logger.debug(f"{tool} not available or timed out: {e}")
                continue
        logger.warning(f"DOC read failed {file_path}: install antiword or catdoc")
        return ""


class RTFExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return rtf_to_text(f.read())
        except Exception as e:
            logger.error(f"RTF read error {file_path}: {e}")
            return ""


class XLSXExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            sheets = pd.read_excel(
                file_path,
                engine='openpyxl',
                sheet_name=None,  # все листы
                nrows=EXCEL_MAX_ROWS,
                dtype=str,
            )
            return "\n".join(
                df.to_string(index=False) for df in sheets.values()
            )
        except Exception as e:
            logger.error(f"XLSX read error {file_path}: {e}")
            return ""


class XLSExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            sheets = pd.read_excel(
                file_path,
                engine='xlrd',
                sheet_name=None,
                nrows=EXCEL_MAX_ROWS,
                dtype=str,
            )
            return "\n".join(
                df.to_string(index=False) for df in sheets.values()
            )
        except Exception as e:
            logger.error(f"XLS read error {file_path}: {e}")
            return ""


class HTMLExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f, 'html.parser')
            # убираем скрипты и стили
            for tag in soup(['script', 'style']):
                tag.decompose()
            return soup.get_text(separator=' ')
        except Exception as e:
            logger.error(f"HTML read error {file_path}: {e}")
            return ""


def preprocess_image(img: Image.Image) -> Image.Image:
    img = ImageEnhance.Contrast(img).enhance(2.0)
    img = img.convert('L')
    img = img.point(lambda x: 0 if x < 128 else 255, '1')
    img = img.filter(ImageFilter.MedianFilter(size=3))
    return img


class ImageExtractor(TextExtractor):
    def __init__(self, use_ocr: bool = False):
        self.use_ocr = use_ocr

    def extract(self, file_path: str) -> str:
        if not self.use_ocr:
            return ""
        try:
            img = Image.open(file_path)
            img = preprocess_image(img)
            img.thumbnail((IMAGE_MAX_SIDE, IMAGE_MAX_SIDE), Image.Resampling.LANCZOS)
            return pytesseract.image_to_string(img, lang='rus+eng')
        except Exception as e:
            logger.error(f"OCR error {file_path}: {e}")
            return ""


class TXTExtractor(TextExtractor):
    MAX_SIZE = 5_000_000

    def extract(self, file_path: str) -> str:
        try:
            size = Path(file_path).stat().st_size
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read(min(size, self.MAX_SIZE))
        except Exception as e:
            logger.error(f"TXT read error {file_path}: {e}")
            return ""


class VideoExtractor(TextExtractor):
    def extract(self, file_path: str) -> str:
        logger.debug(f"MP4 skipped (no audio transcription): {file_path}")
        return ""


_EXTRACTORS = {
    '.csv': CSVExtractor,
    '.json': JSONExtractor,
    '.parquet': ParquetExtractor,
    '.pdf': PDFExtractor,
    '.docx': DOCXExtractor,
    '.doc': DOCExtractor,
    '.rtf': RTFExtractor,
    '.xlsx': XLSXExtractor,
    '.xls': XLSExtractor,
    '.htm': HTMLExtractor,
    '.html': HTMLExtractor,
    '.mp4': VideoExtractor,
    '.txt': TXTExtractor,
    '.md': TXTExtractor,
}

_IMAGE_EXTS = {'.tif', '.tiff', '.jpeg', '.jpg', '.png', '.gif'}


def get_extractor(file_path: str, use_ocr: bool = False):
    ext = Path(file_path).suffix.lower()
    if ext in _IMAGE_EXTS:
        return ImageExtractor(use_ocr)
    cls = _EXTRACTORS.get(ext)
    return cls() if cls else None
