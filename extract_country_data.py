import subprocess
import os
import re
import json
import dateparser
from datetime import timedelta
import xml.etree.ElementTree as ET
import csv
from collections import OrderedDict
import copy

def extract_info(file_name, content):
    root = ET.parse(content).getroot()

    gettext = lambda e:''.join(e.itertext()).replace('\n','')
    offset = lambda e: float(e.attrib['bbox'].split(',')[1])
    slice_dict = lambda dct,y,height: {k:dct[k] for k in filter(lambda k:k<=y and k>y-height, dct.keys())}
    yaxis_parse = lambda s: 0 if s == 'Baseline' else float(s.replace('%',''))/100.0
    xaxis_parse = lambda s: dateparser.parse(s)
    charts = {}
    for page in root.findall('./page'):
      dataset_names = {}
      latest_figures = {}
      xseries_labels = {}
      yseries_labels = {}
      chart_data = {}
      #
      textboxes = page.findall('./textbox')
      for i,e in enumerate(textboxes):
        if e.find('./textline/text[@size="12.927"]') is not None and len(gettext(e))<50:
          dataset_names[offset(textboxes[i])] = gettext(textboxes[i])
          latest_figures[offset(textboxes[i])] = gettext(textboxes[i+1])
        elif e.find('./textline/text[@size="9.341"]') is not None:
          yseries_labels[offset(textboxes[i])] = gettext(textboxes[i])
        elif e.find('./textline/text[@size="8.562"]') is not None:
          xseries_labels[offset(textboxes[i])] = xseries_labels.get(offset(textboxes[i]), []) + [gettext(textboxes[i])]
      #
      for e in page.findall('./figure'):
        bbox = [float(x) for x in e.attrib['bbox'].split(',')]
        if e.find('./curve') is None:
            continue
        curve_pts = [float(x) for x in e.find('./curve').attrib['pts'].split(',')]
        baseline = curve_pts[1]
        current_chart = [curve_pts[1::2][int(len(curve_pts)/4):-1]][0]
        current_chart.reverse()
        chart_data[offset(e)] = (baseline, current_chart)
      #
      for y,dataset_name in dataset_names.items():
        try:
            latest_figures_for_dataset = slice_dict(latest_figures, y, 100)
            xseries_labels_for_dataset = [xaxis_parse(k) for k in list(slice_dict(xseries_labels, y, 100).values())[0]]
            yseries_labels_for_dataset = {yaxis_parse(v): k  for k,v in slice_dict(yseries_labels, y, 100).items()}
            baseline, chart_data_for_dataset = list(slice_dict(chart_data, y, 100).values())[0]
            max_gridline = max(yseries_labels_for_dataset.keys())
            chart_scale = max_gridline/(yseries_labels_for_dataset[max_gridline]-yseries_labels_for_dataset[0])
            chart_data_normalized = [(x-baseline)*chart_scale for x in chart_data_for_dataset]
            date_range = [(min(xseries_labels_for_dataset) + timedelta(days=i)).date().isoformat() for i in range((max(xseries_labels_for_dataset)-min(xseries_labels_for_dataset)).days+1)]
            assert len(date_range) == len(chart_data_normalized)
            charts[dataset_name.strip()] = dict(zip(date_range,chart_data_normalized))
        except:
            print("Skipping {}/'{}' because of parsing errors".format(file_name, dataset_name.strip()))
            pass
    return charts


def read_files():
    data = []
    for f in filter(lambda s: s.endswith('.pdf'), os.listdir('./pdf/')):
        proc = subprocess.Popen(['pdf2txt.py','-t', 'xml', "./pdf/" + f], stdout=subprocess.PIPE)
        print(f)
        extracted_tags = {"file_name": f, "data": extract_info(f, proc.stdout)}
        data.append(extracted_tags)
        print(extracted_tags)
        print("*" * 30)

    return data


data = read_files()
with open('parsed_data.json', 'w') as json_file:
    json.dump(data, json_file)
with open('parsed_data.csv', 'w') as csv_file:
    csv_fields = OrderedDict([("file_name",1), ("dataset",1)])
    for d in data:
        print(d['data'])
        for dataset in d['data'].values():
            for k in sorted(dataset.keys()):
                csv_fields[k] = 1
    w = csv.DictWriter(csv_file, fieldnames=csv_fields.keys())
    w.writeheader()
    for d in data:
        for dataset_name, dataset in d['data'].items():
            row = copy.deepcopy(dataset)
            row.update({"file_name": d['file_name'], 'dataset': dataset_name})
            print(row)
            w.writerow(row)
