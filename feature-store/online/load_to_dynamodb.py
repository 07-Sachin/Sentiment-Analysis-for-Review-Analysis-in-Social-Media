import pandas as pd
import boto3

# Read features file
df = pd.read_csv("../offline/features.csv")

# Connect to DynamoDB
dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("FeatureStore")

# Insert features into DynamoDB
for _, row in df.iterrows():
    table.put_item(
        Item={
            "entity_id": str(row["user_id"]),
            "feature_name": "is_active",
            "feature_value": str(row["is_active"]),
            "timestamp": int(row["last_active_ts"])
        }
    )

print("Features loaded into DynamoDB successfully")
