import sys
import argparse
from ledgereth import get_account_by_path, get_accounts
from ledgereth.comms import init_dongle


def get_args(argv):
    parser = argparse.ArgumentParser(description='Do some ledger ops')
    parser.add_argument('-d', '--debug', action='store_true',
                        help='Print extra debuging information')

    subparsers = parser.add_subparsers(title='Commands', dest='command',
                                       help='Available commands')

    accounts_parser = subparsers.add_parser('accounts', help="Print accounts from the Ledger")
    accounts_parser.add_argument('path', metavar='PATH', type=str, nargs='?',
                                 help='Get the account for a specific path')
    accounts_parser.add_argument('-c', '--count', type=int, default=3,
                                 help='How many accounts to fetch (default: 3)')
    return parser.parse_args(argv)


def print_accounts(dongle, args):
    i = 0
    if args.path:
        account = get_account_by_path(args.path, dongle)
        print('Account {} {}'.format(account.path, account.address))
    else:
        accounts = get_accounts(dongle, count=args.count)
        for a in accounts:
            i += 1
            print('Account {}: {} {}'.format(i, a.path, a.address))


COMMANDS = {
    'accounts': print_accounts,
}


def main(argv=sys.argv[1:]):
    dongle = None
    args = get_args(argv)
    command = args.command

    dongle = init_dongle(debug=args.debug)

    if command in COMMANDS:
        COMMANDS[command](dongle, args)
    else:
        print('Invalid command: {}'.format(command), file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
