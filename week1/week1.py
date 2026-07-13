#Playlist manager

playlist = []

playlist.append('Blinding Lights')
playlist.append('Levitating')
playlist.append('Stay')

playlist.insert(1, 'Peaches')
print(playlist)

song = playlist.pop()
playlist.insert(0, song)
print(playlist)

def remove_name(name):
    if name in playlist:
        playlist.remove(name)
    else:
        print("this song isn't in the playlist")

remove_name('Stay')
print(playlist)
remove_name('melodie')

for song in playlist:
    print(str(playlist.index(song) + 1)  + '.' + song + ', ', end='')


#Student Grade Report
students = [('Alice',92),('Bob',88),('Carol',74),('Dave',55),('Eve',61),('Frank',95),('Grace',48)]

sort_score = sorted(students, key = lambda x : x[1], reverse=True)
print(sort_score)

for i in students:
    if i[1] >= 60:
        print(i[0])

highest = sort_score[0]
lowest = sort_score[-1]
print(str(highest) + " -highest and " + str(lowest) + " -lowest"  )

suma = sum(s[1] for s in students)
average = suma/len(students)
print("average " + str(round(average, 1)))

index = 1
for x in sort_score:
    if 11 <= index % 100 <= 13:
        sufix = 'th'
    else:
        sufix = {1: 'st', 2: 'nd', 3: 'rd'}.get(index % 10, 'th')
    print(f"{index}{sufix} {x[0]} {x[1]}, ", end='')
    index += 1



#shopping cart
print(end='')
cart = [
{'name': 'Headphones', 'price': 79.99, 'qty': 1},
{'name': 'USB Cable', 'price': 9.99, 'qty': 3},
{'name': 'Keyboard', 'price': 49.99, 'qty': 0},
{'name': 'Mouse', 'price': 29.99, 'qty': 2},
{'name': 'USB Cable', 'price': 9.99, 'qty': 2},
]

total = sum(i['price'] * i['qty'] for i in cart)
print(f" total price {total}")

for i in cart:
    if i['price'] > 50:
        i['price'] = i['price'] - i['price']/10
print(cart)

cart = [i for i in cart if i['qty'] != 0]
print(cart)

cart_sort = sorted(cart, key = lambda i: i['price'] * i['qty'], reverse = True)
print(cart_sort)

merged = {}
for i in cart:
    name = i['name']
    if name in merged:
        merged[name]['qty'] += i['qty']
    else:
        merged[name] = i.copy()

cart = list(merged.values())
print(cart)


#Log Tail
print("\n")
logs = [
'auth: User alice logged in',
'db: Query executed in 12ms',
'auth: ERROR invalid token for user bob',
'api: GET /orders 200 OK',
'db: ERROR connection timeout',
'api: POST /checkout 201 Created',
'auth: User carol logged in',
'api: GET /products 200 OK',
]

print(logs[-5:])

print(logs[::2])

logs.reverse()
print(logs)

error_list = list(i for i in logs if "ERROR" in i)
print(error_list)

counts = {}
for i in logs:
    source = i.split(':')[0]
    counts[source] = counts.get(source, 0) + 1
print(counts)


#Word Counter
text = 'to be or not to be that is the question whether tis nobler in the mind to suffer'
words = text.split()
counts = {}
for i in words:
    counts[i] = counts.get(i, 0) + 1
print(counts)

word_sort = sorted(words, key = lambda x: x[1], reverse=True)
print(word_sort[:3])

print('\n')
alph_sort = sorted(words, key = lambda x: x[0])
for word in alph_sort:
    if counts[word] == 1:
        print(word)

def same_count(w1, w2):
        if(counts.get(w1,0) == counts.get(w2, 0)):
            print(f"{w1} {w2} apar de {counts[w1]}")
        else:
            print("nu apar de acelasi nr de ori")

same_count('in', 'or')
same_count('in', 'be')

text2 = 'To be, or not to be? That is the question: whether \'tis nobler in the mind, to suffer!'

punctuation = '.,!?;:\'"()-'
clean_words = []
for word in text2.split():
    word = word.lower()
    word = word.strip(punctuation)
    if word:
        clean_words.append(word)

counts2 = {}
for word in clean_words:
    counts2[word] = counts2.get(word, 0) + 1

print(counts2)


