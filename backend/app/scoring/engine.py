"""Scoring engine (FR-13 to FR-17). Pure and deterministic: the same inputs and config always give the
same output, which is what makes every report traceable to its scoring version."""

import statistics
from collections import defaultdict
from typing import Any

from app.scoring.config import merged
from app.scoring.features import extract, staircase_level
from app.scoring.root_cause import tag_errors
from app.scoring.skills import SKILL_IDS


def normalize(name: str, value: float, band: str, features_cfg: dict) -> float | None:
    spec = features_cfg.get(name)
    if spec is None:
        return None
    lo, hi = spec.get("bands", {}).get(band, [spec["lo"], spec["hi"]])
    if hi == lo:
        return None
    v = (value - lo) / (hi - lo)
    v = max(0.0, min(1.0, v))
    if spec.get("invert"):
        v = 1 - v
    return round(v * 100, 2)


def aggregate(rows: list[dict]) -> dict[str, dict]:
    """Average each feature across sessions and remember which sessions it came from."""
    grouped: dict[str, list[dict]] = defaultdict(list)
    for r in rows:
        grouped[r["name"]].append(r)
    out = {}
    for name, rs in grouped.items():
        out[name] = {
            "value": round(sum(r["value"] for r in rs) / len(rs), 4),
            "sessions": sorted({r["session"] for r in rs}),
            "channel": rs[0]["channel"],
        }
    return out


def evidence_level(n_agree: int, n_sessions: int) -> str:
    """High: 3 signals agree across 2+ sessions. Medium: 2 signals agree across 2+ sessions, or 3 in one
    session. Low: one signal, or a pattern seen in a single session only."""
    if n_agree >= 3 and n_sessions >= 2:
        return "High"
    if (n_agree >= 2 and n_sessions >= 2) or n_agree >= 3:
        return "Medium"
    return "Low"


def _sum(rows: list[dict], name: str) -> float:
    return sum(r["value"] for r in rows if r["name"] == name)


