from ippanel import Client

API_KEY = "IVTn6DeXMSGM4Ke2XZRVwCtIF00kcs7R8Za8Nav7zZI="

# create client instance


class Sms:
    client = Client(API_KEY)

    @staticmethod
    def execute(phone_code, message):
        pattern_values = {
            "verification-code": message,
        }
        bulk_id = Sms.client.send_pattern(
            "3ncl8tmub0",
            "+982000505",  # originator
            phone_code,  # recipients
            pattern_values)  # message
        # print(bulk_id)
