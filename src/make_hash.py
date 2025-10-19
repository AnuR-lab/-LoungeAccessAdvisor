import bcrypt
import json
import getpass
from pathlib import Path

def generate_hash(password: str) -> str:
    """Return a bcrypt hash for a given password."""
    hashed = bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12))
    return hashed.decode("utf-8")

def main():
    print("=== User Hash Generator ===")
    users = []

    while True:
        username = input("Enter username (or press Enter to finish): ").strip()
        if not username:
            break

        password = getpass.getpass(f"Enter password for '{username}': ")
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("❌ Passwords do not match. Try again.")
            continue

        hashed = generate_hash(password)
        print(f"✅ Hash generated for user '{username}'")

        users.append({
            "username": username,
            "password_hash": hashed,
            "roles": ["viewer"]  # default role; you can edit later
        })

    if not users:
        print("No users created. Exiting.")
        return

    # Ask whether to save to file
    save = input("Save as users.json file? (y/n): ").lower().strip()
    if save == "y":
        output_path = Path("users.json")
        with open(output_path, "w") as f:
            json.dump({"users": users}, f, indent=2)
        print(f"💾 Saved {len(users)} users to {output_path.resolve()}")
    else:
        print("\nGenerated users data (you can paste into your JSON):")
        print(json.dumps({"users": users}, indent=2))

if __name__ == "__main__":
    main()
