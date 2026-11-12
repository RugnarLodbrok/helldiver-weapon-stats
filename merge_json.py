import argparse
import json
from pathlib import Path
from typing import Any


INDENT = 2


def _merge(first: Any, second: Any, path: str = '$') -> Any:
    if isinstance(first, list) and isinstance(second, list):
        raise ValueError(f'List merging is not implemented: {path}')
    if isinstance(first, dict) and isinstance(second, dict):
        result = first.copy()
        for key, value in second.items():
            result[key] = (
                _merge(first[key], value, f'{path}[{json.dumps(key, ensure_ascii=False)}]')
                if key in first else value
            )
        return result
    return second


parser = argparse.ArgumentParser(description='Recursively merge JSON, giving priority to the second file.')
parser.add_argument('first', type=Path, help='First JSON file')
parser.add_argument('second', type=Path, help='Second JSON file, takes priority')


def main() -> None:
    args = parser.parse_args()
    try:
        first = json.loads(args.first.read_bytes())
        second = json.loads(args.second.read_bytes())
        result = _merge(first, second)
        output = json.dumps(result, ensure_ascii=False, indent=INDENT, sort_keys=True)
    except (OSError, ValueError, UnicodeError) as error:
        parser.exit(1, f'Error: {error}\n')
    print(output)


if __name__ == '__main__':
    main()
