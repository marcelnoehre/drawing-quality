from itertools import combinations, product
from math import prod
from pathlib import Path

OUTPUT_DIR = Path('./theory')
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

def export_cxt(filename, matrix):
    '''
    Export a binary context in Burmeister .cxt format.
    '''
    num_objects = len(matrix)
    num_attributes = len(matrix[0]) if matrix else 0

    if any(len(row) != num_attributes for row in matrix):
        raise ValueError('Matrix rows have inconsistent lengths.')

    path = OUTPUT_DIR / filename

    with path.open('w', encoding='utf-8') as file:
        file.write('B\n\n')
        file.write(f'{num_objects}\n')
        file.write(f'{num_attributes}\n\n')

        for index in range(1, num_objects + 1):
            file.write(f'g{index}\n')

        for index in range(1, num_attributes + 1):
            file.write(f'm{index}\n')

        for row in matrix:
            file.write(
                ''.join('x' if value else '.' for value in row) + '\n'
            )

    return path

def concept_count(matrix):
    '''
    Count formal concepts by enumerating all object subsets.
    '''
    num_objects = len(matrix)
    num_attributes = len(matrix[0]) if matrix else 0

    concepts = set()

    for mask in range(1 << num_objects):
        intent = tuple(
            attribute
            for attribute in range(num_attributes)
            if all(
                not (mask & (1 << obj)) or matrix[obj][attribute]
                for obj in range(num_objects)
            )
        )

        extent = tuple(
            obj
            for obj in range(num_objects)
            if all(matrix[obj][attribute] for attribute in intent)
        )

        concepts.add((extent, intent))

    return len(concepts)

def validate_context(matrix, expected_size):
    '''
    Validate dimensions and the number of generated concepts.
    '''
    if not matrix:
        raise ValueError('Context must not be empty.')

    num_attributes = len(matrix[0])

    if any(len(row) != num_attributes for row in matrix):
        raise ValueError('Context matrix is not rectangular.')

    if any(value not in (0, 1) for row in matrix for value in row):
        raise ValueError('Context must be binary.')

    actual_size = concept_count(matrix)

    if actual_size != expected_size:
        raise ValueError(
            f'Invalid context: expected {expected_size} concepts, '
            f'got {actual_size}.'
        )

# Boolean lattices B_n
def generate_boolean_context(n):
    '''
    Reduced context of the Boolean lattice B_n.

    Join-irreducibles are the n atoms.
    Meet-irreducibles are the n coatoms.

    Atom i is below coatom j iff i != j.
    '''
    matrix = [
        [int(i != j) for j in range(n)]
        for i in range(n)
    ]

    return matrix

# Divisor lattices D_n
def prime_factorization(n):
    '''
    Return the prime factorization as {prime: exponent}.
    '''
    factors = {}
    divisor = 2

    while divisor * divisor <= n:
        while n % divisor == 0:
            factors[divisor] = factors.get(divisor, 0) + 1
            n //= divisor
        divisor += 1

    if n > 1:
        factors[n] = factors.get(n, 0) + 1

    return factors

def divisors(n):
    '''
    Return all positive divisors of n.
    '''
    result = [1]

    for prime, exponent in prime_factorization(n).items():
        result = [
            value * prime ** power
            for value in result
            for power in range(exponent + 1)
        ]

    return sorted(result)

def generate_divisor_context(n):
    '''
    Reduced context of the divisor lattice D_n.

    Join-irreducibles are the prime powers p^k dividing n.

    Meet-irreducibles are n / p^k.

    Incidence is ordinary divisibility.
    '''
    factors = prime_factorization(n)

    join_irreducibles = [
        prime ** exponent
        for prime, max_exponent in factors.items()
        for exponent in range(1, max_exponent + 1)
    ]

    join_irreducibles.sort()

    meet_irreducibles = [
        n // value
        for value in join_irreducibles
    ]

    matrix = [
        [
            int(meet % join == 0)
            for meet in meet_irreducibles
        ]
        for join in join_irreducibles
    ]

    return matrix

