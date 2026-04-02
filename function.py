import mysql.connector

def connect_to_db():
    return mysql.connector.connect(
    host="localhost",
    user="root",
    password="ghtwht@@@23N",
    database="python_ui"
)


def get_basic_info(cursor):
    queries = {

        "Total suppliers": "select count(*) as total_suppliers from suppliers",

        "Total product": "select count(*) as total_product from products",

        "Total Categories": "select count(distinct category) as total_categories from products",

        "Total sales value (last 3 month)":
            """SELECT 
                ROUND(COALESCE(SUM(ABS(se.change_quantity) * p.price), 0), 2)
            FROM stock_entries se
            JOIN products p ON p.product_id = se.product_id
            WHERE se.change_type = 'Sale'
            AND se.entry_date >= (
                SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
                FROM stock_entries
            )
            """
        ,

        "Total restock value made in last 3 month":
            """SELECT 
                ROUND(SUM(ABS(se.change_quantity) * (p.price)), 2) AS total_restock_value_in_last_3_month
            FROM stock_entries AS se
            JOIN products AS p ON p.product_id = se.product_id
            WHERE se.change_type = 'Restock'
            AND se.entry_date >= (
                SELECT DATE_SUB(MAX(entry_date), INTERVAL 3 MONTH)
                FROM stock_entries
            )""",

        "Below reorder level and no pending record":
            """SELECT COUNT(*)
            FROM products AS p
            WHERE p.stock_quantity < reorder_level
            AND product_id NOT IN (
                SELECT DISTINCT product_id
                FROM reorders
                WHERE status = 'Pending'
            )"""
    }

    result = {}
    for label, query in queries.items():
        cursor.execute(query)
        row = cursor.fetchone()
        result[label] = list(row.values())[0]
    return result


def get_additional_table(cursor):
    queries = {
        "Supplier contact details": "select supplier_name ,contact_name, email,phone from suppliers",

        "Product with supplier and stock":
            """select p.product_name, s.supplier_name , p.stock_quantity ,p.reorder_level
            from products as p
            join suppliers as s on 
            p.supplier_id = s.supplier_id
            order by p.product_name ASC""",

        "Product need reorder":
            """select product_name, product_id,stock_quantity, reorder_level from products where stock_quantity>reorder_level"""
    }

    tables = {}
    for label, query in queries.items():
        cursor.execute(query)
        tables[label] = cursor.fetchall()

    return tables

def get_categories(cursor):
    cursor.execute("SELECT DISTINCT category FROM products ORDER BY category ASC")
    rows = cursor.fetchall()
    return [row["category"] for row in rows]


def get_suplliers(cursor):
    cursor.execute("""
        SELECT supplier_id, supplier_name 
        FROM suppliers 
        ORDER BY supplier_name ASC
    """)
    return cursor.fetchall()


def add_new_manual_id(cursor, db, p_name, p_category, p_price, p_stock, p_reorder, p_supplier):
    proc_call = "CALL AddNewProductManualID(%s,%s,%s,%s,%s,%s)"

    params = (p_name, p_category, p_price, p_stock, p_reorder, p_supplier)

    cursor.execute(proc_call, params)
    db.commit()


def get_all_product(cursor):
    cursor.execute("select product_id ,product_name from products order by product_name")
    return cursor.fetchall()

def get_product_history(cursor , product_id):
    query = "select*from product_inventory_history where product_id = %s order by record_date Desc"
    cursor.execute(query, (product_id,))
    return cursor.fetchall()

def place_reorder(cursor, db,product_id, reorder_quantity):
    query = """INSERT INTO reorders (reorder_id, product_id, reorder_quantity, reorder_date, status)
    SELECT 
    MAX(reorder_id) + 1,
    %s,
    %s,
    CURRENT_DATE(),
    'Ordered'
    FROM reorders;
    """
    cursor.execute(query,(product_id,reorder_quantity))
    db.commit()


def get_pending_reorders(cursor):
    cursor.execute("""
    select r.reorder_id, p.product_name
    from reorders as r join products 
    as p on r.product_id = p.product_id
    """)
    return cursor.fetchall()


def mark_reorder_as_received(cursor, db, reorder_id):
    cursor.callproc("MarkReorderAsReceived",[reorder_id])
    db.commit()