import os
import argparse
import re
import csv
from datetime import datetime as dt

from pdfminer.pdfinterp import PDFResourceManager, PDFPageInterpreter
from pdfminer.converter import PDFPageAggregator
from pdfminer.layout import LTPage, LTChar, LTAnno, LAParams, LTTextBox, LTTextLine
from pdfminer.pdfpage import PDFPage


CSV_DATE_FORMAT = '%m/%d/%Y'
CSV_HEADERS = ['Type', 'Trans Date', 'Post Date', 'Description', 'Amount']
START_DATE = None
END_DATE = None


def sort_and_filter(data):
    key = 'Trans Date'
    return sorted(
        filter(
            lambda d: (d[key] >= START_DATE if START_DATE else True) and (d[key] < END_DATE if END_DATE else True),
            data
        ),
        key=lambda d: d[key]
    )


class LineConverter(PDFPageAggregator):
    def __init__(self, rsrcmgr, pageno=1, laparams=None):
        PDFPageAggregator.__init__(self, rsrcmgr, pageno=pageno, laparams=laparams)
        self.result = {}

    def receive_layout(self, ltpage):
        lines = {}
        def render(item):
            if isinstance(item, (LTPage, LTTextBox)):
                for child in item:
                    render(child)
            elif isinstance(item, LTTextLine):
                child_str = ''
                for child in item:
                    if isinstance(child, (LTChar, LTAnno)):
                        child_str += child.get_text()
                child_str = ' '.join(child_str.split()).strip()
                if child_str:
                    lines.setdefault((self.pageno, item.bbox[1]), []).append(child_str) # page number, bbox y1
                for child in item:
                    render(child)
            return

        render(ltpage)
        self.result = lines

    def get_result(self):
        return list(self.result.values())


def pdf_to_lines(file_name):
    data = []

    with open(file_name, 'rb') as fp:
        rsrcmgr = PDFResourceManager()
        device = LineConverter(rsrcmgr, laparams=LAParams())
        interpreter = PDFPageInterpreter(rsrcmgr, device)

        for page in PDFPage.get_pages(fp):
            interpreter.process_page(page)
            data.extend(device.get_result())

    return data


def translate_to_csv(lines):
    # Attempt to build a range of dates to append year
    #year_guesser = [dt.today()]
    #for row in lines:
    #    if len(row) == 2 and row[0] == 'Opening/Closing Date':
    #        opening, closing = row[1].split(' - ')
    #        year_guesser.append(dt.strptime(opening, '%m/%d/%y'))
    #        year_guesser.append(dt.strptime(closing, '%m/%d/%y'))

    # Sort it, the order is the order that each year will be guessed
    #year_guesser.sort()

    # Regex pattern for matching the year from the data range stated in the top right of the pdf
    year_pattern = r', 20\d\d$'

    #using next to get only the first match in a list comprehension, kind of like a break in a for-loop but in one line
    parsed_year = next((line[0][-4:] for line in lines if re.match(year_pattern, line[0][-6:])), '3000') #* provide default val that will let us know for sure the date wasn't captured

    lastDepositRow = next((lines.index(line) for line in lines if line[0][:14] == 'Total Deposits'), 0) #* default value of zero means there were no deposits that month :(

    # Regex pattern for matching month/day format of each line
    date_pattern = r'\d\d\/\d\d'
    csv_data = []

    rownum = -1
    for row in lines:
        rownum += 1

        if not 2 <= len(row) <= 4:
            continue

        if (len(row) == 2):
            if not re.match(date_pattern + '$', row[0][:5]):
                continue
            date = row[0][:5]
            desc = row[0][6:]
            amount = row[1]
        elif (len(row) == 4):
            if not re.match(date_pattern + '$', row[1]):
                continue
            date = row[1]
            desc = row[0] + ' ' + row[2]
            amount = row[3]
        elif re.match(date_pattern + '$', row[1]):
            desc, date, amount = row
        else:
            date, desc, amount = row

        if re.search(date_pattern, date):
            # Attempt to create dates
            #for d in year_guesser:
            #    if date.split('/')[0] == d.strftime('%m'):
            #        date = dt.strptime(date + '/' + d.strftime('%Y'), '%m/%d/%Y')
            #        break
            #else:
            #    date = dt.strptime(date + '/' + year_guesser[-1].strftime('%Y'), '%m/%d/%Y')
            date = dt.strptime(date + '/' + parsed_year, '%m/%d/%Y')

            #trans_type = 'Sale'

            # Clean up commas from currency ammount
            amount = amount.replace(',', '')

            # Amounts are reversed compared to CSVs, flip them
            #if '-' in amount:
            #    trans_type = 'Return'
            #    amount.strip('-')
            #else:
            #    amount = '-' + amount

            if rownum > lastDepositRow:
                trans_type = 'DEBIT'
                amount = '-' + amount
            else:
                trans_type = 'CREDIT'

            csv_data.append(dict(zip(CSV_HEADERS, [trans_type, date, '', desc, amount])))

    return sort_and_filter(csv_data)


if __name__ == '__main__':

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--start",
        default=None,
        help="The Start Date to filter items (inclusive), uses the date-format"
    )
    parser.add_argument(
        "--end",
        default=None,
        help="The End Date to filter items (exclusive), uses the date-format"
    )
    parser.add_argument(
        "--date-format",
        default=CSV_DATE_FORMAT,
        help="The output date format, default: '%(default)s'"
    )
    parser.add_argument(
        "--output",
        default='Extracted_Chase_Activity_Stmt_{}.csv'.format(dt.today().strftime('%Y%m%d')),
        help="The output filename"
    )
    parser.add_argument(
        "--dir",
        default='.',
        help="The directory to scan pdfs from"
    )

    args = parser.parse_args()

    CSV_DATE_FORMAT = args.date_format
    START_DATE = dt.strptime(args.start, CSV_DATE_FORMAT) if args.start else None
    END_DATE = dt.strptime(args.end, CSV_DATE_FORMAT) if args.end else None
    output_file = args.output

    print('Started chase-ing PDFs:')
    input_files = []

    for file in os.listdir(args.dir):
        if file.endswith(".pdf"):
            input_files.append(os.path.join(args.dir, file))

    all_pdf_data = []
    num_rows = 0
    for file in input_files:
        data = translate_to_csv(pdf_to_lines(file))
        all_pdf_data.extend(data)
        print('Parsed {} rows from file: {}'.format(len(data), file))

    all_pdf_data = sort_and_filter(all_pdf_data)

    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=CSV_HEADERS)
        writer.writeheader()
        # Format out datetime
        for row in all_pdf_data:
            row['Trans Date'] = dt.strftime(row['Trans Date'], CSV_DATE_FORMAT)
            writer.writerow(row)

    print('CSV file generated with {} rows: {}'.format(
        len(all_pdf_data), output_file)
    )