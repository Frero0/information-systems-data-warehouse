-- Modern reference query. Revenue uses the historical order-line price.
-- Discounts and production costs are intentionally excluded from this metric.
SELECT p."ProductID" AS product_id,
       p."ProductName" AS product_name,
       SUM(od."UnitPrice" * od."Quantity") AS gross_revenue
FROM "Order Details" AS od
JOIN "Products" AS p ON p."ProductID" = od."ProductID"
GROUP BY p."ProductID", p."ProductName"
ORDER BY gross_revenue DESC, product_id
LIMIT 5;
