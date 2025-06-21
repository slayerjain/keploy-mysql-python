SET SESSION cte_max_recursion_depth = 100000;

-- Create a user that *explicitly* uses caching_sha2_password
DROP USER IF EXISTS 'demo_user'@'%';
CREATE USER 'demo_user'@'%' IDENTIFIED WITH caching_sha2_password BY 'demopass';
GRANT ALL PRIVILEGES ON demo.* TO 'demo_user'@'%';
FLUSH PRIVILEGES;

-- A table with a ~10 MB row
CREATE TABLE big_table (
  id   INT PRIMARY KEY AUTO_INCREMENT,
  data LONGTEXT
) ENGINE = InnoDB;

-- Insert ≈10 MB of data (10 × 1 MiB blocks)
INSERT INTO big_table (data)
VALUES (REPEAT('X', 1024 * 1024 * 10));

-- For variety, add 5 × 2 MiB rows (another 10 MB total)
INSERT INTO big_table (data)
SELECT REPEAT('Y', 1024 * 1024 * 2) FROM dual
UNION ALL SELECT REPEAT('Y', 1024 * 1024 * 2)
UNION ALL SELECT REPEAT('Y', 1024 * 1024 * 2)
UNION ALL SELECT REPEAT('Y', 1024 * 1024 * 2)
UNION ALL SELECT REPEAT('Y', 1024 * 1024 * 2);


-- ------------------------------------------------------------------
-- A table holding >100 000 rows so we can test high-row-count selects
-- ------------------------------------------------------------------
DROP TABLE IF EXISTS lot_table;
CREATE TABLE lot_table (
  id   INT PRIMARY KEY AUTO_INCREMENT,
  data VARCHAR(50)
) ENGINE = InnoDB;

-- Insert 100 000 rows using a recursive CTE (MySQL 8+)
WITH RECURSIVE seq AS (
  SELECT 1 AS n
  UNION ALL
  SELECT n + 1 FROM seq WHERE n < 100000
)
INSERT INTO lot_table (data)
SELECT CONCAT('row_', n) FROM seq;