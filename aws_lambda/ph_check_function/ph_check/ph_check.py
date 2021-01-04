import phonenumbers as ph
from phonenumbers import PhoneNumberFormat
from phonenumbers.geocoder import description_for_number, country_name_for_number
import logging
import traceback

# below key values taken from phonenumber library, flipping dict to get description
ph_types0 = { 'FIXED_LINE': 0,
              'MOBILE': 1,
              'FIXED_LINE_OR_MOBILE': 2,
              'TOLL_FREE': 3,
              'PREMIUM_RATE': 4,
              'SHARED_COST': 5,
              'VOIP': 6,
              'PERSONAL_NUMBER': 7,
              'PAGER': 8,
              'UAN': 9,
              'VOICEMAIL': 10,
              'UNKNOWN': 99}

ph_types = dict((v,k) for k,v in ph_types0.items())


def check_ph(ph_number, ph_country):
    """Checks the phone number for validity.

    Args:
        ph_number: String
        ph_country: String

    Returns:
        Dictionary with the below informaion:

        - {
        'validity' : [TRUE/FALSE],
        'number_type': '',
        'international_format': '',
        'national_format': '',
        'RFC3966_format': '',
        'E164_format': '',
        'country': '',
        'location': ''
        }

    """

    ph_check_string = ph.is_possible_number_string(str(ph_number), str(ph_country))

    if not ph_check_string:
        return {'validity': False}
    else:
        try:
            #build phone no. object
            ph_obj = ph.parse(str(ph_number), str(ph_country))
        except ph.phonenumberutil.NumberParseException as pe:
            logging.error(f"Number Parsing failed! {traceback.format_exc()}")
            return {'validity': False}
        else:
            # check phone no. validity
            ph_validity = ph.is_valid_number(ph_obj)

            # get the phone no. type
            ph_type = ph_types[int(ph.number_type(ph_obj))]

            if ph_type != 'UNKNOWN':
                out = {
                    'validity' : ph_validity,
                    'number_type': ph_type,
                    'international_format':  ph.format_number(ph_obj, PhoneNumberFormat.INTERNATIONAL),
                    'national_format': ph.format_number(ph_obj, PhoneNumberFormat.NATIONAL),
                    'RFC3966_format': ph.format_number(ph_obj, PhoneNumberFormat.RFC3966),
                    'E164_format': ph.format_number(ph_obj, PhoneNumberFormat.E164),
                    'country': country_name_for_number(ph_obj, 'en'),
                    'location': description_for_number(ph_obj, 'en')
                    }
            else:
                out = {
                    'validity' : ph_validity,
                    'number_type': ph_type
                    }

            return out

    