#Phone Book
# Contacts to add:
# Alice: 555-0101, Bob: 555-0202, Carol: 555-0101
# Dave: 444-0303, Eve: 444-0404

book = {}
book['Alice'] = '555-0101'
book['Bob'] = '555-0202'
book['Carol'] = '555-0101'
book['Eve'] = '444-0404'
book['Dave'] = '444-0303'

def look_up(name):
    if(book.get(name) is None):
        print("Not found")
    else:
        print(book.get(name))
look_up('Alice')
look_up('Diana')

book.pop('Alice', None)
book.pop('Diana', None)

print(sorted(book))

def same_code(book, code):
    for name, number in book.items():
        if number.startswith(code):
            print(name)

same_code(book, '555')
same_code(book, '444')


#Inventory System
inventory = {
'P001': {'name': 'Notebook', 'qty': 50, 'price': 3.99},
'P002': {'name': 'Pen', 'qty': 0, 'price': 0.99},
'P003': {'name': 'Stapler', 'qty': 12, 'price': 7.49},
'P004': {'name': 'Tape', 'qty': 0, 'price': 1.49},
'P005': {'name': 'Highlighter','qty': 34, 'price': 2.29},
}

in_stock = {}
for id, info in inventory.items():
    if info['qty'] == 0:
        print(f"{id}: {info}")
    else:
        in_stock[id] = info

restock_list = [('P002', 20), ('P004', 15), ('P001', 10)]
for id, qty_add in restock_list:
    inventory[id]['qty'] += qty_add

print(inventory)

suma_total = sum(info['price'] * info['qty'] for info in inventory.values())
print(suma_total)

name_to_id = {}
for product_id, info in inventory.items():
    name_to_id[info['name']] = product_id
print(name_to_id)

expensive = sorted(in_stock.values(), key = lambda x:x['price'], reverse=True)[0]
print(expensive)


#Grouping & Indexing
print("\n")
employees = [
{'name':'Alice', 'dept':'Engineering', 'salary':85000, 'manager':'Carol'},
{'name':'Bob', 'dept':'Marketing', 'salary':52000, 'manager':'Dave'},
{'name':'Carol', 'dept':'Engineering', 'salary':95000, 'manager':'Eve'},
{'name':'Dave', 'dept':'Marketing', 'salary':61000, 'manager':'Eve'},
{'name':'Frank', 'dept':'Engineering', 'salary':38000, 'manager':'Carol'},
{'name':'Grace', 'dept':'Support', 'salary':41000, 'manager':'Dave'},
]

dept_index = {}
for emp in employees:
    dept_index.setdefault(emp['dept'], []).append(emp['name'])
print(dept_index)

salary_bracket = {}
for emp in employees:
    if emp['salary'] < 40000:
        salary_bracket.setdefault('junior', []).append(emp['name'])
    elif emp['salary'] >= 70000 :
        salary_bracket.setdefault('senior', []).append(emp['name'])
    else:
        salary_bracket.setdefault('mid', []).append(emp['name'])
print(salary_bracket)


sal_dep = {}
count_dep = {}
for emp in employees:
    sal_dep[emp['dept']] = sal_dep.get(emp['dept'], 0) + emp['salary']
    count_dep[emp['dept']] = count_dep.get(emp['dept'], 0) + 1

for dept in sal_dep:
    print(sal_dep[dept]/count_dep[dept])

manager_index = {}
for emp in employees:
    manager_index.setdefault(emp['manager'], []).append(emp['name'])

print(manager_index)

employee_lookup = {}
for emp in employees:
    employee_lookup[emp['name']] = emp
print(employee_lookup)
print(employee_lookup['Carol'])


#Section 3 – sets
#Duplicate Detector
submissions = ['alice','bob','carol','alice','dave','bob','alice','eve','carol']
counts = {}
for name in submissions:
    counts[name] = counts.get(name, 0) + 1

for name, i in counts.items():
    if i > 1:
        print(name)

deduplicated = set(submissions)
print(deduplicated)

exactly_twice = [name for name, count in counts.items() if count == 2]
three_or_more = [name for name, count in counts.items() if count >= 3]
print(exactly_twice)
print(three_or_more)

def is_taken_set(username):
    return username in deduplicated   # O(1) average
