import json
import time
from ricxappframe.rmr import rmr
from common import PING_MTYPE, PONG_MTYPE, init_rmr, recv_payload

def main():
    ctx = init_rmr()

    rx_msg = rmr.rmr_alloc_msg(ctx, rmr.RMR_MAX_RCV_BYTES)

    while True:
        rx_msg = rmr.rmr_torcv_msg(ctx, rx_msg, 5000)

        if not rx_msg:
            print("Receive returned no buffer")
            rx_msg = rmr.rmr_alloc_msg(ctx, rmr.RMR_MAX_RCV_BYTES)
            continue

        if rx_msg.contents.state != rmr.RMR_OK:
            print(
                f"Receive timeout/error: state={rx_msg.contents.state} "
                f"tp_state={rx_msg.contents.tp_state}"
            )
            continue

        payload = recv_payload(rx_msg)

        try:
            src = rmr.get_src(rx_msg)
        except Exception:
            src = b"unknown"

        print(
            f"[RX] PING received | "
            f"mtype={rx_msg.contents.mtype} | "
            f"src={src.decode(errors='ignore')} | "
            f"state={rx_msg.contents.state} | tp_state={rx_msg.contents.tp_state}"
        )

        if rx_msg.contents.mtype == PING_MTYPE:
            reply_dict = {
                "type": "pong",
                "got": payload,
                "ts": time.time(),
            }
            reply_payload = json.dumps(reply_dict).encode()

            # reuse the received buffer and send it back to the original sender (RTS)
            rx_msg.contents.mtype = PONG_MTYPE
            rmr.set_payload_and_length(reply_payload, rx_msg)

            rx_msg = rmr.rmr_rts_msg(ctx, rx_msg)

            print(
                f"[TX-RTS] PONG sent | "
                f"mtype={PONG_MTYPE} | "
                f"dest=RTS({src.decode(errors='ignore')}) | "
                f"state={rx_msg.contents.state} | tp_state={rx_msg.contents.tp_state}"
            )

if __name__ == "__main__":
    main()