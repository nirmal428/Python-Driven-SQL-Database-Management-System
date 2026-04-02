from logging import exception

import streamlit as st
import pandas as pd

from db_fuction import (
connect_to_db,
get_basic_info,
get_additional_table,
get_categories,
get_suplliers,
add_new_manual_id,
get_all_product,
get_product_history,
place_reorder,
get_pending_reorders,
mark_reorder_as_received
)

#Sidebar
st.sidebar.title("Inventory Management Dashboard")
option = st.sidebar.radio("Select Option",["Basic Information" , "Operational Task"])

#main space
st.title("Inventory and Supply Chain Dashboard")
db = connect_to_db()
cursor =db.cursor(dictionary=True)


# Basic info page
if option=="Basic Information":
    st.header("Basic Metrics")

    #get basic info from DB
    basic_info = get_basic_info(cursor)

    cols = st.columns(3)
    keys = list(basic_info.keys())

    for i in range(3):
        cols[i].metric(label=keys[i],value=basic_info[keys[i]])

    cols = st.columns(3)
    for i in range(3,6):
        cols[i-3].metric(label=keys[i],value=basic_info[keys[i]])

    st.divider()

    # fetch and display detailed tables
    tables = get_additional_table(cursor)
    for labels , data in tables.items():
        st.header(labels)
        df=pd.DataFrame(data)
        st.dataframe(df)
        st.divider()


elif option == "Operational Task":
    st.header("Operational Task")
    selected_task = st.selectbox("Choose Task",["Add new Product","Product History","Place Reorder","Receive Order"])
    if selected_task == "Add new Product":
        st.header("Add new Product")
        categories = get_categories(cursor)
        suppliers = get_suplliers(cursor)

        with st.form("Add_Product_form"):
            product_name = st.text_input("Product_Name")
            product_category = st.selectbox("Category",categories)
            product_price = st.number_input("Price",min_value=0.00)
            product_stock = st.number_input("Stock Quantity",min_value=0,step=1)
            product_level = st.number_input("Reorder Level",min_value=0,step=1)

            supplier_ids = [s["supplier_id"] for s in suppliers]
            supplier_name = [s["supplier_name"] for s in suppliers]

            supplier_id = st.selectbox(
                "Supplier",options=supplier_ids,
                format_func=lambda x: supplier_name[supplier_ids.index(x)]
            )

            submitted = st.form_submit_button("Add Product")

            if submitted:
                if not product_name:
                    st.error("Please enter the product name")
                else:
                    try:
                        add_new_manual_id(cursor,
                                          db,
                                          product_name,
                                          product_category,
                                          product_price,
                                          product_stock,
                                          product_level,
                                          supplier_id
                                          )
                        st.success(f"Product {product_name} added successfully")
                    except Exception as e:
                            st.error(f"Error adding the product: {e}")

  # ----------------------------Product History-------------------

    if selected_task == "Product History":
        st.header("Product Inventory History")

        products = get_all_product(cursor)
        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        selected_product_name = st.selectbox("select product",options=product_names)

        if selected_product_name:
            selected_product_id = product_ids[product_names.index(selected_product_name)]
            history_data = get_product_history(cursor,selected_product_id)
            if history_data:
                df=pd.DataFrame(history_data)
                st.dataframe(df)
            else:
                st.info("No History found")

# ----------------Place and Reorder----------------

    if selected_task =="Place Reorder":
        st.header("Place and Reorder")

        products = get_all_product(cursor)

        product_names = [p["product_name"] for p in products]
        product_ids = [p["product_id"] for p in products]

        selected_product_name = st.selectbox("select product",options=product_names)
        reorder_qty = st.number_input("Reorder Quantity ",min_value=1,step=1)

        if st.button("Place Reorder"):
            if not selected_product_name:
                st.error("Please select Product")
            elif reorder_qty <=0:
                st.error("Reorder quantity must be greater than 0 ")
            else:
                selected_product_id = product_ids[product_names.index(selected_product_name)]
                try:
                    place_reorder(cursor,db,selected_product_id,reorder_qty)
                    st.success(f"order Placed for {selected_product_name} with quantity {reorder_qty}")
                except Exception as e:
                    st.error(f"Error Placing reorder : {e}")


# ------------------------------Place and Received Order-------------------------------

    elif selected_task=="Receive Order":
        st.header("Mark Reorder as Received")
        pending_reorders = get_pending_reorders(cursor)
        if not pending_reorders:
            st.info("No Pending Order to receive")
        else:
            reorder_ids = [r['reorder_id'] for r in pending_reorders]
            reorder_labels = [f"ID {r['reorder_id']} - {r['product_name']}" for r in pending_reorders]

            selected_label = st.selectbox("Select Reorder to mark as Received",options=reorder_labels)

            if selected_label:
                selected_reorder_id = reorder_ids[reorder_labels.index(selected_label)]

                if st.button("Mark as Received"):
                    try:
                        mark_reorder_as_received(cursor,db,selected_reorder_id)
                        st.success(f"Reorder ID {selected_reorder_id} marked as received")
                    except Exception as e:
                        st.error(f"Error : {e}")
