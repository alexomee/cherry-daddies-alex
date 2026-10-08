"""Test insert_bars logic in jamzone_render."""
import numpy as np
import pytest
import jamzone_render as JR
import jamzone_click as JC

SR = JR.SR


def test_insert_bars_click_and_stems():
    # Build a synthetic click track at 120 bpm (beat = 0.5s, bar = 2.0s)
    bpm = 120.0
    beat = 60.0 / bpm
    bar = 4 * beat
    n_bars = 10
    total_samples = int(n_bars * bar * SR)

    jdb = JC.wav_read(JC.DB)
    jdb = jdb / (np.max(np.abs(jdb)) or 1)
    jbt = JC.wav_read(JC.BT)
    jbt = jbt / (np.max(np.abs(jbt)) or 1)

    click = np.zeros((total_samples, 2), np.float32)
    for b in range(n_bars):
        for be in range(4):
            t = (b * 4 + be) * beat + 0.1  # downbeat offset 0.1s
            s = round(t * SR)
            hit = jdb if be == 0 else jbt * 0.5
            n = min(len(hit), total_samples - s)
            if s >= 0 and n > 0:
                click[s:s+n, 0] += hit[:n]
                click[s:s+n, 1] += hit[:n]

    # Stems: silence in bar 1, audio starting in bar 2 (at t = 2.1s)
    stem = np.zeros((total_samples, 2), np.float32)
    stem_start = round(2.1 * SR)
    stem[stem_start:, :] = 0.5

    orig_ons = JR.onsets(click.mean(1))
    assert len(orig_ons) == 40

    # Insert 4 bars at bar 2
    ins_bar = 2
    ins_count = 4
    idx_ins = (ins_bar - 1) * 4

    b_seed, _, _, _ = JR.fit_grid(click.mean(1))
    ins_beat = b_seed
    ins_bar_dur = 4.0 * ins_beat
    ins_samples = round(ins_count * ins_bar_dur * SR)

    t_prev = float(orig_ons[idx_ins - 1])
    t_next = float(orig_ons[idx_ins])
    t_split = (t_prev + t_next) / 2.0
    dt_left = t_split - t_prev
    s_ins_split = round(t_split * SR)

    g = float(np.abs(click).max())
    inserted_click = np.zeros((ins_samples, 2), np.float32)
    for k in range(ins_count * 4):
        rel_t = (k + 1) * ins_beat - dt_left
        s = round(rel_t * SR)
        hit = (jdb if k % 4 == 0 else jbt * 0.5) * g
        n = min(len(hit), ins_samples - s)
        if s >= 0 and n > 0:
            inserted_click[s:s+n, 0] += hit[:n]
            inserted_click[s:s+n, 1] += hit[:n]

    new_click = np.concatenate([click[:s_ins_split], inserted_click, click[s_ins_split:]])
    new_stem = np.concatenate([stem[:s_ins_split], np.zeros((ins_samples, 2), np.float32), stem[s_ins_split:]])

    new_ons = JR.onsets(new_click.mean(1))
    # 40 + 16 = 56 onsets
    assert len(new_ons) == 56

    # Verify fit_grid on new_click
    beat2, db02, resid2, n_on2 = JR.fit_grid(new_click.mean(1))
    assert n_on2 == 56
    assert abs(beat2 - beat) < 0.002
    assert resid2 < 0.01

    # Verify stem audio delayed by ins_samples
    assert np.all(new_stem[:stem_start + ins_samples] == 0)
    assert np.all(new_stem[stem_start + ins_samples:] == 0.5)
