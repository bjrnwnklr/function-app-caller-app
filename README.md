# external-caller-app

Small helper to call the Function App for testing and development.

## Usage

Run the script with defaults:

```bash
python main.py
```

## Command-line options

-   `--n`: How many numbers to generate (int). Default: `10000`.
-   `--m`: How many numbers to match/send (int). Default: `2000`.
-   `--digits`: Number of digits per number (int). Default: `5`.

## Examples

Generate 5k numbers of 6 digits and send 1k to match:

```bash
python main.py --n 5000 --m 1000 --digits 6
```

## Logging

The application uses the Python `logging` module. By default logs are at `INFO` level.

To enable more verbose logging set the `AZURE_IDENTITY_LOG_LEVEL` and the root log level
in your environment or run the script under a configured logging environment.

## Azure authentication

The client requests a token for the Function App using the registered Application ID URI
or the client id. Ensure these environment variables are set when running the script:

-   `AZURE_FUNCTION_APP_CLIENT_ID` - the Application (client) ID of the Function App registration
-   `AZURE_TENANT_ID` - (recommended) tenant id where the app is registered

You can also override the default scope directly:

```bash
export AZURE_SCOPE="api://<your-app-client-id>/.default"
```

If you prefer to use a service principal for local testing, set the usual env vars for
`EnvironmentCredential`:

-   `AZURE_CLIENT_ID`
-   `AZURE_CLIENT_SECRET`
-   `AZURE_TENANT_ID`

If you run `az login` locally, `DefaultAzureCredential` will fall back to `AzureCliCredential`.
