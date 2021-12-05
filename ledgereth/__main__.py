import argparse
import sys

from ledgereth import (
    create_transaction,
    find_account,
    get_account_by_path,
    get_accounts,
)
from ledgereth.comms import init_dongle


def get_args(argv):
    parser = argparse.ArgumentParser(description="Do some ledger ops")
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Print extra debugging information",
    )

    subparsers = parser.add_subparsers(
        title="Commands", dest="command", help="Available commands"
    )

    # `accounts` command
    accounts_parser = subparsers.add_parser(
        "accounts", help="Print accounts from the Ledger"
    )
    accounts_parser.add_argument(
        "path",
        metavar="PATH",
        nargs="?",
        help="Get the account for a specific path",
    )
    accounts_parser.add_argument(
        "-c",
        "--count",
        type=int,
        default=3,
        help="How many accounts to fetch (default: 3)",
    )

    # `send` command
    send_parser = subparsers.add_parser(
        "send", help="Send a value transaction from a Ledger account"
    )
    send_parser.add_argument(
        "from_address",
        metavar="FROM",
        help="Account to sign with",
    )
    send_parser.add_argument(
        "to_address",
        metavar="TO",
        help="Account to send to",
    )
    send_parser.add_argument(
        "wei",
        metavar="WEI",
        type=int,
        help="Amount to send (in wei)",
    )
    send_parser.add_argument(
        "-n",
        "--nonce",
        type=int,
        required=True,
        help="Nonce to use for the transaction",
    )
    send_parser.add_argument(
        "-c",
        "--chainid",
        type=int,
        default=1,
        help="Chain ID (default: 1)",
    )
    send_parser.add_argument(
        "-g",
        "--gas",
        type=int,
        default=22000,
        help="The gas limit to use for the tx (default: 22000)",
    )
    send_parser.add_argument(
        "-p",
        "--gasprice",
        type=int,
        required=True,
        help="The gas price to use for the tx",
    )
    send_parser.add_argument(
        "-d",
        "--data",
        type=str,
        help="The hex data to send with the tx (default: empty)",
    )

    return parser.parse_args(argv)


def print_accounts(dongle, args):
    if args.path:
        account = get_account_by_path(args.path, dongle)
        print(f"Account {account.path} {account.address}")
    else:
        accounts = get_accounts(dongle, count=args.count)
        for i, a in enumerate(accounts):
            print(f"Account {i}: {a.path} {a.address}")


def send_value(dongle, args):
    print(
        f"Sending {args.wei} ETH from {args.from_address} to {args.to_address}"
    )

    account = find_account(args.from_address, dongle)

    if not account:
        print("Account not found on device", file=sys.stderr)
        dongle.close()
        sys.exit(1)

    to_address = args.to_address

    signed = create_transaction(
        to=to_address,
        value=args.wei,
        gas=args.gas,
        gas_price=args.gasprice,
        data=args.data or "",
        nonce=args.nonce,
        chain_id=args.chainid,
        sender_path=account.path,
    )
    print(f"Signed Raw Transaction: {signed.raw_transaction()}")


COMMANDS = {
    "accounts": print_accounts,
    "send": send_value,
}


def main(argv=sys.argv[1:]):
    args = get_args(argv)
    command = args.command

    if command not in COMMANDS:
        print(f"Invalid command: {command}", file=sys.stderr)
        sys.exit(1)

    dongle = init_dongle(debug=args.debug)
    COMMANDS[command](dongle, args)
    dongle.close()


if __name__ == "__main__":
    main()
