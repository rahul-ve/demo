## Azure Function development & deployment demo

Instructions to develop and deploy a simple API to validate phone numbers using the Python port of *Google's libphonenumber library*.

## Docs:
[Azure Function development from cli](https://docs.microsoft.com/en-us/azure/azure-functions/create-first-function-cli-python?tabs=azure-cli%2Cbash%2Cbrowser)

[Phonenumbers library](https://github.com/daviddrysdale/python-phonenumbers)

Below instructions were tested on Windows and Linux.

### Prerequisites

**Must**
- Python
- Node
- Azure Functions Core Tools
- Powershell/Bash

**Optional (only needed if deploying to Azure)**
- Azure Cli
- Azure Subscription

*Above linked doc from Microsoft has detailed instructions on how to install all these prerequisites.*


### Steps

Clone the repo and
```
$ cd az_func
$ python -m venv .venv
$ source .venv/bin/activate
$ cd ph_check_function
$ cp local.settings.json_DEFAULT local.settings.json
$ pip install -r requirements.txt
$ func start
```

### Test Locally

Request:
```
curl --location --request POST 'http://localhost:7071/api/ph_check' \
--header 'Content-Type: application/json' \
--data-raw '{"number" : "03 9865 2800",
            "country" : "AU"}'
```
Response:

```
{
    "validity": true,
    "number_type": "FIXED_LINE",
    "international_format": "+61 3 9865 2800",
    "national_format": "(03) 9865 2800",
    "RFC3966_format": "tel:+61-3-9865-2800",
    "E164_format": "+61398652800",
    "country": "Australia",
    "location": "Australia"
}
```

### Deploy to Azure

**Assuming Azure Subscription, resource group, storage account, Application Insights were already deployed.**

```
$ az functionapp create --resource-group <RG> --consumption-plan-location 'australiaeast' --runtime python --runtime-version 3.8 --functions-version 3 --name <APP_NAME> --storage-account <STORAGE_NAME> --os-type linux --app-insights <APP_INSIGHTS_NAME> --app-insights-key <APP_INSIGHTS_KEY>

$ func azure functionapp publish <APP_NAME> --build remote  --publish-local-settings


```