def score(inputs: dict[str, Any], config: dict | None = None, version: str = "") -> dict[str, Any]:
    cfg = merged(config)
    th = cfg["thresholds"]
    band = inputs["age_band"]
    events = sorted(inputs["events"], key=lambda e: (e["session"], e["seq"], e["id"]))
    client = sorted(
        inputs.get("client_features", []), key=lambda f: (f["session"], f["task"], f.get("item_id", ""), f["name"])
    )
    rows, ctx = extract(events, client, inputs.get("sessions", []), inputs.get("visits", []), th)
    agg = aggregate(rows)
    norm = {name: normalize(name, a["value"], band, cfg["features"]) for name, a in agg.items()}

    skills: dict[str, dict] = {}
    for skill in SKILL_IDS:
        signals = [(f, float(w)) for f, w in cfg["skills"].get(skill, []) if norm.get(f) is not None]
        weighted = [(f, w) for f, w in signals if w > 0]
        gate = None
        if skill == "calibration" and ctx["rated_items"] < th["calibration_min_items"]:
            gate = f"needs {th['calibration_min_items']} rated items, has {ctx['rated_items']}"
        if skill == "growth_mindset" and ctx["growth_events"] < th["growth_min_events"]:
            gate = f"needs {th['growth_min_events']} events, has {ctx['growth_events']}"
        if gate is None and (len(signals) < th["min_signals"] or not weighted):
            gate = f"needs {th['min_signals']} signals, has {len(signals)}"
        raw = None
        if gate is None:
            total_w = sum(w for _, w in weighted)
            raw = round(sum(norm[f] * w for f, w in weighted) / total_w, 2)
        skills[skill] = {
            "raw_score": raw,
            "score": raw,
            "signals": [
                {
                    "feature": f,
                    "weight": w,
                    "value": agg[f]["value"],
                    "norm": norm[f],
                    "sessions": agg[f]["sessions"],
                    "channel": agg[f]["channel"],
                }
                for f, w in signals
            ],
            "gate": gate,
            "language_adjusted": False,
        }

    # Language adjustment (FR-17): English-based scores are lifted when the Hindi/Hinglish version of the same
    # reasoning items scored clearly higher, so English ability is not misread as low ability.
    t23 = ctx.get("t23")
    language_gap = t23["gap"] if t23 else None
    text_lang = inputs.get("text_language", "en")
    adjusted = bool(language_gap is not None and language_gap > th["language_gap_threshold"] and text_lang == "en")
    if adjusted:
        for skill in th["language_adjusted_skills"]:
            s = skills[skill]
            if s["raw_score"] is not None:
                s["score"] = round(min(100.0, s["raw_score"] + th["language_adjust_factor"] * language_gap * 100), 2)
                s["language_adjusted"] = True

    # Relative profile (FR-15): each skill against the student's own average across all scored skills.
    scored = {k: v["score"] for k, v in skills.items() if v["score"] is not None}
    if scored:
        m = statistics.mean(scored.values())
        sd = max(statistics.pstdev(scored.values()) if len(scored) > 1 else 0.0, th["min_profile_sd"])
    else:
        m, sd = 0.0, th["min_profile_sd"]
    k, a = th["relative_sd"], th["agreement_sd"]
    for s in skills.values():
        if s["score"] is None:
            s.update(band="insufficient", evidence="Low", agreeing=0, agree_sessions=[])
            continue
        band_ = "strength" if s["score"] > m + k * sd else "grow" if s["score"] < m - k * sd else "typical"
        agree_sessions: set[int] = set()
        n_agree = 0
        for sig in s["signals"]:
            v = sig["norm"]
            agrees = (
                v > m + a * sd if band_ == "strength" else v < m - a * sd if band_ == "grow" else abs(v - m) <= k * sd
            )
            sig["agrees"] = agrees
            if agrees:
                n_agree += 1
                agree_sessions.update(sig["sessions"])
        s.update(
            band=band_,
            evidence=evidence_level(n_agree, len(agree_sessions)),
            agreeing=n_agree,
            agree_sessions=sorted(agree_sessions),
        )

    levels = {t: staircase_level([e for e in events if e["task"] == t]) for t in ("T1", "T5", "T6", "T10")}
    levels = {t: v for t, v in levels.items() if v is not None}
    t7_err = agg.get("t7.error_rate", {}).get("value")
    clean_events = [e for e in events if e["id"] not in ctx["distraction_ids"] or e.get("correct") is False]
    error_tags = tag_errors(clean_events, th, levels, t7_err)

    patterns = _patterns(rows, agg, ctx, th, error_tags, language_gap, adjusted)
    cues = _screening_cues(agg, ctx, th, skills, cfg["features"], band)
    for skill, skill_cues in cues.items():
        skills[skill]["cues"] = skill_cues

    return {
        "scoring_version": version,
        "features": rows,
        "aggregate": agg,
        "skills": skills,
        "profile": {"mean": round(m, 2), "sd": round(sd, 2), "scored_skills": len(scored)},
        "patterns": patterns,
        "error_tags": error_tags,
        "distraction_event_ids": sorted(ctx["distraction_ids"]),
        "flags": ctx["flags"],
        "language_gap": language_gap,
        "rated_items": ctx["rated_items"],
    }


