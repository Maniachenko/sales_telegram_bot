def generate_price_per_unit_variations():
    units = ["ml", "g", "kg", "l", "liter", "kus", "ks"]
    quantity_ranges = {
        "ml": range(100, 1001, 10),  # Example ranges
        "g": range(100, 1001, 10),
        "kg": range(1, 11, 1),
        "l": range(1, 11, 1),
        "liter": range(1, 11, 1),
        "kus": range(1, 11, 1),
        "ks": range(1, 11, 1)
    }
    variations = []

    # Iterate over each unit and generate prices for the defined range of quantities
    for unit, quantities in quantity_ranges.items():
        for quantity in quantities:
            # Generate variations by modifying price from 0 to 1000 by steps of 0.01
            for p in range(0, 100001):  # Incrementing by 0.01, total 100,001 steps
                new_price = p * 0.01
                variation = f"{quantity}{unit}={new_price:.2f} Kč"
                variations.append(variation)

    return variations

def save_variations_to_file(variations, filename="price_per_unit_variations.txt"):
    with open(filename, 'w') as file:
        for variation in variations:
            file.write(f"{variation}\n")

# Example usage
variations = generate_price_per_unit_variations()
save_variations_to_file(variations)
print("Price per unit variations have been saved to 'price_per_unit_variations.txt'.")
