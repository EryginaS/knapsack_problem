from openpyxl import load_workbook
import pandas as pd

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
                    data[row[0]] = (float(row[1]), float(row[2]))
                except ValueError:
                    return None, False, 'В столбцах, где содержатся числовые данны, были указаны данные не числового типа.'

        print(data)
        return data, True, 'success'
    else:
        return None, False, 'Формат файла неверный'


def bag_task(carrying_capacity, data):
    pass