def _patterns(rows, agg, ctx, th, error_tags, language_gap, adjusted) -> list[dict]:
    out = []
    # Confidence mismatch (calibration direction), needs enough rated items.
    if ctx["rated_items"] >= th["calibration_min_items"]:
        n_by_session = {r["session"]: r["value"] for r in rows if r["name"] == "conf.n"}
        gaps = {r["session"]: r["value"] for r in rows if r["name"] == "conf.gap"}
        total_n = sum(n_by_session.values()) or 1
        overall_gap = sum(gaps[s] * n_by_session.get(s, 0) for s in gaps) / total_n
        right_n, wrong_n = _sum(rows, "conf.right_n"), _sum(rows, "conf.wrong_n")
        unsure_correct, sure_wrong = _sum(rows, "conf.unsure_correct"), _sum(rows, "conf.sure_wrong")
        under_share = unsure_correct / right_n if right_n >= 10 else 0
        over_share = sure_wrong / wrong_n if wrong_n >= 8 else 0
        direction = None
        if overall_gap < -th["mismatch_gap"] or under_share >= th["unsure_correct_share"]:
            direction = "underconfident"
        if overall_gap > th["mismatch_gap"] or over_share >= th["sure_wrong_share"]:
            direction = "overconfident" if direction is None or overall_gap > 0 else direction
        if direction:
            sign = -1 if direction == "underconfident" else 1
            sessions = sorted(s for s, g in gaps.items() if sign * g >= th["mismatch_gap"] / 2)
            signals = [
                abs(overall_gap) >= th["mismatch_gap"],
                (under_share if direction == "underconfident" else over_share)
                >= (th["unsure_correct_share"] if direction == "underconfident" else th["sure_wrong_share"]),
                (agg.get("conf.resolution", {}).get("value", 1) < 0.1)
                if direction == "overconfident"
                else (agg.get("conf.mean", {}).get("value", 1) < 0.5),
            ]
            out.append(
                {
                    "type": "confidence_mismatch",
                    "direction": direction,
                    "evidence": evidence_level(sum(signals), len(sessions)),
                    "data": {
                        "gap": round(overall_gap, 3),
                        "unsure_correct": int(unsure_correct),
                        "right_n": int(right_n),
                        "sure_wrong": int(sure_wrong),
                        "wrong_n": int(wrong_n),
                        "sessions": sessions,
                    },
                }
            )
    # Pressure pattern: drop must repeat across sessions (5 and 7); one bad round alone is ignored.
    t17 = ctx.get("t17", {})
    if t17:
        over = sorted(s for s, r in t17.items() if r["drop"] >= th["pressure_drop_threshold"])
        signals = len(over)
        if agg.get("t17.change_skip_increase", {}).get("value", 0) > 0.05:
            signals += 1
        if agg.get("t17.rt_cv_change", {}).get("value", 0) > 0.05:
            signals += 1
        if over:
            relaxed = statistics.mean(t17[s]["relaxed"] for s in over)
            pressure = statistics.mean(t17[s]["pressure"] for s in over)
            out.append(
                {
                    "type": "pressure_pattern",
                    "evidence": evidence_level(signals, len(over)) if len(over) >= 2 else "Low",
                    "data": {"relaxed": round(relaxed, 3), "pressure": round(pressure, 3), "sessions": over},
                }
            )
    # Language adjustment.
    if adjusted and language_gap is not None:
        lb_tags = [t for t in error_tags if t["tag"] == "language_barrier"]
        t23 = ctx["t23"]
        checks = [
            (True, agg.get("t23.gap", {}).get("sessions", [])),
            (
                agg.get("t23.rt_ratio_inv", {}).get("value", 1) < 0.85,
                agg.get("t23.rt_ratio_inv", {}).get("sessions", []),
            ),
            (len(lb_tags) >= 2, sorted({t["session"] for t in lb_tags})),
            (agg.get("t8.reread_rate", {}).get("value", 0) >= 1.0, agg.get("t8.reread_rate", {}).get("sessions", [])),
            (agg.get("t7.error_rate", {}).get("value", 0) > 0.08, agg.get("t7.error_rate", {}).get("sessions", [])),
        ]
        signals = sum(1 for ok, _ in checks if ok)
        sessions = {s for ok, ss in checks if ok for s in ss}
        out.append(
            {
                "type": "language_adjustment",
                "evidence": evidence_level(signals, len(sessions)),
                "data": {
                    "native": round(t23["native"], 3),
                    "english": round(t23["en"], 3),
                    "gap": round(language_gap, 3),
                    "sessions": sorted(sessions),
                },
            }
        )
    return out


