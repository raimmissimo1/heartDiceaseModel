print("===== You are welcome =====")

customer = input("Enter customer name: ")

item_count = 0
subtotal = 0

while True:
    product = input("Enter product name ('done' to quit): ")
    
    if product == "done":
        break
    
    price = float(input("Enter price: "))
    
    subtotal += price
    item_count += 1

print("-"*33)

print("Customer :", customer.upper())
print("Items :", item_count)
print("Subtotal :", subtotal, "KZT")

print("-"*33)

if subtotal < 3000:
    discount_rate = 0
    discount_lvl = "No discount"
elif subtotal < 7000:
    discount_rate = 0.05
    discount_lvl = "5% discount"
else:
    discount_rate = 0.15
    discount_lvl = "15% discount"

discount = subtotal * discount_rate
total = subtotal - discount

print("Discount tier :", discount_lvl)
print("Discount :", discount, "KZT")
print("Total :", total, "KZT")

print("-"*33)

print("Name uppercase :", customer.upper())
print("Name lowercase :", customer.lower())
print("Name length :", len(customer))

if len(customer) > 5:
    print("Long name")
else:
    print("Short name")
