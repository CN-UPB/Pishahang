# Remote service instantion using Postman

## Retrieving the token 

<B>URL:</B>

`http://<IP>/api/v2/sessions`

<B>Method:</B>

`POST`

<B>Body</B>

`{"username": "<user>", "password": "<pass>"}`

<B> Possible response </B>

'"username": "pishahang",
    "session_began_at": "2019-11-27 08:58:35 UTC",
    "token": {
        "access_token": "TOKEN",
        "expires_in": 1200,
        "refresh_expires_in": 1800,
        "refresh_token": "TOKEN",
        "token_type": "bearer",
        "not-before-policy": 0,
        "session_state": "63774142-afc6-4d47-a7d1-cebf320dec37"
    }
}'

The value of the `access_token` should be used in the following call

## Service instantiation 

<B>URL:</B>

`http://<IP address>:32001/api/v2/requests`

<B>Method:</B>

`POST`

<B>Body:</B>

`{"service_uuid":"<Service ID>","ingresses":[],"egresses":[]}`

<B>Token:</B>

`a token`

<B>Possible response:</B>

`{
    "id": "<Service ID>",
    "created_at": "2019-11-27T06:42:39.992Z",
    "updated_at": "2019-11-27T06:42:39.992Z",
    "service_uuid": "2f2a7f33-e654-40fa-acbe-50fe80da0043",
    "status": "NEW",
    "request_type": "CREATE",
    "service_instance_uuid": null,
    "began_at": "2019-11-27T06:42:39.974Z",
    "callback": "http://son-gtkkpi:5400/service-instantiation-time"
}`


