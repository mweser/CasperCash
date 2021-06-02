import os

from CsvImport import CsvImport

# source_dir = "sampledata/"
import_file = "Extracted_Chase_Activity_Stmt_20210601.csv"

new_import = CsvImport.to_dict(import_file)
visits = {}
total_spends = {}

def add_to_dict(name, value):
    if name in visits.keys():
        visits[name] += 1
    else:
        visits[name] = 1

    if name in total_spends.keys():
        total_spends[name] += round(float(value), 2)
    else:
        total_spends[name] = round(float(value), 2)

for item in new_import:
    try:
        float(item['Amount'].replace('--', '-'))
    except ValueError:
        # print(f"{item['Amount']} is not a number")
        orig_amount = item['Amount']
        orig_description = item['Description']

        item['Description'] = orig_amount
        item['Amount'] = orig_description

    item['Amount'] = item['Amount'].replace('--', '-').replace('-', '')
    item['Description'] = item['Description'].replace('-', '').split(' ')[0].split('*')[0].strip(' ')
    add_to_dict(item['Description'], item['Amount'])
    # if "DOORDASH" in item['Description']:
    #     print(item)



for key in sorted(total_spends.keys()):
    output_amount = round(float(total_spends[key]), 2)
    print(f'{visits[key]}x\t${str(output_amount).replace("-", "")}\t{key}')

