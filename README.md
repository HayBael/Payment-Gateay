# PaymentBot

## Features
- Create new transactions with QRIS
- View transaction history
- Notify via Discord bot

## Installation Guide

1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd PaymentBot
   ```

2. Install dependencies:
   ```bash
   pip install flask discord.py requests
   ```

3. Run the application:
   ```bash
   python main.py
   ```

4. Configure your Discord bot token in the `main.py` file.

## Usage

### Create a new transaction
Send a POST request to `/new_transaction` with the following JSON:
```json
{
    "amount": 10000,
    "description": "Payment for service",
    "qris_image": "path_to_qris_image.jpg"
}
```

### View transaction history
Send a GET request to `/transactions`.

### Notify via Discord
Use the `!notify <transaction_id>` command in your Discord server.
