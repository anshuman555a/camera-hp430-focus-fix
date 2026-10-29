"""
Lock a UVC webcam's focus (autofocus OFF, manual focus = value) on Windows.
No admin rights needed.

Setup (user-level install, no admin):
    pip install --user opencv-python

Usage:
    python lock_focus.py --list                  # see which camera indexes open
    python lock_focus.py --index 1 --preview     # check you picked the HP 430
    python lock_focus.py --index 1               # set once and exit
    python lock_focus.py --index 1 --keep 5      # re-apply every 5 s (Ctrl+C to stop)
    python lock_focus.py --index 1 --focus 20    # a different focus value
    python lock_focus.py --index 1 --backend msmf   # try this if dshow can't open
                                                    # the camera while an app uses it

Notes:
  * Starting a camera app (Camera, Teams, Zoom) can reset the focus. Apply it
    AFTER the app has started streaming, or use --keep to keep re-applying.
  * dshow (default) usually needs exclusive access to the camera.
    msmf goes through Windows' camera sharing service and may open the camera
    even while another app is streaming. Camera indexes can differ between the
    two, so run --list with the same --backend you plan to use.
  * --keep and --preview keep the camera open.
"""
import argparse
import sys
import time

import cv2

BACKENDS = {"dshow": cv2.CAP_DSHOW, "msmf": cv2.CAP_MSMF}


def list_cameras(backend, max_index=5):
    for i in range(max_index):
        cap = cv2.VideoCapture(i, backend)
        if cap.isOpened():
            w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            print(f"index {i}: opens ({w}x{h})")
        else:
            print(f"index {i}: no camera")
        cap.release()


def apply_focus(cap, focus):
    af_ok = cap.set(cv2.CAP_PROP_AUTOFOCUS, 0)
    f_ok = cap.set(cv2.CAP_PROP_FOCUS, focus)
    print(
        f"autofocus set ok={af_ok} (reads {cap.get(cv2.CAP_PROP_AUTOFOCUS)}), "
        f"focus set ok={f_ok} (reads {cap.get(cv2.CAP_PROP_FOCUS)})"
    )


def main():
    p = argparse.ArgumentParser(description="Lock webcam focus (autofocus off).")
    p.add_argument("--index", type=int, default=0, help="camera index (default 0)")
    p.add_argument("--focus", type=float, default=0, help="manual focus value (default 0)")
    p.add_argument("--keep", type=float, default=0, help="re-apply every N seconds")
    p.add_argument("--preview", action="store_true", help="show live video, press q to quit")
    p.add_argument("--list", action="store_true", help="list camera indexes and exit")
    p.add_argument("--backend", choices=BACKENDS, default="dshow", help="dshow (default) or msmf")
    args = p.parse_args()
    backend = BACKENDS[args.backend]

    if args.list:
        list_cameras(backend)
        return

    cap = cv2.VideoCapture(args.index, backend)
    if not cap.isOpened():
        sys.exit(
            f"Could not open camera {args.index} with {args.backend}. "
            "Another app may be holding it: close it, try --backend msmf, "
            "or try another --index (use --list)."
        )

    try:
        cap.read()  # often needs a frame before controls take effect
        apply_focus(cap, args.focus)

        if args.preview:
            while True:
                ok, frame = cap.read()
                if ok:
                    cv2.imshow("preview (q to quit)", frame)
                if cv2.waitKey(30) & 0xFF == ord("q"):
                    break
        elif args.keep > 0:
            print(f"Re-applying every {args.keep}s. Ctrl+C to stop.")
            while True:
                time.sleep(args.keep)
                cap.read()
                apply_focus(cap, args.focus)
    except KeyboardInterrupt:
        pass
    finally:
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()