import argparse
import codecs
import json
import os
import stat
import tempfile
from pathlib import Path
from urllib.parse import quote

from pydantic import BaseModel, ConfigDict, JsonValue, RootModel, ValidationError


BASE_DIR = Path(__file__).resolve().parent.parent
STATS_FILENAME = 'hellforge-stats.json'
METADATA_FILENAME = '_metadata.json'
CATALOG_PATTERN = 'editor-catalog-*.json'
ENCODING = 'utf-8'
INDENT = 2
WINDOWS_NEWLINE = b'\r\n'


class Document(RootModel[dict[str, JsonValue]]):
    pass


class CatalogObject(BaseModel):
    model_config = ConfigDict(strict=True)

    id: str
    name: str
    category: str
    subtitle: str | None = None


class Catalog(BaseModel):
    objects: list[CatalogObject]


def _read_document(path: Path) -> dict[str, JsonValue]:
    try:
        return Document.model_validate_json(path.read_text(encoding='utf-8-sig')).root
    except (ValueError, UnicodeError) as error:
        raise ValueError(f'{path}: {error}') from error


def _merge(existing: JsonValue, incoming: JsonValue) -> JsonValue:
    if isinstance(existing, dict) and isinstance(incoming, dict):
        result = existing.copy()
        for key, value in incoming.items():
            result[key] = _merge(result[key], value) if key in result else value
        return result
    return incoming


def _merge_documents(
    existing: dict[str, JsonValue], incoming: dict[str, JsonValue],
) -> dict[str, JsonValue]:
    return Document.model_validate(_merge(existing, incoming)).root


def _write_document(path: Path, data: dict[str, JsonValue]) -> None:
    original = path.read_bytes() if path.exists() else b''
    newline = WINDOWS_NEWLINE if WINDOWS_NEWLINE in original else b'\n'
    output = json.dumps(Document(data).root, ensure_ascii=False, indent=INDENT)
    encoded = (output + '\n').encode(ENCODING).replace(b'\n', newline)
    if original.startswith(codecs.BOM_UTF8):
        encoded = codecs.BOM_UTF8 + encoded
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(dir=path.parent, delete=False) as temporary:
            temporary_path = Path(temporary.name)
            temporary.write(encoded)
        if path.exists():
            temporary_path.chmod(stat.S_IMODE(path.stat().st_mode))
        os.replace(temporary_path, path)
    finally:
        if temporary_path is not None:
            temporary_path.unlink(missing_ok=True)


def _load_catalogs(directory: Path) -> dict[tuple[str, str], CatalogObject]:
    paths = sorted(directory.glob(CATALOG_PATTERN))
    if not paths:
        raise ValueError(f'No catalogs matching {CATALOG_PATTERN} found in {directory}')
    index: dict[tuple[str, str], CatalogObject] = {}
    for path in paths:
        try:
            catalog = Catalog.model_validate_json(path.read_text(encoding='utf-8-sig'))
        except (ValueError, UnicodeError) as error:
            raise ValueError(f'{path}: {error}') from error
        for entry in catalog.objects:
            section, separator, name = entry.id.partition('/')
            if not separator or not section or not name:
                raise ValueError(f'{path}: invalid object id: {entry.id!r}')
            key = (section, name)
            if key in index and index[key] != entry:
                raise ValueError(f'{path}: conflicting catalog entries for {entry.id!r}')
            index[key] = entry
    return index


def _path_segment(value: str) -> str:
    if not value:
        raise ValueError('Object or category name must not be empty')
    encoded = quote(value, safe=' -_')
    return encoded.replace('.', '%2E')  # Prevents `..` and trailing dots on Windows.


def _object_path(directory: Path, section: str, name: str, entry: CatalogObject | None) -> Path:
    category = entry.category if entry else section
    folder = directory / _path_segment(category)
    if entry and entry.subtitle:
        folder /= _path_segment(entry.subtitle)
    return folder / f'{_path_segment(name)}.json'


def _partition(
    data: dict[str, JsonValue], directory: Path, index: dict[tuple[str, str], CatalogObject],
) -> dict[Path, dict[str, JsonValue]]:
    fragments: dict[Path, dict[str, JsonValue]] = {}
    metadata: dict[str, JsonValue] = {}
    for section, objects in data.items():
        if not isinstance(objects, dict) or not objects:
            metadata[section] = objects
            continue
        for name, values in objects.items():
            path = _object_path(directory, section, name, index.get((section, name)))
            fragment: dict[str, JsonValue] = {section: {name: values}}
            fragments[path] = _merge_documents(fragments.get(path, {}), fragment)
    if metadata:
        fragments[directory / METADATA_FILENAME] = metadata
    return fragments


def _split(source: Path, directory: Path, catalogs: Path) -> int:
    data = _read_document(source)
    fragments = _partition(data, directory, _load_catalogs(catalogs))
    results = {}
    for path, fragment in fragments.items():
        existing = _read_document(path) if path.exists() else {}
        results[path] = _merge_documents(existing, fragment)
    for path, result in results.items():
        _write_document(path, result)
    return len(results)


def _join(target: Path, directory: Path) -> int:
    paths = sorted(directory.rglob('*.json'))
    if not paths:
        raise ValueError(f'No JSON files found in {directory}')
    if target.resolve() in {path.resolve() for path in paths}:
        raise ValueError('The working file must be outside the stats directory')
    result = _read_document(target) if target.exists() else {}
    for path in paths:
        result = _merge_documents(result, _read_document(path))
    _write_document(target, result)
    return len(paths)


parser = argparse.ArgumentParser(description='Split and join HellForge stats with recursive merging.')
parser.add_argument('mode', choices=('split', 'join'))
parser.add_argument('--file', type=Path, default=BASE_DIR / STATS_FILENAME, help='Working JSON file')
parser.add_argument('--stats-dir', type=Path, default=BASE_DIR / 'stats', help='Fragment directory')
parser.add_argument('--catalog-dir', type=Path, default=BASE_DIR.parent / 'hellforge-editor',
                    help='Editor catalog directory (required only for split)')


def main() -> None:
    args = parser.parse_args()
    try:
        if args.mode == 'split':
            if args.file.resolve().is_relative_to(args.stats_dir.resolve()):
                raise ValueError('The working file must be outside the stats directory')
            count = _split(args.file, args.stats_dir, args.catalog_dir)
            print(f'Updated {count} files in {args.stats_dir}')
        else:
            count = _join(args.file, args.stats_dir)
            print(f'Merged {count} files into {args.file}')
    except (OSError, ValueError, UnicodeError, ValidationError) as error:
        parser.exit(1, f'Error: {error}\n')


if __name__ == '__main__':
    main()
