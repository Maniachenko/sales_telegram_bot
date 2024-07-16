def generate_price_variations(base_price, max_price=1000.00, int_variation=1, cent_variation=0.10):
    prices = set()
    current_price = base_price
    while current_price <= max_price:
        int_part = int(current_price)
        for i in range(-int_variation, int_variation + 1):
            new_int_part = int_part + i
            if new_int_part < 0:
                continue

            decimal_part = current_price - int_part
            j = -cent_variation
            while j <= cent_variation + 0.01:  # Increment by 0.01 to ensure covering all cent variations
                new_decimal_part = decimal_part + j
                if new_decimal_part >= 1.0:
                    new_decimal_part -= 1.0
                    new_int_part += 1
                elif new_decimal_part < 0:
                    if new_int_part == 0:
                        break
                    new_decimal_part += 1.0
                    new_int_part -= 1

                new_price = new_int_part + new_decimal_part
                if new_price <= max_price:
                    prices.add(round(new_price, 2))  # Round to two decimal places for precision
                j += 0.01

        current_price += 1  # Increment by 1 to move to the next integer part of price

    return prices

def save_prices_to_file(prices, filename="price_variations.txt"):
    with open(filename, 'w') as file:
        for price in sorted(prices):
            file.write(f"{price:.2f}\n")

base_price = 0.10
prices = generate_price_variations(base_price)
save_prices_to_file(prices)
print(f"Prices have been saved to 'price_variations.txt'.")
