import os

from CsvImport import CsvImport

# source_dir = "sampledata/"
import_file = "Chase5722_Activity_20210602.CSV"

new_import = CsvImport.to_dict(import_file)

def add_to_dict(name, value, visits, total_spends):
    if name in visits.keys():
        visits[name] += 1
    else:
        visits[name] = 1

    if name in total_spends.keys():
        total_spends[name] += round(float(value), 2)
    else:
        total_spends[name] = round(float(value), 2)
    return visits, total_spends

def print_report(monthIndex, yearIndex):
    visits = {}
    total_spends = {}

    for item in new_import:
        dateArr = item["Posting Date"].split("/")
        month = int(dateArr[0])
        year = int(dateArr[2])

        if month == monthIndex and year == yearIndex:
            # print(int(item["Trans Date"].split("/")[0]))

            # try:
            #     float(item['Amount'].replace('--', '-'))
            # except ValueError:
            #     orig_amount = item['Amount']
            #     orig_description = item['Description']
            #
            #     item['Description'] = orig_amount
            #     item['Amount'] = orig_description

            item['Amount'] = item['Amount'].replace('--', '-')
            item['Description'] = item['Description'].replace('-', '').split(' ')[0].split('*')[0].strip(' ')
            visits, total_spends = add_to_dict(item['Description'], item['Amount'], visits, total_spends)

    for key in sorted(total_spends.keys()):
        output_amount = round(float(total_spends[key]), 2)
        print(f'{visits[key]}x\t${str(output_amount).replace("-", "")}\t{key}')


for j in range(2019,2021):
    for i in range(1, 12):
        print(f'Report for {i}/{j}:')
        print_report(i, j)
        print()





