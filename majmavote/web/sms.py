from ippanel import Client

API_KEY = "IVTn6DeXMSGM4Ke2XZRVwCtIF00kcs7R8Za8Nav7zZI="

# create client instance


class Sms:
    client = Client(API_KEY)
    pre_message = 'کد تایید ورود به مجمع‌یار :'

    @staticmethod
    def execute(phone_code, message):
        bulk_id = Sms.client.send(
            "+98sim",  # originator
            [phone_code],  # recipients
            Sms.pre_message + message)  # message
        # print(bulk_id)
