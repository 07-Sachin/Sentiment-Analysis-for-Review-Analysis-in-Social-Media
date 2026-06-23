from sdk.feature_sdk import get_feature

result = get_feature("1", "is_active")

print("Feature fetched from DynamoDB:")
print(result)
