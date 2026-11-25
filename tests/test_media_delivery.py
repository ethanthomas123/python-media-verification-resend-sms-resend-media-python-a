from media_delivery import DeliveryState, MediaAsset, resend_stuck_delivery


class FakeSms:
    def __init__(self):
        self.calls = []
        self.states = [[{"status": "stuck"}], [{"status": "queued"}]]

    def events(self, message_id):
        self.calls.append(("events", message_id))
        return self.states.pop(0)

    def resend(self, message_id):
        self.calls.append(("resend", message_id))
        return {"message_id": message_id}


def test_stuck_delivery_is_resent_and_state_is_refreshed():
    client = FakeSms()
    asset = MediaAsset("asset-7", "creator-2", "job-9", "message-4")
    result = resend_stuck_delivery(asset, client)
    assert isinstance(result, DeliveryState)
    assert result.status == "queued"
    assert client.calls == [("events", "message-4"), ("resend", "message-4"), ("events", "message-4")]
