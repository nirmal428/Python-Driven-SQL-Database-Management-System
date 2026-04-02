create database python_ui;

CREATE TABLE `products` (
  `product_id` int DEFAULT NULL,
  `product_name` text,
  `category` text,
  `price` double DEFAULT NULL,
  `stock_quantity` int DEFAULT NULL,
  `reorder_level` int DEFAULT NULL,
  `supplier_id` int DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `reorders` (
  `reorder_id` int DEFAULT NULL,
  `product_id` int DEFAULT NULL,
  `reorder_quantity` int DEFAULT NULL,
  `reorder_date` text,
  `status` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `shipments` (
  `shipment_id` int DEFAULT NULL,
  `product_id` int DEFAULT NULL,
  `supplier_id` int DEFAULT NULL,
  `quantity_received` int DEFAULT NULL,
  `shipment_date` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `stock_entries` (
  `entry_id` int DEFAULT NULL,
  `product_id` int DEFAULT NULL,
  `change_quantity` int DEFAULT NULL,
  `change_type` text,
  `entry_date` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


CREATE TABLE `suppliers` (
  `supplier_id` int DEFAULT NULL,
  `supplier_name` text,
  `contact_name` text,
  `email` text,
  `phone` text,
  `address` text
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;


select*from products;
select*from reorders;

-- 1. Total suppliers
select count(*) as total_supliers from suppliers;

-- 2. Total product
select count(*) as total_product from products;

-- 3. Total Categories
select count(distinct category) as total_categories from products;


-- 4. Total sales value made in last 3 month (quantity * price)
SELECT
    ROUND(SUM(ABS(se.change_quantity) * (p.price)),
            2) AS total_sales_value_in_last_3_month
FROM
    stock_entries AS se
        JOIN
    products AS p ON p.product_id = se.product_id
WHERE
    se.change_type = 'Sale'
        AND se.entry_date >= (SELECT
            DATE_SUB(MAX(entry_date),
                    INTERVAL 3 MONTH)
        FROM
            stock_entries);

  -- 5. Total restock value made in last 3 month (quantity * price)
SELECT
    ROUND(SUM(ABS(se.change_quantity) * (p.price)),
            2) AS total_sales_value_in_last_3_month
FROM
    stock_entries AS se
        JOIN
    products AS p ON p.product_id = se.product_id
WHERE
    se.change_type = 'Restock'
        AND se.entry_date >= (SELECT
            DATE_SUB(MAX(entry_date),
                    INTERVAL 3 MONTH)
        FROM
            stock_entries);


-- 6.
SELECT
    COUNT(*)
FROM
    products AS p
WHERE
    p.stock_quantity < reorder_level
        AND product_id NOT IN (SELECT DISTINCT
            product_id
        FROM
            reorders
        WHERE
            status = 'Pending');

-- 7 Supplier and their contact details
select supplier_name ,contact_name, email,phone from suppliers;

-- 8. Product with thweir supplier and current stock
select p.product_name, s.supplier_name , p.stock_quantity ,p.reorder_level
from products as p
join suppliers as s on
p.supplier_id = s.supplier_id
order by p.product_name ASC;

-- 9. Product need reorder
select product_name, product_id,stock_quantity, reorder_level from products where stock_quantity>reorder_level;




-- 10. Add New Product
delimiter $$
create procedure AddNewProductManualID(
     in p_name varchar(255),
     in p_category varchar(100),
     in p_price decimal(10,2),
     in p_stock int,
     in p_reorder int,
     in p_supplier int
)
DELIMITER $$

CREATE PROCEDURE AddNewProductManualID(
    IN p_name VARCHAR(255),
    IN p_category VARCHAR(100),
    IN p_price DECIMAL(10,2),
    IN p_stock INT,
    IN p_reorder INT,
    IN p_supplier INT
)
BEGIN
    DECLARE new_prod_id INT;
    DECLARE new_shipment_id INT;
    DECLARE new_entry_id INT;

    -- Product ID
    SELECT IFNULL(MAX(product_id), 0) + 1 INTO new_prod_id FROM products;

    INSERT INTO products(
        product_id, product_name, category, price,
        stock_quantity, reorder_level, supplier_id
    )
    VALUES(
        new_prod_id, p_name, p_category, p_price,
        p_stock, p_reorder, p_supplier
    );

    -- Shipment ID
    SELECT IFNULL(MAX(shipment_id), 0) + 1 INTO new_shipment_id FROM shipments;

    INSERT INTO shipments(
        shipment_id, product_id, supplier_id,
        quantity_received, shipment_date
    )
    VALUES(
        new_shipment_id, new_prod_id, p_supplier,
        p_stock, CURDATE()
    );

    -- Stock Entry ID
    SELECT IFNULL(MAX(entry_id), 0) + 1 INTO new_entry_id FROM stock_entries;

    INSERT INTO stock_entries(
        entry_id, product_id, change_quantity,
        change_type, entry_date
    )
    VALUES(
        new_entry_id, new_prod_id, p_stock,
        'Restock', CURDATE()
    );

END $$

DELIMITER ;


# add changes
call AddNewProductManualID("Smart watch","electronics",99.99,100,25,5);
#chech changes
select * from products where product_name = "Bettles";
select*from shipments where product_id=201;
select*from stock_entries where product_id=201;
select*from shipments;


-- product history

create or replace view product_inventory_history as
select
pih.product_id,
pih.record_type,
pih.record_date,
pih.Quantity,
pih.change_type,
pr.supplier_id
 from(

select product_id,
"Stock Entry" as record_type,
shipment_date as record_date,
quantity_received as Quantity,
null change_type
 from shipments

 union all

select
product_id,
"Stock Entry" as record_type,
entry_date as record_date,
change_quantity as Quantity,
change_type
from stock_entries)
pih
join products pr on pr.product_id=pih.product_id;

select*from
product_inventory_history
where product_id=123
order by record_date desc;


-- Place and Reorder
INSERT INTO reorders (reorder_id, product_id, reorder_quantity, reorder_date, status)
SELECT
    MAX(reorder_id) + 1,
    101,
    200,
    CURRENT_DATE(),
    'ordered'
FROM reorders;

select *from reorders where product_id=101 order by reorder_id desc;



-- Received Order
DELIMITER $$

CREATE PROCEDURE MarkReorderAsReceived(IN in_reorder_id INT)
BEGIN
    DECLARE prod_id INT;
    DECLARE qty INT;
    DECLARE sup_id INT;
    DECLARE new_shipment_id INT;
    DECLARE new_entry_id INT;

    START TRANSACTION;

    SELECT product_id, reorder_quantity
    INTO prod_id, qty
    FROM reorders
    WHERE reorder_id = in_reorder_id;

    SELECT supplier_id
    INTO sup_id
    FROM products
    WHERE product_id = prod_id;

    UPDATE reorders
    SET status = 'Received'
    WHERE reorder_id = in_reorder_id;

    UPDATE products
    SET stock_quantity = stock_quantity + qty
    WHERE product_id = prod_id;

    SELECT IFNULL(MAX(shipment_id),0)+1 INTO new_shipment_id FROM shipments;

    INSERT INTO shipments (shipment_id, product_id, supplier_id, quantity_received, shipment_date)
    VALUES (new_shipment_id, prod_id, sup_id, qty, CURDATE());

    SELECT IFNULL(MAX(entry_id),0)+1 INTO new_entry_id FROM stock_entries;

    INSERT INTO stock_entries (entry_id, product_id, change_quantity, change_type, entry_date)
    VALUES (new_entry_id, prod_id, qty, 'Restock', CURDATE());

    COMMIT;
END$$

DELIMITER ;