# Partition lattices Pi_n
def generate_partition_context(n):
    '''
    Reduced context of the partition lattice Pi_n.

    Join-irreducibles are the atomic partitions obtained by merging
    exactly two elements.

    Meet-irreducibles are the two-block partitions.
    '''
    elements = tuple(range(n))

    join_irreducibles = list(combinations(elements, 2))

    meet_irreducibles = []

    for size in range(1, n // 2 + 1):
        for subset in combinations(elements, size):
            block_a = frozenset(subset)
            block_b = frozenset(set(elements) - block_a)

            # For equal-sized blocks, choose one canonical ordering.
            if len(block_a) == len(block_b):
                if 0 not in block_a:
                    continue

            meet_irreducibles.append((block_a, block_b))

    matrix = []

    for left, right in join_irreducibles:
        row = []

        for block_a, block_b in meet_irreducibles:
            same_block = (
                (left in block_a and right in block_a)
                or
                (left in block_b and right in block_b)
            )

            row.append(int(same_block))

        matrix.append(row)

    return matrix

# Projective/subspace lattices L(F_q^3)
def normalize_projective_vector(vector, q):
    '''
    Normalize a non-zero vector over GF(q).
    '''
    first_nonzero = next(value for value in vector if value != 0)
    inverse = pow(first_nonzero, -1, q)

    return tuple(
        (value * inverse) % q
        for value in vector
    )

def projective_points(q):
    '''
    Generate canonical representatives of the points of PG(2,q).
    '''
    points = set()

    for vector in product(range(q), repeat=3):
        if vector == (0, 0, 0):
            continue

        points.add(normalize_projective_vector(vector, q))

    return sorted(points)

def generate_projective_context(q):
    '''
    Reduced context of the subspace lattice L(F_q^3).

    Objects are one-dimensional subspaces.
    Attributes are two-dimensional subspaces.

    The incidence relation is point-on-line incidence.
    '''
    points = projective_points(q)

    matrix = []

    for point in points:
        row = []

        for line in points:
            incidence = (
                sum(
                    point[index] * line[index]
                    for index in range(3)
                ) % q
                == 0
            )

            row.append(int(incidence))

        matrix.append(row)

    return matrix

# Free modular lattice FM(3)
def gf2_span(generators):
    '''
    Return the GF(2)-linear span of a collection of bit vectors.
    '''
    span = {0}

    for vector in generators:
        span |= {
            element ^ vector
            for element in list(span)
        }

    return frozenset(span)

def subspace_join(left, right):
    '''
    Join of two GF(2) subspaces.
    '''
    return gf2_span(left | right)

def subspace_meet(left, right):
    '''
    Meet of two GF(2) subspaces.
    '''
    return frozenset(left & right)

def lower_covers(element, lattice):
    '''
    Return the elements covered by element.
    '''
    candidates = [
        other
        for other in lattice
        if other < element
    ]

    return [
        candidate
        for candidate in candidates
        if not any(
            candidate < middle < element
            for middle in lattice
        )
    ]

def upper_covers(element, lattice):
    '''
    Return the elements covering element.
    '''
    candidates = [
        other
        for other in lattice
        if element < other
    ]

    return [
        candidate
        for candidate in candidates
        if not any(
            element < middle < candidate
            for middle in lattice
        )
    ]

def generate_free_modular_lattice():
    '''
    Generate Dedekind's 28-element free modular lattice on three
    generators and derive its reduced formal context.

    The generators are represented as subspaces of GF(2)^8.
    Their generated lattice has exactly 28 elements.
    '''
    X = gf2_span([
        1 << 1,
        1 << 3,
        1 << 4,
        1 << 7,
    ])

    Y = gf2_span([
        1 << 1,
        1 << 2,
        1 << 5,
        1 << 6,
    ])

    Z = gf2_span([
        1 << 0,
        1 << 3,
        1 << 5,
        (1 << 6) ^ (1 << 7),
    ])

    lattice = {X, Y, Z}

    changed = True

    while changed:
        changed = False
        current = list(lattice)

        for left in current:
            for right in current:
                for result in (
                    subspace_join(left, right),
                    subspace_meet(left, right),
                ):
                    if result not in lattice:
                        lattice.add(result)
                        changed = True

    if len(lattice) != 28:
        raise ValueError(
            f'Expected 28 elements in FM(3), got {len(lattice)}.'
        )

    join_irreducibles = [
        element
        for element in lattice
        if len(lower_covers(element, lattice)) == 1
    ]

    meet_irreducibles = [
        element
        for element in lattice
        if len(upper_covers(element, lattice)) == 1
    ]

    def sort_key(subspace):
        return (
            len(subspace),
            tuple(sorted(subspace)),
        )

    join_irreducibles.sort(key=sort_key)
    meet_irreducibles.sort(key=sort_key)

    matrix = [
        [
            int(join <= meet)
            for meet in meet_irreducibles
        ]
        for join in join_irreducibles
    ]

    return matrix

# Free distributive lattices FD(n)
def generate_free_distributive_context(n):
    '''
    Reduced context of the bounded free distributive lattice FD(n).

    Join-irreducibles can be represented by conjunctions indexed by
    subsets of the generators.

    Meet-irreducibles can be represented dually by disjunctions.

    Empty subsets correspond to top on the join-irreducible side and
    bottom on the meet-irreducible side.

    For non-empty subsets S and T,

        meet(S) <= join(T)

    iff S and T intersect.

    Consequently the empty row and empty column contain only zeros.
    '''
    subsets = [
        frozenset(subset)
        for size in range(n + 1)
        for subset in combinations(range(n), size)
    ]

    matrix = [
        [
            int(bool(left and right and left.intersection(right)))
            for right in subsets
        ]
        for left in subsets
    ]

    return matrix

# Expected lattice sizes
def bell_number(n):
    '''
    Compute the Bell number B_n.
    '''
    bell = [[0] * (n + 1) for _ in range(n + 1)]
    bell[0][0] = 1

    for i in range(1, n + 1):
        bell[i][0] = bell[i - 1][i - 1]

        for j in range(1, i + 1):
            bell[i][j] = bell[i - 1][j - 1] + bell[i][j - 1]

    return bell[n][0]

def gaussian_binomial(n, k, q):
    '''
    Gaussian binomial coefficient [n choose k]_q.
    '''
    numerator = prod(q ** (n - i) - 1 for i in range(k))
    denominator = prod(q ** (k - i) - 1 for i in range(k))

    return numerator // denominator

def subspace_lattice_size(dimension, q):
    '''Number of subspaces of GF(q)^dimension.'''
    return sum(
        gaussian_binomial(dimension, k, q)
        for k in range(dimension + 1)
    )

CONTEXTS = [
    ('boolean_B3.cxt', lambda: generate_boolean_context(3), 8),
    ('boolean_B4.cxt', lambda: generate_boolean_context(4), 16),
    ('boolean_B5.cxt', lambda: generate_boolean_context(5), 32),
    ('boolean_B6.cxt', lambda: generate_boolean_context(6), 64),
    ('divisor_D36.cxt', lambda: generate_divisor_context(36), 9),
    ('divisor_D60.cxt', lambda: generate_divisor_context(60), 12),
    ('divisor_D180.cxt', lambda: generate_divisor_context(180), 18),
    ('divisor_D210.cxt', lambda: generate_divisor_context(210), 16),
    ('divisor_D360.cxt', lambda: generate_divisor_context(360), 24),
    ('divisor_D900.cxt', lambda: generate_divisor_context(900), 27),
    ('divisor_D1200.cxt', lambda: generate_divisor_context(1200), 30),
    ('partition_Pi4.cxt', lambda: generate_partition_context(4), 15),
    ('partition_Pi5.cxt', lambda: generate_partition_context(5), 52),
    ('subspace_L3_F2.cxt', lambda: generate_projective_context(2), 16),
    ('subspace_L3_F3.cxt', lambda: generate_projective_context(3), 28),
    ('modular_FM3.cxt', generate_free_modular_lattice, 28),
    ('distributive_FD3.cxt', lambda: generate_free_distributive_context(3), 20),
    ('distributive_FD4.cxt', lambda: generate_free_distributive_context(4), 168)
]

def main():
    print(f'Generating {len(CONTEXTS)} formal contexts\n')

    for filename, generator, expected_size in CONTEXTS:
        matrix = generator()

        validate_context(matrix, expected_size)

        path = export_cxt(filename, matrix)

        print(
            f'OK  {filename:<28} '
            f'{len(matrix):>2} objects x '
            f'{len(matrix[0]):>2} attributes  '
            f'{expected_size:>3} concepts  '
            f'{path}'
        )

    print('\nAll contexts passed validation.')


if __name__ == '__main__':
    main()
    