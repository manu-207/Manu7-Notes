import boto3
import datetime
import pandas as pd

# Initialize Boto3 clients
elbv2_client = boto3.client("elbv2")  # For ALB & NLB
elb_client = boto3.client("elb")  # For Classic ELB
iam_client = boto3.client("iam")  # For SSL certificate expiry

# Function to get ELBv2 (ALB & NLB) details
def get_elbv2_load_balancers():
    load_balancers = []
    response = elbv2_client.describe_load_balancers()

    for lb in response["LoadBalancers"]:
        lb_name = lb["LoadBalancerName"]
        lb_arn = lb["LoadBalancerArn"]
        region = lb["AvailabilityZones"][0]["ZoneName"][:-2]
        created_on = lb["CreatedTime"].strftime("%Y-%m-%d %H:%M:%S")
        lb_type = lb["Type"]
        public_access = "Yes" if "internet-facing" in lb["Scheme"] else "No"
        cross_zone = "Yes" if lb.get("IpAddressType", "") == "dualstack" else "No"

        # Get listeners (open ports & SSL certificates)
        listeners = elbv2_client.describe_listeners(LoadBalancerArn=lb_arn)
        open_ports = []
        ssl_expiry = "N/A"
        for listener in listeners["Listeners"]:
            open_ports.append(listener["Port"])
            if "SslCertificateArn" in listener:
                cert_arn = listener["SslCertificateArn"]
                cert_details = iam_client.get_server_certificate(ServerCertificateName=cert_arn.split("/")[-1])
                ssl_expiry = cert_details["ServerCertificate"]["Expiration"].strftime("%Y-%m-%d")

        # Get target groups (instance count)
        target_groups = elbv2_client.describe_target_groups(LoadBalancerArn=lb_arn)
        instance_count = sum(
            len(elbv2_client.describe_target_health(TargetGroupArn=tg["TargetGroupArn"])["TargetHealthDescriptions"])
            for tg in target_groups["TargetGroups"]
        )

        load_balancers.append([
            lb["VpcId"], region, lb_name, lb_type, created_on, instance_count, "N/A",
            cross_zone, "N/A", "N/A", public_access, ",".join(map(str, open_ports)), ssl_expiry, "N/A"
        ])
    
    return load_balancers

# Function to get Classic ELB details
def get_elb_classic_load_balancers():
    load_balancers = []
    response = elb_client.describe_load_balancers()

    for lb in response["LoadBalancerDescriptions"]:
        lb_name = lb["LoadBalancerName"]
        region = lb["AvailabilityZones"][0][:-2]
        created_on = "N/A"  # Classic ELB doesn't provide creation time
        lb_type = "Classic"
        public_access = "Yes" if lb["Scheme"] == "internet-facing" else "No"
        cross_zone = "Yes" if lb.get("CrossZoneLoadBalancing", {}).get("Enabled", False) else "No"

        # Open ports
        open_ports = [listener["LoadBalancerPort"] for listener in lb["ListenerDescriptions"]]

        # Instance count
        instance_count = len(lb["Instances"])

        load_balancers.append([
            lb["VPCId"], region, lb_name, lb_type, created_on, instance_count, "N/A",
            cross_zone, "N/A", "N/A", public_access, ",".join(map(str, open_ports)), "N/A", "N/A"
        ])

    return load_balancers

# Combine results from both ELBv2 and Classic ELB
elb_data = get_elbv2_load_balancers() + get_elb_classic_load_balancers()

# Create DataFrame
columns = [
    "Account ID", "Region", "Load Balancer Name", "Load Balancer Type", 
    "Created On", "Instance/Target Count", "Last Active Date", 
    "Cross-Zone Load Balancing", "Logging Enabled", "Security Groups", 
    "Publicly Accessible", "Open Ports", "SSL Certificate Expiry", "WAF Enabled"
]

df = pd.DataFrame(elb_data, columns=columns)

# Save to Excel
df.to_excel("Load_Balancer_Details.xlsx", index=False)

print("Load balancer details exported successfully to Load_Balancer_Details.xlsx")
