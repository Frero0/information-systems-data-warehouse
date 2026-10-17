#!/usr/bin/env python3
"""Check analytical semantics using temporary synthetic tables in PostgreSQL."""
import argparse
from pathlib import Path
from analyze import fetch

ROOT = Path(__file__).resolve().parents[1]

def check(data):
    top = data['top_products']
    assert [r['product_id'] for r in top] == [1, 5, 3, 2, 4], top
    assert [r['gross_revenue'] for r in top] == [1200, 520, 320, 106, 24], top
    rolling = data['rolling_by_product']
    p1 = [r for r in rolling if r['product_id'] == 1]
    assert [r['quantity'] for r in p1] == [10, 20, 30, 0, 40], p1
    assert [r['moving_average_3q'] for r in p1] == [10, 15, 20, 16.67, 23.33], p1
    p2 = [r for r in rolling if r['product_id'] == 2]
    assert len(p2) == 1 and p2[0]['moving_average_3q'] == 5, p2
    country = data['rolling_by_product_country']
    italy = [r for r in country if r['product_id'] == 1 and r['country'] == 'Italy']
    france = [r for r in country if r['product_id'] == 1 and r['country'] == 'France']
    assert [r['quantity'] for r in italy] == [10, 0, 30], italy
    assert [r['moving_average_3q'] for r in italy] == [10, 5, 13.33], italy
    assert [r['moving_average_3q'] for r in france] == [20, 10, 6.67, 13.33], france
    customers = {r['customer_id']: r for r in data['customer_features']}
    assert set(customers) == set('ABCDEF'), customers
    a = customers['A']
    assert (a['order_count'], a['distinct_products'], a['gross_spend'], a['net_spend'], a['total_quantity']) == (2, 3, 520, 474, 46), a
    assert abs(a['mean_discount'] - 0.0875) < 1e-12, a
    assert customers['F']['net_spend'] == 420
    print('SQL verified: historical prices, top-five ranking, product identities, calendar gaps, year boundaries, product/country isolation, partial windows, distinct orders and discount arithmetic.')

def fixture():
    return (ROOT / 'sql/demo_data.sql').read_text().replace('CREATE TABLE ', 'CREATE TEMP TABLE ')

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--database', default='postgres')
    parser.add_argument('--psql', default='psql')
    args = parser.parse_args()
    check(fetch(args.database, args.psql, fixture()))
