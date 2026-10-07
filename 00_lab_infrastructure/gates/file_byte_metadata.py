"""Independently compute a closed set of file facts from approved local bytes.

Optional execution dependency: pypdf==6.19.0. No network, server metadata,
Lean execution or certificate verdict is consumed here. Unknown facts fail closed.
"""
from __future__ import annotations

from decimal import Decimal, InvalidOperation, localcontext
import hashlib
from io import BytesIO
import logging
from pathlib import Path
import re
import threading

PYPDF_VERSION = '6.19.0'
PARSER_NAME = 'ViridisApprovedPDFByteFacts'
PARSER_VERSION = '1'
SUPPORTED_FIELDS = frozenset({'width', 'height', 'page_count', 'number_of_pages',
    'num_pages', 'mimetype', 'mime_type', 'format', 'pdf_version'})
_PARSE_LOCK = threading.RLock()


class ByteMetadataHold(ValueError):
    pass


def _hold(reason):
    raise ByteMetadataHold('BYTE_METADATA_' + reason)


def _decimal_text(value):
    if not value.is_finite():
        _hold('NONFINITE_PDF_NUMBER')
    return format(value.normalize(), 'f')


def compute_pdf_facts(content):
    """Strict parser with original PDF numeric tokens, without float rounding.

    The approved initial geometry subset is uniform pages, matching MediaBox /
    CropBox, rotation zero, UserUnit one. Other geometry is explicitly unsupported.
    Missing CropBox uses the PDF MediaBox default and is recorded. Every page's
    box is checked, even though server width/height denotes page one.
    """
    if not isinstance(content, bytes) or not content or len(content) > 100 * 1024 * 1024:
        _hold('PDF_BYTE_INPUT_SIZE_OR_TYPE')
    if re.match(rb'%PDF-1\.[0-9](?:\r|\n|\s)', content) is None:
        _hold('UNSUPPORTED_FILE_FORMAT')
    try:
        import pypdf
        from pypdf.generic import NumberObject, FloatObject
    except ImportError:
        _hold('PINNED_PARSER_DEPENDENCY_UNAVAILABLE')
    if pypdf.__version__ != PYPDF_VERSION:
        _hold('PINNED_PARSER_VERSION_MISMATCH')
    # pypdf resolves xref/object streams and inherited page attributes. Its float
    # wrapper rounds on repr; retain the exact token at the parser entry point.
    # The lock confines this deterministic reader hook to this helper invocation.
    owner_thread = threading.get_ident()

    def capture_number(stream):
        if threading.get_ident() != owner_thread:
            return original(stream)
        start = stream.tell()
        value = original(stream)
        end = stream.tell()
        stream.seek(start); token = stream.read(end - start); stream.seek(end)
        if len(token) > 256 or re.fullmatch(rb'[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)', token) is None:
            _hold('MALFORMED_PDF_NUMBER_TOKEN')
        value._viridis_exact_pdf_token = token.decode('ascii')
        return value

    def number(value):
        value = value.get_object() if hasattr(value, 'get_object') else value
        if not isinstance(value, (NumberObject, FloatObject)) or isinstance(value, bool):
            _hold('PDF_NUMBER_TYPE')
        token = getattr(value, '_viridis_exact_pdf_token', None)
        if not isinstance(token, str):
            _hold('EXACT_PDF_NUMERIC_TOKEN_UNAVAILABLE')
        try: result = Decimal(token)
        except InvalidOperation: _hold('MALFORMED_PDF_NUMBER')
        if not result.is_finite(): _hold('NONFINITE_PDF_NUMBER')
        return result

    def box(value):
        value = value.get_object() if hasattr(value, 'get_object') else value
        if not isinstance(value, (list, tuple)) or len(value) != 4:
            _hold('PDF_BOX_SHAPE')
        result = [number(item) for item in value]
        if result[2] <= result[0] or result[3] <= result[1]:
            _hold('NONPOSITIVE_PDF_BOX')
        return result

    warnings = []
    class WarningCapture(logging.Handler):
        def emit(self, record):
            if threading.get_ident() == owner_thread and record.levelno >= logging.WARNING: warnings.append(record.getMessage())

    with _PARSE_LOCK:
        # Capture only after the lock: another caller must never retain our hook.
        original = NumberObject.read_from_stream
        logger = logging.getLogger('pypdf'); handler = WarningCapture()
        logger.addHandler(handler)
        NumberObject.read_from_stream = staticmethod(capture_number)
        try:
            reader = pypdf.PdfReader(BytesIO(content), strict=True)
            if reader.is_encrypted: _hold('ENCRYPTED_PDF_UNSUPPORTED')
            if '/Version' in reader.root_object:
                _hold('CATALOG_VERSION_OVERRIDE_UNSUPPORTED')
            count = len(reader.pages)
            if not 0 < count <= 10000: _hold('PDF_PAGE_COUNT_UNSUPPORTED')
            root_count = number(reader.root_object['/Pages'].get_object()['/Count'])
            if root_count != count: _hold('PDF_PAGE_TREE_COUNT_MISMATCH')
            pages = []
            with localcontext() as context:
                context.prec = 1024
                for index, page in enumerate(reader.pages):
                    if '/MediaBox' not in page: _hold('PDF_MEDIABOX_MISSING')
                    media = box(page['/MediaBox'])
                    crop_present = '/CropBox' in page
                    crop = box(page['/CropBox']) if crop_present else list(media)
                    rotate = number(page['/Rotate']) if '/Rotate' in page else Decimal(0)
                    unit = number(page['/UserUnit']) if '/UserUnit' in page else Decimal(1)
                    if crop != media: _hold('CROPBOX_MEDIABOX_DIFFER_UNSUPPORTED')
                    if rotate != 0: _hold('NONZERO_ROTATION_UNSUPPORTED')
                    if unit != 1: _hold('NONUNIT_USERUNIT_UNSUPPORTED')
                    width, height = media[2] - media[0], media[3] - media[1]
                    if width <= 0 or height <= 0: _hold('NONPOSITIVE_PDF_GEOMETRY')
                    pages.append({'page': index + 1, 'mediabox': [_decimal_text(x) for x in media],
                        'cropbox': [_decimal_text(x) for x in crop], 'cropbox_present': crop_present,
                        'selected_box': 'MediaBox', 'width_points': _decimal_text(width),
                        'height_points': _decimal_text(height), 'rotation_applied': _decimal_text(rotate),
                        'user_unit': _decimal_text(unit)})
            if any(row['width_points'] != pages[0]['width_points'] or row['height_points'] != pages[0]['height_points'] for row in pages):
                _hold('MIXED_PAGE_GEOMETRY_UNSUPPORTED')
            if warnings: _hold('PDF_PARSER_WARNING_UNSUPPORTED')
            version = reader.pdf_header.removeprefix('%PDF-')
        except ByteMetadataHold:
            raise
        except Exception as exc:
            _hold('PDF_PARSE_FAILURE_' + type(exc).__name__)
        finally:
            NumberObject.read_from_stream = staticmethod(original)
            logger.removeHandler(handler)
    return {'parser': {'name': PARSER_NAME, 'version': PARSER_VERSION,
        'dependency_name': 'pypdf', 'dependency_version': PYPDF_VERSION,
        'mode': 'strict; exact numeric tokens; uniform matching boxes; zero rotation; unit one'},
        'source_sha256': hashlib.sha256(content).hexdigest(), 'source_size': len(content),
        'facts': {'width': {'type': 'NUMBER', 'decimal': pages[0]['width_points']},
            'height': {'type': 'NUMBER', 'decimal': pages[0]['height_points']},
            **{field: {'type': 'INTEGER', 'value': count} for field in ('page_count', 'number_of_pages', 'num_pages')},
            **{field: {'type': 'STRING', 'value': 'application/pdf'} for field in ('mimetype', 'mime_type')},
            'format': {'type': 'STRING', 'value': 'PDF'}, 'pdf_version': {'type': 'STRING', 'value': version}},
        'page_geometries': pages, 'format': 'PDF', 'acceptance_authority': False}


