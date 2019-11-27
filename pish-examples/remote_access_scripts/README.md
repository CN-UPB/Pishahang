# Remote service instantion using Postman

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


