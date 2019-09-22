from typing import Optional

import numpy as np
from copy import deepcopy


class Simplexx:
    def __init__(self, a: np.ndarray, b: np.ndarray, lambdas: np.ndarray, signs: np.ndarray):
        self.matr = a
        self.b = b
        self.lambdas = lambdas
        self.signs = signs
        self.tbl = None
        self.header_top = []
        self.header_left = []
        self.solutions = []

    def create_simplex_table(self) -> np.ndarray:
        row_num = self.matr.shape[0]
        col_num = self.matr.shape[1]

        self.header_top = ['b']
        i = 1
        while i <= col_num:
            self.header_top.append(f'x_{i}')
            i += 1

        self.header_left = []
        j = 0
        while j < row_num:
            # продолжаем счет переменных
            self.header_left.append(f'x_{i + j}')
            j += 1

        tbl = self.matr

        # добавляем колонку b'шек слева
        tbl = np.hstack((self.b, tbl))

        # добавляем строку лямбд внизу
        pos = 0
        additional_zero_elem = 0
        lambdas = np.insert(self.lambdas, pos, additional_zero_elem, axis=0)
        tbl = np.vstack((tbl, lambdas))
        tbl = tbl.astype(dtype='float64')
        return tbl

    # проверим, что в столбце свободных членов все эл-ты положительные
    # иначе вернем строку с отрицательным элементом
    def find_negative_free_var_row(self) -> Optional[int]:
        i = 0
        while i < self._get_rows() - 1:  # пропускаем подвал таблицы
            if self.tbl[i, 0] < 0:
                return i
            i += 1

        return None

    # В строке ищем первый отрицательный элемент
    def find_first_negative_col(self, row: int) ->Optional[int]:
        #  пропускаем 0й столбец со свободными переменными
        i = 1
        while i < self._get_cols():
            if self.tbl[row, i] < 0:
                return i
        return None

    # поиск резрешающего столбца
    def find_determining_column(self) -> Optional[int]:
        lambdas_row = self.tbl[self._get_rows() - 1:]
        labdas_row_len = lambdas_row.shape[1]
        i = 0
        while i < labdas_row_len:
            if float(lambdas_row[0, i]) > 0:
                # ищем первый положительный элемент
                # возвращаем разрешающий столбец
                return i
            i += 1
        return None

    # поиск резрешающей строки
    def find_determining_row(self, determining_col: int) -> Optional[int]:
        # Найдем минимальное положительное отношение элемента свободных членов
        # si0 к соответствующем эле- менту в разрешающем столбце
        min_relation = 999999
        determining_row = None
        i = 0
        while i < self._get_rows() - 1:
            if 0 == self.tbl[i, determining_col]:
                i += 1
                continue

            curr_relation = self.tbl[i, 0] / self.tbl[i, determining_col]
            if 0 < curr_relation < min_relation:
                min_relation = curr_relation
                determining_row = i
            i += 1
        # разрешающая строка
        return determining_row

    def change_basis(self, r: int, k: int):
        print(f'Changing basis: {self.header_left[r]} <-> {self.header_top[k]}, row: {r}, col: {k}')
        # r - разр. строка
        # k - разр. столбец
        s_rk = self.tbl[r, k]
        self.tbl[r, k] = 1 / s_rk

        original_table = deepcopy(self.tbl)

        # меняем разрешающую строку, кроме разрешающего элемента
        j = 0
        while j < self._get_cols():
            if j == k:
                j += 1
                continue
            else:
                self.tbl[r, j] = original_table[r, j] / s_rk
            j += 1

        # обновляем разрешающий столбец
        i = 0
        while i < self._get_rows():
            if i == r:
                i += 1
                continue
            else:
                self.tbl[i, k] = -1 * original_table[i, k] / s_rk
            i += 1

        # обновляем все остальное
        i = 0
        while i < self._get_rows():
            j = 0
            while j < self._get_cols():
                if i == r or j == k:
                    j += 1
                    continue
                else:
                    t = original_table[i, k] * original_table[r, j] / s_rk
                    self.tbl[i, j] = original_table[i, j] - t
                j += 1
            i += 1

        # меняем иксы в колонке и столбце
        tmp = self.header_top[k]
        self.header_top[k] = self.header_left[r]
        self.header_left[r] = tmp

    def run(self) -> (dict, float):
        self.tbl = self.create_simplex_table()

        while True:
            negative_free_var_row = self.find_negative_free_var_row()
            if negative_free_var_row is None:
                break

            determining_col = self.find_first_negative_col(negative_free_var_row)
            if determining_col is None:
                break

            # Найдем минимальное положительное отношение элмента свободных членов si0
            # к соответствующем эле- менту в разрешающем столбце
            determining_row = self.find_determining_row(determining_col)
            print(f'determining row: {determining_col}')
            if determining_row is None:
                break

            self.change_basis(determining_row, determining_col)

        # Так как все элементы столбца si0 неотрицательны, имеем опорное решение
        self.add_solution()

        while True:
            determining_col = self.find_determining_column()
            print(f'determining col: {determining_col}')
            if determining_col is None:
                break

            determining_row = self.find_determining_row(determining_col)
            print(f'determining row: {determining_col}')

            if determining_row is None:
                break

            self.change_basis(determining_row, determining_col)

            self.add_solution()

        return self.solutions

    def add_solution(self):
        variables = self.get_variables_mapping()
        value = self.target_func()
        self.solutions.append((variables, {'F': value}))

    def target_func(self) -> float:
        # так как все свобоные переменные = 0,
        # то ответ лежит в первой клетке подвала таблицы
        rows = self.tbl.shape[0]
        return self.tbl[rows - 1, 0]

    def get_variables_mapping(self) -> dict:
        res = dict()
        for x_i in self.header_top:
            if 'b' == x_i:
                continue
            else:
                res[x_i] = 0
        j = 0
        for x_j in self.header_left:
            res[x_j] = self.tbl[j, 0]
            j += 1
        return res

    def _at(self, row, col) -> float:
        return self.tbl[row, col]

    def _get_rows(self) -> int:
        return self.tbl.shape[0]

    def _get_cols(self) -> int:
        return self.tbl.shape[1]

    def _to_column(self, xs: np.ndarray) -> np.ndarray:
        return xs.reshape(xs.shape[0], 1)


def main():
    a = np.array([[1, -2],
                  [-2, 1],
                  [1, 1]])
    b = np.array([[2],
                  [-2],
                  [5]])
    signs = np.array([['='],
                      ['='],
                      ['=']])
    lambdas = np.array([1, -1])   # TODO ищем минимум, хотя в задании указан максимум

    s = Simplexx(a, b, lambdas, signs)
    solutions = s.run()

    [print(s) for s in solutions]


if __name__ == '__main__':
    main()