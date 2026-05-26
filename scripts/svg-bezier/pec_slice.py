"""
Slice pectoralis_major_l/r SVG paths into clavicular/sternal/costal
3-way horizontal subdivisions using svgpathtools Bezier intersection.

User decision (2026-05-26): anatomic ratio approx 30% / 50% / 20%
→ y_top = 233, y_bot = 291 (within original y 198.5 - 315.2).
"""

from svgpathtools import parse_path, Line, Path

PEC_L = "M314.842 203.634C320.092 200.134 329.592 199.384 343.342 198.509C346.592 198.298 350.342 201.884 354.467 203.634C358.592 205.384 361.717 203.634 375.467 208.259C389.217 212.884 396.592 224.634 401.842 229.259C407.092 233.884 412.717 236.884 418.217 255.134C412.317 252.334 404.842 246.467 401.842 243.884V246.509L403.125 261.75C400.25 268.5 394.15 285.825 392.75 301.125C388.35 305.325 377.062 309.881 371.967 311.634C362.689 314.207 351.318 315.195 337.717 313.384C291.717 307.259 297.842 269.134 298.217 245.759C298.592 222.384 309.592 207.134 314.842 203.634Z"

PEC_R = "M271.625 203.634C266.375 200.134 256.875 199.384 243.125 198.509C239.875 198.298 236.125 201.884 232 203.634C227.875 205.384 224.75 203.634 211 208.259C197.25 212.884 189.875 224.634 184.625 229.259C179.375 233.884 173.75 236.884 168.25 255.134C174.15 252.334 181.625 246.467 184.625 243.884V246.509L183.342 261.75C186.217 268.5 192.317 285.825 193.717 301.125C198.117 305.325 209.405 309.881 214.5 311.634C223.777 314.207 235.149 315.195 248.75 313.384C294.75 307.259 288.625 269.134 288.25 245.759C287.875 222.384 276.875 207.134 271.625 203.634Z"

Y_TOP = 233.0  # clavicular / sternal boundary
Y_BOT = 291.0  # sternal / costal boundary


def find_global_T(path, y):
    """Find the two T values (path-global 0..1) where path crosses
    horizontal line y. Closed convex-ish path = 2 crossings.
    Returns sorted list."""
    line = Line(0 + y * 1j, 587 + y * 1j)
    intersections = path.intersect(line)
    # intersections: list of ((T1, seg1, t1), (T2, seg2, t2))
    Ts = sorted(set(round(item[0][0], 6) for item in intersections))
    return Ts


