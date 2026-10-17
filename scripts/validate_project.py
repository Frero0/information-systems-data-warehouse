#!/usr/bin/env python3
"""Validate workflow structure, SQL synchronization, credentials and packaging."""
from pathlib import Path
import re
import xml.etree.ElementTree as ET
import zipfile

ROOT = Path(__file__).resolve().parents[1]
NS = {'k': 'http://www.knime.org/2008/09/XMLConfig'}

def validate():
    source = ROOT / 'knime/PROGETTO'
    workflow = ET.parse(source / 'workflow.knime').getroot()
    ids = set()
    for node in workflow.find("k:config[@key='nodes']", NS):
        node_id = int(node.find("k:entry[@key='id']", NS).get('value'))
        assert node_id not in ids, 'Duplicate node ID'
        ids.add(node_id)
        path = source / node.find("k:entry[@key='node_settings_file']", NS).get('value')
        assert path.is_file(), f'Missing settings: {path.name}'
    incoming = set()
    edges = []
    for edge in workflow.find("k:config[@key='connections']", NS):
        values = {e.get('key'): int(e.get('value')) for e in edge}
        a, b = values['sourceID'], values['destID']
        assert a in ids and b in ids, 'Dangling connection'
        destination = (b, values['destPort'])
        assert destination not in incoming, 'Multiple edges into one input port'
        incoming.add(destination)
        edges.append((a, b))
    remaining = set(ids)
    while remaining:
        ready = {n for n in remaining if not any(a in remaining and b == n for a, b in edges)}
        assert ready, 'Cycle in workflow'
        remaining -= ready
    connectors = 0
    selectors = {}
    for path in source.rglob('*.xml'):
        tree = ET.parse(path)
        for element in tree.iter():
            if element.get('type') == 'xpassword':
                assert element.get('value', '') == '', 'Saved password found'
            if element.get('key') in ('username', 'credentials'):
                assert element.get('value', '') == '', 'Saved authentication value found'
        if path.parent.name.startswith('PostgreSQL Connector'):
            connectors += 1
        if path.parent.name.startswith('DB Table Selector'):
            node_id = int(re.search(r'#(\d+)', path.parent.name).group(1))
            model = tree.getroot().find("k:config[@key='model']", NS)
            assert model.find("k:entry[@key='custom_query']", NS).get('value') == 'true'
            selectors[node_id] = model.find("k:entry[@key='sql_statement']", NS).get('value')
    assert connectors == 4
    for node_id, filename in [(2, '01_top_products.sql'), (13, '02_rolling_by_product.sql'),
                              (14, '03_rolling_by_product_country.sql'),
                              (76, '04_customer_features.sql'), (101, '04_customer_features.sql')]:
        query = (ROOT / 'sql' / filename).read_text().strip().rstrip(';')
        assert query in selectors[node_id], f'KNIME query differs from {filename}'
    with zipfile.ZipFile(ROOT / 'knime/PROGETTO.knwf') as archive:
        assert archive.testzip() is None
        expected = {p.relative_to(source.parent).as_posix(): p.read_bytes()
                    for p in source.rglob('*') if p.is_file()}
        assert set(archive.namelist()) == set(expected), 'Archive file list differs'
        for name, content in expected.items():
            assert archive.read(name) == content, f'Archive out of date: {name}'
    for path in ROOT.rglob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)', path.read_text()):
            if target.startswith(('https://', 'http://', '#', 'mailto:')):
                continue
            assert (path.parent / target.split('#')[0]).exists(), f'Broken local link: {target}'
    print(f'Project verified: {len(ids)} nodes, {len(edges)} edges, four empty connector credentials, synchronized SQL, current archive and local links.')

if __name__ == '__main__':
    validate()
