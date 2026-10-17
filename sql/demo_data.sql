-- Synthetic demonstration data, created for this repository.
-- This is NOT the original Northwind backup and contains no real customers.
-- Run only in an empty, dedicated database. No DROP or replacement operations.
CREATE TABLE "Customers" (
    "CustomerID" text PRIMARY KEY,
    "CompanyName" text NOT NULL
);
CREATE TABLE "Products" (
    "ProductID" integer PRIMARY KEY,
    "ProductName" text NOT NULL,
    "UnitPrice" numeric NOT NULL CHECK ("UnitPrice" >= 0)
);
CREATE TABLE "Orders" (
    "OrderID" integer PRIMARY KEY,
    "CustomerID" text NOT NULL REFERENCES "Customers",
    "OrderDate" timestamp,
    "ShipCountry" text
);
CREATE TABLE "Order Details" (
    "OrderID" integer REFERENCES "Orders",
    "ProductID" integer REFERENCES "Products",
    "UnitPrice" numeric NOT NULL CHECK ("UnitPrice" >= 0),
    "Quantity" integer NOT NULL CHECK ("Quantity" > 0),
    "Discount" numeric NOT NULL CHECK ("Discount" BETWEEN 0 AND 1),
    PRIMARY KEY ("OrderID", "ProductID")
);
INSERT INTO "Customers" VALUES
    ('A', 'Demo Alpha'), ('B', 'Demo Beta'), ('C', 'Demo Gamma'),
    ('D', 'Demo Delta'), ('E', 'Demo Epsilon'), ('F', 'Demo Zeta'),
    ('G', 'Demo No Purchases');
-- Products 1 and 2 deliberately share a name to test grouping by identity.
-- Catalogue prices deliberately differ from historical order-line prices.
INSERT INTO "Products" VALUES
    (1, 'Demo Tea', 999), (2, 'Demo Tea', 888), (3, 'Demo Coffee', 777),
    (4, 'Demo Cocoa', 666), (5, 'Demo Juice', 555), (6, 'Demo Water', 444);
INSERT INTO "Orders" VALUES
    (1, 'A', '2024-01-15', 'Italy'), (2, 'A', '2024-07-15', 'Italy'),
    (3, 'B', '2024-04-15', 'France'), (4, 'B', '2025-01-15', 'France'),
    (5, 'C', '2024-01-20', 'Italy'), (6, 'D', '2024-10-10', 'Spain'),
    (7, 'E', '2024-01-20', 'Italy'), (8, 'F', '2024-01-21', 'France'),
    (9, 'F', '2024-07-21', 'France');
INSERT INTO "Order Details" VALUES
    (1, 1, 10, 10, 0), (1, 2, 20, 2, 0.25),
    (2, 1, 12, 30, 0.10), (2, 3, 5, 4, 0),
    (3, 1, 11, 20, 0), (3, 4, 3, 8, 0.50),
    (4, 1, 13, 40, 0), (5, 2, 22, 3, 0),
    (6, 3, 6, 50, 0.20), (6, 5, 2, 10, 0),
    (7, 6, 1, 1, 0), (8, 5, 2, 100, 0.10),
    (9, 5, 3, 100, 0.20);