def slice_three(path_d, y_top, y_bot, label):
    p = parse_path(path_d)
    T_top = find_global_T(p, y_top)
    T_bot = find_global_T(p, y_bot)
    print(f"  {label}: T_top={T_top}, T_bot={T_bot}")
    if len(T_top) != 2 or len(T_bot) != 2:
        raise RuntimeError(f"{label}: expected 2 crossings per line, got {T_top} {T_bot}")
    # Closed paths: 4 cut points dividing path into 4 arcs.
    # Sorted T: T_top[0] < T_bot[0] < T_bot[1] < T_top[1] (typical)
    # OR T_top[0] < T_top[1] < T_bot[0] < T_bot[1] (M-start above y_top)
    # We need: clavicular = arc(T_top[0]→T_top[1]) closed by horizontal Line at y_top
    #          costal     = arc(T_bot[0]→T_bot[1]) closed by horizontal Line at y_bot
    #          sternal    = arc(T_top[1]→T_bot[0]) + Line(y_bot side) + arc(T_bot[1]→T_top[0]) + Line(y_top side)
    # Determine arc direction by sampling.
    p_top0 = p.point(T_top[0])
    p_top1 = p.point(T_top[1])
    p_bot0 = p.point(T_bot[0])
    p_bot1 = p.point(T_bot[1])
    # Check which T_top is on the left (lower x) for clarity.
    print(f"  pt_top0={p_top0}, pt_top1={p_top1}, pt_bot0={p_bot0}, pt_bot1={p_bot1}")

    # CLAVICULAR: arc from T_top[0] to T_top[1] (going through y<y_top) + Line back.
    # In closed path, M-start (T=0) is somewhere; need arc that stays above y_top.
    # Sample midpoint between T_top[0] and T_top[1] to see if y < y_top.
    mid_T_top = (T_top[0] + T_top[1]) / 2
    pt_mid = p.point(mid_T_top)
    if pt_mid.imag < y_top:
        # Arc T_top[0]→T_top[1] stays above (clavicular arc)
        clav_arc = p.cropped(T_top[0], T_top[1])
    else:
        # Arc wraps around — go T_top[1] → end → start → T_top[0]
        clav_arc = Path(*p.cropped(T_top[1], 1.0)._segments, *p.cropped(0.0, T_top[0])._segments)
    # Close clavicular with horizontal line at y_top, then back to start.
    clav_path = Path(*clav_arc._segments, Line(clav_arc.end, clav_arc.start))

    # COSTAL: arc through y > y_bot
    mid_T_bot = (T_bot[0] + T_bot[1]) / 2
    pt_mid_bot = p.point(mid_T_bot)
    if pt_mid_bot.imag > y_bot:
        cost_arc = p.cropped(T_bot[0], T_bot[1])
    else:
        cost_arc = Path(*p.cropped(T_bot[1], 1.0)._segments, *p.cropped(0.0, T_bot[0])._segments)
    cost_path = Path(*cost_arc._segments, Line(cost_arc.end, cost_arc.start))

    # STERNAL: the middle band between y_top and y_bot. Two arcs (left + right side)
    # plus two horizontal closures. Find arcs between T_top and T_bot crossings.
    # Sort all 4 T values, identify which arcs lie in y_top < y < y_bot.
    all_T = sorted(set([T_top[0], T_top[1], T_bot[0], T_bot[1]]))
    sternal_segments = []
    for i in range(len(all_T)):
        t_start = all_T[i]
        t_end = all_T[(i + 1) % len(all_T)]
        if t_end < t_start:
            # Wraps around end
            arc = Path(*p.cropped(t_start, 1.0)._segments, *p.cropped(0.0, t_end)._segments)
        else:
            arc = p.cropped(t_start, t_end)
        if len(arc._segments) == 0:
            continue
        mid_arc = arc.point(0.5)
        if y_top < mid_arc.imag < y_bot:
            sternal_segments.append(arc)
    # Build sternal closed loop: arc1 (left side, top→bot) + Line(y_bot) +
    # arc2 (right side, bot→top) + Line(y_top back to start)
    if len(sternal_segments) == 2:
        s1 = sternal_segments[0]
        s2 = sternal_segments[1]
        # Check if s2 starts near s1 end or vice versa via x coord
        if abs(s2.start.real - s1.end.real) < abs(s2.end.real - s1.end.real):
            # s2.start near s1.end → s1.end → s2.start direct line
            sternal_path = Path(
                *s1._segments,
                Line(s1.end, s2.start),
                *s2._segments,
                Line(s2.end, s1.start),
            )
        else:
            # reverse s2
            s2_rev = s2.reversed()
            sternal_path = Path(
                *s1._segments,
                Line(s1.end, s2_rev.start),
                *s2_rev._segments,
                Line(s2_rev.end, s1.start),
            )
    else:
        raise RuntimeError(f"{label}: expected 2 sternal arc segments, got {len(sternal_segments)}")

    return clav_path.d(), sternal_path.d(), cost_path.d()


for label, d in [("PEC_L", PEC_L), ("PEC_R", PEC_R)]:
    print(f"\n=== {label} ===")
    clav, stern, cost = slice_three(d, Y_TOP, Y_BOT, label)
    print(f"clavicular d= {clav}")
    print(f"sternal d= {stern}")
    print(f"costal d= {cost}")
