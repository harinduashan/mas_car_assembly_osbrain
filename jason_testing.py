import json

with open('resources.json', 'r') as file:
    data = json.load(file)

print(data)
print(data['stocks'])
print(data['stocks']['engine'])

data['stocks']['engine'] = 15

with open('resources.json', 'w') as output_file:
    json.dump(data, output_file)
