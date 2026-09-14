import os

INPUT_DIR = './original'
OUTPUT_DIR = './reduced'

os.makedirs(OUTPUT_DIR, exist_ok=True)

def read_cxt(path):
    with open(path, 'r', encoding='utf-8') as f:
        lines = [line.rstrip('\n\r') for line in f]

    if not lines or lines[0].strip() != 'B':
        raise ValueError(f'Invalid CXT file: {path}')

    idx = 1
    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    num_objects = int(lines[idx].strip())
    idx += 1

    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    num_attributes = int(lines[idx].strip())
    idx += 1

    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    objects = lines[idx:idx + num_objects]
    idx += num_objects

    attributes = lines[idx:idx + num_attributes]
    idx += num_attributes

    while idx < len(lines) and not lines[idx].strip():
        idx += 1

    matrix = [
        list(lines[idx + i].strip().lower())
        for i in range(num_objects)
    ]

    return objects, attributes, matrix

def reduce_context(matrix):
    unique_object_rows = []
    seen_objects = set()

    for row in matrix:
        key = tuple(row)

        if key not in seen_objects:
            seen_objects.add(key)
            unique_object_rows.append(row)

    matrix = unique_object_rows

    attribute_columns = list(zip(*matrix)) if matrix else []

    unique_attribute_columns = []
    seen_attributes = set()

    for column in attribute_columns:
        key = tuple(column)

        if key not in seen_attributes:
            seen_attributes.add(key)
            unique_attribute_columns.append(column)

    if matrix:
        matrix = [
            [
                unique_attribute_columns[j][i]
                for j in range(len(unique_attribute_columns))
            ]
            for i in range(len(matrix))
        ]

    keep_objects = []

    for i, row in enumerate(matrix):
        other_rows = matrix[:i] + matrix[i + 1:]

        if not other_rows:
            keep_objects.append(i)
            continue

        intersection = [
            all(other_row[j] == 'x' for other_row in other_rows)
            for j in range(len(row))
        ]

        intent = [value == 'x' for value in row]

        if intersection != intent:
            keep_objects.append(i)

    matrix = [matrix[i] for i in keep_objects]

    if matrix:
        keep_attributes = []

        for j in range(len(matrix[0])):
            other_columns = [
                k for k in range(len(matrix[0]))
                if k != j
            ]

            if not other_columns:
                keep_attributes.append(j)
                continue

            intersection = [
                all(matrix[i][k] == 'x' for k in other_columns)
                for i in range(len(matrix))
            ]

            extent = [
                matrix[i][j] == 'x'
                for i in range(len(matrix))
            ]

            if intersection != extent:
                keep_attributes.append(j)

        matrix = [
            [row[j] for j in keep_attributes]
            for row in matrix
        ]

    return matrix

def write_cxt(path, matrix):
    num_objects = len(matrix)
    num_attributes = len(matrix[0]) if matrix else 0

    with open(path, 'w', encoding='utf-8', newline='\n') as f:
        f.write('B\n\n')
        f.write(f'{num_objects}\n')
        f.write(f'{num_attributes}\n\n')

        for i in range(num_objects):
            f.write(f'g{i + 1}\n')

        for j in range(num_attributes):
            f.write(f'm{j + 1}\n')

        for i, row in enumerate(matrix):
            f.write(''.join('x' if value.lower() == 'x' else '.' for value in row))
            if i < len(matrix) - 1:
                f.write('\n')

def process_directory():
    for filename in sorted(os.listdir(INPUT_DIR)):
        if not filename.lower().endswith('.cxt'):
            continue

        input_path = os.path.join(INPUT_DIR, filename)
        output_path = os.path.join(OUTPUT_DIR, filename)

        objects, attributes, matrix = read_cxt(input_path)
        reduced_matrix = reduce_context(matrix)
        write_cxt(output_path, reduced_matrix)

        print(
            f'{filename}: '
            f'{len(objects)}x{len(attributes)} -> '
            f'{len(reduced_matrix)}x'
            f'{len(reduced_matrix[0]) if reduced_matrix else 0}'
        )

if __name__ == '__main__':
    process_directory()