def _screening_cues(agg, ctx, th, skills, cfg_features, band) -> dict[str, list[str]]:
    def v(name):
        return agg.get(name, {}).get("value")

    cues: dict[str, list[str]] = defaultdict(list)
    fs, bs = v("t1.forward_span"), v("t1.backward_span")
    if fs is not None and bs is not None and fs - bs >= 3:
        cues["working_memory"].append("forward_fine_backward_low")
    imm, ret = v("t2.immediate_acc"), v("t2.retention")
    if imm is not None and ret is not None and imm >= 0.75 and ret < 0.6:
        cues["long_term_recall"].append("learns_not_retains")
    if (v("t3.decline_after_2") or 0) >= 0.2 and (v("all.distraction_rate") or 0) > 0.05:
        cues["sustained_attention"].append("decline_after_minute_2")
    for withheld in ctx["flags"].get("speed_withheld", []):
        name = f"{withheld['task'].lower()}.median_rt_correct"
        spec = cfg_features.get(name)
        if spec:
            fast = normalize(name, withheld["median_rt"], band, cfg_features)
            if fast is not None and fast >= 60:
                cues["processing_speed"].append("fast_but_inaccurate")
                break
    sc, lc = v("t5.short_chain_acc"), v("t5.long_chain_acc")
    if sc is not None and lc is not None and sc >= 0.75 and lc <= 0.4:
        cues["logical_reasoning"].append("long_chains_check_memory")
    sa, ra = v("t6.sequence_acc"), v("t6.rotation_acc")
    if sa is not None and ra is not None and abs(sa - ra) >= 0.3:
        cues["pattern_spatial"].append("sequence_rotation_split")
    di, inf = v("t8.direct_acc"), v("t8.inference_acc")
    if di is not None and inf is not None and di >= 0.75 and inf <= 0.5:
        cues["reading_comprehension"].append("surface_reading")
    comp = v("t8.comprehension")
    silent = skills["reading_fluency"]["signals"]
    silent_norm = next((s["norm"] for s in silent if s["feature"] == "t8.silent_time_per_100w"), None)
    if silent_norm is not None and comp is not None:
        if silent_norm < 35 and comp >= 0.7:
            cues["reading_fluency"].append("slow_but_accurate")
        elif silent_norm > 75 and comp < 0.5:
            cues["reading_fluency"].append("skimming")
    rec, far = v("t12.recall_acc"), v("t12.far_acc")
    if rec is not None and far is not None and rec >= 0.75 and far <= 0.4:
        cues["concept_transfer"].append("memorizes_not_applies")
    if (v("t14.plan_ratio") or 1) < 0.1 and (v("t14.restarts") or 0) >= 1.5:
        cues["strategy_planning"].append("starts_instantly_restarts")
    if (v("all.net_changes") or 0) < 0:
        cues["error_detection"].append("changes_right_to_wrong")
    if (v("t16.front_load") or 0) >= 0.6:
        cues["time_management"].append("front_loads")
    if (v("conf.mean") or 1) < 0.45 and (v("conf.gap") or 0) < -0.15:
        cues["confidence"].append("underconfident_good_news")
    if (v("t18.after_error_easy") or 0) >= 0.75:
        cues["motivation"].append("avoids_after_error")
    if (v("all.post_error_acc") or 1) <= 0.4:
        cues["resilience"].append("post_error_drop")
    if v("t20.retry_rate") is not None and v("t20.retry_rate") <= 0.3:
        cues["growth_mindset"].append("tends_to_avoid_retrying")
    if (v("t21.study_days") or 0) >= 5 and v("log.return_rate") == 0:
        cues["study_consistency"].append("reports_daily_no_returns")
    if v("t22.voice_share") is not None and v("t22.voice_share") < 0.3 and (v("t22.answered_rate") or 0) > 0.5:
        cues["communication"].append("prefers_typing")
    if v("t11.voice_share") is not None and v("t22.voice_share") is not None:
        cues["expression"].append("prefers_speaking" if v("t22.voice_share") >= 0.5 else "prefers_typing")
    return dict(cues)
