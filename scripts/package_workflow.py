#!/usr/bin/env python3
"""Build a deterministic KNIME archive from the tracked workflow directory."""
from pathlib import Path
import zipfile
import xml.etree.ElementTree as ET
from sync_workflow_sql import synchronize

ROOT = Path(__file__).resolve().parents[1]

def build():
    source = ROOT / 'knime/PROGETTO'
    target = ROOT / 'knime/PROGETTO.knwf'
    for path in source.rglob('*.xml'):
        for element in ET.parse(path).iter():
            if (element.get('type') == 'xpassword' or
                    element.get('key') in ('username', 'credentials')) and element.get('value', ''):
                raise ValueError(f'Clear saved authentication values before packaging: {path.relative_to(ROOT)}')
    synchronize()
    with zipfile.ZipFile(target, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in sorted(source.rglob('*')):
            if not path.is_file() or path.name == '.DS_Store':
                continue
            info = zipfile.ZipInfo(path.relative_to(source.parent).as_posix(), (2025, 7, 2, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o100644 << 16
            archive.writestr(info, path.read_bytes())
    print(f'Built {target.relative_to(ROOT)}')

if __name__ == '__main__':
    build()
