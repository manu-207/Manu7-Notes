import boto3
import pandas as pd

# Initialize Boto3 client for EC2 to get all available AWS regions
ec2_client = boto3.client("ec2")

# Get all AWS regions
def get_all_regions():
    response = ec2_client.describe_regions()
    return [region["RegionName"] for region in response["Regions"]]

# Function to get CloudTrail details for a specific region
def get_cloudtrail_details(region):
    cloudtrail_data = []
    cloudtrail_client = boto3.client("cloudtrail", region_name=region)
    response = cloudtrail_client.describe_trails()

    for trail in response["trailList"]:
        name = trail.get("Name", "N/A")
        home_region = trail.get("HomeRegion", "N/A")
        multi_region = "Yes" if trail.get("IsMultiRegionTrail", False) else "No"
        insights = "Yes" if trail.get("InsightSelectors", []) else "No"
        org_trail = "Yes" if trail.get("IsOrganizationTrail", False) else "No"
        s3_bucket = trail.get("S3BucketName", "N/A")
        log_prefix = trail.get("S3KeyPrefix", "N/A")
        cloudwatch_log_group = trail.get("CloudWatchLogsLogGroupArn", "N/A")

        # Get trail status (Handle missing trails)
        try:
            status_response = cloudtrail_client.get_trail_status(Name=name)
            status = "Enabled" if status_response.get("IsLogging", False) else "Disabled"
        except cloudtrail_client.exceptions.TrailNotFoundException:
            status = "Not Found"

        cloudtrail_data.append([
            name, home_region, multi_region, insights, org_trail, 
            s3_bucket, log_prefix, cloudwatch_log_group, status, region
        ])

    return cloudtrail_data

# Fetch CloudTrail details for all regions and combine into a single DataFrame
regions = get_all_regions()
all_cloudtrail_data = []

for region in regions:
    cloudtrail_data = get_cloudtrail_details(region)
    all_cloudtrail_data.extend(cloudtrail_data)

# Define columns
columns = [
    "Name", "Home Region", "Multi-Region Trail", "Insights", 
    "Organization Trail", "S3 Bucket", "Log File Prefix", 
    "CloudWatch Logs Log Group", "Status", "Region"
]

# Create DataFrame
df = pd.DataFrame(all_cloudtrail_data, columns=columns)

# Save to Excel (Single Sheet)
file_name = "new-222CloudTrail_Details_All_Regions.xlsx"
df.to_excel(file_name, index=False)

print(f"CloudTrail details for all regions exported successfully to {file_name}")
