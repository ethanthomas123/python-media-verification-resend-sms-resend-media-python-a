"""Runnable example: resend a creator's stuck media verification message."""

import argparse

from media_delivery import InfraiSms, MediaAsset, resend_stuck_delivery


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--asset-id", required=True)
    parser.add_argument("--creator-id", required=True)
    parser.add_argument("--job-id", required=True)
    parser.add_argument("--message-id", required=True)
    args = parser.parse_args()
    asset = MediaAsset(args.asset_id, args.creator_id, args.job_id, args.message_id)
    state = resend_stuck_delivery(asset, InfraiSms())
    print({"asset_id": asset.asset_id, "processing_job_id": asset.processing_job_id, "delivery": state.status})


if __name__ == "__main__":
    main()
