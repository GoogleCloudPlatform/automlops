import pandas as pd
from sklearn import preprocessing
from google.cloud import aiplatform

file_path = 'examples/training/data/Dry_Beans_Dataset.csv'
dataframe = pd.read_csv(file_path)
le = preprocessing.LabelEncoder()
dataframe['Class_encoded'] = le.fit_transform(dataframe['Class'])
print(dataframe.head())

seen = set()
res = []
for num in dataframe['Class_encoded']:
    if num not in seen:
        seen.add(num)
        res.append(num)
print(res)
print(dataframe['Class_encoded'].unique())
print(le.inverse_transform([5,0,1,2,4,6,3]))

# endpoints = aiplatform.Endpoint.list(order_by="create_time desc")
# for endpoint in endpoints: 
#     print(endpoint.resource_name)
# endpoint = aiplatform.Endpoint(f"projects/1063498356496/locations/us-central1/endpoints/{endpoint_id}")



