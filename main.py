import os
import requests
import stripe
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv
import time
import threading
import pytz
from flask import Flask

# Load environment variables from .env file
load_dotenv()

# Ensure environment variables are set
API_KEY = os.getenv('API_KEY')
BASE_ID = os.getenv('BASE_ID')
CONTACTS_TABLE_ID = os.getenv('CONTACTS_TABLE_ID')
STRIPE_API_KEY = os.getenv('STRIPE_API_KEY')

# Initialize Stripe
stripe.api_key = STRIPE_API_KEY

# Define Airtable API URL and headers
API_URL = f'https://api.airtable.com/v0/{BASE_ID}/{CONTACTS_TABLE_ID}'
HEADERS = {
    'Authorization': f'Bearer {API_KEY}',
    'Content-Type': 'application/json'
}

app = Flask(__name__)


@app.route('/')
def home():
    return "Server is running"


def fetch_new_contacts():
    try:
        response = requests.get(API_URL, headers=HEADERS)
        response.raise_for_status()
        records = response.json()['records']
        print(f"Fetched {len(records)} records from Airtable")

        # Filter newly created contacts with PROCESS='new' and empty paylink
        new_contacts = []
        for record in records:
            fields = record.get('fields', {})
            if fields.get('PROCESS') == 'new' and not fields.get('paylink'):
                new_contacts.append(record)

        print(
            f"Found {len(new_contacts)} new contacts with PROCESS='new' and empty paylink"
        )
        return new_contacts
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
    except Exception as err:
        print(f"Other error occurred: {err}")
    return []


def create_stripe_customer(contact):
    fields = contact.get('fields', {})
    try:
        customer = stripe.Customer.create(name=fields.get('Name'),
                                          email=fields.get('Email'),
                                          metadata={
                                              'debitor':
                                              fields.get('Debitor name'),
                                              'ref_id':
                                              fields.get('Client REF ID')
                                          })
        print(
            f"Created Stripe customer: {customer.id} for contact: {fields.get('Name')}"
        )
        return customer.id
    except Exception as e:
        print(f"Error creating Stripe customer: {e}")
        return None


def create_stripe_price(contact):
    fields = contact.get('fields', {})
    overdue_amount = fields.get('Overdue amount')

    if overdue_amount is None:
        print(f"Missing 'Overdue amount' for contact: {fields.get('Name')}")
        return None

    amount = int(overdue_amount * 100)  # Convert to cents
    try:
        price = stripe.Price.create(
            unit_amount=amount,
            currency='aud',
            product='prod_QbFLLPk2A67lJi',  # Replace with your product ID
        )
        print(
            f"Created Stripe price: {price.id} for contact: {fields.get('Name')}"
        )
        return price.id
    except Exception as e:
        print(f"Error creating Stripe price: {e}")
        return None