def is_taken_list(username):
    return username in submissions  # O(n), scans the whole list

print(is_taken_set('carol'))
print(is_taken_set('frank'))
print(is_taken_list('carol'))

print(len(deduplicated))

#Tag System
posts = {
'A': {'python', 'tutorial', 'beginner', 'coding'},
'B': {'python', 'advanced', 'decorators', 'coding'},
'C': {'javascript', 'tutorial', 'beginner', 'web'},
'D': {'python', 'tutorial', 'coding', 'tips'},
}

common = set.intersection(posts['A'], posts['B'])
print(common)

only_a = posts['A'] - posts['B']
print(only_a)

all_tags = set()
for tags in posts.values():
    all_tags = all_tags | tags
print(all_tags)

print(set.intersection(*posts.values()))

def similar_posts(posts, target_id):
    target_tags = posts[target_id]
    result = []
    for post_id, tags in posts.items():
        if post_id == target_id:
            continue
        shared = target_tags & tags
        if len(shared) >= 2:
            result.append(post_id)
    return result

print(similar_posts(posts, 'A'))


#Access Control
roles = {
'admin': {'read','write','delete','publish','manage_users'},
'editor': {'read','write','publish'},
'viewer': {'read'},
}
users = {'alice':'admin', 'bob':'editor', 'carol':'viewer', 'dave':'editor'}

def has_permission(user, action, users, roles):
    r = users[user]
    if action in roles[r]:
        return True
    else:
        return False
print(has_permission('alice', 'write', users, roles))
print(has_permission('carol', 'write', users, roles))

print(roles['admin'] - roles['editor'])
print(set.intersection(roles['editor'], roles['viewer']))

users_with_delete = [user for user, role in users.items() if 'delete' in roles.get(role, set())]
print(users_with_delete)

def combined_permissions(user, extra_role, users, roles):
    base_role = users[user]
    base_permissions = roles.get(base_role, set())
    extra_permissions = roles.get(extra_role, set())
    return frozenset(base_permissions | extra_permissions)

combined = combined_permissions('bob', 'admin', users, roles)
print(combined)
print(roles['editor'])
print(users)



#Coordinate Geometry
points = [(3,4),(0,0),(-1,2),(5,-3),(3,4),(1,1),(-4,-4),(2,0)]

minimum = 10000
point = []
distances = {}
for p in points:
    l = (p[0] ** 2 + p[1] ** 2) ** 0.5
    distances[p] =  l
    if minimum > l and l != 0:
        minimum = l
        point = p


print("the closest point to the origine" + str(point))

print("1st quadrant")
for p in points:
    if p[0] > 0 and p[1] > 0 :
        print(p)

print(distances)
print(sorted(distances.items(), key = lambda x : x[1]))

xs = [p[0] for p in points]
ys = [p[1] for p in points]
bounding_box = (min(xs), min(ys), max(xs), max(ys))
print(bounding_box)

seen = set()
duplicates = set()
for p in points:
    if p in seen:
        duplicates.add(p)
    else:
        seen.add(p)

print(duplicates)


#CSV Row Parser
csv_data = '''name,category,price,quantity
Widget A,Electronics,29.99,100
Widget B,Electronics,49.99,50
Gadget C,Accessories,9.99,300
Gadget D,Accessories,14.99,0
Device E,Electronics,199.99,25'''

lines = csv_data.strip().split('\n')
print(lines)
rows = [tuple(value.strip() for value in line.split(','))for line in lines]
for r in rows:
    print(r)
headers = rows[0]
data_rows = rows[1:]
records = []
for row in data_rows:
    record = {}
    for header, value in zip(headers, row):
        record[header] = value
    records.append(record)
print('\n')
for r in records:
    print(r)

for record in records:
    record['price'] = float(record['price'])
    record['quantity'] = int(record['quantity'])

for record in records:
    print(record)

summary = {
    'total_rows': len(records),
    'columns': list(headers),
}
numeric_columns = ['price', 'quantity']
for col in numeric_columns:
    values = [r[col] for r in records]
    summary[col] = {
        'min': min(values),
        'max': max(values),
        'avg': round(sum(values) / len(values), 2)
    }
print(summary)

highes_value = sorted(records, key = lambda x : x['price'] * x['quantity'], reverse = True)
print(highes_value[0])

