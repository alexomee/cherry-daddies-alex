"""Read-only loudness comparison of Alex's Logic bounce against current pb-other.

Run with Python + numpy. ffmpeg supplies decoded PCM and EBU R128/true-peak.
400ms / 100ms gated mono RMS matches the documented renderer measurement.
"""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import json
import re
import subprocess
import numpy as np

HERE=Path(__file__).resolve().parent
SONGS=HERE.parents[2]
SOURCE=Path('/Users/alex/Documents/kukla_kolduna_pb_other.mp3')


def db(power):
    return float(10*np.log10(max(float(power),1e-20)))


def measure(path):
    command=['ffmpeg','-hide_banner','-nostats','-i',str(path),'-af','ebur128=peak=true',
             '-f','null','-']
    process=subprocess.run(command,capture_output=True,text=True,check=True)
    summary=process.stderr.rsplit('Summary:',1)[-1]
    def metric(pattern):
        return float(re.search(pattern,summary).group(1))
    pcm=subprocess.run(['ffmpeg','-v','error','-i',str(path),'-f','f32le','-ar','22050',
                        '-ac','2','-'],capture_output=True,check=True).stdout
    x=np.frombuffer(pcm,dtype=np.float32).reshape(-1,2).astype(np.float64)
    sr=22050; win=round(.4*sr); hop=round(.1*sr)
    starts=np.arange(0,len(x)-win+1,hop)
    def windows(power):
        cs=np.r_[0.,np.cumsum(power)]
        return (cs[starts+win]-cs[starts])/win
    mono=windows(x.mean(axis=1)**2)
    stereo=windows((x*x).mean(axis=1))
    gate=mono>=mono.max()*.01
    sgate=stereo>=stereo.max()*.01
    # Short-term (3s) loudness from ffmpeg, same relative gate used by R128 I.
    integrated=metric(r'I:\s+([-\d.]+) LUFS')
    st=np.array([float(s) for s in re.findall(r'\bS:\s*([-\d.]+)',process.stderr)])
    st=st[st>max(-70,integrated-10)]
    config={}
    if path.name=='pb-other.wav':
        config=json.loads((path.parent.parent/'mix.json').read_text()).get('pb-other') or {}
    result={
        'name':'NEW: Kukla Logic bounce' if path==SOURCE else path.parent.parent.name,
        'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
        'duration_s':round(len(x)/sr,3),'integrated_lufs':integrated,
        'lra_lu':metric(r'LRA:\s+([-\d.]+) LU'),
        'true_peak_dbtp':metric(r'Peak:\s+([-\d.]+) dBFS'),
        'gated_mono_rms_dbfs':round(db(mono[gate].mean()),2),
        'gated_stereo_rms_dbfs':round(db(stereo[sgate].mean()),2),
        'active_window_fraction':round(float(gate.mean()),3),
        'rms_400ms_p95_dbfs':round(db(np.percentile(stereo[sgate],95)),2),
        'short_term_p95_lufs':round(float(np.percentile(st,95)),2) if len(st) else None,
        'short_term_max_lufs':round(float(st.max()),2) if len(st) else None,
        'config':config,
    }
    if path==SOURCE:
        segments=[]
        for t in range(0,int(len(x)/sr),10):
            indices=(starts/sr>=t)&(starts/sr<t+10)&sgate
            segments.append({'start_s':t,'end_s':min(t+10,len(x)/sr),
                             'active_rms_dbfs':round(db(stereo[indices].mean()),2) if indices.any() else None})
        result['segments_10s']=segments
    return result


if __name__=='__main__':
    paths=[SOURCE]+sorted(SONGS.glob('*/auto-render/pb-other.wav'))
    assert len(paths)>20, (SONGS,len(paths))
    with ThreadPoolExecutor(max_workers=4) as pool:
        results=list(pool.map(measure,paths))
    (HERE/'measurements.json').write_text(json.dumps(results,ensure_ascii=False,indent=2)+'\n')
    for r in sorted(results,key=lambda r:r['integrated_lufs'],reverse=True):
        print(f"{r['integrated_lufs']:6.1f} LUFS | {r['true_peak_dbtp']:5.1f} dBTP | RMS {r['gated_mono_rms_dbfs']:6.2f} | S95 {r['short_term_p95_lufs']:6.2f} | {r['name']}")
