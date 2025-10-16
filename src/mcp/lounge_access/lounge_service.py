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

    def get_lounges_by_airport(self, airport_code: str):
        """
        Get all lounges at a specific airport without access rules.
        
        Args:
            airport_code (str): The 3-letter airport code
            
        Returns:
            list: List of lounges at the airport
        """
        try:
            response = self.lounges_table.query(
                KeyConditionExpression=Key("airport").eq(airport_code.upper())
            )
            return response.get("Items", [])
        except Exception as e:
            print(f"Error retrieving lounges for {airport_code}: {e}")
            return []

    def get_lounge_by_id(self, airport_code: str, lounge_id: str):
        """
        Get a specific lounge by airport and lounge ID.
        
        Args:
            airport_code (str): The 3-letter airport code
            lounge_id (str): The unique lounge identifier
            
        Returns:
            dict: Lounge information or None if not found
        """
        try:
            response = self.lounges_table.get_item(
                Key={
                    "airport": airport_code.upper(),
                    "lounge_id": lounge_id
                }
            )
            return response.get("Item")
        except Exception as e:
            print(f"Error retrieving lounge {lounge_id} at {airport_code}: {e}")
            return None

    def create_sample_lounges(self):
        """
        Creates sample lounges and access providers for testing.
        
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Sample lounges data
            sample_lounges = [
                {
                    "airport": "JFK",
                    "lounge_id": "JFK_DELTA_SKY_CLUB_T4",
                    "name": "Delta Sky Club Terminal 4",
                    "terminal": "Terminal 4",
                    "access_providers": ["Delta SkyMiles", "Amex Platinum", "Priority Pass"],
                    "amenities": ["Buffet", "WiFi", "Showers", "Business Center"],
                    "hours": "05:00-23:00",
                    "peak_hours": "07:00-10:00,17:00-20:00",
                    "avg_wait_minutes": 15,
                    "crowd_level": "Medium",
                    "rating": 4.2
                },
                {
                    "airport": "JFK",
                    "lounge_id": "JFK_AMEX_CENTURION_T4",
                    "name": "American Express Centurion Lounge Terminal 4",
                    "terminal": "Terminal 4",
                    "access_providers": ["Amex Platinum", "Amex Centurion"],
                    "amenities": ["Fine Dining", "WiFi", "Showers", "Spa", "Business Center"],
                    "hours": "05:30-22:30",
                    "peak_hours": "08:00-11:00,18:00-21:00",
                    "avg_wait_minutes": 25,
                    "crowd_level": "High",
                    "rating": 4.8
                },
                {
                    "airport": "LAX",
                    "lounge_id": "LAX_STAR_ALLIANCE_TBIT",
                    "name": "Star Alliance Lounge TBIT",
                    "terminal": "TBIT",
                    "access_providers": ["Star Alliance Gold", "Priority Pass"],
                    "amenities": ["Buffet", "WiFi", "Quiet Zones", "Business Center"],
                    "hours": "06:00-22:00",
                    "peak_hours": "09:00-12:00,16:00-19:00",
                    "avg_wait_minutes": 10,
                    "crowd_level": "Low",
                    "rating": 4.0
                },
                {
                    "airport": "ORD",
                    "lounge_id": "ORD_UNITED_CLUB_T1",
                    "name": "United Club Terminal 1",
                    "terminal": "Terminal 1",
                    "access_providers": ["United Club", "Chase Sapphire Reserve", "Priority Pass"],
                    "amenities": ["Buffet", "WiFi", "Showers", "Quiet Zones"],
                    "hours": "05:00-23:30",
                    "peak_hours": "07:00-10:00,17:00-20:00",
                    "avg_wait_minutes": 12,
                    "crowd_level": "Medium",
                    "rating": 3.9
                }
            ]

            # Sample access providers
            sample_providers = [
                {
                    "provider_name": "Amex Platinum",
                    "guest_policy": "2 guests free, additional $50 each",
                    "conditions": "Must be traveling same day",
                    "notes": "Primary cardholder must be present"
                },
                {
                    "provider_name": "Priority Pass",
                    "guest_policy": "Guests $32 each",
                    "conditions": "Must be traveling same day",
                    "notes": "Digital card accepted"
                },
                {
                    "provider_name": "Chase Sapphire Reserve",
                    "guest_policy": "2 guests free, additional $27 each",
                    "conditions": "Must be traveling same day",
                    "notes": "Primary cardholder must be present"
                },
                {
                    "provider_name": "Delta SkyMiles",
                    "guest_policy": "Varies by status",
                    "conditions": "Flying Delta same day",
                    "notes": "Status-dependent benefits"
                },
                {
                    "provider_name": "United Club",
                    "guest_policy": "2 guests $59 each",
                    "conditions": "Flying United same day",
                    "notes": "Members and eligible passengers only"
                }
            ]

            # Insert lounges
            with self.lounges_table.batch_writer() as batch:
                for lounge in sample_lounges:
                    batch.put_item(Item=lounge)

            # Insert access providers
            with self.providers_table.batch_writer() as batch:
                for provider in sample_providers:
                    batch.put_item(Item=provider)

            print("Successfully created sample lounges and access providers")
            return True

        except Exception as e:
            print(f"Error creating sample lounges: {e}")
            return False
