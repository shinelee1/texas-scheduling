import numpy as np
import matplotlib.pyplot as plt
from scipy import stats

# Approximate miles west from the Public Garden, then monthly rent in dollars.
# Replace approximate distances with your Google Maps measurements.
distance = np.array([
    0.00, 0.08, 0.38, 0.50, 0.57,
    0.58, 0.61, 0.72, 0.75, 0.90,
    0.96, 1.16, 1.18, 1.21, 1.24
])

rent = np.array([
    4300, 4300, 3900, 2900, 2100,
    3700, 3500, 2000, 3700, 3100,
    3450, 2450, 2600, 2700, 2900
])

# Scatterplot and fitted linear trend
slope, intercept, r, p_ols, se = stats.linregress(distance, rent)
x_line = np.linspace(distance.min(), distance.max(), 100)

plt.scatter(distance, rent)
plt.plot(x_line, intercept + slope * x_line, color="red")
plt.xlabel("Distance west from the Public Garden (miles)")
plt.ylabel("Monthly asking rent ($)")
plt.title("Commonwealth Avenue rents by distance")
plt.grid(alpha=0.3)
plt.show()

# OLS test: is the linear rent trend different from zero?
df = len(rent) - 2
critical_t = stats.t.ppf(0.975, df)
ci_low = slope - critical_t * se
ci_high = slope + critical_t * se

print(f"OLS slope: ${slope:,.0f} per mile")
print(f"OLS p-value: {p_ols:.3f}")
print(f"95% CI for slope: ${ci_low:,.0f} to ${ci_high:,.0f} per mile")

# Spearman test: is there a monotonic association?
rho, p_spearman = stats.spearmanr(distance, rent)
print(f"Spearman correlation: {rho:.3f}")
print(f"Spearman p-value: {p_spearman:.3f}")