def create_or_update_stripe_payment_link(price_id, contact):
    fields = contact.get('fields', {})
    paylink = fields.get('paylink')
    invoice_id = fields.get('Invoice ID')

    if paylink:
        try:
            payment_link = stripe.PaymentLink.modify(
                paylink,
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                metadata={
                    'customer_email': fields.get('Email'),
                    'customer_id': fields.get('Client REF ID'),
                    'customer_name': fields.get('Name')
                },
                payment_method_types=[
                    'card', 'afterpay_clearpay', 'link', 'zip'
                ],
                allow_promotion_codes=True,
                invoice_creation={
                    'enabled': True,
                    'invoice_data': {
                        'description': f"Invoice for {fields.get('Name')}",
                        'metadata': {
                            'Customer Email': fields.get('Email'),
                            'Customer ID': fields.get('Client REF ID')
                        }
                    }
                },
                shipping_address_collection={
                    'allowed_countries': ['AU', 'US', 'CA', 'GB', 'NZ']
                },
                billing_address_collection='required',
                phone_number_collection={'enabled': True},
                after_completion={
                    'type': 'redirect',
                    'redirect': {
                        'url': 'https://example.com/success'
                    }
                })
            print(
                f"Updated Stripe payment link: {payment_link.url} for contact: {fields.get('Name')}"
            )
            return payment_link.url
        except Exception as e:
            print(f"Error updating Stripe payment link: {e}")
            return None
    else:
        try:
            payment_link = stripe.PaymentLink.create(
                line_items=[{
                    'price': price_id,
                    'quantity': 1
                }],
                metadata={
                    'customer_email': fields.get('Email'),
                    'customer_id': fields.get('Client REF ID'),
                    'customer_name': fields.get('Name')
                },
                payment_method_types=[
                    'card', 'afterpay_clearpay', 'link', 'zip'
                ],
                allow_promotion_codes=True,
                invoice_creation={
                    'enabled': True,
                    'invoice_data': {
                        'description': f"Invoice for {fields.get('Name')}",
                        'metadata': {
                            'Customer Email': fields.get('Email'),
                            'Customer ID': fields.get('Client REF ID')
                        }
                    }
                },
                shipping_address_collection={
                    'allowed_countries': ['AU', 'US', 'CA', 'GB', 'NZ']
                },
                billing_address_collection='required',
                phone_number_collection={'enabled': True},
                after_completion={
                    'type': 'redirect',
                    'redirect': {
                        'url': 'https://example.com/success'
                    }
                })
            print(
                f"Created Stripe payment link: {payment_link.url} for contact: {fields.get('Name')}"
            )
            return payment_link.url
        except Exception as e:
            print(f"Error creating Stripe payment link: {e}")
            return None


def update_airtable_record(record_id, fields):
    try:
        url = f"{API_URL}/{record_id}"
        data = {"fields": fields}
        response = requests.patch(url, json=data, headers=HEADERS)
        response.raise_for_status()
        print(f"Successfully updated record {record_id} with fields {fields}")
    except requests.exceptions.HTTPError as err:
        print(f"HTTP error occurred: {err}")
        print(f"Response content: {err.response.content}")
    except Exception as err:
        print(f"Other error occurred: {err}")


def process_contacts():
    contacts = fetch_new_contacts()
    for contact in contacts:
        contact_id = contact['id']
        fields = contact.get('fields', {})
        print(f"Processing contact: {contact_id} - {fields.get('Name')}")

        customer_id = create_stripe_customer(contact)
        if not customer_id:
            print(
                f"Skipping contact {contact_id} due to customer creation failure"
            )
            continue

        price_id = create_stripe_price(contact)
        if not price_id:
            print(
                f"Skipping contact {contact_id} due to price creation failure")
            continue

        payment_link = create_or_update_stripe_payment_link(price_id, contact)
        if payment_link:
            update_fields = {
                'paylink': payment_link,
                'PROCESS': 'START',
                'Stripe Log in':
                'https://billing.stripe.com/p/login/fZe5o106saRx6ZO3cc',  
                'Stripe REF ID':
                customer_id  
            }
            update_airtable_record(contact_id, update_fields)
        else:
            print(f"Failed to create payment link for contact: {contact_id}")


def get_brisbane_time():
    tz_brisbane = pytz.timezone('Australia/Brisbane')
    brisbane_time = datetime.now(tz_brisbane)
    current_time_str = brisbane_time.isoformat()
    print(f"Current Brisbane Time: {current_time_str}")
    return brisbane_time


def is_within_business_hours():
    current_time = get_brisbane_time()
    current_day = current_time.weekday()
    current_hour = current_time.hour
    print(f"Current Day: {current_day}, Current Hour: {current_hour}"
          )  # Debugging line
    return current_day < 5 and 7 <= current_hour < 19


if __name__ == "__main__":
    threading.Thread(target=app.run, kwargs={
        'host': '0.0.0.0',
        'port': 5000
    }).start()
    while True:
        if is_within_business_hours():
            process_contacts()
        else:
            print("Outside business hours. Sleeping until next check...")
        time.sleep(30)
