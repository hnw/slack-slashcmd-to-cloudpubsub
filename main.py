import hashlib
import hmac
import sys
import os
from time import time
from google.cloud import pubsub_v1

def slack_slashcmd_to_pubsub(request):
    """Responds to any HTTP request.
    Args:
        request (flask.Request): HTTP request object.
    Returns:
        The response text or any set of values that can be turned into a
        Response object using
        `make_response <http://flask.pocoo.org/docs/0.12/api/#flask.Flask.make_response>`.
    """
    # Workaround for setting value to request.data
    # see also: https://stackoverflow.com/questions/10999990/get-raw-post-body-in-python-flask-regardless-of-content-type-header
    request.get_data()

    if request.method == 'GET':
        return make_response("These are not the slackbots you're looking for.", 404)
    if not request.form:
        sys.exit('request.form is empty')
    for env_name in ['GCP_PROJECT_ID', 'GCP_TOPIC']:
        if os.environ.get(env_name) is None:
            sys.exit('Specify environment variable "%s"' % env_name)

    slack_signing_secret = os.environ.get('SLACK_SIGNING_SECRET')     
    if not verify_slack_headers(request, slack_signing_secret):
        sys.exit('Signature verification failed')

    topic = 'projects/{project_id}/topics/{topic}'.format(
        project_id=os.environ.get('GCP_PROJECT_ID'),
        topic=os.environ.get('GCP_TOPIC')
    )
    data = request.form['command'] + ' ' + request.form['text']
    data = data.encode('utf-8')

    publisher = pubsub_v1.PublisherClient()
    publisher.publish(topic, data, **(request.form.to_dict()))
    return '_'

def verify_slack_headers(request, signing_secret):
    req_timestamp = request.headers.get('X-Slack-Request-Timestamp')
    req_signature = request.headers.get('X-Slack-Signature')

    if not signing_secret:
        # verifyしようがないのでTrue
        return True

    if not req_timestamp:
        # timestamp header not received
        # "Slash Commands"アプリを利用していると思われる、警告だけ出してTrue
        print('X-Slack-Request-Timestamp not received.')
        return True

    if not req_signature:
        # signature header not received
        print('X-Slack-Signature not received.')
        return True

    if abs(time() - int(req_timestamp)) > 60 * 5:
        # Invalid request timestamp
        print('Invalid request timestamp')
        return False

    if not verify_slack_signature(request.data, req_timestamp, signing_secret, req_signature):
        return False

    return True

def verify_slack_signature(body, timestamp, signing_secret, signature):
    # Verify the request signature of the request sent from Slack
    # Generate a new hash using the app's signing secret and request data
    #
    # Requires Python 2.7.7+ for hmac.compare_digest()
    basestring = str.encode('v0:' + str(timestamp) + ':') + body
    request_hash = 'v0=' + hmac.new(
        str.encode(signing_secret),
        basestring, hashlib.sha256
    ).hexdigest()
    return hmac.compare_digest(request_hash, signature)
