# SQL Assessment Set (SQL001–SQL010)

Use `sqlite3 assessment.db < sql/schema.sql` to load the sample schema. The examples use SQLite; explain dialect differences where relevant.

## SQL001 — Customers Without Orders (Easy)

Return customer IDs and names for customers who have never placed an order.

**Schema:** `customers(customer_id, name); orders(order_id, customer_id, order_date, amount)`

**Reference query:**
```sql
SELECT c.customer_id, c.name FROM customers c LEFT JOIN orders o ON o.customer_id = c.customer_id WHERE o.order_id IS NULL ORDER BY c.customer_id;
```

**Pitfall:** LEFT JOIN plus IS NULL or NOT EXISTS; avoid NOT IN if the subquery may contain NULL.

## SQL002 — Revenue by Region (Easy)

Return each region and total order revenue, including only regions with revenue above 1000.

**Schema:** `customers(customer_id, name, region); orders(order_id, customer_id, order_date, amount)`

**Reference query:**
```sql
SELECT c.region, SUM(o.amount) AS revenue FROM customers c JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.region HAVING SUM(o.amount) > 1000 ORDER BY revenue DESC;
```

**Pitfall:** Filter aggregated results with HAVING, not WHERE.

## SQL003 — Second Highest Salary (Easy)

Return the second-highest distinct salary, or NULL if it does not exist.

**Schema:** `employees(employee_id, name, salary)`

**Reference query:**
```sql
SELECT MAX(salary) AS second_highest_salary FROM employees WHERE salary < (SELECT MAX(salary) FROM employees);
```

**Pitfall:** Distinct salary levels matter; MAX below the maximum handles ties.

## SQL004 — Top Employee per Department (Medium)

Return all employees tied for the highest salary in each department.

**Schema:** `employees(employee_id, name, department_id, salary)`

**Reference query:**
```sql
WITH ranked AS (SELECT e.*, DENSE_RANK() OVER (PARTITION BY department_id ORDER BY salary DESC) AS rnk FROM employees e) SELECT employee_id, name, department_id, salary FROM ranked WHERE rnk = 1 ORDER BY department_id, employee_id;
```

**Pitfall:** Use DENSE_RANK or RANK to preserve ties; ROW_NUMBER returns only one winner.

## SQL005 — Monthly Revenue (Easy)

Return monthly revenue grouped by year and month. Ignore rows with NULL amount.

**Schema:** `orders(order_id, order_date, amount)`

**Reference query:**
```sql
SELECT strftime('%Y-%m', order_date) AS month, SUM(amount) AS revenue FROM orders WHERE amount IS NOT NULL GROUP BY strftime('%Y-%m', order_date) ORDER BY month;
```

**Pitfall:** This reference uses SQLite strftime; date syntax varies by database.

## SQL006 — Duplicate Emails (Easy)

Return email addresses that occur more than once. Ignore NULL email values.

**Schema:** `users(user_id, email)`

**Reference query:**
```sql
SELECT email FROM users WHERE email IS NOT NULL GROUP BY email HAVING COUNT(*) > 1 ORDER BY email;
```

**Pitfall:** Use COUNT(*) after excluding NULLs; grouping by user_id would defeat duplicate detection.

## SQL007 — Customers With At Least Three Orders (Easy)

Return each customer ID and name for customers with at least three orders.

**Schema:** `customers(customer_id, name); orders(order_id, customer_id, order_date, amount)`

**Reference query:**
```sql
SELECT c.customer_id, c.name FROM customers c JOIN orders o ON o.customer_id = c.customer_id GROUP BY c.customer_id, c.name HAVING COUNT(o.order_id) >= 3 ORDER BY c.customer_id;
```

**Pitfall:** COUNT orders, not amount; aggregate by customer identity.

## SQL008 — Running Account Balance (Medium)

For each account transaction, return transaction ID, account ID, date, amount, and running balance. Order same-day transactions by transaction_id.

**Schema:** `transactions(transaction_id, account_id, transaction_date, amount)`

**Reference query:**
```sql
SELECT transaction_id, account_id, transaction_date, amount, SUM(amount) OVER (PARTITION BY account_id ORDER BY transaction_date, transaction_id ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW) AS running_balance FROM transactions ORDER BY account_id, transaction_date, transaction_id;
```

**Pitfall:** Include a deterministic tie-breaker and explicit ROWS frame.

## SQL009 — Products Never Sold (Medium)

Return product IDs and names for products that do not appear in any order item.

**Schema:** `products(product_id, name); order_items(order_id, product_id, quantity)`

**Reference query:**
```sql
SELECT p.product_id, p.name FROM products p WHERE NOT EXISTS (SELECT 1 FROM order_items oi WHERE oi.product_id = p.product_id) ORDER BY p.product_id;
```

**Pitfall:** A product can exist without sales; NOT EXISTS avoids NULL pitfalls.

## SQL010 — Daily Active Users (Medium)

Return each date and count of distinct users who performed at least one event that day.

**Schema:** `events(event_id, user_id, event_time)`

**Reference query:**
```sql
SELECT date(event_time) AS event_date, COUNT(DISTINCT user_id) AS active_users FROM events WHERE user_id IS NOT NULL GROUP BY date(event_time) ORDER BY event_date;
```

**Pitfall:** Count distinct users rather than events; date truncation depends on SQL dialect.
