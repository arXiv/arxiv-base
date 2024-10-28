# GCP Service Account Auth Token Tiny Library

A library to acquire an identity auth token of service account for authenticated services.
Expected to be used for GCP functions, Cloud runs and also at CIT web node.

## Service account role requirements

When using this, the library gets the id token of the service account. For non-GCP, 
you can use GOOGLE_APPLICATION_CREDENTIALS to point to the SA credentials.

The service account needs "Cloud Run Invoker" role
