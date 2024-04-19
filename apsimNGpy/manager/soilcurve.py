
soil_types_c2bare = {
    "Sand": 68,
    "Heavy clay": 73,
    "Loamy clay": 84,
    "Loam": 73,
    "Sandy loam": 68,
    "Sandy clay": 68,
    "Clay loam": 73,
    "Sandy clay loam": 73,
    "Loamy sand": 73,
    'Silty clay loam': 73,
     'Silt loam':73,
     'Silty clay': 68,
     'Fine sandy loam':68,
      'Loamy very fine sand':73,
      'Loamy fine sand': 73
}

for i in ['Clay loam', 'Silty clay loam', 'Sandy loam', 'Sandy clay loam',
       'Loam', 'Fine sandy loam', 'Loamy very fine sand',
       'Loamy fine sand', 'Loamy sand', 'Sand', 'Silt loam', 'Silty clay']:
    cl = soil_types_c2bare[i]
    print(cl)