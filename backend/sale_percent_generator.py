def generate_percent_variations(min_percent=-99, max_percent=-1):
    # Generate percent variations within the specified range
    percents = set(range(min_percent, max_percent + 1))

    return percents

def save_percents_to_file(percents, filename="percent_variations.txt"):
    with open(filename, 'w') as file:
        for percent in sorted(percents):
            file.write(f"{percent}%\n")

# Example usage:
percents = generate_percent_variations()
save_percents_to_file(percents)
print(f"Percents have been saved to 'percent_variations.txt'.")
