import json
from pathlib import Path


# Find the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent

ORDERS_FILE = PROJECT_ROOT / "data" / "orders.json"
INVENTORY_FILE = PROJECT_ROOT / "data" / "inventory.json"


def load_json(file_path):
    """Load data from a JSON file."""
    with open(file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_order_status(order_id):
    """
    Read-only tool that retrieves information for an order.
    """

    # Validate order ID format
    if not isinstance(order_id, str) or not order_id.upper().startswith("ORD"):
        return {
            "success": False,
            "error": "Invalid order ID. Order IDs must start with 'ORD'."
        }

    orders = load_json(ORDERS_FILE)

    for order in orders:
        if order["order_id"].upper() == order_id.upper():
            return {
                "success": True,
                "data": order
            }

    return {
        "success": False,
        "error": f"Order {order_id} was not found."
    }

def check_inventory(sku):
    """
    Read-only tool that retrieves available inventory for a SKU.
    """

    # Validate SKU format
    if not isinstance(sku, str) or not sku.upper().startswith("SKU"):
        return {
            "success": False,
            "error": "Invalid SKU. SKU values must start with 'SKU'."
        }

    inventory = load_json(INVENTORY_FILE)

    for item in inventory:
        if item["sku"].upper() == sku.upper():
            return {
                "success": True,
                "data": item
            }

    return {
        "success": False,
        "error": f"SKU {sku} was not found."
    }

# Simple test
if __name__ == "__main__":

    print("Testing order tool:")
    print(get_order_status("ORD102"))

    print("\nTesting inventory tool:")
    print(check_inventory("SKU204"))

    print("\nTesting failed order lookup:")
    print(get_order_status("ORD999"))