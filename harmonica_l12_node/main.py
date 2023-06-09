import schedule
import os
import time
from pydantic import BaseModel
from dotenv import dotenv_values
from harmonica_l12_node.l12_utility import get_traffic_counter
from harmonica_l12_node.harmonica_utility import create_l12_traffic


def update_once(
    router_url: str,
    api_url: str,
    api_token: str,
    timeout: float,
    timezone: str,
):
    traffic_counter = get_traffic_counter(
        router_url=router_url,
        timeout=timeout,
        timezone=timezone,
    )

    daily_usage_gigabytes = traffic_counter.daily / (10**9)
    monthly_usage_gigabytes = traffic_counter.monthly / (10**9)

    print(
        f"{traffic_counter.timestamp.isoformat()} Daily: {daily_usage_gigabytes:.02f}, Monthly: {monthly_usage_gigabytes:.02f}"
    )

    result = create_l12_traffic(
        api_url=api_url,
        api_token=api_token,
        timeout=timeout,
        daily=traffic_counter.daily,
        monthly=traffic_counter.monthly,
        timestamp=traffic_counter.timestamp.isoformat(),
    )

    print(f"Created a daily sensor value ({result.daily.id}).")
    print(f"Created a monthly sensor value ({result.monthly.id}).")


class ConfigRun(BaseModel):
    router_url: str
    api_url: str
    api_token: str
    timeout: float
    output_timezone: str
    output_interval: int


class ConfigRunOnce(BaseModel):
    router_url: str
    api_url: str
    api_token: str
    timeout: float
    output_timezone: str


def execute_run(args):
    config = ConfigRun(**vars(args))

    schedule.every(config.output_interval).seconds.do(
        update_once,
        router_url=config.router_url,
        api_url=config.api_url,
        api_token=config.api_token,
        timeout=config.timeout,
        timezone=config.output_timezone,
    )

    while True:
        schedule.run_pending()
        time.sleep(1)


def execute_run_once(args):
    config = ConfigRunOnce(**vars(args))

    update_once(
        router_url=config.router_url,
        api_url=config.api_url,
        api_token=config.api_token,
        timeout=config.timeout,
        timezone=config.output_timezone,
    )


def main():
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--env_file", type=str, default=os.environ.get("ENV_FILE"))

    pre_args, rest_pre_args = parser.parse_known_args()
    env_file: str | None = pre_args.env_file
    env_vals = dict(os.environ)
    if env_file:
        dotenv_vals = dotenv_values(dotenv_path=env_file)
        env_vals.update(dotenv_vals)

    subparsers = parser.add_subparsers()

    subparser_run = subparsers.add_parser("run")
    subparser_run.add_argument(
        "--router_url",
        type=str,
        default=env_vals.get("HL12N_ROUTER_URL"),
    )
    subparser_run.add_argument(
        "--output_timezone",
        type=str,
        default=env_vals.get("HL12N_OUTPUT_TIMEZONE"),
    )
    subparser_run.add_argument(
        "--output_interval",
        type=int,
        default=env_vals.get("HL12N_OUTPUT_INTERVAL"),
    )
    subparser_run.add_argument(
        "--api_url",
        type=str,
        default=env_vals.get("HL12N_API_URL"),
    )
    subparser_run.add_argument(
        "--api_token",
        type=str,
        default=env_vals.get("HL12N_API_TOKEN"),
    )
    subparser_run.add_argument(
        "--timeout",
        type=float,
        default=env_vals.get("HL12N_TIMEOUT", "10.0"),
    )
    subparser_run.set_defaults(handler=execute_run)

    subparser_run_once = subparsers.add_parser("run_once")
    subparser_run_once.add_argument(
        "--router_url",
        type=str,
        default=env_vals.get("HL12N_ROUTER_URL"),
    )
    subparser_run_once.add_argument(
        "--output_timezone",
        type=str,
        default=env_vals.get("HL12N_OUTPUT_TIMEZONE"),
    )
    subparser_run_once.add_argument(
        "--api_url",
        type=str,
        default=env_vals.get("HL12N_API_URL"),
    )
    subparser_run_once.add_argument(
        "--api_token",
        type=str,
        default=env_vals.get("HL12N_API_TOKEN"),
    )
    subparser_run_once.add_argument(
        "--timeout",
        type=float,
        default=env_vals.get("HL12N_TIMEOUT", "10.0"),
    )
    subparser_run_once.set_defaults(handler=execute_run_once)

    args = parser.parse_args()

    if hasattr(args, "handler"):
        args.handler(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
