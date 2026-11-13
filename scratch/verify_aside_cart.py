with open('frontend/cart.html', 'r', encoding='utf-8') as f:
    c = f.read()

aside = c[c.find('<aside'):c.find('</aside>')+8]
print('inside aside: <div =', aside.count('<div'), '</div =', aside.count('</div'))
assert aside.count('<div') == aside.count('</div'), "Aside div mismatch!"

print("Aside div balance is perfect!")

