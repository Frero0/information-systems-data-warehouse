#!/usr/bin/env python3
"""Keep KNIME's DB Table Selector queries synchronized with sql/."""
from pathlib import Path
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
URI = 'http://www.knime.org/2008/09/XMLConfig'
NS = {'k': URI}
ET.register_namespace('', URI)

def synchronize():
    def query(filename):
        return (ROOT / 'sql' / filename).read_text().strip().rstrip(';')
    features = query('04_customer_features.sql')
    queries = {
        2: query('01_top_products.sql'),
        13: query('02_rolling_by_product.sql'),
        14: query('03_rolling_by_product_country.sql'),
        76: 'SELECT customer_id AS "CustomerID", order_count AS "Count*(OrderID)", '
            'distinct_products AS "Unique count*(ProductID)", gross_spend AS "Sum(Spesa tot)" '
            f'FROM (\n{features}\n) AS features',
        101: 'SELECT customer_id AS "CustomerID", order_count AS "Count*(OrderID)", '
             'total_quantity AS "Sum(Quantity)", net_spend AS "Sum(Custom Aggregation)", '
             'mean_discount AS "Mean(Discount)" '
             f'FROM (\n{features}\n) AS features',
    }
    for node_id, sql in queries.items():
        path = ROOT / f'knime/PROGETTO/DB Table Selector (#{node_id})/settings.xml'
        tree = ET.parse(path)
        model = tree.getroot().find("k:config[@key='model']", NS)
        model.find("k:entry[@key='sql_statement']", NS).set('value', sql)
        tree.write(path, encoding='UTF-8', xml_declaration=True)

if __name__ == '__main__':
    synchronize()
    print('Synchronized five KNIME SQL selectors.')
