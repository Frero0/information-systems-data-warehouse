#!/usr/bin/env python3
"""Export PostgreSQL analyses and deterministic customer segmentation."""
import argparse
import csv
import html
import json
import math
import os
from pathlib import Path
import random
import subprocess

ROOT = Path(__file__).resolve().parents[1]
QUERIES = {
    'top_products': '01_top_products.sql',
    'rolling_by_product': '02_rolling_by_product.sql',
    'rolling_by_product_country': '03_rolling_by_product_country.sql',
    'customer_features': '04_customer_features.sql',
}
MODELS = {
    'purchase_behaviour': ('order_count', 'distinct_products', 'gross_spend'),
    'discount_behaviour': ('order_count', 'total_quantity', 'net_spend', 'mean_discount'),
}

def query_bundle():
    pairs = []
    for name, filename in QUERIES.items():
        query = (ROOT / 'sql' / filename).read_text().strip().rstrip(';')
        pairs.append(f"'{name}', (SELECT COALESCE(json_agg(t), '[]'::json) FROM (\n{query}\n) AS t)")
    return 'SELECT json_build_object(\n' + ',\n'.join(pairs) + '\n);\n'

def fetch(database, psql='psql', fixture=None):
    # One snapshot keeps the four analyses consistent. Fixtures are session-local.
    if fixture is None:
        source = 'BEGIN ISOLATION LEVEL REPEATABLE READ READ ONLY;\n'
    else:
        source = 'BEGIN;\nSET LOCAL search_path TO pg_temp;\n' + fixture + '\n'
    source += query_bundle() + 'ROLLBACK;\n'
    result = subprocess.run(
        [psql, '-X', '-w', '-qAt', '--set=ON_ERROR_STOP=1', '--dbname', database],
        input=source, text=True, capture_output=True, check=False,
    )
    if result.returncode:
        raise RuntimeError(result.stderr.strip())
    return json.loads(result.stdout)

def squared_distance(a, b):
    return sum((x - y) ** 2 for x, y in zip(a, b))

def normalize(points):
    if not points or not points[0]:
        raise ValueError('At least one observation and one feature are required.')
    width = len(points[0])
    if any(len(row) != width or any(not math.isfinite(v) for v in row) for row in points):
        raise ValueError('Feature values must be finite and rectangular.')
    minima = [min(row[j] for row in points) for j in range(width)]
    maxima = [max(row[j] for row in points) for j in range(width)]
    scaled = [[(v - minima[j]) / (maxima[j] - minima[j])
               if maxima[j] > minima[j] else 0.0
               for j, v in enumerate(row)] for row in points]
    return scaled, minima, maxima

def kmeans(points, k=3, seed=0, restarts=10, max_iterations=99):
    """Lloyd k-means with seeded restarts; input must already be scaled."""
    unique = sorted(set(tuple(row) for row in points))
    if k < 1 or len(unique) < k:
        raise ValueError(f'Clustering needs at least {k} distinct customer feature vectors.')
    if restarts < 1 or max_iterations < 1:
        raise ValueError('Restarts and iterations must be positive.')
    rng = random.Random(seed)
    best = None
    for _ in range(restarts):
        centers = [list(row) for row in rng.sample(unique, k)]
        for iteration in range(max_iterations):
            labels = [min(range(k), key=lambda c: squared_distance(row, centers[c])) for row in points]
            updated = []
            for cluster in range(k):
                members = [row for row, label in zip(points, labels) if label == cluster]
                # An empty cluster keeps its centroid. It is reported with size zero.
                updated.append([sum(row[j] for row in members) / len(members)
                                for j in range(len(points[0]))] if members else centers[cluster])
            movement = sum(squared_distance(a, b) for a, b in zip(centers, updated))
            centers = updated
            if movement <= 1e-12:
                break
        labels = [min(range(k), key=lambda c: squared_distance(row, centers[c])) for row in points]
        inertia = sum(squared_distance(row, centers[label]) for row, label in zip(points, labels))
        candidate = (inertia, labels, centers, iteration + 1)
        if best is None or candidate[0] < best[0]:
            best = candidate
    inertia, labels, centers, iterations = best
    # Stable numeric labels for display, without assigning business meanings.
    order = sorted(range(k), key=lambda c: tuple(centers[c]))
    remap = {old: new for new, old in enumerate(order)}
    return [remap[label] for label in labels], [centers[c] for c in order], inertia, iterations

def write_csv(path, records):
    with path.open('w', newline='', encoding='utf-8') as stream:
        if not records:
            return
        writer = csv.DictWriter(stream, fieldnames=list(records[0]), lineterminator='\n')
        writer.writeheader()
        writer.writerows(records)

