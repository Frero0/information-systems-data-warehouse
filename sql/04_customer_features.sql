-- Corrected feature definitions for the two customer-segmentation models.
-- Customers without purchases are excluded. Discount is averaged per order line.
SELECT c."CustomerID" AS customer_id, c."CompanyName" AS company_name,
       COUNT(DISTINCT o."OrderID") AS order_count,
       COUNT(DISTINCT od."ProductID") AS distinct_products,
       SUM(od."UnitPrice" * od."Quantity") AS gross_spend,
       SUM(od."UnitPrice" * od."Quantity" *
           (1 - COALESCE(od."Discount", 0))) AS net_spend,
       SUM(od."Quantity") AS total_quantity,
       AVG(COALESCE(od."Discount", 0)) AS mean_discount
FROM "Customers" AS c
JOIN "Orders" AS o ON o."CustomerID" = c."CustomerID"
JOIN "Order Details" AS od ON od."OrderID" = o."OrderID"
GROUP BY c."CustomerID", c."CompanyName"
ORDER BY customer_id;
