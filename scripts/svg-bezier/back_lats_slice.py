"""Slice latissimus_dorsi_l/r into upper/lower via horizontal line at y=365.5."""

from svgpathtools import parse_path, Line, Path

LAT_R = "M338.361 282.302C328.781 303.643 310.447 326.184 300.25 337.25C300.25 365 308.162 397 313.537 403C318.912 409 313.287 422.375 321.287 433.125C329.287 443.875 329.412 453.75 337.287 447C340.258 444.454 342.837 442.548 345.287 441.255C367.412 425.125 386.162 397 387.162 388.375C387.382 386.794 387.946 382.443 388.05 381.375C388.536 376.399 390.435 372.365 392.376 368.245L392.55 367.875C394.55 363.625 395.05 363.125 397.05 355.125C399.05 347.125 407.037 328.173 410.162 318.548C408.738 309.932 409.958 299.866 411.798 281.704C394.706 287.32 375.956 291.056 358.76 288.699C351.616 287.719 344.739 285.687 338.361 282.302Z"

LAT_L = "M256.926 282.302C266.506 303.643 284.84 326.184 295.037 337.25C295.037 365 287.125 397 281.75 403C276.375 409 282 422.375 274 433.125C266 443.875 265.875 453.75 258 447C255.029 444.454 252.45 442.548 250 441.255C227.875 425.125 209.125 397 208.125 388.375C207.905 386.794 207.341 382.443 207.237 381.375C206.751 376.399 204.852 372.365 202.911 368.245L202.737 367.875C200.737 363.625 200.237 363.125 198.237 355.125C196.237 347.125 188.25 328.173 185.125 318.548C186.549 309.932 185.329 299.866 183.489 281.704C200.581 287.32 219.331 291.056 236.527 288.699C243.672 287.719 250.548 285.687 256.926 282.302Z"

Y_MID = 365.5


def slice_two(path_d, y_mid, label):
    p = parse_path(path_d)
    line = Line(0 + y_mid * 1j, 587 + y_mid * 1j)
    its = p.intersect(line)
    Ts = sorted(set(round(item[0][0], 6) for item in its))
    print(f"  {label}: T crossings = {Ts}")
    if len(Ts) != 2:
        raise RuntimeError(f"{label}: expected 2 crossings, got {Ts}")
    pt_a = p.point(Ts[0])
    pt_b = p.point(Ts[1])
    print(f"  pt_a={pt_a}, pt_b={pt_b}")

    mid_T = (Ts[0] + Ts[1]) / 2
    pt_mid = p.point(mid_T)
    print(f"  pt_mid={pt_mid} (y={pt_mid.imag})")

    if pt_mid.imag < y_mid:
        upper_arc = p.cropped(Ts[0], Ts[1])
        lower_arc = Path(*p.cropped(Ts[1], 1.0)._segments, *p.cropped(0.0, Ts[0])._segments)
    else:
        upper_arc = Path(*p.cropped(Ts[1], 1.0)._segments, *p.cropped(0.0, Ts[0])._segments)
        lower_arc = p.cropped(Ts[0], Ts[1])

    upper = Path(*upper_arc._segments, Line(upper_arc.end, upper_arc.start))
    lower = Path(*lower_arc._segments, Line(lower_arc.end, lower_arc.start))
    return upper.d(), lower.d()


for label, d in [("LAT_L", LAT_L), ("LAT_R", LAT_R)]:
    print(f"\n=== {label} ===")
    u, l = slice_two(d, Y_MID, label)
    print(f"upper d= {u}")
    print(f"lower d= {l}")
