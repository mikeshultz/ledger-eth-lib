import argparse
import sys
from enum import IntEnum

from eth_utils import decode_hex, encode_hex

from ledgereth import (
    create_transaction,
    find_account,
    get_account_by_path,
    get_accounts,
    sign_message,
    sign_typed_data_draft,
)
from ledgereth.comms import init_dongle


class ExitCodes(IntEnum):
    SUCCESS = 0
    GENERAL_ERROR = 1
    INVALID_ARGUMENT = 2


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
        help="The gas price to use for the tx",
    )
    send_parser.add_argument(
        "-f",
        "--max-fee",
        type=int,
        help="The max fee per gas to use for the tx",
    )
    send_parser.add_argument(
        "-b",
        "--priority-fee",
        type=int,
        default=0,
        help="The priority fee per gas to use for the tx (default: 0)",
    )
    send_parser.add_argument(
        "-d",
        "--data",
        type=str,
        help="The hex data to send with the tx (default: empty)",
    )

    # `sign` command
    sign_parser = subparsers.add_parser(
        "sign", help="Sign a text message with a Ledger account using EIP-191 v0"
    )
    sign_parser.add_argument(
        "account_address",
        metavar="ADDRESS",
        help="Address of the account to sign with",
    )
    sign_parser.add_argument(
        "message",
        metavar="MESSAGE",
        help="Message to sign",
    )

    # `signtyped` command
    signtyped_parser = subparsers.add_parser(
        "signtyped", help="Sign a text message with a Ledger account using EIP-191 v0"
    )
    signtyped_parser.add_argument(
        "account_address",
        metavar="ADDRESS",
        help="Address of the account to sign with",
    )
    signtyped_parser.add_argument(
        "domain_hash",
        metavar="DOMAIN",
        help="Domain hash to sign",
    )
    signtyped_parser.add_argument(
        "message_hash",
        metavar="MESSAGE",
        help="Message hash to sign",
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
    print(f"Sending {args.wei} ETH from {args.from_address} to {args.to_address}")

    account = find_account(args.from_address, dongle)

    if not account:
        print("Account not found on device", file=sys.stderr)
        dongle.close()
        sys.exit(ExitCodes.INVALID_ARGUMENT)

    if not args.gasprice and not args.max_fee:
        print("Either --gasprice or --max-fee must be provided", file=sys.stderr)
        dongle.close()
        sys.exit(ExitCodes.INVALID_ARGUMENT)

    to_address = args.to_address

    signed = create_transaction(
        destination=to_address,
        amount=args.wei,
        gas=args.gas,
        gas_price=args.gasprice,
        max_fee_per_gas=args.max_fee,
        max_priority_fee_per_gas=args.priority_fee,
        data=args.data or "",
        nonce=args.nonce,
        chain_id=args.chainid,
        sender_path=account.path,
    )

    print(f"Signed Raw Transaction: {signed.raw_transaction()}")


def sign_text_message(dongle, args):
    print(f'Signing "{args.message}" with {args.account_address}')

    account = find_account(args.account_address, dongle)
    signed = sign_message(args.message, account.path)

    print(f"Signature: {signed.signature}")


def sign_typed_data(dongle, args):
    print(f"Signing typed data with account {args.account_address}")
    print(f"Domain hash: {args.domain_hash}")
    print(f"Message hash: {args.message_hash}")

    account = find_account(args.account_address, dongle)
    signed = sign_typed_data_draft(
        decode_hex(args.domain_hash), decode_hex(args.message_hash), account.path
    )

    print(f"Signature: {signed.signature}")


COMMANDS = {
    "accounts": print_accounts,
    "send": send_value,
    "sign": sign_text_message,
    "signtyped": sign_typed_data,
}


def main(argv=sys.argv[1:]):
    args = get_args(argv)
    command = args.command

    if command not in COMMANDS:
        print(f"Invalid command: {command}", file=sys.stderr)
        sys.exit(ExitCodes.INVALID_ARGUMENT)

    dongle = init_dongle(debug=args.debug)
    COMMANDS[command](dongle, args)
    dongle.close()


if __name__ == "__main__":
    main()
