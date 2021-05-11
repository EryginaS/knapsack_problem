from openpyxl import load_workbook
import pandas as pd
import matplotlib as plt
import seaborn as sns

def xlsx_valid(xlsx_doc_name):
    """
    Валидация
    :param xlsx_doc_name:
    :return:
    """

    if xlsx_doc_name[-4:] == 'xlsx' or xlsx_doc_name[-3:] == 'xls':
        data = {}
        dfs = pd.read_excel(xlsx_doc_name, sheet_name=None, engine = 'openpyxl', header=None)
        dict_from_doc = []
        for d in dfs.keys():
            dict_from_doc.append(dfs[d].to_dict('split'))

        for sheet in dict_from_doc:
            for row in sheet['data']:
                if not row[0]:
                    return None, False, 'Пустая ячейка'
                if not row[1]:
                    return None, False, 'Пустая ячейка'
                if not row[2]:
                    return None, False, 'Пустая ячейка'

                try:
                    data[row[0]] = (int(row[1]), int(row[2]))
                except ValueError:
                    return None, False, 'В столбцах, где содержатся числовые данны, были указаны данные не числового типа.'

        print(data)
        return data, True, 'success'
    else:
        return None, False, 'Формат файла неверный'

def get_area_and_value(stuffdict):
    """

    :param stuffdict: Словарь, где ключ это вещь, а значение это кортеж, где 0 элемент это вес, а 1 это ценность
    :return: список веса (area) и список value - ценность
    """
    area = [stuffdict[item][0] for item in stuffdict]
    value = [stuffdict[item][1] for item in stuffdict]
    return area, value


def get_memtable(stuffdict, A):
    area, value = get_area_and_value(stuffdict)
    n = len(value)  # находим размеры таблицы

    # создаём таблицу из нулевых значений
    V = [[0 for a in range(A + 1)] for i in range(n + 1)]

    for i in range(n + 1):
        for a in range(A + 1):
            # базовый случай
            if i == 0 or a == 0:
                V[i][a] = 0

            # если площадь предмета меньше площади столбца,
            # максимизируем значение суммарной ценности
            elif area[i - 1] <= a:
                V[i][a] = max(value[i - 1] + V[i - 1][a - area[i - 1]], V[i - 1][a])

            # если площадь предмета больше площади столбца,
            # забираем значение ячейки из предыдущей строки
            else:
                V[i][a] = V[i - 1][a]
    return V, area, value


def get_selected_items_list(stuffdict, A):
    V, area, value = get_memtable(stuffdict, A)
    n = len(value)
    res = V[n][A]  # начинаем с последнего элемента таблицы
    a = A  # начальная площадь - максимальная
    items_list = []  # список площадей и ценностей

    for i in range(n, 0, -1):  # идём в обратном порядке
        if res <= 0:  # условие прерывания - собрали "рюкзак"
            break
        if res == V[i - 1][a]:  # ничего не делаем, двигаемся дальше
            continue
        else:
            # "забираем" предмет
            items_list.append((area[i - 1], value[i - 1]))
            res -= value[i - 1]  # отнимаем значение ценности от общей
            a -= area[i - 1]  # отнимаем площадь от общей

    selected_stuff = []

    # находим ключи исходного словаря - названия предметов
    for search in items_list:
        for key, value in stuffdict.items():
            if value == search:
                selected_stuff.append(key)

    return selected_stuff

# def create_map(V, stuffdict):
#     plt.figure(figsize=(30, 15))
#     item_list = list(stuffdict.keys())
#     item_list.insert(0, 'empty')
#     sns.heatmap(V, yticklabels=item_list)
#     plt.yticks(size=25)
#     plt.xlabel('Area', size=25)
#     plt.ylabel('Added item', size=25)
#     plt.title('Value for Area with Set of Items', size=30)
#     plt.show()


def convert_result_task_to_xls(stuffdict, stuff):
    data_for_df = {}
    for key in stuffdict.keys():
        if key in stuff:
            data_for_df[key] = stuffdict[key]
    totarea = sum([stuffdict[item][0] for item in stuff])
    totvalue = sum([stuffdict[item][1] for item in stuff])
    data_for_df['total'] = (totarea, totvalue)
    return pd.DataFrame(data_for_df.items(), columns=['Вещь', 'Характеристики'])


