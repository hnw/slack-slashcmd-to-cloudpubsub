# slack-slashcmd-to-cloudpubsub

Google Cloud Function which transfers the inputs from Slash Commands in Slack to Google Cloud Pub/Sub

## How to deploy

```
$ gcloud beta functions deploy [function_name] \
    --runtime=python37 --entry-point=slack_slashcmd_to_pubsub \
    --trigger-http \
    --set-env-vars=GCP_PROJECT_ID=[projct_id],GCP_TOPIC=[topic]
```

## Environment variables

- GCP_PROJECT_ID (required)
- GCP_TOPIC (required)
- SLACK_SIGNING_SECRET
