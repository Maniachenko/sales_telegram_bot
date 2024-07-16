def generate_measure_variations():
    variations = []
    # Generating variations for each measure type
    variations.extend([f"{i} ks" for i in range(1, 50)])  # 1 to 49 pieces
    variations.extend([f"{i*0.1:.1f} l" for i in range(0, 10000)])  # 1.0 to 999.9 liters
    variations.extend([f"{i} g" for i in range(200, 10000)])  # 200 to 9999 grams
    variations.extend([f"{i} kg" for i in range(1, 100)])  # 1 to 99 kilograms
    variations.extend(['1 roli', '2 role', '3 role', '4 role'])  # 1 to 4 rolls
    variations.extend([f"{0.5 + i*0.1:.1f} l+zaloha" for i in range(10)])  # 0.5 to 1.4 liters + deposit
    variations.extend([f"{i} Kus" for i in range(1, 11)])  # 1 to 10 pieces
    variations.append('cena za 1 kus pri koupu baleni 6 kus')  # Specific phrase, no variation
    variations.append('cen za multipack')  # Specific phrase, no variation
    return variations

def save_measure_units_to_file(variations, filename="measure_variations.txt"):
    with open(filename, 'w') as file:
        for variation in variations:
            file.write(f"{variation}\n")

# Example usage:
measure_variations = generate_measure_variations()
save_measure_units_to_file(measure_variations)
print(f"Measure unit variations have been saved to 'measure_variations.txt'.")
