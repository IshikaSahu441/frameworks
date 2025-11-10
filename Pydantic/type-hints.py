# # without python type hints
def calculate_total_without_hints(items, discount):
    return sum(items) * (1 - discount)

calculate_total_without_hints([100, 200, 300], "10%")

# # with python type hints
def calculate_total(items: list[float], discount: float) -> float:
    return sum(items) * (1 - discount)

calculate_total([100, 200, 300], "10%")

