from datetime import datetime

class VPNUtils:
    @staticmethod
    def format_expiry_date(expiry_datetime):
        return expiry_datetime.strftime("%d.%m.%Y %H:%M")

    @staticmethod
    def get_vpn_email(chat_id):
        return f"user_{chat_id}@stormyvpn.com"

    @staticmethod
    def parse_expiry_date(date_str):
        return datetime.strptime(date_str, "%d.%m.%Y %H:%M")

    @staticmethod
    def time_until_expiry(expiry_date_str):
        expiry_datetime = VPNUtils.parse_expiry_date(expiry_date_str)
        return (expiry_datetime - datetime.now()).total_seconds()
