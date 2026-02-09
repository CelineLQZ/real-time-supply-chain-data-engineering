customer_columns = ["Customer Id", "Customer Email", "Customer Fname", "Customer Lname",
                    "Customer Segment", "Customer City", "Customer Country",
                    "Customer State", "Customer Street", "Customer Zipcode"]

product_columns = ["Product Card Id", "Product Category Id", "Category Name", "Product Description",
                   "Product Image", "Product Name", "Product Price", "Product Status"]

location_columns = ["Order Zipcode", "Order City", "Order State", "Order Region","Order Country",
                    "Latitude", "Longitude"]

order_columns = ["Order Id","order date (DateOrders)", "Order Customer Id", "Order Item Id","Product Card Id",
                "Order Item Discount", "Order Item Discount Rate", "Order Item Product Price",
                "Order Item Profit Ratio", "Order Item Quantity", "Sales per customer", "Sales",
                "Order Item Total", "Order Profit Per Order", "Order Status","Department Id"]

shipping_columns = ["shipping date (DateOrders)", "Days for shipping (real)", "Days for shipment (scheduled)",
                    "Shipping Mode","Delivery Status"]

department_columns = ["Department Id", "Department Name" ,"Market"]
metadata_columns = ["key","offset","partition","time","topic"]

# 列名映射：原始列名 -> 标准化列名（用下划线替代空格）
column_name_mapping = {
    # customer
    "Customer Id": "Customer_Id",
    "Customer Email": "Customer_Email",
    "Customer Fname": "Customer_Fname",
    "Customer Lname": "Customer_Lname",
    "Customer Segment": "Customer_Segment",
    "Customer City": "Customer_City",
    "Customer Country": "Customer_Country",
    "Customer State": "Customer_State",
    "Customer Street": "Customer_Street",
    "Customer Zipcode": "Customer_Zipcode",
    # product
    "Product Card Id": "Product_Card_Id",
    "Product Category Id": "Product_Category_Id",
    "Category Name": "Category_Name",
    "Product Description": "Product_Description",
    "Product Image": "Product_Image",
    "Product Name": "Product_Name",
    "Product Price": "Product_Price",
    "Product Status": "Product_Status",
    # location
    "Order Zipcode": "Order_Zipcode",
    "Order City": "Order_City",
    "Order State": "Order_State",
    "Order Region": "Order_Region",
    "Order Country": "Order_Country",
    "Latitude": "Latitude",
    "Longitude": "Longitude",
    # order/fact_order
    "Order Id": "Order_Id",
    "order date (DateOrders)": "Order_Date",
    "Order Customer Id": "Order_Customer_Id",
    "Order Item Id": "Order_Item_Id",
    "Product Card Id": "Product_Card_Id",
    "Order Item Discount": "Order_Item_Discount",
    "Order Item Discount Rate": "Order_Item_Discount_Rate",
    "Order Item Product Price": "Order_Item_Product_Price",
    "Order Item Profit Ratio": "Order_Item_Profit_Ratio",
    "Order Item Quantity": "Order_Item_Quantity",
    "Sales per customer": "Sales_per_customer",
    "Sales": "Sales",
    "Order Item Total": "Order_Item_Total",
    "Order Profit Per Order": "Order_Profit_Per_Order",
    "Order Status": "Order_Status",
    "Department Id": "Department_Id",
    # shipping
    "shipping date (DateOrders)": "Shipping_date",
    "Days for shipping (real)": "Days_for_shipping_real",
    "Days for shipment (scheduled)": "Days_for_shipping_scheduled",
    "Shipping Mode": "Shipping_Mode",
    "Delivery Status": "Delivery_Status",
    # department
    "Department Name": "Department_Name",
    "Market": "Market",
    # metadata
    "key": "key",
    "offset": "offset",
    "partition": "partition",
    "time": "time",
    "topic": "topic"
}