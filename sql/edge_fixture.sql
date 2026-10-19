-- Applied after clearing the sample data. Expected rows are maintained by hand
-- in question_bank.json, not generated from the reference queries.
INSERT INTO customers VALUES (1,'One','North'),(2,'Two',NULL),(3,'Three','North');
INSERT INTO orders VALUES (1,1,'2025-12-31',500),(2,1,'2026-01-01',500),(3,1,'2026-01-02',NULL),(4,2,'2026-01-01',1001);
INSERT INTO employees VALUES (1,'A',10,50),(2,'B',10,50),(3,'C',20,50);
INSERT INTO users VALUES (1,NULL),(2,NULL),(3,'x'),(4,'x'),(5,'y');
INSERT INTO products VALUES (1,'Sold'),(2,'Unsold');
INSERT INTO order_items VALUES (1,1,1),(2,NULL,1);
INSERT INTO transactions VALUES (1,7,'2025-12-31',100),(2,7,'2025-12-31',-100),(3,7,'2026-01-01',10),(4,8,'2026-01-01',-5);
INSERT INTO events VALUES (1,1,'2025-12-31 23:59:59'),(2,1,'2025-12-31 23:59:59'),(3,2,'2026-01-01 00:00:00'),(4,NULL,'2026-01-01 01:00:00');
