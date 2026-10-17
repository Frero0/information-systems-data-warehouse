-- Country means Orders.ShipCountry. Unknown dates/countries are excluded.
WITH quarterly AS (
    SELECT od."ProductID" AS product_id, o."ShipCountry" AS country,
           DATE_TRUNC('quarter', o."OrderDate")::date AS quarter,
           SUM(od."Quantity") AS quantity
    FROM "Orders" AS o
    JOIN "Order Details" AS od ON od."OrderID" = o."OrderID"
    WHERE o."OrderDate" IS NOT NULL AND o."ShipCountry" IS NOT NULL
    GROUP BY od."ProductID", o."ShipCountry",
             DATE_TRUNC('quarter', o."OrderDate")::date
), calendar AS (
    SELECT product_id, country,
           GENERATE_SERIES(MIN(quarter)::timestamp, MAX(quarter)::timestamp,
                           INTERVAL '3 months')::date AS quarter
    FROM quarterly
    GROUP BY product_id, country
), dense AS (
    SELECT c.product_id, c.country, c.quarter, COALESCE(q.quantity, 0) AS quantity
    FROM calendar AS c
    LEFT JOIN quarterly AS q USING (product_id, country, quarter)
)
SELECT product_id, country, quarter, quantity,
       ROUND(AVG(quantity) OVER (
           PARTITION BY product_id, country ORDER BY quarter
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 2) AS moving_average_3q
FROM dense
ORDER BY product_id, country, quarter;
