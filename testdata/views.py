import os, pickle, codecs
from django.shortcuts import render, redirect
from django.http import HttpResponse, HttpResponseServerError
from django.core.serializers.json import DjangoJSONEncoder
from xero.auth import PartnerCredentials
from xero import Xero
from xero.exceptions import XeroException, XeroUnauthorized, XeroNotVerified, XeroForbidden, XeroNotAvailable, XeroNotFound

# config
user_agent = 'claimer/1.0 pyxero/0.9.0' + os.environ['XERO_CONSUMER_KEY']
callback_uri = 'https://localhost:1337/verify'
fewfw
# custom exception for authentication errors
class ReAuthenticationRequired(Exception):
    def __init__(self, httpResponse, msg=None):
        self.httpResponse = httpResponse
        super().__init__(msg)

def index(request):
    proceed = request.GET.get('proceed')

    credentials = auth()

    # action page
    if proceed:
        xero = Xero(credentials)

        try:
            response = populate_bank_transactions(xero)
        # @TODO: fix to only redirect if actually expired...

        except ReAuthenticationRequired as e:
            return e.httpResponse

        return HttpResponse(response)

    else:
        # index page
        return render(request, 'testdata/populate.html')

# Add test bank transaction data
def populate_bank_transactions(xero):
    def callback(xero):
        # Example request. @TODO: create actual request!
        return xero.invoices.filter(
            order='Date DESC',
            Type='ACCPAY',
            Status='PAID',
        )

    return api_call(callback, xero)

def connect(request):
    credentials = auth(True)

    return render(request, 'testdata/connect.html', { 'credentials': credentials })

def verify(request):
    verifycode = request.GET.get('oauth_verifier')

    credentials = auth()

    credentials.verify(verifycode)

    # save state
    save_state(credentials.state)

    return redirect('index')

# xero methods
def auth(reset=False):
    if 'XERO_CONSUMER_KEY' not in os.environ or not len(os.environ['XERO_CONSUMER_KEY']):
        return HttpResponseServerError('Error: <strong>XERO_CONSUMER_KEY</strong> environment variable is not set.')
    elif 'XERO_CONSUMER_SECRET' not in os.environ or not len(os.environ['XERO_CONSUMER_SECRET']):
        return HttpResponseServerError('Error: <strong>XERO_CONSUMER_SECRET</strong> environment variable is not set.')
    elif 'XERO_RSA_LOCATION' not in os.environ or not len(os.environ['XERO_RSA_LOCATION']):
        return HttpResponseServerError("Error: <strong>XERO_RSA_LOCATION</strong> environment variable is not set (should be the absolute path to the 'xero_id_rsa' file).")

    # see if we have a state
    xero_state = read_state()

    # attempt to read private xero RSA key
    f = open(os.environ['XERO_RSA_LOCATION'], 'r')

    if reset or not xero_state:
        credentials = PartnerCredentials(
            os.environ['XERO_CONSUMER_KEY'],
            os.environ['XERO_CONSUMER_SECRET'],
            f.read(),
            callback_uri=callback_uri,
            # scope='payroll.employees,payroll.payruns,payroll.payslip',
            user_agent=user_agent,
        );

        # save state
        save_state(credentials.state)
    else:
        credentials = PartnerCredentials(**xero_state, rsa_key=f.read())

    # check if expired etc.
    if credentials.expired():
        credentials.refresh()
        save_state(credentials.state)

    return credentials

def save_state(state):
    f = open('xero_state','w')
    f.write(codecs.encode(pickle.dumps(state), "base64").decode())
    f.close()

def read_state():
    try:
        f = open('xero_state')

        data = f.read()

        if len(data):
            return pickle.loads(codecs.decode(data.encode(), "base64"))

    except FileNotFoundError:
        pass

    return False

# Runs a callback function containing a Xero API call
def api_call(callback, *args):
    try:
        return callback(*args)

    except (XeroNotVerified, XeroUnauthorized) as e:
        raise ReAuthenticationRequired(redirect('connect'), 'Xero credentials invalid or expired, please reconnect.')

    except XeroException as e:
        # custom handle other exceptions here
        raise e
