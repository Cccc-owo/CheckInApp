# Jielong

Run: `sh start.sh` and get usage(Linux only).

## Environment

Use `python3 -m venv venv` to create a virtual environment.

Then activate the venv, use `pip install -r .\requirements.txt` to install dependencies.

Note that you have to ensure the CHROME_BINARY_PATH and CHROMEDRIVER_PATH in `shared_config.py` correctly.

Also, if you want the email notification(to notify the expiration of token) works, you need to check `config.ini`.

## Details

Please edit the config and payload by yourself to meet your actual need.

### JieLong Payload

Jielong Payload: `payload` in the `try-catch` block of `perform_check_in()` function in `check_in_worker.py`

You may use [Reqable](https://reqable.com/) or other tools to get the payload of JieLong. (Tips: Catch the request of "EditRecord" and you will find what you want.)

Meanwhile, `config.csv` is used to build the payload. You may need edit the `config.csv` related codes to add support to new payload. Searching the usage of `read_configs()` function will tell you the things.

### Config

APScheduler config: `app.py`

Other config: `shared_config.py`

JieLong Token data: `config.csv`

Email notification config: `config.ini`