def compute_approved_file_facts(path, *, sha256, checksum, size):
    """Read the pinned local file once; validate independent hashes before parsing."""
    if not isinstance(path, str) or not Path(path).is_absolute(): _hold('APPROVED_LOCAL_PATH_REQUIRED')
    source = Path(path)
    if source.is_symlink() or not source.is_file(): _hold('APPROVED_REGULAR_LOCAL_FILE_REQUIRED')
    if re.fullmatch(r'[0-9a-f]{64}', str(sha256)) is None or type(size) is not int or size <= 0:
        _hold('APPROVED_SOURCE_HASH_OR_SIZE_REQUIRED')
    try: content = source.read_bytes()
    except OSError: _hold('APPROVED_LOCAL_FILE_UNREADABLE')
    if hashlib.sha256(content).hexdigest() != sha256 or len(content) != size or 'md5:' + hashlib.md5(content).hexdigest() != checksum:
        _hold('APPROVED_LOCAL_BYTES_MISMATCH')
    result = compute_pdf_facts(content)
    result['source_path'] = str(source)
    result['source_checksum'] = checksum
    return result


def require_computed_field(value, *, field, facts):
    """Closed computable fact registry, exact numeric equality and JSON types."""
    if field not in SUPPORTED_FIELDS or field not in facts:
        _hold('FIELD_NOT_INDEPENDENTLY_COMPUTABLE_' + str(field))
    fact = facts[field]
    if fact['type'] == 'NUMBER':
        if type(value) not in (int, float): _hold('COMPUTED_NUMBER_WRONG_JSON_TYPE_' + field)
        try: actual = Decimal(str(value))
        except InvalidOperation: _hold('COMPUTED_NUMBER_MALFORMED_' + field)
        if not actual.is_finite() or actual <= 0 or actual != Decimal(fact['decimal']):
            _hold('RECOMPUTATION_MISMATCH_' + field)
    elif fact['type'] == 'INTEGER':
        if type(value) is not int: _hold('COMPUTED_INTEGER_WRONG_JSON_TYPE_' + field)
        if value != fact['value']: _hold('RECOMPUTATION_MISMATCH_' + field)
    elif fact['type'] == 'STRING':
        if type(value) is not str: _hold('COMPUTED_STRING_WRONG_JSON_TYPE_' + field)
        if value != fact['value']: _hold('RECOMPUTATION_MISMATCH_' + field)
    else:
        _hold('COMPUTED_FACT_TYPE_UNSUPPORTED')
