"""Generate a single-page Power BI paginated report from the committed backtest."""
import csv
import statistics
import xml.etree.ElementTree as ET
from pathlib import Path

folder = Path(__file__).resolve().parent
with (folder.parent / 'backtest.csv').open() as source:
    rows = list(csv.DictReader(source))

ns = 'http://schemas.microsoft.com/sqlserver/reporting/2008/01/reportdefinition'
ET.register_namespace('', ns)
root = ET.Element(f'{{{ns}}}Report')


def element(parent, tag, value=None, **attributes):
    node = ET.SubElement(parent, f'{{{ns}}}{tag}', attributes)
    if value is not None:
        node.text = str(value)
    return node


body = element(root, 'Body')
items = element(body, 'ReportItems')


def label(name, value, x, y, width, height, size, color='#17354A'):
    box = element(items, 'Textbox', Name=name)
    paragraph = element(element(box, 'Paragraphs'), 'Paragraph')
    run = element(element(paragraph, 'TextRuns'), 'TextRun')
    element(run, 'Value', value)
    style = element(run, 'Style')
    element(style, 'FontFamily', 'Segoe UI')
    element(style, 'FontSize', f'{size}pt')
    element(style, 'Color', color)
    for tag, length in [('Top', y), ('Left', x), ('Width', width), ('Height', height)]:
        element(box, tag, f'{length:.2f}in')


label('Title', 'How far ahead can we forecast passenger demand?', 0, 0, 9, .45, 23)
label('Subtitle', 'AirPassengers   /   82 forecast origins   /   Mean absolute error in thousands of passengers', 0, .58, 9, .35, 12)
for i, title in enumerate(['Forecast model', '1 month ahead', '3 months ahead']):
    label(f'Header{i}', title, [0, 4.6, 6.7][i], 1.25, [4.5, 2, 2][i], .32, 13, '#096555')
models = [('holt_winters', 'Holt–Winters on log counts'), ('growth_adjusted', 'Growth-adjusted seasonal'), ('log_trend', 'Log-linear seasonal trend'), ('seasonal', 'Same month last year'), ('last_month', 'Last observed month')]
for i, (model, title) in enumerate(models):
    y = 1.72 + i * .39
    label(f'Model{i}', title, 0, y, 4.5, .3, 12)
    for h, x in [(1, 4.6), (3, 6.7)]:
        errors = [abs(float(r['actual_thousands']) - float(r['forecast_thousands'])) for r in rows if r['model'] == model and int(r['horizon_months']) == h]
        label(f'Error{i}H{h}', f'{statistics.mean(errors):.2f}', x, y, 1.8, .3, 12)
label('Finding', 'The three-month ranking depends on the fit', 0, 3.95, 9, .4, 18)
label('Detail', 'A separate statsmodels check gave Holt–Winters errors of 11.28 and 17.00. At three months the growth adjustment scored 16.67, reversing their order.', 0, 4.43, 9, .65, 12)
label('Case', 'March 1960   /   A seasonal rebound that failed to materialize', 0, 5.22, 9, .45, 18)
label('CaseDetail', 'One month ahead, Holt–Winters forecast 466 thousand passengers. Actual demand was 419 thousand, an overestimate of about 47 thousand.', 0, 5.72, 9, .65, 12)
element(body, 'Height', '6.5in')
element(root, 'Width', '9in')
page = element(root, 'Page')
for tag, length in [('PageHeight', 8.5), ('PageWidth', 11), ('LeftMargin', .75), ('RightMargin', .75), ('TopMargin', .75), ('BottomMargin', .75)]:
    element(page, tag, f'{length}in')
ET.indent(root)
ET.ElementTree(root).write(folder / 'Forecast-review.rdl', encoding='utf-8', xml_declaration=True)
