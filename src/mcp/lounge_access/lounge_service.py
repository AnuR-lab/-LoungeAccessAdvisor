import boto3
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key


class LoungeService:
    """Service class for managing Lounges and AccessProviders in DynamoDB."""

    def __init__(self, lounges_table="Lounges", providers_table="AccessProviders"):
        self.dynamodb = boto3.resource("dynamodb")
        self.lounges_table_name = lounges_table
        self.providers_table_name = providers_table
        self.lounges_table = self.dynamodb.Table(lounges_table)
        self.providers_table = self.dynamodb.Table(providers_table)

        # Optionally verify the tables exist
        self._ensure_table_exists(self.lounges_table_name, key_schema=[
            {"AttributeName": "airport", "KeyType": "HASH"},
            {"AttributeName": "lounge_id", "KeyType": "RANGE"},
        ])
        self._ensure_table_exists(self.providers_table_name, key_schema=[
            {"AttributeName": "provider_name", "KeyType": "HASH"},
        ])

    # ---------- core queries ----------

    def get_lounges_with_access_rules(self, airport_code: str):
        """Return all lounges at an airport merged with their provider rules."""
        try:
            lounges_resp = self.lounges_table.query(
                KeyConditionExpression=Key("airport").eq(airport_code.upper())
            )
            lounges = lounges_resp.get("Items", [])
            if not lounges:
                return {"airport": airport_code.upper(), "lounges": []}

            # gather providers
            provider_names = set()
            for l in lounges:
                provider_names.update(l.get("access_providers", []))

            # batch-get provider policies
            rules = {}
            keys = [{"provider_name": p} for p in provider_names]
            for batch in range(0, len(keys), 100):
                resp = self.dynamodb.batch_get_item(
                    RequestItems={self.providers_table_name: {"Keys": keys[batch: batch+100]}}
                )
                for item in resp["Responses"].get(self.providers_table_name, []):
                    rules[item["provider_name"]] = item

            # merge into lounges
            result = []
            for l in lounges:
                details = []
                for prov in l.get("access_providers", []):
                    r = rules.get(prov, {})
                    details.append({
                        "provider_name": prov,
                        "guest_policy": r.get("guest_policy"),
                        "conditions": r.get("conditions"),
                        "notes": r.get("notes")
                    })
                l["access_details"] = details
                result.append(l)

            return {"airport": airport_code.upper(), "lounges": result}

        except Exception as e:
            print(f"Error building consolidated response for {airport_code}: {e}")
            return {"airport": airport_code.upper(), "lounges": []}

    # ---------- helpers ----------

    def _ensure_table_exists(self, name, key_schema):
        """Create table if missing (on-demand billing)."""
        try:
            tbl = self.dynamodb.Table(name)
            tbl.load()
            print(f"{name} table found.")
        except ClientError as e:
            if e.response["Error"]["Code"] == "ResourceNotFoundException":
                print(f"{name} table not found; creating ...")
                self.dynamodb.create_table(
                    TableName=name,
                    KeySchema=key_schema,
                    AttributeDefinitions=[
                        {"AttributeName": k["AttributeName"], "AttributeType": "S"}
                        for k in key_schema
                    ],
                    BillingMode="PAY_PER_REQUEST",
                ).wait_until_exists()
                print(f"{name} created.")
            else:
                print(f"Error checking {name}: {e}")
