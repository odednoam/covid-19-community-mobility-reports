import os
import re
import json


def extract_info(content):
    retail_recreation = re.findall(r"Retail & recreation\s+(.\d+)\%\s+", content)
    grocery_pharmacy = re.findall(r"Grocery & pharmacy\s+(.\d+)\%\s+", content)
    parks = re.findall(r"Parks\s+(.\d+)\%\s+", content)
    transit_station = re.findall(r"Transit stations\s+(.\d+)\%\s+", content)
    workplaces = re.findall(r"Workplaces\s+(.\d+)\%\s+", content)
    residential = re.findall(r"Residential\s+(.\d+)\%\s+", content)

    return {
        "retail_recreation": retail_recreation[0] if retail_recreation else None,
        "grocery_pharmacy": grocery_pharmacy[0] if grocery_pharmacy else None,
        "parks": parks[0] if parks else None,
        "transit_station": transit_station[0] if transit_station else None,
        "workplaces": workplaces[0] if workplaces else None,
        "residential": residential[0] if residential else None
    }


def read_files():
    data = []
    for f in os.listdir('./pdf/'):
        os.system("pdf2txt.py -m 2 -o output.txt {}".format("./pdf/" + f))
        content = open("output.txt").read()

        print(f)
        extracted_tags = extract_info(content)
        extracted_tags["file_name"] = f
        data.append(extracted_tags)
        print(extracted_tags)
        print("*" * 30)

    return data


data = read_files()
with open('parsed_data.json', 'w') as json_file:
    json.dump(data, json_file)
