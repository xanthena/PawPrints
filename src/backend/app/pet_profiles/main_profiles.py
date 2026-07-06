"""Command-line adapter for the pet profile service."""

import argparse
import json
from pathlib import Path

from .store import PetProfileStore


def _parser():
    parser = argparse.ArgumentParser(description="Manage up to two pet identities.")
    parser.add_argument("--profile-dir", type=Path)
    subparsers = parser.add_subparsers(dest="command", required=True)

    register = subparsers.add_parser("register", help="Add a named reference photo.")
    register.add_argument("name")
    register.add_argument("image", type=Path)

    subparsers.add_parser("list", help="List registered pets.")
    remove = subparsers.add_parser("remove", help="Remove by name or profile id.")
    remove.add_argument("identifier")
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    store = PetProfileStore(args.profile_dir) if args.profile_dir else PetProfileStore()

    if args.command == "register":
        payload = store.register(args.name, args.image).to_dict()
    elif args.command == "remove":
        payload = store.remove(args.identifier).to_dict()
    else:
        payload = [profile.to_dict() for profile in store.list()]
    print(json.dumps(payload, indent=4, ensure_ascii=False))


if __name__ == "__main__":
    main()
