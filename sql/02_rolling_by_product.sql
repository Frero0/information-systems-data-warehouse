-- Fill internal missing calendar quarters with zero sales.
-- Each series spans its own first through last observed order quarter.
WITH quarterly AS (
    SELECT od."ProductID" AS product_id,
           DATE_TRUNC('quarter', o."OrderDate")::date AS quarter,
           SUM(od."Quantity") AS quantity
    FROM "Orders" AS o
    JOIN "Order Details" AS od ON od."OrderID" = o."OrderID"
    WHERE o."OrderDate" IS NOT NULL
    GROUP BY od."ProductID", DATE_TRUNC('quarter', o."OrderDate")::date
), calendar AS (
    SELECT product_id,
           GENERATE_SERIES(MIN(quarter)::timestamp, MAX(quarter)::timestamp,
                           INTERVAL '3 months')::date AS quarter
    FROM quarterly
    GROUP BY product_id
), dense AS (
    SELECT c.product_id, c.quarter, COALESCE(q.quantity, 0) AS quantity
    FROM calendar AS c
    LEFT JOIN quarterly AS q USING (product_id, quarter)
)
SELECT product_id, quarter, quantity,
       ROUND(AVG(quantity) OVER (
           PARTITION BY product_id ORDER BY quarter
           ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
       ), 2) AS moving_average_3q
FROM dense
ORDER BY product_id, quarter;
