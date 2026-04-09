#!/usr/bin/env python3
"""
智桥 SSL 证书生成工具

命令行工具用于生成和管理 SSL 证书
"""

import argparse
import sys
from pathlib import Path

# 添加 relay-server 路径
sys.path.insert(0, str(Path(__file__).parent))

from logger import get_logger
from ssl_manager import (
    check_wss_requirements,
    generate_self_signed_cert,
    get_certificate_info,
    print_wss_setup_instructions,
    setup_development_certificates,
    validate_certificates,
)

logger = get_logger(__name__)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="Zhineng-bridge SSL Certificate Management Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # generate 命令
    gen_parser = subparsers.add_parser(
        "generate",
        help="Generate self-signed SSL certificates",
    )
    gen_parser.add_argument(
        "--output-dir",
        help="Output directory for certificates",
        default=None,
    )
    gen_parser.add_argument(
        "--cert-name",
        help="Certificate filename",
        default="cert.pem",
    )
    gen_parser.add_argument(
        "--key-name",
        help="Private key filename",
        default="key.pem",
    )
    gen_parser.add_argument(
        "--common-name",
        help="Common name (CN) for the certificate",
        default="localhost",
    )
    gen_parser.add_argument(
        "--days",
        help="Number of days the certificate is valid",
        type=int,
        default=365,
    )
    gen_parser.add_argument(
        "--force",
        help="Force overwrite existing certificates",
        action="store_true",
    )

    # validate 命令
    val_parser = subparsers.add_parser(
        "validate",
        help="Validate SSL certificates",
    )
    val_parser.add_argument(
        "--cert",
        help="Certificate file path",
        required=True,
    )
    val_parser.add_argument(
        "--key",
        help="Private key file path",
        required=True,
    )

    # info 命令
    info_parser = subparsers.add_parser(
        "info",
        help="Get SSL certificate information",
    )
    info_parser.add_argument(
        "--cert",
        help="Certificate file path",
        required=True,
    )

    # setup 命令
    subparsers.add_parser(
        "setup",
        help="Setup development SSL certificates",
    )

    # check 命令
    subparsers.add_parser(
        "check",
        help="Check WSS configuration",
    )

    # instructions 命令
    subparsers.add_parser(
        "instructions",
        help="Print WSS setup instructions",
    )

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    try:
        if args.command == "generate":
            print("\n🔐 Generating self-signed SSL certificates...\n")
            cert_path, key_path = generate_self_signed_cert(
                output_dir=args.output_dir,
                cert_filename=args.cert_name,
                key_filename=args.key_name,
                common_name=args.common_name,
                days_valid=args.days,
                force=args.force,
            )
            print("\n✅ Certificates generated successfully:")
            print(f"   Certificate: {cert_path}")
            print(f"   Private Key: {key_path}\n")
            print("\nTo use these certificates, set the following environment variables:")
            print("   export ZHINENG_BRIDGE_ENABLE_WSS=true")
            print(f"   export ZHINENG_BRIDGE_CERT_FILE={cert_path}")
            print(f"   export ZHINENG_BRIDGE_KEY_FILE={key_path}\n")

        elif args.command == "validate":
            print("\n🔍 Validating SSL certificates...\n")
            is_valid, error_msg = validate_certificates(args.cert, args.key)
            if is_valid:
                print("✅ Certificates are valid and match each other\n")
            else:
                print(f"❌ Validation failed: {error_msg}\n")
                return 1

        elif args.command == "info":
            print("\n📋 Certificate Information:\n")
            info = get_certificate_info(args.cert)
            if info:
                for key, value in info.items():
                    print(f"   {key}: {value}")
                print()
            else:
                print("❌ Failed to retrieve certificate information\n")
                return 1

        elif args.command == "setup":
            print("\n🚀 Setting up development SSL certificates...\n")
            cert_path, key_path = setup_development_certificates()
            print("\n✅ Development certificates ready:")
            print(f"   Certificate: {cert_path}")
            print(f"   Private Key: {key_path}\n")

        elif args.command == "check":
            print("\n🔍 Checking WSS configuration...\n")
            is_ready, missing = check_wss_requirements()
            if is_ready:
                print("✅ WSS configuration is complete\n")
            else:
                print("❌ WSS configuration is incomplete:")
                for item in missing:
                    print(f"   - {item}")
                print()
                return 1

        elif args.command == "instructions":
            print_wss_setup_instructions()

        return 0

    except Exception as e:
        logger.error("SSL certificate management failed", error=str(e), exc_info=True)
        print(f"\n❌ Error: {e}\n")
        return 1


if __name__ == "__main__":
    sys.exit(main())
