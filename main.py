from lattice_metrics import evaluate_all, load_layout


def main():
    path = input('Path to .graphml file: ').strip()
    layout = load_layout(path)
    for name, score in evaluate_all(layout).items():
        print(f'{name}: {score:.4f}')


if __name__ == "__main__":
    main()
