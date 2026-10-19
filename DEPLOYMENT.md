# Deployment and operations

## Supported deployment

Use one always-on Windows or Linux host, one Waitress process and a local
persistent SQLite file. This is suitable for a private demo or small team.
Do not deploy this synchronous compiler/SQLite application to an ephemeral
serverless function without redesigning its execution and storage boundaries.

Waitress supports Windows and uses a single process with thread workers, as
described in the [official Flask deployment guide](https://flask.palletsprojects.com/en/stable/deploying/waitress/).
The server binds to loopback so a shared deployment can enforce HTTPS and
authentication at its reverse proxy.

## Installation and preflight

1. Copy the **inner** project directory to an application directory. Exclude
   `.venv`, `.env`, generated reports, test/demo databases and local secrets.
2. Install Python 3.11+ and C++17 g++. Create a virtual environment and install
   `python -m pip install -r requirements-dev.txt`. Hypothesis is needed when
   offering the property suite in the web UI. `requirements.txt` alone is enough
   for serving/browsing and Python/SQL/C++ reference suites.
3. Run `python -m pip check`, `g++ --version`, and `python runner.py`. Keep the
   generated `reports/verification.json` as release evidence. Release only
   when the command exits zero; missing g++ or Hypothesis is a failure.
4. Create a persistent data directory owned by the service account. Configure
   `ASSESSMENT_DB` with an absolute path outside the application release folder.
   The app creates parent directories and tables. The account needs write
   permission there and in its temporary directory, and read permission for
   the application. Give it no unnecessary privileges or cloud credentials.
5. Supply a unique runner token using the deployment service's secret settings.
   Generate one with `python -c "import secrets; print(secrets.token_urlsafe(32))"`.
   Share it only with authorized operators through an approved secret channel.

## Configuration

The application reads process environment variables at startup. `.env.example`
is a reference file, not an automatically loaded configuration.

| Variable | Default | Meaning |
| --- | --- | --- |
| `ASSESSMENT_RUNNER_TOKEN` | empty | Empty disables POST execution; use a random 32-byte secret |
| `ASSESSMENT_DB` | `reports/runs.db` under project | Persistent SQLite file; use absolute production path |
| `ASSESSMENT_TRUSTED_HOSTS` | `localhost,127.0.0.1` | Comma-separated allowed hostnames, without scheme/port |
| `ASSESSMENT_LOG_LEVEL` | `INFO` | Python logging level, e.g. INFO/WARNING |
| `PORT` | `8080` | Loopback port used by `serve.py` |

Example PowerShell deployment environment (substitute your values):

```powershell
$env:ASSESSMENT_DB = 'D:\assessment-data\runs.db'
$env:ASSESSMENT_TRUSTED_HOSTS = 'localhost,127.0.0.1,assessment.example.com'
$env:PORT = '8080'
# Inject ASSESSMENT_RUNNER_TOKEN from your secret manager or service environment.
python serve.py
```

On Linux, set the same environment variables in your service manager and use
the virtual environment's Python executable as the `ExecStart` for `serve.py`.
On Windows, configure an existing service wrapper/process supervisor to run
the same command with its working directory set to the inner project directory.
Enable restart-on-failure and stdout/stderr log collection. Service-manager,
reverse-proxy and OS policy configuration must be adapted and tested on the
chosen host; no host-specific installation has been performed here.

## Shared HTTPS access

Place an authenticated HTTPS reverse proxy in front of `127.0.0.1:8080`.
Protect **every** route, including questions, analytics, exports and health.
The runner token protects execution only. Preserve the public Host header and
configure that exact hostname in `ASSESSMENT_TRUSTED_HOSTS`. Keep direct
Waitress access restricted to loopback; do not expose another bypass port.

The application compares an Origin header against Flask's request origin.
For TLS termination, run Waitress with explicitly configured trusted proxy
handling so Flask sees the original scheme. For example, instead of `serve.py`:

```text
waitress-serve --host=127.0.0.1 --port=8080 --threads=4 --trusted-proxy=127.0.0.1 --trusted-proxy-headers="x-forwarded-proto" web.app:app
```

Have the loopback reverse proxy overwrite `X-Forwarded-Proto` with `https`.
Do not trust arbitrary proxies or client-supplied forwarded headers. This CLI
entry point performs bank checks on requests through the common loader;
`serve.py` additionally checks the bank before startup. Confirm these flags
with the pinned Waitress `--help` on the deployment host.

Set proxy body limits to 16 KB, rate-limit execution requests, and allow at
least 180 seconds for runner responses. Use **one** application process:
the in-process execution lock is not distributed. Multiple users receive 409
while another suite is running. Suite failures return completed results with
exit_code != 0; runner errors use 503 and deadlines use 504. A browser/network
disconnect does not cancel a running validation.

## Smoke test and operations

- `GET /healthz` should return HTTP 200 with `status: ok` and `questions: 30`.
  It validates the bank contract and opens/queries history storage, including
  initial table creation. It does not test the compiler or all dependencies.
- Browse a question. Enter the token on Run Tests and run Python, SQL, C++
  and the property suite. Confirm status/counts and recent runs in analytics.
- Download both CSV exports. Verify counts and case detail. The limits are
  latest 1,000 runs and latest 5,000 cases; the UI does not paginate history.
- Requests log an ID, method, path, status and duration; suites log status,
  exit code and duration. Server exceptions retain stack traces in logs.
  Tokens/request bodies are not logged. Send logs to your existing collector,
  set retention/rotation and alert on repeated 5xx, failed health or failed runs.
- Back up SQLite using its backup API or stop the service before copying the
  DB. Include it in the normal backup policy and test restoring to a separate
  path before relying on the backup. History contains validator error details;
  restrict file and backup access. No backup service is configured by this repo.
- Rotate the token by changing the environment and restarting the service.
  Operators enter the new value on the page. It is a shared secret, not per-user
  identity/audit attribution.

## Updates and rollback

Keep a copy of the prior release, its pinned requirements and verified report.
Run the full suite on the new release, stop the service, back up history, replace
application files, then restart and smoke-test. Restore the previous release
and environment if startup/health fails. Database changes here are additive
table creation only; no destructive migration or reset command is provided.

Never enable Flask debug mode in shared deployments. Never run hostile C++
or Python submissions on this host. The Python SQLite
[authorizer and progress handler](https://docs.python.org/3/library/sqlite3.html#sqlite3.Connection.set_authorizer)
restrict query behavior but are not an OS sandbox. For a public judge, first
build an isolated worker service with network denial, filesystem isolation,
CPU/memory/process/output quotas and explicit cleanup, plus authentication,
tenant isolation, queueing and abuse controls.

## Deployment verification status

Local Windows/Python 3.13.3/g++ validation and loopback Waitress browser flow
were exercised. No remote host, TLS proxy, system service, restore drill,
load test or hosted CI run was exercised. The workflow is configured for pushes and pull requests in the existing
GitHub repository. Its hosted results must be checked after publishing.
