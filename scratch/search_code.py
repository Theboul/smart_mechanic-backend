import os

def search_files(directory, term):
    results = []
    for root, dirs, files in os.walk(directory):
        for file in files:
            if file.endswith(('.ts', '.html', '.js')):
                path = os.path.join(root, file)
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        for line_num, line in enumerate(f, 1):
                            if term in line:
                                results.append((path, line_num, line.strip()))
                except Exception as e:
                    pass
    return results

print("Searching for 'maps.googleapis.com' in taller-frontend...")
matches = search_files('c:\\Users\\brad3\\Proyectos\\Proyecto-SI2-Examen-1\\taller-frontend\\src', 'maps.googleapis.com')
for m in matches:
    print(f"{m[0]}:{m[1]} -> {m[2]}")

print("\nSearching for 'rol_taller' in tests...")
matches_t = search_files('c:\\Users\\brad3\\Proyectos\\Proyecto-SI2-Examen-1\\taller-backend\\tests', 'rol_taller')
for m in matches_t:
    print(f"{m[0]}:{m[1]} -> {m[2]}")