def scatter(path, records, labels, xkey, ykey, title):
    colors = ['#2563eb', '#d97706', '#059669']
    xs = [float(row[xkey]) for row in records]
    ys = [float(row[ykey]) for row in records]
    xmax, ymax = max(xs) or 1, max(ys) or 1
    parts = ['<svg xmlns="http://www.w3.org/2000/svg" width="960" height="580" viewBox="0 0 960 580">',
             '<rect width="960" height="580" fill="#f8fafc"/>',
             '<g font-family="Arial,sans-serif" fill="#0f172a">',
             f'<text x="80" y="40" font-size="24">{html.escape(title)}</text>',
             '<text x="80" y="65" font-size="13">Two-feature projection; clustering uses all model features.</text>']
    for i in range(6):
        x, y = 80 + i * 152, 480 - i * 76
        parts += [f'<path d="M{x} 100 V480 M80 {y} H840" stroke="#dbe3ed" fill="none"/>',
                  f'<text x="{x}" y="505" text-anchor="middle" font-size="12">{xmax*i/5:.3g}</text>',
                  f'<text x="68" y="{y+4}" text-anchor="end" font-size="12">{ymax*i/5:.3g}</text>']
    for row, label, x, y in zip(records, labels, xs, ys):
        tooltip = html.escape(f'{row["customer_id"]} | cluster {label} | {xkey}={x:g} | {ykey}={y:g}')
        parts.append(f'<circle cx="{80+760*x/xmax:.2f}" cy="{480-380*y/ymax:.2f}" r="6" '
                     f'fill="{colors[label % len(colors)]}" fill-opacity="0.8" stroke="white"><title>{tooltip}</title></circle>')
    parts += [f'<text x="460" y="545" text-anchor="middle" font-size="15">{html.escape(xkey)}</text>',
              f'<text transform="translate(22 290) rotate(-90)" text-anchor="middle" font-size="15">{html.escape(ykey)}</text>']
    for label in sorted(set(labels)):
        parts.append(f'<circle cx="880" cy="{130+label*30}" r="6" fill="{colors[label % len(colors)]}"/>'
                     f'<text x="895" y="{134+label*30}" font-size="12">{label}</text>')
    parts.append('</g></svg>\n')
    path.write_text('\n'.join(parts))

def export(data, output):
    customers = data['customer_features']
    if len(customers) < 3:
        raise ValueError('At least three purchasing customers are required for k=3.')
    results = {}
    # Complete validation and clustering before creating outputs.
    for name, features in MODELS.items():
        points = [[float(row[key]) for key in features] for row in customers]
        scaled, minima, maxima = normalize(points)
        labels, centers, inertia, iterations = kmeans(scaled)
        results[name] = (features, labels, centers, inertia, iterations, minima, maxima)
    output.mkdir(parents=True, exist_ok=True)
    for name, records in data.items():
        write_csv(output / f'{name}.csv', records)
    summary = {'k': 3, 'seed': 0, 'restarts': 10, 'max_iterations': 99,
               'normalization': 'min-max [0, 1]; constant features become zero',
               'customer_count': len(customers), 'models': {}}
    for name, (features, labels, centers, inertia, iterations, minima, maxima) in results.items():
        rows = [dict(row, cluster=label) for row, label in zip(customers, labels)]
        write_csv(output / f'clusters_{name}.csv', rows)
        summary['models'][name] = {
            'features': features, 'feature_minima': minima, 'feature_maxima': maxima,
            'inertia': inertia, 'iterations_of_best_restart': iterations,
            'cluster_sizes': [labels.count(c) for c in range(3)],
            'centroids_normalized': centers,
            'centroids_original_units': [[minima[j] + v*(maxima[j]-minima[j])
                                          for j, v in enumerate(center)] for center in centers],
        }
        xkey, ykey = ('distinct_products', 'gross_spend') if name == 'purchase_behaviour' else ('total_quantity', 'net_spend')
        scatter(output / f'clusters_{name}.svg', customers, labels, xkey, ykey, name.replace('_', ' ').title())
    (output / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
    return summary

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default=os.environ.get('PGDATABASE', 'si_demo'))
    parser.add_argument('--psql', default=os.environ.get('PSQL', 'psql'))
    parser.add_argument('--output-dir', type=Path, default=ROOT / 'results')
    args = parser.parse_args()
    try:
        summary = export(fetch(args.database, args.psql), args.output_dir)
    except (OSError, RuntimeError, ValueError) as error:
        parser.exit(1, f'Analysis failed: {error}\n')
    print(f'Exported four analyses and two clustering models for {summary["customer_count"]} customers to {args.output_dir}.')

if __name__ == '__main__':
    main()
