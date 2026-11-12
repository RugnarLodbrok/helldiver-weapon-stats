import codecs
import importlib.util
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

import yaml
from pydantic import JsonValue

sys.dont_write_bytecode = True
SCRIPT = Path(__file__).resolve().with_name('stats.py')
PROJECT_DIR = SCRIPT.parent.parent
spec = importlib.util.spec_from_file_location('hellforge_stats', SCRIPT)
assert spec is not None and spec.loader is not None
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class StatsTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.source = self.root / 'hellforge-stats.json'
        self.folder = self.root / 'stats'
        self.catalogs = self.root / 'catalogs'
        self.catalogs.mkdir()
        entries = [
            {'id': 'weapons/AR/GL-21 Test', 'name': 'AR/GL-21 Test',
             'category': 'primary', 'subtitle': 'Assault Rifle'},
            {'id': 'weapons/Support', 'name': 'Support',
             'category': 'support', 'subtitle': None},
            {'id': 'enemies/internal_id', 'name': 'Display name',
             'category': 'enemies', 'subtitle': None},
        ]
        self._write(self.catalogs / 'editor-catalog-test.json', {'objects': entries})
        self.data = {
            'format': 1,
            'raw': [{'value': 10}],
            'weapons': {'AR/GL-21 Test': {'damage': 100, 'nested': {'a': 2}},
                        'Support': {'ammo': 5}, 'Unknown': {'custom': 7}},
            'enemies': {'internal_id': {'health': 99}},
            'empty': {},
        }
        self._write(self.source, self.data)

    def _write(self, path: Path, data: dict[str, JsonValue]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        output = yaml.safe_dump(data, sort_keys=False) if path.suffix == '.yml' else json.dumps(data)
        path.write_text(output, encoding='utf-8')

    def _split(self) -> int:
        return module._split(self.source, self.folder, self.catalogs)

    def _read(self, path: Path) -> dict[str, JsonValue]:
        text = path.read_text(encoding='utf-8-sig')
        return yaml.safe_load(text) if path.suffix == '.yml' else json.loads(text)

    def test_roundtrip_and_routes(self) -> None:
        self.assertEqual(self._split(), 5)
        self.assertTrue((self.folder / 'primary/Assault Rifle/AR%2FGL-21 Test.yml').is_file())
        self.assertTrue((self.folder / 'support/Support.yml').is_file())
        self.assertTrue((self.folder / 'weapons/Unknown.yml').is_file())
        self.assertTrue((self.folder / 'enemies/internal_id.yml').is_file())
        self.assertFalse([*self.folder.rglob('*.json')])
        self.source.unlink()
        module._join(self.source, self.folder)
        self.assertEqual(self._read(self.source), self.data)

    def test_merge_precedence_and_preservation(self) -> None:
        fragment = self.folder / 'primary/Assault Rifle/AR%2FGL-21 Test.yml'
        self._write(fragment, {'weapons': {'AR/GL-21 Test': {
            'damage': 1, 'extra': 9, 'nested': {'a': 0, 'b': 8}}}})
        self._split()
        weapon = self._read(fragment)['weapons']['AR/GL-21 Test']
        self.assertEqual(weapon, {'damage': 100, 'extra': 9, 'nested': {'a': 2, 'b': 8}})
        weapon['damage'] = 200
        self._write(fragment, {'weapons': {'AR/GL-21 Test': weapon}})
        current = self._read(self.source)
        current['weapons']['AR/GL-21 Test']['local'] = 4
        current['raw'] = [{'value': 50}]
        self._write(self.source, current)
        module._join(self.source, self.folder)
        result = self._read(self.source)
        self.assertEqual(result['weapons']['AR/GL-21 Test']['damage'], 200)
        self.assertEqual(result['weapons']['AR/GL-21 Test']['local'], 4)
        self.assertEqual(result['raw'], [{'value': 10}])

    def test_invalid_split_does_not_write_other_files(self) -> None:
        fragment = self.folder / 'support/Support.yml'
        fragment.parent.mkdir(parents=True)
        fragment.write_text('{broken')
        original = self.source.read_bytes()
        with self.assertRaises(ValueError):
            self._split()
        self.assertFalse((self.folder / '_metadata.yml').exists())
        self.assertEqual(self.source.read_bytes(), original)

    def test_invalid_join_keeps_target(self) -> None:
        self._split()
        (self.folder / 'zz-invalid.yml').write_text('[]')
        original = self.source.read_bytes()
        with self.assertRaises(ValueError):
            module._join(self.source, self.folder)
        self.assertEqual(self.source.read_bytes(), original)

    def test_bom_newlines_and_key_order(self) -> None:
        self._split()
        self.source.write_bytes(codecs.BOM_UTF8 + b'{\r\n  "format": 1\r\n}\r\n')
        module._join(self.source, self.folder)
        result = self.source.read_bytes()
        self.assertTrue(result.startswith(codecs.BOM_UTF8))
        self.assertNotIn(b'\n', result.replace(b'\r\n', b''))
        self.assertEqual([*self._read(self.source)], sorted(self._read(self.source)))

    def test_no_catalogs_and_empty_join(self) -> None:
        with self.assertRaises(ValueError):
            module._split(self.source, self.folder, self.root / 'missing')
        with self.assertRaises(ValueError):
            module._join(self.source, self.folder)

    def _assert_sorted(self, value: JsonValue) -> None:
        if isinstance(value, dict):
            self.assertEqual([*value], sorted(value))
            for item in value.values():
                self._assert_sorted(item)
        elif isinstance(value, list):
            for item in value:
                self._assert_sorted(item)

    def test_recursive_sorting_and_yaml_scalar_types(self) -> None:
        self.data['weapons']['Unknown'] = {
            'z': None, 'a': {'z': 2, 'a': 1}, 'label': 'yes',
            'date': '2026-01-01', 'flag': True, 'values': [{'z': 2, 'a': 1}],
        }
        self._write(self.source, self.data)
        self._split()
        module._join(self.source, self.folder)
        self.assertEqual(self._read(self.source), self.data)
        for path in [self.source, *self.folder.rglob('*.yml')]:
            with self.subTest(path=path):
                self._assert_sorted(self._read(path))

    def test_join_escapes_ampersands_in_json(self) -> None:
        name = 'SG-225SP Breaker Spray&Pray'
        self.data['weapons'][name] = {'damage': 100, 'label': r'A&B literal \u0026'}
        self._write(self.source, self.data)
        self._split()
        module._join(self.source, self.folder)
        output = self.source.read_text(encoding='utf-8')
        self.assertIn(r'SG-225SP Breaker Spray\u0026Pray', output)
        self.assertNotIn('&', output)
        self.assertEqual(self._read(self.source), self.data)
        fragment = self.folder / 'weapons/SG-225SP Breaker Spray%26Pray.yml'
        self.assertIn(name, fragment.read_text(encoding='utf-8'))

    def test_shell_wrappers_accept_filename_with_spaces_from_another_directory(self) -> None:
        source = self.root / 'other stats.json'
        self._write(source, self.data)
        options = ['--stats-dir', str(self.folder), '--catalog-dir', str(self.catalogs)]
        commands = [
            ('split', [source.name]),
            ('split', ['--file', source.name]),
            ('join', ['--file', source.name]),
        ]
        for mode, arguments in commands:
            with self.subTest(mode=mode, arguments=arguments):
                result = subprocess.run(
                    [str(PROJECT_DIR / f'{mode}.sh'), *arguments, *options],
                    cwd=self.root, capture_output=True, text=True,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(self._read(source), self.data)


if __name__ == '__main__':
    unittest.main()
