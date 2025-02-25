import boto3

# AWS SES Configuration
AWS_REGION = "us-west-1"
SENDER_EMAIL = "ebabelCryptoArb@gmail.com"


def send_email(recipient_emails, subject, message):
    """Send an email notification using Amazon SES."""
    client = boto3.client("ses", region_name=AWS_REGION)

    try:
        response = client.send_email(
            Source=SENDER_EMAIL,
            Destination={"ToAddresses": recipient_emails},
            Message={
                "Subject": {"Data": subject},
                "Body": {"Text": {"Data": message}},
            },
        )
        print(f"Email sent to {recipient_emails}. Message ID: {response['MessageId']}")
    except Exception as e:
        print(f"Error sending email: {e}")

# Example usage
if __name__ == "__main__":
    send_email("babelethan@gmail.com", "Test Email", "This is a test email from Amazon SES.")