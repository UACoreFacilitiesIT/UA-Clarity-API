# UA-Clarity-API

Provides a simple REST implementation for use with Clarity endpoints.

## Motivation

Was designed to implement a simple way to interact with Clarity REST architecture.

## Features

- Get will do a batch get if that end point exists, otherwise it will return a response similar to what a batch get returns.
- Caller can add queries to get using a keyword.
- Caches every get to eliminate excessive get calls.
- All REST calls will throw an exception if they failed.

## Code Example

```python
from ua_clarity_api import ua_clarity_api


api = ua_clarity_api.ClarityApi(host, username, password)
uris_files = api.download_files("some file uri")
data = api.get("some endpoint")
```

## Installation

```bash
pip install ua-clarity-api
```

## Tests

```bash
pip install --update nose
cd ./repo
cd ./tests
nosetests test_ua_clarity_api.py
```

## How to Use

- You'll need to instantiate a ClarityApi object with a correct host, and the username/password to access that host's endpoints.
- Get can retrieve resources from endpoints and can utilize queries with the "parameters" keyword.
- Put and Post can update or create new resources given the appropriate endpoint and a well-formed payload.
- Delete can remove a resource from an endpoint.
- Download_files will create temporary files from a list of file uris and returns them as a dictionary mapping of uri: tempfile.

## Credits

[sterns1](https://github.com/sterns1)
[raflopjr](https://github.com/raflopjr)
[RyanJohannesBland](https://github.com/RyaJohannesBland)

## License

MIT
