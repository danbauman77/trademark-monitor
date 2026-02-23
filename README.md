# USPTO Trademark Monitor

Python script to regularly monitor USPTO trademark applications with keyword filtering and email alerts.


## Install

```bash
pip install -r requirements.txt
```


### Configure

Edit `config.json`:

```json
{
  "uspto_api_key": "your_api_key_here",
  "max_results_per_email": 100,
  "email": {
    "smtp_server": "smtp.gmail.com",
    "smtp_port": 587,
    "sender_email": "your_email@gmail.com",
    "sender_password": "your_app_password",
    "recipient_emails": ["recipient@example.com"]
  },
  "filters": {

    "See below"

    }
  }
}
```

How to set up a Google App Password: https://docs.contentstudio.io/article/1080-how-to-set-a-google-app-password



### Run the Monitor

```bash
python trademark_monitor.py
```


### Current Keyword Filtering


#### Owner State Filtering: 

```json
    "owner_states": [
      "AL",
      "AK",
      "AZ",
      "AR",
      "CA",
      "CO",
      "CT",
      "DE",
      "FL",
      "GA",
      "HI",
      "ID",
      "IL",
      "IN",
      "IA",
      "KS",
      "KY",
      "LA",
      "ME",
      "MD",
      "MA",
      "MI",
      "MN",
      "MS",
      "MO",
      "MT",
      "NE",
      "NV",
      "NH",
      "NJ",
      "NM",
      "NY",
      "NC",
      "ND",
      "OH",
      "OK",
      "OR",
      "PA",
      "RI",
      "SC",
      "SD",
      "TN",
      "TX",
      "UT",
      "VT",
      "VA",
      "WA",
      "WV",
      "WI",
      "WY",
      "DC",
      "GU",
      "PR",
      "VI",
      "AS",
      "MP",
      "US"
    ]
```


#### Legal Entity Codes: 

```json
    "legal_entity_codes": [
      "02",
      "03",
      "04",
      "05",
      "06",
      "07",
      "08",
      "09",
      "10",
      "11",
      "12",
      "13",
      "14",
      "15",
      "16",
      "17",
      "18",
      "19",
      "98",
      "99"
    ]
```


#### Keyword Search on owner_name

```json
"owner_name": [
        "*univ*",
        "* u *",
        "* u. *",
        "*school*",
        "*colleg*",
        "*institut*",
        "*acad*",
        "*regent*",
        "*higher ed*",
        "*post-secondary*",
        "*post secondary*",
        "*postsecondary*",
        "*seminar*",
        "*suny*",
        "*cuny*",
        "*conservator*",
        "*board of trustee*",
        "*board of governor*",
        "*board of visitor*",
        "*board of curator*"
      ],
```


#### Keyword Search on email_addresses

```json
"email_addresses": ["*.edu*"]
```


### State Reset

To start over from a specific serial number:

```python
from state_manager import StateManager
sm = StateManager()
sm.reset_state(start_sn=88000000)  # Start from Serial Number 88000000
```


### API Reference

USPTO TSDR API: https://tsdrapi.uspto.gov/ts/cd/caseMultiStatus/sn

Also see: https://mustberuss.github.io/TSDR-Swagger/

Batch query format (up to 20):

```
https://tsdrapi.uspto.gov/ts/cd/caseMultiStatus/sn?ids=86761080,86761081,86761082
```

Requires `API_KEY` header. (https://account.uspto.gov/api-manager)


### Acknowledgements
- Coded and debugged with the assistance of claude.ai