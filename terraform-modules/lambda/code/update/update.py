#!/usr/bin/env python
import json

from utils.utils_aws import publish_to_sns
from utils.utils_db import db_list_all_unfixed_vulnerabilities, db_vulnerability_fixed
from utils.utils_dns import dns_deleted, vulnerable_ns, vulnerable_alias, vulnerable_cname
from utils.utils_requests import vulnerable_storage


def lambda_handler(event, context):  # pylint:disable=unused-argument

    vulnerabilities = db_list_all_unfixed_vulnerabilities()
    json_data = {"Fixed": []}

    for vulnerability in vulnerabilities:
        domain = vulnerability["Domain"]["S"]
        vulnerability_type = vulnerability["VulnerabilityType"]["S"]
        resource_type = vulnerability["ResourceType"]["S"]
        cloud = vulnerability["Cloud"]["S"]
        account = vulnerability["Account"]["S"]

        if vulnerability_type == "NS":
            if dns_deleted(domain) or not vulnerable_ns(domain):
                db_vulnerability_fixed(domain)
                json_data["Fixed"].append(
                    {"Account": account, "Cloud": cloud, "Domain": domain, "ResourceType": resource_type}
                )

        elif "S3" in resource_type or "Google cloud storage" in resource_type:
            if dns_deleted(domain) or not vulnerable_storage(domain, https_timeout=3, http_timeout=3):
                db_vulnerability_fixed(domain)
                json_data["Fixed"].append(
                    {"Account": account, "Cloud": cloud, "Domain": domain, "ResourceType": resource_type}
                )

        elif vulnerability_type == "CNAME":
            if dns_deleted(domain) or not vulnerable_cname(domain):
                db_vulnerability_fixed(domain)
                json_data["Fixed"].append(
                    {"Account": account, "Cloud": cloud, "Domain": domain, "ResourceType": resource_type}
                )

        elif vulnerability_type == "Alias":
            if dns_deleted(domain) or not vulnerable_alias(domain):
                db_vulnerability_fixed(domain)
                json_data["Fixed"].append(
                    {"Account": account, "Cloud": cloud, "Domain": domain, "ResourceType": resource_type}
                )

    if len(json_data["Fixed"]) == 0:
        print("No new fixed vulnerabilities")

    else:
        print(json.dumps(json_data, sort_keys=True, indent=2))
        publish_to_sns(json_data, "Domains no longer vulnerable to takeover")
