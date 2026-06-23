import boto3

dynamodb = boto3.resource("dynamodb", region_name="ap-south-1")
table = dynamodb.Table("FeatureStore")

def get_feature(entity_id, feature_name):
    response = table.get_item(
        Key={
            "entity_id": str(entity_id),
            "feature_name": feature_name
        }
    )
    return response.get("Item")
