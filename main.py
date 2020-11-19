import requests
import csv
import xlsxwriter
from datetime import datetime
import zipfile
import os
import pandas as pd
from plotly import graph_objs as go
from pathlib import Path

EXCEL_FILE = 'reciepts.xlsx'
ZIP_FILE = 'data.zip'

STATES = ["FL", "GA", "NC", "PA"]
CANDIDATES = ['Trump', 'Biden']
COLUMNS = [
    'contribution_receipt_date',
    'entity_type_desc',
    'contributor_zip',
    'contributor_employer',
    'contributor_occupation',
    'contribution_receipt_amount',
]

CONTRIBUTION_FILTER_MIN = 0

def parse_date(date_str):
    date, time = date_str.split(' ')
    month, day, year = date.split('/')
    return datetime(int('20' + year), int(month), int(day))

def load_state_reciepts():
    records = {}
    time_series = {}
    for candidate in CANDIDATES:
        records[candidate] = {}
        time_series[candidate] = {}

        for state in STATES:
            records[candidate][state] = []
            time_series[candidate][state] = []
            state_records = records[candidate][state]
            state_time_series = time_series[candidate][state]
            date_totals = {}
            cum_amt = 0

            with open('data/{}-{}.csv'.format(state, candidate), newline='') as csvfile:
                reader = csv.DictReader(csvfile)

                for row in reader:
                    entry = {}

                    for column in COLUMNS:
                        value = row.get(column)
                        entry[column] = value

                    date = parse_date(entry['contribution_receipt_date'])
                    entry['date'] = date
                    state_records.append(entry)

            state_records.sort(key=lambda record: record['date'])
            for record in state_records:
                date = record['date']
                cum_amt += float(entry.get('contribution_receipt_amount', 0))
                date_totals[date] = cum_amt

            for date in date_totals:
                state_time_series.append({'date': date, 'total': date_totals[date]})

    return records, time_series

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

def expand_data():
    with zipfile.ZipFile(ZIP_FILE) as zip_file:
        for file in zip_file.namelist():
            zip_file.extract(file, '.')

def build_graph(time_series):
    lines = []
    for candidate in CANDIDATES:
        for state in STATES:
            candidate_state_data = time_series[candidate][state]
            df = pd.DataFrame.from_records(candidate_state_data)
            line = go.Scatter(x=df['date'], y=df['total'], name='{} {}'.format(candidate, state))
            lines.append(line)
    go.Figure(lines).write_image('graph.pdf')


if __name__ == '__main__':
    if not Path('data').is_dir():
        print('expanding data...')
        expand_data()

    print('loading state reciepts...')
    data, time_series = load_state_reciepts()

    print('building graph...')
    build_graph(time_series)

    print('exporting data to {}...'.format(EXCEL_FILE))
    wb = xlsxwriter.Workbook(EXCEL_FILE)
    export_state_data_to_excel(wb, data)
    wb.close()