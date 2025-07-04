import csv
import os
import openai
import os

INVENTORY_FILE = 'restaurant_inventory.csv'
LOW_STOCK_THRESHOLD = 10  # Example threshold
FORECAST_DAYS = 7
# change 


class InventoryTrackingAgent:
    
    def __init__(self, filename=INVENTORY_FILE):
        self.filename = filename

    def read_inventory(self):
        inventory = []
        with open(self.filename, newline='') as csvfile:
            reader = csv.DictReader(csvfile)
            for row in reader:
                row['current_stock'] = int(row['current_stock'])
                row['sales_history'] = [int(x) for x in row['sales_history'].split('|') if x]
                inventory.append(row)
        return inventory

    def update_stock(self, product_id, quantity):
        inventory = self.read_inventory()
        for item in inventory:
            if item['product_id'] == product_id:
                # LLM agent prompt for restocking
                prompt = f"You are a helpful inventory tracking agent. The current stock for {item['product_name']} (ID: {product_id}) is {item['current_stock']}. The user wants to restock {quantity} units. What should the new stock be? Just return the integer value."
                new_stock = self.ask_llm(prompt)
                try:
                    item['current_stock'] = int(new_stock)
                except Exception:
                    item['current_stock'] += quantity  # fallback
        self.write_inventory(inventory)

    def record_sale(self, product_id, quantity):
        inventory = self.read_inventory()
        for item in inventory:
            if item['product_id'] == product_id:
                # LLM agent prompt for sale
                prompt = f"You are a helpful inventory tracking agent. The current stock for {item['product_name']} (ID: {product_id}) is {item['current_stock']}. The user reports a sale of {quantity} units. What should the new stock be? Just return the integer value."
                new_stock = self.ask_llm(prompt)
                try:
                    item['current_stock'] = int(new_stock)
                except Exception:
                    item['current_stock'] -= quantity  # fallback
                item['sales_history'].append(quantity)
        self.write_inventory(inventory)

    def write_inventory(self, inventory):
        with open(self.filename, 'w', newline='') as csvfile:
            fieldnames = ['product_id', 'product_name', 'current_stock', 'sales_history']
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for item in inventory:
                item_copy = item.copy()
                item_copy['sales_history'] = '|'.join(map(str, item['sales_history']))
                writer.writerow(item_copy)

    def ask_llm(self, prompt):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OPENAI_API_KEY not set. Using fallback logic.")
            return None
        openai.api_key = api_key
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful inventory management assistant."},
                          {"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}. Using fallback logic.")
            return None


class SalesForecastingAgent:
    def forecast(self, sales_history, days=FORECAST_DAYS):
        prompt = (
            f"You are a helpful sales forecasting agent. "
            f"Given the following sales history for a product: {sales_history}, "
            f"predict the total sales for the next {days} days. "
            f"Just return the integer value."
        )
        result = self.ask_llm(prompt)
        if result is not None:
            try:
                return int(result)
            except Exception:
                pass
        # fallback: simple moving average
        if not sales_history:
            return 0
        from statistics import mean
        window = min(len(sales_history), days)
        return int(mean(sales_history[-window:])) * days

    def ask_llm(self, prompt):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OPENAI_API_KEY not set. Using fallback logic.")
            return None
        openai.api_key = api_key
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful sales forecasting agent."},
                          {"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}. Using fallback logic.")
            return None


class ReorderAgent:
    def suggest_reorder(self, current_stock, forecasted_sales, safety_stock=LOW_STOCK_THRESHOLD):
        prompt = (
            f"You are a helpful reorder agent. "
            f"Current stock: {current_stock}. "
            f"Forecasted sales for next period: {forecasted_sales}. "
            f"Safety stock threshold: {safety_stock}. "
            f"How many units should be reordered? Just return the integer value."
        )
        result = self.ask_llm(prompt)
        if result is not None:
            try:
                return int(result)
            except Exception:
                pass
        # fallback logic
        reorder_qty = forecasted_sales + safety_stock - current_stock
        return reorder_qty if reorder_qty > 0 else 0

    def ask_llm(self, prompt):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OPENAI_API_KEY not set. Using fallback logic.")
            return None
        openai.api_key = api_key
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful reorder agent."},
                          {"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}. Using fallback logic.")
            return None


class StockLevelMonitorAgent:
    def check_low_stock(self, inventory, threshold=LOW_STOCK_THRESHOLD):
        low_stock_items = []
        for item in inventory:
            prompt = (
                f"You are a helpful stock level monitor agent. "
                f"The current stock for {item['product_name']} (ID: {item['product_id']}) is {item['current_stock']}. "
                f"The low stock threshold is {threshold}. "
                f"Is this product low on stock? Reply with 'yes' or 'no'."
            )
            result = self.ask_llm(prompt)
            if result is not None and result.lower().startswith('y'):
                low_stock_items.append(item)
            elif result is None:
                # fallback logic
                if item['current_stock'] < threshold:
                    low_stock_items.append(item)
        return low_stock_items

    def ask_llm(self, prompt):
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            print("OPENAI_API_KEY not set. Using fallback logic.")
            return None
        openai.api_key = api_key
        try:
            response = openai.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "system", "content": "You are a helpful stock level monitor agent."},
                          {"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"LLM error: {e}. Using fallback logic.")
            return None

def main():
    inventory_agent = InventoryTrackingAgent()
    forecast_agent = SalesForecastingAgent()
    reorder_agent = ReorderAgent()
    monitor_agent = StockLevelMonitorAgent()

    while True:
        print("\nAI Inventory Management System")
        print("1. View Inventory")
        print("2. Record Sale")
        print("3. Restock Product")
        print("4. Forecast Sales & Reorder Suggestions")
        print("5. Check Low Stock Alerts")
        print("0. Exit")
        choice = input("Select an option: ")

        if choice == '1':
            inventory = inventory_agent.read_inventory()
            for item in inventory:
                print(f"{item['product_id']}: {item['product_name']} | Stock: {item['current_stock']} | Sales History: {item['sales_history']}")
        elif choice == '2':
            pid = input("Enter product_id: ")
            qty = int(input("Enter quantity sold: "))
            inventory_agent.record_sale(pid, qty)
            print("Sale recorded.")
        elif choice == '3':
            pid = input("Enter product_id: ")
            qty = int(input("Enter quantity to restock: "))
            inventory_agent.update_stock(pid, qty)
            print("Product restocked.")
        elif choice == '4':
            inventory = inventory_agent.read_inventory()
            for item in inventory:
                forecast = forecast_agent.forecast(item['sales_history'])
                reorder = reorder_agent.suggest_reorder(item['current_stock'], forecast)
                print(f"{item['product_name']}: Forecast next {FORECAST_DAYS} days = {forecast}, Suggested reorder = {reorder}")
        elif choice == '5':
            inventory = inventory_agent.read_inventory()
            low_stock = monitor_agent.check_low_stock(inventory)
            if not low_stock:
                print("No products are below the low stock threshold.")
            else:
                for item in low_stock:
                    print(f"ALERT: {item['product_name']} (ID: {item['product_id']}) is low on stock: {item['current_stock']}")
        elif choice == '0':
            print("Exiting.")
            break
        else:
            print("Invalid option. Try again.")


if __name__ == "__main__":
    main()