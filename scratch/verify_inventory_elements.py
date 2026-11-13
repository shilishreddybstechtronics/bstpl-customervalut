with open('frontend/inventory.html', 'r', encoding='utf-8') as f:
    c = f.read()

required_elements = [
    'id="optValuesCard"',
    'id="uploadPolicyCard"',
    'id="optModel"',
    'id="optNewModel"',
    'id="optFirmware"',
    'id="optFlash"',
    'id="optDispatchedDate"',
    'id="optActDate"',
    'id="optExpiryDate"',
    'id="optSimProvider"',
    'id="dupMode"',
    'id="polGrid"',
    'name="polPick"'
]

for el in required_elements:
    assert el in c, f'Missing: {el}'

print('All required IDs and attributes verified in inventory.html!')

