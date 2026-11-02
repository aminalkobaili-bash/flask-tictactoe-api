from dataclasses import dataclass


@dataclass
class GameField:
    matrix: list[list[int]]

    def __post_init__(self):

        if len(self.matrix) != 3:
            raise ValueError("Field must be 3x3")

        if any(len(row) != 3 for row in self.matrix):
            raise ValueError("Field must be 3x3")

        for row in self.matrix:
            for cell in row:
                if cell not in (0, 1, 2):
                    raise ValueError("Cell values must be 0, 1 or 2")

    def is_cell_empty(self, row: int, col: int) -> bool:

        return self.matrix[row][col] == 0

    def get_empty_cells(self) -> list[tuple[int, int]]:

        return [(r, c) for r in range(3) for c in range(3) if self.matrix[r][c] == 0]

    def count_cells(self, value: int) -> int:

        return sum(1 for row in self.matrix for cell in row if cell == value)

    def is_full(self) -> bool:

        return self.count_cells(0) == 0

    @classmethod
    def empty(cls) -> "GameField":
        return cls(matrix=[[0, 0, 0], [0, 0, 0], [0, 0, 0]])
