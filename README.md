# debt-collector-ai

`debt-collector-ai` is a Python-based application designed to automate the process of managing and collecting debts via integrating with Airtable and Stripe APIs. The application fetches new contacts from Airtable, creates Stripe customers and prices, generates or updates payment links, and updates the Airtable records accordingly.

## Features

- Fetch new contacts from Airtable with specific criteria.
- Create Stripe customers and prices.
- Generate or update Stripe payment links.
- Update the Airtable records with payment link and status.
- Check and operate only within business hours (Brisbane timezone by default, but can be customized).

## Getting Started

### Prerequisites

- A Replit account.
- Python 3.6+ environment.
- Stripe and Airtable API keys.

### Clone or Fork the Repository on Replit

1. Go to your Replit account.
2. Clone or fork the repository using the following URL: `https://github.com/VW3st/debt-collector-ai`
3. Open the cloned project in your Replit workspace.

### Installation

Replit automatically handles dependency installation via the `requirements.txt` file. However, if needed, you can manually install dependencies using:


pip install -r requirements.txt


## Setup Environment Variables

Add the necessary environment variables in the Secrets tab within the Replit sidebar:

- `API_KEY`: Your Airtable API key
- `BASE_ID`: Your Airtable base ID
- `CONTACTS_TABLE_ID`: Your Airtable contacts table ID
- `STRIPE_API_KEY`: Your Stripe API key

## Customizing Timezone

The application is set to operate based on Brisbane timezone by default. If you need to change the timezone, update the `get_brisbane_time` function in `main.py`:

```python
def get_brisbane_time():
    # Replace 'Australia/Brisbane' with your desired timezone
    tz = pytz.timezone('Your/Timezone')
    local_time = datetime.now(tz)
    current_time_str = local_time.isoformat()
    print(f"Current Local Time: {current_time_str}")
    return local_time
```

## Running the Application

You can run the application by clicking the "Run" button in the Replit interface or by executing the following command in the Replit shell:

```bash
python main.py
```

This will start the Flask server and begin processing contacts based on the specified business hours.

# Usage

The application fetches new contacts from Airtable and processes them based on the specified criteria. It creates Stripe customers, prices, and payment links, and updates Airtable records accordingly.

# Contributing

1. Fork the repository.
2. Create a feature branch (`git checkout -b feature-xyz`).
3. Commit your changes (`git commit -m 'Add some feature'`).
4. Push to the branch (`git push origin feature-xyz`).
5. Open a pull request.

# License

This project is licensed under the MIT License - see the LICENSE file for details.

# Contact

Created by VW3st. If you have any questions or suggestions, feel free to reach out to agencympire@gmail.com.
```


