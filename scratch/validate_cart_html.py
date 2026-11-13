html_path = r'c:\Users\soumy\OneDrive\Documents\bstpl-view\frontend\cart.html'

with open(html_path, 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Assert header is removed
assert '<header class="cv-top-header">' not in content, "cv-top-header still in content!"
assert 'id="userAvatarCircle"' not in content, "userAvatarCircle still in content!"
assert 'Good morning, Shilish Reddy' not in content, "Greeting still in content!"
assert 'Alerts: ON' not in content, "Alerts button still in content!"
print("✓ Top user bar (S, Good afternoon, ADMIN, Search, Refresh, Alerts, Cart, Logout) successfully removed.")

# 2. Assert grid format in one line
assert 'id="cartKpiStrip"' in content, "cartKpiStrip id missing"
assert 'grid-template-columns:repeat(4, 1fr)' in content or 'grid-template-columns: repeat(4, 1fr)' in content, "1-line grid missing"
assert 'id="statTotalItems"' in content, "statTotalItems missing"
assert 'id="statTotalCusts"' in content, "statTotalCusts missing"
assert 'id="statTotalDevs"' in content, "statTotalDevs missing"
assert 'id="statTotalErrs"' in content, "statTotalErrs missing"
print("✓ 4 KPI Metric cards (Total in Cart, Deleted Customers, Customer Entries, Errored Entries) formatted into 1-line grid.")

print("All validations passed!")

