import requests
import csv
import xlsxwriter
from datetime import datetime

EXCEL_FILE = 'bireciepts.xlsx'

STATES = ["FL", "GA", "NC", "PA"]
CANDIDATES = ['Biden']
COLUMNS = [
    'contribution_receipt_date',
    'entity_type_desc',
    'contributor_zip',
    'contributor_employer',
    'contributor_occupation',
    'contribution_receipt_amount',
]

CONTRIBUTION_FILTER_MIN = 200

def parse_date(date_str):
    date, time = date_str.split(' ')
    month, day, year = date.split('/')
    hour, minute = time.split(':')
    return datetime(int('20' + year), int(month), int(day), int(hour), int(minute))

def load_state_reciepts():
    records = {}
    for candidate in CANDIDATES:
        records[candidate] = {}

        for state in STATES:
            records[candidate][state] = []
            state_records = records[candidate][state]

            with open('data/{}-{}.csv'.format(state, candidate), newline='') as csvfile:
                reader = csv.DictReader(csvfile)
                for row in reader:
                    entry = {}

                    if float(row.get('contribution_receipt_amount', 0)) < float(CONTRIBUTION_FILTER_MIN):
                        continue

                    for column in COLUMNS:
                        value = row.get(column)
                        entry[column] = value
                    entry['date'] = parse_date(entry['contribution_receipt_date'])
                    state_records.append(entry)
            
            state_records.sort(key=lambda record: record['date'])

    return records

def write_header(sheet, columns):
    for index, column in enumerate(columns):
        col = chr(65 + index)
        sheet.write('{}1'.format(col), column)

def export_state_data_to_excel(wb, data):
    for candidate in CANDIDATES:
        for state in STATES:
            sheet_name = '{} for {}'.format(state, candidate)
            sheet = wb.add_worksheet(sheet_name)
            write_header(sheet, COLUMNS)

            state_data = data[candidate][state]
            print('exporting {} reciept records ({})...'.format(len(state_data), sheet_name))
            for index, record in enumerate(state_data):
                for col_index, column in enumerate(COLUMNS):
                    col = chr(65 + col_index)
                    value = record.get(column)
                    sheet.write('{}{}'.format(col, index + 2), value)
        

if __name__ == '__main__':
    print('loading state reciepts...')
    data = load_state_reciepts()

    print('exporting data to {}...'.format(EXCEL_FILE))
    wb = xlsxwriter.Workbook(EXCEL_FILE)
    export_state_data_to_excel(wb, data)
    wb.close()

